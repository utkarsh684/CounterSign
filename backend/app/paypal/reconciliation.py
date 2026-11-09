"""PayPal Payout Status Reconciliation via official GET endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.ledger.audit_service import AuditService
from app.models.paypal import PayPalPayout
from app.paypal.client import PayPalClient


class PayPalReconciliationService:
    @classmethod
    async def reconcile_payout_batch(cls, db: Session, payout_id: str) -> PayPalPayout:
        """Polls official PayPal GET /v1/payments/payouts/{batch_id} to reconcile status."""
        payout = db.query(PayPalPayout).filter(PayPalPayout.id == payout_id).first()
        if not payout:
            raise ValueError(f"PayPal payout '{payout_id}' not found")

        if not payout.paypal_batch_id:
            return payout

        batch_data = await PayPalClient.get_payout_batch(payout.paypal_batch_id)
        header = batch_data.get("batch_header", {})
        batch_status = header.get("batch_status", payout.batch_status)
        payout.batch_status = batch_status

        items = batch_data.get("items", [])
        if items:
            first_item = items[0]
            item_status = first_item.get("transaction_status", payout.item_status)
            payout.item_status = item_status
            payout.paypal_payout_item_id = first_item.get("payout_item_id")

            if item_status == "SUCCESS":
                payout.reconciled_at = datetime.now(timezone.utc)
                if payout.approval_decision and payout.approval_decision.payment_request:
                    payout.approval_decision.payment_request.status = "EXECUTED"
            elif item_status in ["FAILED", "BLOCKED", "RETURNED"]:
                payout.reconciled_at = datetime.now(timezone.utc)
                if payout.approval_decision and payout.approval_decision.payment_request:
                    payout.approval_decision.payment_request.status = "FAILED"

        db.commit()
        db.refresh(payout)

        AuditService.record_event(
            db=db,
            event_type="PAYPAL_POLL_RECONCILED",
            summary=f"Polled reconciliation for batch {payout.paypal_batch_id}: Status {payout.item_status}",
            payload={"batch_status": payout.batch_status, "item_status": payout.item_status},
            paypal_payout_id=payout.id,
        )

        return payout
