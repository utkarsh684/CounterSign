"""AI Mandate Management Routes."""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.ai.mandate_compiler import MandateCompilerService
from app.core.dependencies import get_current_owner, get_db
from app.core.security import compute_mandate_hmac
from app.ledger.audit_service import AuditService
from app.models.mandate import Mandate, MandateVersion
from app.models.user import User
from app.schemas.mandate import (
    MandateActivateRequest,
    MandateCompileRequest,
    MandateCompileResponse,
    MandateResponse,
    MandateVersionResponse,
)

router = APIRouter(prefix="/mandates", tags=["AI Spending Mandates"])


@router.post("/compile", response_model=MandateCompileResponse)
async def compile_mandate_from_prompt(
    request: MandateCompileRequest,
    owner: User = Depends(get_current_owner),
):
    """Compiles natural-language instructions into structured, Pydantic-validated constraints."""
    return await MandateCompilerService.compile_mandate(request)


@router.get("", response_model=List[MandateResponse])
def list_mandates(owner: User = Depends(get_current_owner), db: Session = Depends(get_db)):
    mandates = db.query(Mandate).filter(Mandate.user_id == owner.id).all()
    results = []
    for m in mandates:
        active_ver = m.versions[0] if m.versions else None
        res = MandateResponse(
            id=m.id,
            title=m.title,
            natural_language_prompt=m.natural_language_prompt,
            status=m.status,
            current_version=m.current_version,
            created_at=m.created_at,
            updated_at=m.updated_at,
            active_version=MandateVersionResponse.model_validate(active_ver) if active_ver else None,
        )
        results.append(res)
    return results


@router.post("", response_model=MandateResponse, status_code=status.HTTP_201_CREATED)
def activate_mandate(
    data: MandateActivateRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Activates an AI compiled mandate with cryptographic HMAC signing."""
    # Deactivate any existing active mandate for this owner
    existing_actives = db.query(Mandate).filter(Mandate.user_id == owner.id, Mandate.status == "ACTIVE").all()
    for em in existing_actives:
        em.status = "REVOKED"

    mandate = Mandate(
        user_id=owner.id,
        title=data.title,
        natural_language_prompt=data.natural_language_prompt,
        status="ACTIVE",
        current_version=1,
    )
    db.add(mandate)
    db.flush()

    # Compute server-side HMAC signature of canonical mandate spec
    spec_dict = data.spec.model_dump()
    hmac_sig = compute_mandate_hmac(spec_dict)

    version = MandateVersion(
        mandate_id=mandate.id,
        version=1,
        currency_allowlist=data.spec.currency_allowlist,
        per_transaction_limit_minor=data.spec.per_transaction_limit_minor,
        daily_limit_minor=data.spec.daily_limit_minor,
        weekly_limit_minor=data.spec.weekly_limit_minor,
        allowed_weekdays=data.spec.allowed_weekdays,
        allow_existing_payees_only=data.spec.allow_existing_payees_only,
        unknown_payee_action=data.spec.unknown_payee_action,
        third_party_evidence_limit_minor=data.spec.third_party_evidence_limit_minor,
        human_confirmation_required=True,
        compiler_explanation=data.explanation,
        compiler_rules_breakdown=[r.model_dump() for r in data.rules_breakdown],
        hmac_signature=hmac_sig,
        authorized_by_user_id=owner.id,
    )
    db.add(version)
    db.commit()
    db.refresh(mandate)

    # Record tamper-evident audit entry
    AuditService.record_event(
        db=db,
        event_type="MANDATE_ACTIVATED",
        summary=f"Activated Spending Mandate: '{mandate.title}' (v1)",
        payload={
            "mandate_id": mandate.id,
            "version": 1,
            "per_tx_minor": data.spec.per_transaction_limit_minor,
            "weekly_minor": data.spec.weekly_limit_minor,
            "currencies": data.spec.currency_allowlist,
            "hmac": hmac_sig,
        },
        user_id=owner.id,
    )

    return MandateResponse(
        id=mandate.id,
        title=mandate.title,
        natural_language_prompt=mandate.natural_language_prompt,
        status=mandate.status,
        current_version=1,
        created_at=mandate.created_at,
        updated_at=mandate.updated_at,
        active_version=MandateVersionResponse.model_validate(version),
    )


@router.post("/{mandate_id}/revoke", response_model=MandateResponse)
def revoke_mandate(
    mandate_id: str,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id, Mandate.user_id == owner.id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")

    mandate.status = "REVOKED"
    db.commit()

    AuditService.record_event(
        db=db,
        event_type="MANDATE_REVOKED",
        summary=f"Revoked Spending Mandate '{mandate.title}'",
        payload={"mandate_id": mandate.id},
        user_id=owner.id,
    )

    active_ver = mandate.versions[0] if mandate.versions else None
    return MandateResponse(
        id=mandate.id,
        title=mandate.title,
        natural_language_prompt=mandate.natural_language_prompt,
        status=mandate.status,
        current_version=mandate.current_version,
        created_at=mandate.created_at,
        updated_at=mandate.updated_at,
        active_version=MandateVersionResponse.model_validate(active_ver) if active_ver else None,
    )
