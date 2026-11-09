"""Security Kill Switch and Alerts Routes."""

from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dependencies import get_current_owner, get_db
from app.ledger.audit_service import AuditService
from app.models.audit import SecurityAlert
from app.models.user import User

router = APIRouter(prefix="/security", tags=["Security & Kill Switch"])


class KillSwitchToggleRequest(BaseModel):
    enabled: bool
    reason: str = "Owner manual security override"


@router.post("/kill-switch")
def toggle_kill_switch(
    data: KillSwitchToggleRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Owner-only global kill switch. Immediately blocks all gateway payouts."""
    settings.KILL_SWITCH_ENABLED = data.enabled

    alert_title = "Global Security Kill Switch ACTIVATED" if data.enabled else "Global Security Kill Switch DEACTIVATED"
    severity = "CRITICAL" if data.enabled else "INFO"

    AuditService.record_security_alert(
        db=db,
        title=alert_title,
        details=f"Owner '{owner.email}' toggled kill switch: {data.reason}",
        source="KILL_SWITCH",
        severity=severity,
    )

    AuditService.record_event(
        db=db,
        event_type="KILL_SWITCH_TOGGLED",
        summary=f"Kill switch set to {data.enabled} by owner",
        payload={"enabled": data.enabled, "reason": data.reason},
        user_id=owner.id,
    )

    return {
        "kill_switch_enabled": settings.KILL_SWITCH_ENABLED,
        "message": f"Global kill switch is now {'ACTIVE' if settings.KILL_SWITCH_ENABLED else 'INACTIVE'}.",
    }


@router.get("/status")
def get_security_status():
    return {
        "kill_switch_enabled": settings.KILL_SWITCH_ENABLED,
        "sandbox_environment_lock": True,
        "ai_direct_payout_execution": False,  # Strict boundary
        "rate_limiting_active": True,
    }


@router.get("/alerts")
def get_security_alerts(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    alerts = db.query(SecurityAlert).order_by(SecurityAlert.created_at.desc()).limit(50).all()
    return [
        {
            "id": a.id,
            "severity": a.severity,
            "title": a.title,
            "details": a.details,
            "source": a.source,
            "is_resolved": a.is_resolved,
            "created_at": a.created_at,
        }
        for a in alerts
    ]
