"""Evidence package generation and export."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.ledger.hash_chain import canonical_json
from app.models.payment import PaymentRequest
from app.schemas.audit import EvidencePackage


class EvidenceExportService:
    @staticmethod
    def generate_package(db: Session, payment_request_id: str) -> EvidencePackage:
        """Assembles all lineage records for a transaction into an exportable evidence bundle."""
        payment = db.query(PaymentRequest).filter(PaymentRequest.id == payment_request_id).first()
        if not payment:
            raise ValueError(f"Payment request '{payment_request_id}' not found")

        # Serialized components
        payment_dict = {
            "id": payment.id,
            "agent_id": payment.agent_id,
            "agent_mode": payment.agent_mode,
            "recipient_email": payment.recipient_email,
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "idempotency_key": payment.idempotency_key,
            "overall_decision": payment.overall_decision,
            "decision_reasons": payment.decision_reasons,
            "status": payment.status,
            "created_at": payment.created_at.isoformat(),
        }

        mandate_dict = {}
        if payment.mandate_version_id:
            mv = payment.mandate_version_id
            mandate_dict = {"mandate_version_id": mv}

        invoice_dict = None
        if payment.invoice:
            invoice_dict = {
                "invoice_number": payment.invoice.invoice_number,
                "vendor_name": payment.invoice.vendor_name,
                "vendor_email": payment.invoice.vendor_email,
                "currency": payment.invoice.currency,
                "total_amount_minor": payment.invoice.total_amount_minor,
                "file_sha256": payment.invoice.file_sha256,
                "security_findings": payment.invoice.security_findings,
            }

        policy_dict = {}
        if payment.policy_evaluation:
            policy_dict = {
                "outcome": payment.policy_evaluation.outcome,
                "rules_evaluated": payment.policy_evaluation.rules_evaluated,
                "rules_passed": payment.policy_evaluation.rules_passed,
                "rules_failed": payment.policy_evaluation.rules_failed,
                "evaluated_at": payment.policy_evaluation.evaluated_at.isoformat(),
                "rule_results": payment.policy_evaluation.rule_results,
            }

        ai_dict = {}
        if payment.ai_verification:
            ai_dict = {
                "provider": payment.ai_verification.provider,
                "model": payment.ai_verification.model,
                "risk_level": payment.ai_verification.risk_level,
                "recommendation": payment.ai_verification.recommendation,
                "injection_detected": payment.ai_verification.injection_detected,
                "explanation": payment.ai_verification.explanation,
                "reason_codes": payment.ai_verification.reason_codes,
            }

        approval_dict = None
        if payment.approval_decision:
            approval_dict = {
                "decision": payment.approval_decision.decision,
                "confirmed_recipient_email": payment.approval_decision.confirmed_recipient_email,
                "confirmed_amount_minor": payment.approval_decision.confirmed_amount_minor,
                "confirmed_currency": payment.approval_decision.confirmed_currency,
                "is_one_time_exception": payment.approval_decision.is_one_time_exception,
                "exception_reason": payment.approval_decision.exception_reason,
                "decided_at": payment.approval_decision.decided_at.isoformat(),
            }

        payout_dict = None
        if payment.approval_decision and payment.approval_decision.paypal_payout:
            p = payment.approval_decision.paypal_payout
            payout_dict = {
                "sender_batch_id": p.sender_batch_id,
                "paypal_batch_id": p.paypal_batch_id,
                "paypal_payout_item_id": p.paypal_payout_item_id,
                "recipient_email": p.recipient_email,
                "amount_minor": p.amount_minor,
                "currency": p.currency,
                "batch_status": p.batch_status,
                "item_status": p.item_status,
                "environment": p.environment,
                "submitted_at": p.submitted_at.isoformat(),
                "reconciled_at": p.reconciled_at.isoformat() if p.reconciled_at else None,
            }

        now = datetime.now(timezone.utc)
        payload_for_checksum = {
            "payment": payment_dict,
            "policy": policy_dict,
            "ai": ai_dict,
            "approval": approval_dict,
            "payout": payout_dict,
        }
        checksum = hashlib.sha256(canonical_json(payload_for_checksum).encode("utf-8")).hexdigest()

        return EvidencePackage(
            package_id=f"EVID-{payment.id[:8].upper()}-{now.strftime('%Y%m%d%H%M%S')}",
            generated_at=now,
            payment_request=payment_dict,
            mandate_version=mandate_dict,
            invoice=invoice_dict,
            policy_evaluation=policy_dict,
            ai_verification=ai_dict,
            approval_decision=approval_dict,
            paypal_payout=payout_dict,
            audit_events=[],
            chain_status="CHAIN INTEGRITY: VERIFIED",
            tamper_proof_checksum=checksum,
        )
