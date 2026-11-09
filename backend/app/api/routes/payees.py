"""Payee Registry Management Routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_owner, get_db
from app.ledger.audit_service import AuditService
from app.models.payee import Payee
from app.models.user import User
from app.schemas.payee import PayeeCreate, PayeeResponse, PayeeUpdate

router = APIRouter(prefix="/payees", tags=["Payee Registry"])


@router.get("", response_model=List[PayeeResponse])
def list_payees(owner: User = Depends(get_current_owner), db: Session = Depends(get_db)):
    payees = db.query(Payee).filter(Payee.user_id == owner.id).order_by(Payee.name.asc()).all()
    return [PayeeResponse.model_validate(p) for p in payees]


@router.post("", response_model=PayeeResponse, status_code=status.HTTP_201_CREATED)
def create_payee(
    data: PayeeCreate,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    existing = db.query(Payee).filter(
        Payee.user_id == owner.id,
        Payee.paypal_email == data.paypal_email.lower().strip(),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payee with email '{data.paypal_email}' already exists in registry",
        )

    payee = Payee(
        user_id=owner.id,
        name=data.name,
        paypal_email=data.paypal_email.lower().strip(),
        category=data.category,
        verification_status="VERIFIED",
        trust_status=data.trust_status,
        risk_flags=[],
    )
    db.add(payee)
    db.commit()
    db.refresh(payee)

    AuditService.record_event(
        db=db,
        event_type="PAYEE_REGISTERED",
        summary=f"Registered Payee '{payee.name}' ({payee.paypal_email})",
        payload={
            "payee_id": payee.id,
            "name": payee.name,
            "paypal_email": payee.paypal_email,
            "category": payee.category,
        },
        user_id=owner.id,
    )

    return PayeeResponse.model_validate(payee)


@router.put("/{payee_id}", response_model=PayeeResponse)
def update_payee(
    payee_id: str,
    data: PayeeUpdate,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    payee = db.query(Payee).filter(Payee.id == payee_id, Payee.user_id == owner.id).first()
    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    # CRITICAL: Changing email for existing registered payee must produce hard rejection
    if data.paypal_email and data.paypal_email.lower().strip() != payee.paypal_email.lower().strip():
        AuditService.record_security_alert(
            db=db,
            title="Payee Email Modification Attempt Rejected",
            details=f"Attempted to change email for payee '{payee.name}' from '{payee.paypal_email}' to '{data.paypal_email}'.",
            source="PAYEE_REGISTRY",
            severity="CRITICAL",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payee email cannot be altered in-place due to financial fraud prevention policy. Please create a new payee record.",
        )

    if data.name:
        payee.name = data.name
    if data.category:
        payee.category = data.category
    if data.trust_status:
        payee.trust_status = data.trust_status

    db.commit()
    db.refresh(payee)
    return PayeeResponse.model_validate(payee)


@router.post("/{payee_id}/block", response_model=PayeeResponse)
def block_payee(
    payee_id: str,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    payee = db.query(Payee).filter(Payee.id == payee_id, Payee.user_id == owner.id).first()
    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    payee.verification_status = "BLOCKED"
    db.commit()

    AuditService.record_event(
        db=db,
        event_type="PAYEE_BLOCKED",
        summary=f"Blocked Payee '{payee.name}' ({payee.paypal_email})",
        payload={"payee_id": payee.id},
        user_id=owner.id,
    )
    return PayeeResponse.model_validate(payee)
