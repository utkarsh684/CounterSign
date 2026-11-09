"""Tamper-Evident Audit Ledger and Evidence Export Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_owner, get_db
from app.ledger.audit_service import AuditService
from app.ledger.evidence_export import EvidenceExportService
from app.models.audit import AuditEvent
from app.models.user import User
from app.schemas.audit import AuditEventResponse, ChainVerificationResult, EvidencePackage

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Ledger"])


@router.get("", response_model=List[AuditEventResponse])
def get_audit_ledger(
    limit: int = Query(default=100, ge=1, le=1000),
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Returns chronological audit records with cryptographic SHA-256 hashes."""
    events = db.query(AuditEvent).order_by(AuditEvent.sequence_number.desc()).limit(limit).all()
    return [AuditEventResponse.model_validate(e) for e in events]


@router.get("/verify", response_model=ChainVerificationResult)
def verify_hash_chain_integrity(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Traverses all audit events from genesis and verifies SHA-256 link validity."""
    return AuditService.verify_ledger_integrity(db)


@router.get("/{payment_id}/evidence", response_model=EvidencePackage)
def get_payment_evidence_package(
    payment_id: str,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Generates an exportable, tamper-proof JSON evidence bundle for a transaction."""
    try:
        return EvidenceExportService.generate_package(db, payment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/simulate-tamper")
def simulate_local_tamper(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Demonstration feature: Deliberately alters payload of latest audit record to demonstrate tamper detection."""
    latest = db.query(AuditEvent).order_by(AuditEvent.sequence_number.desc()).first()
    if not latest:
        raise HTTPException(status_code=400, detail="No audit records available to tamper with")

    latest.payload = {"tampered": True, "original": latest.payload}
    db.commit()
    return {
        "status": "TAMPER_SIMULATED",
        "message": f"Deliberately corrupted payload of audit record #{latest.sequence_number}. Run verification to witness detection.",
    }
