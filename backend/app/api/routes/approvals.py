"""Human Payment Approval Center Routes."""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_owner, get_db
from app.core.exceptions import PolicyViolationException
from app.ledger.audit_service import AuditService
from app.models.approval import ApprovalDecision
from app.models.payment import PaymentRequest
from app.models.user import User
from app.paypal.payouts import PayPalPayoutService
from app.policy.money import minor_units_to_decimal
from app.schemas.approval import ApprovalConfirmRequest, ApprovalResponse, RejectionRequest

router = APIRouter(prefix="/approvals", tags=["Payment Approval Center"])


@router.get("", response_model=List[ApprovalResponse])
def list_pending_approvals(owner: User = Depends(get_current_owner), db: Session = Depends(get_db)):
    # Returns all approval records
    approvals = db.query(ApprovalDecision).filter(ApprovalDecision.user_id == owner.id).order_by(ApprovalDecision.decided_at.desc()).all()
    return [ApprovalResponse.model_validate(a) for a in approvals]


@router.post("/{payment_id}/approve", response_model=ApprovalResponse)
async def approve_payment_request(
    payment_id: str,
    data: ApprovalConfirmRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    payment = db.query(PaymentRequest).filter(
        PaymentRequest.id == payment_id,
        PaymentRequest.user_id == owner.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment request not found")

    # Hard rejection cannot be approved
    if payment.overall_decision == "DENY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve a payment that received a deterministic DENY outcome.",
        )

    # Check for duplicate approval
    existing = db.query(ApprovalDecision).filter(ApprovalDecision.payment_request_id == payment_id).first()
    if existing:
        return ApprovalResponse.model_validate(existing)

    # Exact amount & recipient match check
    if data.confirmed_amount_minor != payment.amount_minor:
        raise HTTPException(
            status_code=400,
            detail=f"Confirmed amount ({data.confirmed_amount_minor}) does not match payment request amount ({payment.amount_minor})",
        )
    if data.confirmed_recipient_email.lower().strip() != payment.recipient_email.lower().strip():
        raise HTTPException(
            status_code=400,
            detail=f"Confirmed recipient email ({data.confirmed_recipient_email}) does not match requested recipient ({payment.recipient_email})",
        )

    # For high-value transactions (> $1,000 / 100,000 cents), require typed amount confirmation
    if payment.amount_minor >= 100000:
        expected_str = f"{minor_units_to_decimal(payment.amount_minor):.2f}"
        if not data.typed_amount_confirmation or data.typed_amount_confirmation.strip() != expected_str:
            raise HTTPException(
                status_code=400,
                detail=f"High-value payment requires typed confirmation matching '{expected_str}'",
            )

    approval = ApprovalDecision(
        payment_request_id=payment.id,
        user_id=owner.id,
        decision="APPROVED",
        confirmed_recipient_email=data.confirmed_recipient_email.lower().strip(),
        confirmed_amount_minor=data.confirmed_amount_minor,
        confirmed_currency=data.confirmed_currency.upper().strip(),
        typed_amount_confirmation=data.typed_amount_confirmation,
        is_one_time_exception=data.is_one_time_exception,
        exception_reason=data.exception_reason,
        notes=data.notes,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(approval)
    payment.status = "APPROVED"
    db.commit()
    db.refresh(approval)

    AuditService.record_event(
        db=db,
        event_type="PAYMENT_EXPLICITLY_APPROVED",
        summary=f"Owner approved payout of {payment.amount_minor} minor units to {approval.confirmed_recipient_email}",
        payload={
            "payment_id": payment.id,
            "amount_minor": approval.confirmed_amount_minor,
            "currency": approval.confirmed_currency,
            "recipient_email": approval.confirmed_recipient_email,
            "is_exception": approval.is_one_time_exception,
        },
        user_id=owner.id,
        payment_request_id=payment.id,
    )

    # Execute PayPal Sandbox Payout (Only for non-simulated requests)
    if not payment.is_simulated_attack:
        try:
            await PayPalPayoutService.execute_approved_payout(
                db=db,
                payment_request_id=payment.id,
                user_id=owner.id,
            )
        except Exception as e:
            # Re-read approval to return updated state
            db.refresh(approval)

    return ApprovalResponse.model_validate(approval)


@router.post("/{payment_id}/reject", response_model=ApprovalResponse)
def reject_payment_request(
    payment_id: str,
    data: RejectionRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    payment = db.query(PaymentRequest).filter(
        PaymentRequest.id == payment_id,
        PaymentRequest.user_id == owner.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment request not found")

    approval = ApprovalDecision(
        payment_request_id=payment.id,
        user_id=owner.id,
        decision="REJECTED",
        confirmed_recipient_email=payment.recipient_email,
        confirmed_amount_minor=payment.amount_minor,
        confirmed_currency=payment.currency,
        notes=data.reason,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(approval)
    payment.status = "REJECTED"
    db.commit()
    db.refresh(approval)

    AuditService.record_event(
        db=db,
        event_type="PAYMENT_REJECTED",
        summary=f"Owner rejected payout {payment.id[:8]}: {data.reason}",
        payload={"payment_id": payment.id, "reason": data.reason},
        user_id=owner.id,
        payment_request_id=payment.id,
    )
    return ApprovalResponse.model_validate(approval)
