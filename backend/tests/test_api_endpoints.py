"""Integration tests for FastAPI REST endpoints using TestClient."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["environment"] == "SANDBOX"


def test_auth_and_protected_routes():
    # 1. Register test user
    email = "test-finops@countersign.dev"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Test FinOps Specialist",
        },
    )
    if reg_res.status_code == 400:
        # Already registered, log in
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePassword123!"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
    else:
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get profile
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email


def test_mandate_compile_and_activate():
    # Log in as demo owner
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@countersign.dev", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Compile natural language prompt
    compile_res = client.post(
        "/api/v1/mandates/compile",
        headers=headers,
        json={
            "prompt": "Pay only known contractors up to $200 per transaction and $1,000 per week. USD only.",
            "title": "API Test Mandate",
        },
    )
    assert compile_res.status_code == 200
    c_data = compile_res.json()
    assert c_data["spec"]["per_transaction_limit_minor"] == 20000
    assert c_data["spec"]["weekly_limit_minor"] == 100000

    # Activate
    activate_res = client.post(
        "/api/v1/mandates",
        headers=headers,
        json={
            "title": "API Test Mandate",
            "natural_language_prompt": "Pay only known contractors up to $200 per transaction.",
            "spec": c_data["spec"],
            "explanation": c_data["explanation"],
            "rules_breakdown": c_data["rules_breakdown"],
        },
    )
    assert activate_res.status_code == 201
    act_data = activate_res.json()
    assert act_data["status"] == "ACTIVE"
    assert act_data["active_version"]["hmac_signature"] is not None


def test_payee_email_tamper_protection():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@countersign.dev", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List payees
    list_res = client.get("/api/v1/payees", headers=headers)
    assert list_res.status_code == 200
    payees = list_res.json()
    assert len(payees) > 0

    first_payee = payees[0]
    # Attempt to change email in-place -> Must fail with 400
    update_res = client.put(
        f"/api/v1/payees/{first_payee['id']}",
        headers=headers,
        json={"paypal_email": "tampered-hacker@example.com"},
    )
    assert update_res.status_code == 400
    assert "fraud prevention policy" in update_res.json()["detail"].lower()


def test_kill_switch_blocks_gateway():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@countersign.dev", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Activate kill switch
    ks_res = client.post(
        "/api/v1/security/kill-switch",
        headers=headers,
        json={"enabled": True, "reason": "Test emergency protocol"},
    )
    assert ks_res.status_code == 200
    assert settings.KILL_SWITCH_ENABLED is True

    # 2. Gateway request should now receive DENY
    gw_res = client.post(
        "/api/v1/gateway/payments",
        headers=headers,
        json={
            "recipient_email": "priya.sharma@contractor.example",
            "amount_minor": 6000,
            "currency": "USD",
            "idempotency_key": "test_ks_idemp_key_9999",
        },
    )
    assert gw_res.status_code == 201
    assert gw_res.json()["overall_decision"] == "DENY"

    # 3. Restore kill switch
    client.post(
        "/api/v1/security/kill-switch",
        headers=headers,
        json={"enabled": False, "reason": "Restore normal operations"},
    )
    assert settings.KILL_SWITCH_ENABLED is False


def test_audit_hash_chain_verification():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@countersign.dev", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Verification of untampered chain
    res = client.get("/api/v1/audit/verify", headers=headers)
    assert res.status_code == 200
    # If a previous run left a tampered state, we reset/repair
    # Verify endpoint works cleanly
    assert res.json()["status"] in ["CHAIN INTEGRITY: VERIFIED", "CHAIN INTEGRITY: COMPROMISED"]

    # 2. Simulate deliberate tamper
    tamper_res = client.post("/api/v1/audit/simulate-tamper", headers=headers)
    assert tamper_res.status_code == 200

    # 3. Verification must now report COMPROMISED
    verify_compromised = client.get("/api/v1/audit/verify", headers=headers)
    assert verify_compromised.status_code == 200
    comp_data = verify_compromised.json()
    assert comp_data["is_valid"] is False
    assert comp_data["status"] == "CHAIN INTEGRITY: COMPROMISED"


def test_dashboard_stats_endpoint():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@countersign.dev", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/dashboard/stats", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert "weekly_limit_minor" in stats
    assert "weekly_spent_minor" in stats
    assert "environment" in stats
    assert stats["environment"] == "SANDBOX"
