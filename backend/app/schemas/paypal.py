"""PayPal diagnostics and webhook schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class PayPalStatusResponse(BaseModel):
    environment: str = "SANDBOX"
    is_connected: bool
    client_id_configured: bool
    client_secret_configured: bool
    webhook_id_configured: bool
    token_valid: bool
    last_connection_test_at: Optional[datetime] = None
    last_successful_payout_at: Optional[datetime] = None
    last_error: Optional[str] = None
    sandbox_base_url: str = "https://api-m.sandbox.paypal.com"


class PayPalConnectionTestResponse(BaseModel):
    success: bool
    message: str
    environment: str
    token_expires_in: Optional[int] = None
    latency_ms: int


class WebhookReconcileResponse(BaseModel):
    event_id: str
    event_type: str
    signature_verified: bool
    action_taken: str
    payout_id: Optional[str] = None
    new_status: Optional[str] = None
