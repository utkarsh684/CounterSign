"""PayPal Webhook Ingress Endpoint."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.paypal.webhooks import PayPalWebhookService

router = APIRouter(tags=["PayPal Webhooks"])


@router.post("/api/webhooks/paypal")
@router.post("/api/v1/webhooks/paypal")
async def handle_paypal_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Ingests official PayPal Webhook notifications with signature verification and idempotency."""
    raw_headers = dict(request.headers)
    try:
        raw_body: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    success, message = await PayPalWebhookService.process_webhook(
        db=db,
        raw_headers=raw_headers,
        raw_body=raw_body,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"status": "SUCCESS", "message": message}
