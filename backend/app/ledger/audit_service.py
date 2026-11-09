"""Audit Service: Appends hash-chained records to the persistent ledger."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.ledger.hash_chain import (
    GENESIS_PREVIOUS_HASH,
    compute_audit_record_hash,
    verify_audit_chain,
)
from app.models.audit import AuditEvent, SecurityAlert
from app.schemas.audit import ChainVerificationResult


class AuditService:
    @staticmethod
    def record_event(
        db: Session,
        event_type: str,
        summary: str,
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
        payment_request_id: Optional[str] = None,
        paypal_payout_id: Optional[str] = None,
    ) -> AuditEvent:
        """Appends a cryptographically chained audit event to the ledger."""
        # Find the latest audit event in the chain
        latest_event = (
            db.query(AuditEvent)
            .order_by(AuditEvent.sequence_number.desc())
            .first()
        )

        if latest_event:
            next_seq = latest_event.sequence_number + 1
            prev_hash = latest_event.current_hash
        else:
            next_seq = 1
            prev_hash = GENESIS_PREVIOUS_HASH

        now = datetime.now(timezone.utc)
        ts_iso = now.isoformat()
        current_hash = compute_audit_record_hash(
            previous_hash=prev_hash,
            sequence_number=next_seq,
            event_type=event_type,
            timestamp_iso=ts_iso,
            payload=payload,
        )

        event = AuditEvent(
            sequence_number=next_seq,
            event_type=event_type,
            user_id=user_id,
            payment_request_id=payment_request_id,
            paypal_payout_id=paypal_payout_id,
            summary=summary,
            payload=payload,
            previous_hash=prev_hash,
            current_hash=current_hash,
            timestamp_iso=ts_iso,
            created_at=now,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def verify_ledger_integrity(db: Session) -> ChainVerificationResult:
        """Loads all audit events in sequence order and verifies the cryptographic chain."""
        events = db.query(AuditEvent).order_by(AuditEvent.sequence_number.asc()).all()
        records = [
            {
                "sequence_number": e.sequence_number,
                "event_type": e.event_type,
                "created_at": getattr(e, "timestamp_iso", e.created_at.isoformat() if hasattr(e.created_at, "isoformat") else str(e.created_at)),
                "payload": e.payload,
                "previous_hash": e.previous_hash,
                "current_hash": e.current_hash,
            }
            for e in events
        ]
        return verify_audit_chain(records)

    @staticmethod
    def record_security_alert(
        db: Session,
        title: str,
        details: str,
        source: str,
        severity: str = "WARNING",
    ) -> SecurityAlert:
        alert = SecurityAlert(
            title=title,
            details=details,
            source=source,
            severity=severity,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
