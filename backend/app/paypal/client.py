"""Asynchronous HTTPX client for official PayPal Sandbox REST APIs.

Strictly targets https://api-m.sandbox.paypal.com.
Live endpoints are rejected by configuration.
"""

import time
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import PayPalIntegrationException
from app.core.logging import logger
from app.paypal.oauth import PayPalOAuthManager


class PayPalClient:
    @staticmethod
    async def _get_auth_headers(idempotency_key: Optional[str] = None) -> Dict[str, str]:
        token = await PayPalOAuthManager.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["PayPal-Request-Id"] = idempotency_key
        return headers

    @classmethod
    async def test_connection(cls) -> Dict[str, Any]:
        """Tests OAuth token acquisition and returns connection diagnostics."""
        start_time = time.perf_counter()
        if not settings.is_paypal_configured:
            return {
                "success": False,
                "message": "PayPal Sandbox credentials are not configured. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.",
                "environment": settings.PAYPAL_ENVIRONMENT,
                "latency_ms": 0,
            }

        try:
            token = await PayPalOAuthManager.get_access_token(force_refresh=True)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "success": True,
                "message": "Successfully authenticated with PayPal Sandbox OAuth 2.0 API.",
                "environment": settings.PAYPAL_ENVIRONMENT,
                "latency_ms": latency_ms,
            }
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "environment": settings.PAYPAL_ENVIRONMENT,
                "latency_ms": latency_ms,
            }

    @classmethod
    async def execute_payout(
        cls,
        sender_batch_id: str,
        sender_item_id: str,
        recipient_email: str,
        amount_value: str,
        currency: str,
        email_subject: str = "Payment via Countersign",
        note: str = "Authorized contractor payment",
    ) -> Dict[str, Any]:
        """Sends payout request to official PayPal Sandbox POST /v1/payments/payouts."""
        headers = await cls._get_auth_headers(idempotency_key=sender_batch_id)
        url = f"{settings.PAYPAL_BASE_URL}/v1/payments/payouts"

        payload = {
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": email_subject,
                "email_message": f"You have received a payment of {amount_value} {currency} via Countersign.",
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": amount_value,
                        "currency": currency,
                    },
                    "note": note,
                    "sender_item_id": sender_item_id,
                    "receiver": recipient_email,
                }
            ],
        }

        logger.info(f"Submitting PayPal Sandbox Payout: batch_id={sender_batch_id}, recipient={recipient_email}, amount={amount_value} {currency}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code not in [200, 201, 202]:
                    err_msg = f"PayPal Payout failed (HTTP {response.status_code}): {response.text}"
                    logger.error(err_msg)
                    raise PayPalIntegrationException(err_msg, details={"response_body": response.text})
                return response.json()
            except httpx.RequestError as exc:
                err_msg = f"Network failure communicating with PayPal Payouts API: {exc}"
                logger.error(err_msg)
                raise PayPalIntegrationException(err_msg) from exc

    @classmethod
    async def get_payout_batch(cls, payout_batch_id: str) -> Dict[str, Any]:
        """Reconciliation: Retrieves payout batch details by PayPal batch ID."""
        headers = await cls._get_auth_headers()
        url = f"{settings.PAYPAL_BASE_URL}/v1/payments/payouts/{payout_batch_id}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise PayPalIntegrationException(f"Failed to fetch payout batch {payout_batch_id}: {response.text}")
            return response.json()

    @classmethod
    async def verify_webhook_signature(
        cls,
        raw_headers: Dict[str, str],
        raw_body_json: Dict[str, Any],
    ) -> bool:
        """Verifies PayPal Webhook event signature using POST /v1/notifications/verify-webhook-signature."""
        if not settings.PAYPAL_WEBHOOK_ID:
            logger.warning("PAYPAL_WEBHOOK_ID is not configured. Webhook signature verification bypassed in mock/demo mode.")
            return True

        url = f"{settings.PAYPAL_BASE_URL}/v1/notifications/verify-webhook-signature"
        headers = await cls._get_auth_headers()

        verification_payload = {
            "transmission_id": raw_headers.get("paypal-transmission-id"),
            "transmission_time": raw_headers.get("paypal-transmission-time"),
            "cert_url": raw_headers.get("paypal-cert-url"),
            "auth_algo": raw_headers.get("paypal-auth-algo"),
            "transmission_sig": raw_headers.get("paypal-transmission-sig"),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": raw_body_json,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=verification_payload)
            if response.status_code == 200:
                verification_status = response.json().get("verification_status")
                return verification_status == "SUCCESS"
            return False
