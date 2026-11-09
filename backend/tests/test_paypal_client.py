"""Unit tests for PayPal Sandbox client, OAuth caching, and Webhook verification."""

from unittest.mock import AsyncMock, patch
import httpx
import pytest
from app.core.exceptions import PayPalIntegrationException
from app.paypal.client import PayPalClient
from app.paypal.oauth import PayPalOAuthManager


@pytest.mark.asyncio
async def test_paypal_connection_unconfigured():
    with patch("app.core.config.settings.PAYPAL_CLIENT_ID", None):
        res = await PayPalClient.test_connection()
        assert res["success"] is False
        assert "not configured" in res["message"]


@pytest.mark.asyncio
async def test_paypal_oauth_token_caching():
    with patch("app.core.config.settings.PAYPAL_CLIENT_ID", "mock_client_id"), \
         patch("app.core.config.settings.PAYPAL_CLIENT_SECRET", "mock_client_secret"):

        mock_resp = httpx.Response(
            200,
            json={"access_token": "mock_sandbox_access_token_12345", "expires_in": 3600},
            request=httpx.Request("POST", "https://api-m.sandbox.paypal.com/v1/oauth2/token"),
        )
        mock_post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient.post", mock_post):
            # First call: fetches fresh token
            token1 = await PayPalOAuthManager.get_access_token(force_refresh=True)
            assert token1 == "mock_sandbox_access_token_12345"

            # Second call: returns cached token without network request
            token2 = await PayPalOAuthManager.get_access_token(force_refresh=False)
            assert token2 == "mock_sandbox_access_token_12345"
            assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_paypal_payout_execution_mock():
    with patch("app.paypal.oauth.PayPalOAuthManager.get_access_token", AsyncMock(return_value="mock_token")):
        mock_resp = httpx.Response(
            201,
            json={
                "batch_header": {
                    "payout_batch_id": "PAYPAL_BATCH_9999",
                    "batch_status": "SUBMITTED",
                }
            },
            request=httpx.Request("POST", "https://api-m.sandbox.paypal.com/v1/payments/payouts"),
        )
        mock_post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient.post", mock_post):
            res = await PayPalClient.execute_payout(
                sender_batch_id="cs_batch_test",
                sender_item_id="cs_item_test",
                recipient_email="priya.sharma@contractor.example",
                amount_value="60.00",
                currency="USD",
            )
            assert res["batch_header"]["payout_batch_id"] == "PAYPAL_BATCH_9999"
            assert res["batch_header"]["batch_status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_webhook_signature_verification_mock():
    with patch("app.paypal.oauth.PayPalOAuthManager.get_access_token", AsyncMock(return_value="mock_token")), \
         patch("app.core.config.settings.PAYPAL_WEBHOOK_ID", "mock_webhook_id"):

        mock_resp = httpx.Response(
            200,
            json={"verification_status": "SUCCESS"},
            request=httpx.Request("POST", "https://api-m.sandbox.paypal.com/v1/notifications/verify-webhook-signature"),
        )
        mock_post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient.post", mock_post):
            is_valid = await PayPalClient.verify_webhook_signature(
                raw_headers={"paypal-transmission-id": "trans-1"},
                raw_body_json={"event_type": "PAYMENT.PAYOUTS-ITEM.SUCCEEDED"},
            )
            assert is_valid is True
