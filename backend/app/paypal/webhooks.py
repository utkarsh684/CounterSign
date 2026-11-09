"""PayPal Webhook event processing and signature verification."""

from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import PayPalIntegrationException
from app.core.logging import logger
from app.ledger.audit_service import AuditService
from app.models.payment import PaymentRequest
from app.models.paypal import PayPalPayout, PayPalWebhookEvent
from app.paypal.client import PayPalClient


class PayPalWebhookService:
    @classmethod
    async def process_webhook(
        cls,
        db: Session,
        raw_headers: Dict[str, str],
        raw_body: Dict[str, Any],
    ) -> Tuple[bool, str]:
        event_id = raw_body.get("id")
        event_type = raw_body.get("event_type", "UNKNOWN")
        resource_type = raw_body.get("resource_type", "UNKNOWN")
        resource = raw_body.get("resource", {})

        if not event_id:
            return False, "Missing event id in webhook body"

        # 1. Deduplicate by PayPal event ID
        existing = db.query(PayPalWebhookEvent).filter(PayPalWebhookEvent.paypal_event_id == event_id).first()
        if existing:
            logger.info(f"Duplicate webhook event ignored: {event_id}")
            return True, "Duplicate event previously processed"

        # 2. Verify signature
        is_verified = await PayPalClient.verify_webhook_signature(raw_headers, raw_body)
        if not is_verified:
            logger.warning(f"PayPal webhook signature verification failed for event: {event_id}")
            # Record unverified event in audit for forensics
            AuditService.record_security_alert(
                db=db,
                title="Unverified PayPal Webhook Received",
                details=f"Event {event_id} ({event_type}) failed signature verification.",
                source="PAYPAL_WEBHOOK",
                severity="CRITICAL",
            )
            return False, "Invalid webhook signature"

        # 3. Store verified webhook event
        webhook_event = PayPalWebhookEvent(
            paypal_event_id=event_id,
            event_type=event_type,
            resource_type=resource_type,
            summary=raw_body.get("summary", ""),
            status="VERIFIED",
            transmission_id=raw_headers.get("paypal-transmission-id", ""),
            transmission_time=raw_headers.get("paypal-transmission-time", ""),
            signature_verification_status="SUCCESS",
            raw_headers=raw_headers,
            raw_payload=raw_body,
            created_at=datetime.now(timezone.utc),
        )
        db.add(webhook_event)
        db.commit()

        # 4. Map event to PayPalPayout record
        payout_item_id = resource.get("payout_item_id")
        payout_batch_id = resource.get("payout_batch_id")
        sender_batch_id = resource.get("sender_batch_id") or resource.get("sender_batch_header", {}).get("sender_batch_id")

        payout = None
        if payout_batch_id:
            payout = db.query(PayPalPayout).filter(PayPalPayout.paypal_batch_id == payout_batch_id).first()
        if not payout and sender_batch_id:
            payout = db.query(PayPalPayout).filter(PayPalPayout.sender_batch_id == sender_batch_id).first()
        if not payout and payout_item_id:
            payout = db.query(PayPalPayout).filter(PayPalPayout.paypal_payout_item_id == payout_item_id).first()

        now = datetime.now(timezone.utc)

        if payout:
            if payout_item_id and not payout.paypal_payout_item_id:
                payout.paypal_payout_item_id = payout_item_id

            if event_type == "PAYMENT.PAYOUTS-ITEM.SUCCEEDED":
                payout.item_status = "SUCCESS"
                payout.batch_status = "SUCCESS"
                payout.reconciled_at = now
                if payout.approval_decision and payout.approval_decision.payment_request:
                    payout.approval_decision.payment_request.status = "EXECUTED"

            elif event_type in ["PAYMENT.PAYOUTS-ITEM.FAILED", "PAYMENT.PAYOUTS-ITEM.BLOCKED", "PAYMENT.PAYOUTSBATCH.DENIED"]:
                payout.item_status = "FAILED"
                payout.batch_status = "DENIED"
                payout.reconciled_at = now
                if payout.approval_decision and payout.approval_decision.payment_request:
                    payout.approval_decision.payment_request.status = "FAILED"

            elif event_type == "PAYMENT.PAYOUTSBATCH.SUCCESS":
                payout.batch_status = "SUCCESS"
                payout.reconciled_at = now

            elif event_type == "PAYMENT.PAYOUTSBATCH.PROCESSING":
                payout.batch_status = "PROCESSING"

            db.commit()

            # Record hash-chained audit event
            AuditService.record_event(
                db=db,
                event_type="PAYPAL_WEBHOOK_RECONCILED",
                summary=f"Reconciled {event_type} for Payout batch {payout.sender_batch_id}: Status {payout.item_status}",
                payload={
                    "event_id": event_id,
                    "event_type": event_type,
                    "payout_id": payout.id,
                    "sender_batch_id": payout.sender_batch_id,
                    "item_status": payout.item_status,
                },
                paypal_payout_id=payout.id,
            )
            return True, f"Reconciled payout to {payout.item_status}"

        return True, "Event recorded (no matching local payout)"
