"""Unit tests for SHA-256 Tamper-Evident Hash Chain."""

from datetime import datetime, timezone
import pytest
from app.ledger.hash_chain import (
    GENESIS_PREVIOUS_HASH,
    compute_audit_record_hash,
    verify_audit_chain,
)


def test_empty_chain_is_valid():
    res = verify_audit_chain([])
    assert res.is_valid is True
    assert res.status == "CHAIN INTEGRITY: VERIFIED"
    assert res.total_records == 0


def test_single_record_chain():
    now = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc).isoformat()
    payload = {"action": "MANDATE_ACTIVATED", "limit_minor": 20000}
    current_hash = compute_audit_record_hash(
        previous_hash=GENESIS_PREVIOUS_HASH,
        sequence_number=1,
        event_type="MANDATE_ACTIVATED",
        timestamp_iso=now,
        payload=payload,
    )

    records = [
        {
            "sequence_number": 1,
            "event_type": "MANDATE_ACTIVATED",
            "created_at": now,
            "payload": payload,
            "previous_hash": GENESIS_PREVIOUS_HASH,
            "current_hash": current_hash,
        }
    ]

    res = verify_audit_chain(records)
    assert res.is_valid is True
    assert res.status == "CHAIN INTEGRITY: VERIFIED"
    assert res.total_records == 1


def test_three_record_valid_chain():
    records = []
    prev_hash = GENESIS_PREVIOUS_HASH

    for i in range(1, 4):
        now = datetime(2026, 11, 2, 10, i, tzinfo=timezone.utc).isoformat()
        payload = {"event_index": i, "data": f"sample_event_{i}"}
        curr_hash = compute_audit_record_hash(
            previous_hash=prev_hash,
            sequence_number=i,
            event_type="EVENT_TEST",
            timestamp_iso=now,
            payload=payload,
        )
        records.append({
            "sequence_number": i,
            "event_type": "EVENT_TEST",
            "created_at": now,
            "payload": payload,
            "previous_hash": prev_hash,
            "current_hash": curr_hash,
        })
        prev_hash = curr_hash

    res = verify_audit_chain(records)
    assert res.is_valid is True
    assert res.status == "CHAIN INTEGRITY: VERIFIED"
    assert res.total_records == 3


def test_tampered_payload_detected():
    """Deliberately modify the payload in record #2 and verify detection."""
    records = []
    prev_hash = GENESIS_PREVIOUS_HASH

    for i in range(1, 4):
        now = datetime(2026, 11, 2, 10, i, tzinfo=timezone.utc).isoformat()
        payload = {"event_index": i, "amount": 100 * i}
        curr_hash = compute_audit_record_hash(
            previous_hash=prev_hash,
            sequence_number=i,
            event_type="PAYMENT_PROPOSED",
            timestamp_iso=now,
            payload=payload,
        )
        records.append({
            "sequence_number": i,
            "event_type": "PAYMENT_PROPOSED",
            "created_at": now,
            "payload": payload,
            "previous_hash": prev_hash,
            "current_hash": curr_hash,
        })
        prev_hash = curr_hash

    # Malicious actor tampers with amount in record 2
    records[1]["payload"]["amount"] = 999999

    res = verify_audit_chain(records)
    assert res.is_valid is False
    assert res.status == "CHAIN INTEGRITY: COMPROMISED"
    assert res.broken_sequence_number == 2


def test_tampered_previous_hash_detected():
    """Deliberately alter previous_hash pointer in record #3."""
    records = []
    prev_hash = GENESIS_PREVIOUS_HASH

    for i in range(1, 4):
        now = datetime(2026, 11, 2, 10, i, tzinfo=timezone.utc).isoformat()
        payload = {"step": i}
        curr_hash = compute_audit_record_hash(
            previous_hash=prev_hash,
            sequence_number=i,
            event_type="STEP",
            timestamp_iso=now,
            payload=payload,
        )
        records.append({
            "sequence_number": i,
            "event_type": "STEP",
            "created_at": now,
            "payload": payload,
            "previous_hash": prev_hash,
            "current_hash": curr_hash,
        })
        prev_hash = curr_hash

    # Rogue actor breaks pointer
    records[2]["previous_hash"] = "f" * 64

    res = verify_audit_chain(records)
    assert res.is_valid is False
    assert res.status == "CHAIN INTEGRITY: COMPROMISED"
    assert res.broken_sequence_number == 3
