"""Payment Request Gateway: Secure Ingress for AI Agent Proposals."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.ai.intent_verifier import IntentVerifierService
from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.ledger.audit_service import AuditService
from app.models.invoice import Invoice
from app.models.mandate import Mandate, MandateVersion
from app.models.payee import Payee
from app.models.payment import AIVerification, PaymentRequest, PolicyEvaluation
from app.models.user import User
from app.policy.decision import PolicyOutcome, combine_decisions
from app.policy.engine import DeterministicPolicyEngine, PolicyContext
from app.schemas.payment import (
    AIVerificationResponse,
    PaymentRequestCreate,
    PaymentRequestResponse,
    PolicyEvaluationResponse,
)

router = APIRouter(prefix="/gateway", tags=["Payment Gateway"])


@router.post("/payments", response_model=PaymentRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_payment_request(
    data: PaymentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Idempotency Check
    existing = db.query(PaymentRequest).filter(PaymentRequest.idempotency_key == data.idempotency_key).first()
    if existing:
        return PaymentRequestResponse.model_validate(existing)

    # 2. Check for active mandate
    mandate = db.query(Mandate).filter(Mandate.user_id == current_user.id, Mandate.status == "ACTIVE").first()
    active_version = mandate.versions[0] if mandate and mandate.versions else None

    # 3. Payee lookup
    payee = db.query(Payee).filter(
        Payee.user_id == current_user.id,
        Payee.paypal_email == data.recipient_email.lower().strip(),
    ).first()

    # 4. Invoice lookup
    invoice = None
    if data.invoice_id:
        invoice = db.query(Invoice).filter(Invoice.id == data.invoice_id).first()

    # 5. Deterministic Policy Evaluation
    ctx = PolicyContext(
        amount_minor=data.amount_minor,
        currency=data.currency,
        recipient_email=data.recipient_email,
        mandate_status=mandate.status if mandate else "INACTIVE",
        is_mandate_revoked=mandate.status == "REVOKED" if mandate else False,
        currency_allowlist=active_version.currency_allowlist if active_version else ["USD"],
        per_transaction_limit_minor=active_version.per_transaction_limit_minor if active_version else 20000,
        daily_limit_minor=active_version.daily_limit_minor if active_version else 50000,
        weekly_limit_minor=active_version.weekly_limit_minor if active_version else 100000,
        allowed_weekdays=active_version.allowed_weekdays if active_version else [1, 2, 3, 4, 5],
        payee_registered=bool(payee),
        payee_verified=payee.verification_status == "VERIFIED" if payee else False,
        registered_payee_email=payee.paypal_email if payee else None,
        is_known_vendor=bool(payee),
        has_evidence=bool(invoice or not active_version or not active_version.allow_existing_payees_only),
        invoice_amount_minor=invoice.total_amount_minor if invoice else None,
        has_suspicious_text=bool(invoice.security_findings) if invoice else False,
        suspicious_snippet=invoice.security_findings[0].get("evidence_snippet") if (invoice and invoice.security_findings) else None,
        kill_switch_enabled=settings.KILL_SWITCH_ENABLED,
    )

    policy_res: PolicyEvaluationResponse = DeterministicPolicyEngine.evaluate(ctx)

    # 6. Independent AI Intent Verification
    mandate_summary = (
        f"Allowed currencies: {active_version.currency_allowlist if active_version else ['USD']}. "
        f"Per-tx limit: {active_version.per_transaction_limit_minor if active_version else 20000} minor units. "
        f"Weekly limit: {active_version.weekly_limit_minor if active_version else 100000} minor units."
    )

    ai_res: AIVerificationResponse = await IntentVerifierService.verify_payment_intent(
        recipient_email=data.recipient_email,
        amount_minor=data.amount_minor,
        currency=data.currency,
        mandate_summary=mandate_summary,
        invoice_text=invoice.raw_text if invoice else None,
        registered_payee_email=payee.paypal_email if payee else None,
    )

    # 7. Combine Decisions (AI can only make decision stricter, never override DENY)
    combined = combine_decisions(
        policy_decision=PolicyOutcome(policy_res.outcome),
        ai_risk_level=ai_res.risk_level,
    )

    status_str = (
        "AWAITING_APPROVAL" if combined in [PolicyOutcome.READY_FOR_APPROVAL, PolicyOutcome.ESCALATE]
        else "BLOCKED"
    )

    decision_reasons = [r.reason for r in policy_res.rule_results if not r.passed]
    if ai_res.recommendation != "CLEAR":
        decision_reasons.append(f"AI Security Verifier: {ai_res.explanation}")

    payment = PaymentRequest(
        user_id=current_user.id,
        invoice_id=data.invoice_id,
        payee_id=payee.id if payee else None,
        mandate_version_id=active_version.id if active_version else None,
        agent_id=data.agent_id,
        agent_mode=data.agent_mode,
        idempotency_key=data.idempotency_key,
        recipient_email=data.recipient_email,
        amount_minor=data.amount_minor,
        currency=data.currency,
        overall_decision=combined.value,
        decision_reasons=decision_reasons,
        status=status_str,
        is_simulated_attack=data.is_simulated_attack,
    )
    db.add(payment)
    db.flush()

    # Store policy evaluation record
    db_policy = PolicyEvaluation(
        payment_request_id=payment.id,
        outcome=policy_res.outcome,
        rules_evaluated=policy_res.rules_evaluated,
        rules_passed=policy_res.rules_passed,
        rules_failed=policy_res.rules_failed,
        rule_results=[r.model_dump() for r in policy_res.rule_results],
        latency_ms=policy_res.latency_ms,
    )
    db.add(db_policy)

    # Store AI verification record
    db_ai = AIVerification(
        payment_request_id=payment.id,
        provider=ai_res.provider,
        model=ai_res.model,
        risk_level=ai_res.risk_level,
        recommendation=ai_res.recommendation,
        injection_detected=ai_res.injection_detected,
        reason_codes=ai_res.reason_codes,
        evidence_references=ai_res.evidence_references,
        explanation=ai_res.explanation,
        latency_ms=ai_res.latency_ms,
    )
    db.add(db_ai)
    db.commit()
    db.refresh(payment)

    # Record tamper-evident audit event
    AuditService.record_event(
        db=db,
        event_type="PAYMENT_REQUEST_EVALUATED",
        summary=f"Gateway Evaluated Payment {payment.id[:8]}: Decision {payment.overall_decision}",
        payload={
            "payment_id": payment.id,
            "recipient_email": payment.recipient_email,
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "policy_outcome": policy_res.outcome,
            "ai_risk_level": ai_res.risk_level,
            "combined_decision": payment.overall_decision,
        },
        user_id=current_user.id,
        payment_request_id=payment.id,
    )

    return PaymentRequestResponse.model_validate(payment)


@router.get("/payments", response_model=List[PaymentRequestResponse])
def list_payment_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payments = db.query(PaymentRequest).filter(PaymentRequest.user_id == current_user.id).order_by(PaymentRequest.created_at.desc()).all()
    return [PaymentRequestResponse.model_validate(p) for p in payments]


@router.get("/payments/{payment_id}", response_model=PaymentRequestResponse)
def get_payment_request(payment_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(PaymentRequest).filter(PaymentRequest.id == payment_id, PaymentRequest.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment request not found")
    return PaymentRequestResponse.model_validate(p)
