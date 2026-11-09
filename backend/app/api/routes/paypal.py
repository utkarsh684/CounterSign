"""PayPal Sandbox Integration and Diagnostics Routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dependencies import get_current_owner, get_db
from app.models.paypal import PayPalPayout
from app.paypal.client import PayPalClient
from app.paypal.oauth import PayPalOAuthManager
from app.paypal.reconciliation import PayPalReconciliationService
from app.schemas.paypal import PayPalConnectionTestResponse, PayPalStatusResponse

router = APIRouter(prefix="/paypal", tags=["PayPal Sandbox Integration"])


@router.get("/status", response_model=PayPalStatusResponse)
def get_paypal_status(db: Session = Depends(get_db)):
    """Provides complete real-time diagnostics of the PayPal Sandbox connection."""
    latest_payout = db.query(PayPalPayout).order_by(PayPalPayout.submitted_at.desc()).first()

    return PayPalStatusResponse(
        environment=settings.PAYPAL_ENVIRONMENT,
        is_connected=settings.is_paypal_configured,
        client_id_configured=bool(settings.PAYPAL_CLIENT_ID),
        client_secret_configured=bool(settings.PAYPAL_CLIENT_SECRET),
        webhook_id_configured=bool(settings.PAYPAL_WEBHOOK_ID),
        token_valid=PayPalOAuthManager.is_token_valid(),
        last_successful_payout_at=latest_payout.submitted_at if latest_payout else None,
        last_error=None,
        sandbox_base_url=settings.PAYPAL_BASE_URL,
    )


@router.post("/test-connection", response_model=PayPalConnectionTestResponse)
async def test_paypal_connection(owner=Depends(get_current_owner)):
    """Initiates an on-demand live OAuth test against PayPal Sandbox API."""
    result = await PayPalClient.test_connection()
    return PayPalConnectionTestResponse(
        success=result["success"],
        message=result["message"],
        environment=result["environment"],
        token_expires_in=32400 if result["success"] else None,
        latency_ms=result["latency_ms"],
    )


@router.post("/payments/{payout_id}/reconcile")
async def reconcile_payout_status(
    payout_id: str,
    owner=Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Triggers an on-demand status reconciliation against PayPal Payouts API."""
    try:
        payout = await PayPalReconciliationService.reconcile_payout_batch(db, payout_id)
        return {
            "payout_id": payout.id,
            "sender_batch_id": payout.sender_batch_id,
            "paypal_batch_id": payout.paypal_batch_id,
            "batch_status": payout.batch_status,
            "item_status": payout.item_status,
            "reconciled_at": payout.reconciled_at,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
