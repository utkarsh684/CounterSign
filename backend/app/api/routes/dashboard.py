"""Financial Security Dashboard and SSE Streaming Routes."""

import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dependencies import get_current_owner, get_db
from app.models.approval import ApprovalDecision
from app.models.audit import AuditEvent, SecurityAlert
from app.models.mandate import Mandate
from app.models.payment import PaymentRequest
from app.models.paypal import PayPalPayout
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Live Financial Dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Calculates live financial and security statistics strictly from persisted records."""
    # Active Mandate
    active_mandate = db.query(Mandate).filter(Mandate.user_id == owner.id, Mandate.status == "ACTIVE").first()
    active_version = active_mandate.versions[0] if active_mandate and active_mandate.versions else None

    weekly_cap_minor = active_version.weekly_limit_minor if active_version else 100000

    # Payouts
    confirmed_payouts = db.query(PayPalPayout).filter(PayPalPayout.item_status == "SUCCESS").all()
    submitted_payouts = db.query(PayPalPayout).filter(PayPalPayout.item_status == "SUBMITTED").all()

    total_spent_minor = sum(p.amount_minor for p in confirmed_payouts)

    # Payment Requests counts
    pending_approvals = db.query(PaymentRequest).filter(
        PaymentRequest.user_id == owner.id,
        PaymentRequest.status == "AWAITING_APPROVAL",
    ).count()

    blocked_count = db.query(PaymentRequest).filter(
        PaymentRequest.user_id == owner.id,
        PaymentRequest.status == "BLOCKED",
    ).count()

    escalated_count = db.query(PaymentRequest).filter(
        PaymentRequest.user_id == owner.id,
        PaymentRequest.overall_decision == "ESCALATE",
    ).count()

    # Alerts & Audit
    recent_alerts = db.query(SecurityAlert).order_by(SecurityAlert.created_at.desc()).limit(5).all()
    recent_events = db.query(AuditEvent).order_by(AuditEvent.sequence_number.desc()).limit(10).all()

    return {
        "active_mandate_title": active_mandate.title if active_mandate else "No Active Mandate",
        "active_mandate_version": active_mandate.current_version if active_mandate else 0,
        "weekly_limit_minor": weekly_cap_minor,
        "weekly_spent_minor": total_spent_minor,
        "weekly_utilization_percent": round((total_spent_minor / weekly_cap_minor) * 100, 1) if weekly_cap_minor > 0 else 0.0,
        "pending_approvals_count": pending_approvals,
        "submitted_payouts_count": len(submitted_payouts),
        "confirmed_payouts_count": len(confirmed_payouts),
        "blocked_attacks_count": blocked_count,
        "escalated_requests_count": escalated_count,
        "paypal_connected": settings.is_paypal_configured,
        "kill_switch_active": settings.KILL_SWITCH_ENABLED,
        "environment": "SANDBOX",
        "recent_alerts": [
            {"id": a.id, "title": a.title, "severity": a.severity, "created_at": a.created_at}
            for a in recent_alerts
        ],
        "recent_audit_events": [
            {"seq": e.sequence_number, "type": e.event_type, "summary": e.summary, "hash": e.current_hash[:16]}
            for e in recent_events
        ],
    }


@router.get("/stream")
async def stream_dashboard_events():
    """SSE endpoint for live dashboard telemetry."""
    async def event_generator():
        while True:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kill_switch": settings.KILL_SWITCH_ENABLED,
                "status": "HEALTHY",
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
