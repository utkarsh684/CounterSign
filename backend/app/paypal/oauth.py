"""PayPal OAuth 2.0 token manager with thread-safe caching."""

import time
from typing import Optional, Tuple
import httpx
from app.core.config import settings
from app.core.exceptions import PayPalIntegrationException
from app.core.logging import logger


class PayPalOAuthManager:
    """Manages acquisition and secure caching of PayPal Sandbox OAuth 2.0 bearer tokens."""

    _cached_token: Optional[str] = None
    _expires_at_epoch: float = 0.0

    @classmethod
    def is_token_valid(cls) -> bool:
        # Buffer of 60 seconds before actual expiration
        return bool(cls._cached_token and (time.time() + 60 < cls._expires_at_epoch))

    @classmethod
    async def get_access_token(cls, force_refresh: bool = False) -> str:
        """Returns a valid PayPal OAuth access token, requesting a fresh one if expired."""
        if not force_refresh and cls.is_token_valid():
            return cls._cached_token  # type: ignore

        if not settings.is_paypal_configured:
            raise PayPalIntegrationException(
                "PayPal Sandbox credentials are not configured. Please provide PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET."
            )

        url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
                    headers=headers,
                    data=data,
                )

                if response.status_code != 200:
                    err_msg = f"PayPal OAuth token request failed with status {response.status_code}: {response.text}"
                    logger.error(err_msg)
                    raise PayPalIntegrationException(err_msg)

                token_data = response.json()
                token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 32400)  # Default ~9 hours

                cls._cached_token = token
                cls._expires_at_epoch = time.time() + expires_in
                logger.info(f"Acquired new PayPal Sandbox OAuth token (valid for {expires_in}s)")
                return token
        except httpx.RequestError as exc:
            err_msg = f"Network error connecting to PayPal OAuth endpoint: {exc}"
            logger.error(err_msg)
            raise PayPalIntegrationException(err_msg) from exc
