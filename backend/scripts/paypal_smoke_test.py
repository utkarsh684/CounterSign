"""PayPal Sandbox Smoke Test Script.

Performs live diagnostics against the official PayPal Sandbox REST API:
1. Validates presence of PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.
2. Performs OAuth 2.0 Client Credentials token exchange (POST /v1/oauth2/token).
3. Validates sandbox base URL lock (https://api-m.sandbox.paypal.com).
4. Prints exact manual setup checklist if credentials are not configured.
"""

import asyncio
import os
import sys
from app.core.config import settings
from app.paypal.client import PayPalClient


async def main():
    print("=" * 70)
    print(" COUNTERSIGN: PAYPAL SANDBOX INTEGRATION SMOKE TEST")
    print("=" * 70)
    print(f"Target Environment : {settings.PAYPAL_ENVIRONMENT}")
    print(f"Target Base URL    : {settings.PAYPAL_BASE_URL}")
    print(f"Client ID Config   : {'[CONFIGURED]' if settings.PAYPAL_CLIENT_ID else '[NOT SET]'}")
    print(f"Secret Config      : {'[CONFIGURED]' if settings.PAYPAL_CLIENT_SECRET else '[NOT SET]'}")
    print(f"Webhook ID Config  : {'[CONFIGURED]' if settings.PAYPAL_WEBHOOK_ID else '[NOT SET]'}")
    print("-" * 70)

    if not settings.is_paypal_configured:
        print("[NOTICE] PayPal Sandbox credentials are not yet configured in .env.")
        print("")
        print("To configure your live PayPal Sandbox test:")
        print("1. Log in to the PayPal Developer Portal: https://developer.paypal.com")
        print("2. Navigate to 'Apps & Credentials' and select 'Sandbox'.")
        print("3. Create or select an App and copy 'Client ID' and 'Secret'.")
        print("4. Add the following to your backend/.env file:")
        print("   PAYPAL_CLIENT_ID=<your-sandbox-client-id>")
        print("   PAYPAL_CLIENT_SECRET=<your-sandbox-client-secret>")
        print("   PAYPAL_WEBHOOK_ID=<your-registered-webhook-id>")
        print("5. Ensure you have sandbox balance in your business test account.")
        print("=" * 70)
        return

    print("Initiating live OAuth 2.0 handshake with PayPal Sandbox...")
    result = await PayPalClient.test_connection()

    if result["success"]:
        print(f"[SUCCESS] {result['message']} (Latency: {result['latency_ms']}ms)")
        print("PayPal Sandbox connection is HEALTHY and ready for Payouts.")
    else:
        print(f"[ERROR] {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
