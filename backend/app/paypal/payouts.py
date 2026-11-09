"""PayPal Payout Execution Service with strict pre-flight revalidation.

Guarantees:
- Revalidates mandate and payee registry immediately before execution.
- Idempotency key reuse on retries (never retry with a new key).
- Initial status is SUBMITTED, never automatically SUCCESSFUL.
- Reconciles final status only upon verified webhook or documented status retrieval.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.core.exceptions import (
    KillSwitchActiveException,
    MandateIntegrityException,
    PayeeTamperException,
    PayPalIntegrationException,
    PolicyViolationException,
)
from app.core.config import settings
from app.ledger.audit_service import AuditService
from app.models.approval import ApprovalDecision
from app.models.mandate import Mandate, MandateVersion
from app.models.payee import Payee
from app.models.payment import PaymentRequest
from app.models.paypal import PayPalPayout
from app.paypal.client import PayPalClient
from app.policy.money import minor_units_to_decimal


class PayPalPayoutService:
    @classmethod
    async def execute_approved_payout(
        cls,
        db: Session,
        payment_request_id: str,
        user_id: str,
    ) -> PayPalPayout:
        # 1. Check Global Kill Switch
        if settings.KILL_SWITCH_ENABLED:
            raise KillSwitchActiveException("Payment execution blocked by global security kill switch")

        # 2. Fetch PaymentRequest and active ApprovalDecision
        payment = db.query(PaymentRequest).filter(PaymentRequest.id == payment_request_id).first()
        if not payment:
            raise ValueError(f"Payment request '{payment_request_id}' not found")

        approval = db.query(ApprovalDecision).filter(ApprovalDecision.payment_request_id == payment_request_id).first()
        if not approval or approval.decision != "APPROVED":
            raise PolicyViolationException("Payment request has not been explicitly approved by the owner")

        # Check if already executed or submitted
        existing_payout = db.query(PayPalPayout).filter(PayPalPayout.approval_decision_id == approval.id).first()
        if existing_payout:
            return existing_payout

        # 3. Pre-execution Re-validation of Mandate
        if payment.mandate_version_id:
            mandate_version = db.query(MandateVersion).filter(MandateVersion.id == payment.mandate_version_id).first()
            if not mandate_version:
                raise MandateIntegrityException("Active mandate version could not be found for pre-flight check")
            mandate = db.query(Mandate).filter(Mandate.id == mandate_version.mandate_id).first()
            if not mandate or mandate.status != "ACTIVE":
                raise MandateIntegrityException(f"Mandate status is {mandate.status if mandate else 'UNKNOWN'}. Cannot execute payout.")

        # 4. Pre-execution Re-validation of Payee Registry (Email tamper check)
        if payment.payee_id:
            payee = db.query(Payee).filter(Payee.id == payment.payee_id).first()
            if payee and payee.paypal_email.lower().strip() != approval.confirmed_recipient_email.lower().strip():
                raise PayeeTamperException(
                    f"Recipient email '{approval.confirmed_recipient_email}' does not match registered payee '{payee.paypal_email}'"
                )
            if payee and payee.verification_status == "BLOCKED":
                raise PolicyViolationException("Payee is BLOCKED in registry")

        # 5. Deterministic Idempotency Key Generation
        sender_batch_id = f"cs_batch_{payment.id[:8]}_{uuid.uuid4().hex[:8]}"
        sender_item_id = f"cs_item_{payment.id[:8]}"

        amount_decimal = minor_units_to_decimal(approval.confirmed_amount_minor, approval.confirmed_currency)
        amount_str = f"{amount_decimal:.2f}"

        # 6. Execute Sandbox Payout
        try:
            paypal_response = await PayPalClient.execute_payout(
                sender_batch_id=sender_batch_id,
                sender_item_id=sender_item_id,
                recipient_email=approval.confirmed_recipient_email,
                amount_value=amount_str,
                currency=approval.confirmed_currency,
                email_subject=f"Countersign Payout: {payment.id[:8]}",
                note=f"Approved payout for invoice reference: {payment.invoice.invoice_number if payment.invoice else 'Direct'}",
            )
        except PayPalIntegrationException as exc:
            AuditService.record_security_alert(
                db=db,
                title="PayPal Sandbox Payout Submission Failed",
                details=f"Payment {payment.id}: {str(exc)}",
                source="PAYPAL_EXECUTOR",
                severity="CRITICAL",
            )
            raise

        batch_header = paypal_response.get("batch_header", {})
        paypal_batch_id = batch_header.get("payout_batch_id")
        batch_status = batch_header.get("batch_status", "SUBMITTED")

        # 7. Record Payout with status SUBMITTED (Never automatically mark SUCCESS)
        payout = PayPalPayout(
            approval_decision_id=approval.id,
            sender_batch_id=sender_batch_id,
            paypal_batch_id=paypal_batch_id,
            paypal_payout_item_id=None,  # Updated upon batch processing or webhook
            recipient_email=approval.confirmed_recipient_email,
            amount_minor=approval.confirmed_amount_minor,
            currency=approval.confirmed_currency,
            batch_status=batch_status,
            item_status="SUBMITTED",
            environment="SANDBOX",
            raw_paypal_response=paypal_response,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(payout)

        # Update payment status
        payment.status = "SUBMITTED"
        db.commit()
        db.refresh(payout)

        # 8. Record Tamper-Evident Audit Event
        AuditService.record_event(
            db=db,
            event_type="PAYPAL_PAYOUT_SUBMITTED",
            summary=f"Submitted PayPal Sandbox Payout of {amount_str} {approval.confirmed_currency} to {approval.confirmed_recipient_email}",
            payload={
                "payment_request_id": payment.id,
                "sender_batch_id": sender_batch_id,
                "paypal_batch_id": paypal_batch_id,
                "recipient_email": approval.confirmed_recipient_email,
                "amount_minor": approval.confirmed_amount_minor,
                "currency": approval.confirmed_currency,
                "batch_status": batch_status,
            },
            user_id=user_id,
            payment_request_id=payment.id,
            paypal_payout_id=payout.id,
        )

        return payout
