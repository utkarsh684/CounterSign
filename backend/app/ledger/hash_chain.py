"""SHA-256 Tamper-Evident Cryptographic Hash Chain.

Guarantees:
- Every record commits to the exact SHA-256 hash of its predecessor.
- Payloads are canonically serialized with sorted keys to ensure deterministic hashing.
- Any manual edit in the database breaks the cryptographic chain immediately.
- Clearly labeled as a tamper-evident hash-chained audit log (not blockchain or immutable storage).
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from app.schemas.audit import ChainVerificationResult

GENESIS_PREVIOUS_HASH = "0" * 64


def canonical_json(data: Dict[str, Any]) -> str:
    """Produces canonical JSON string with sorted keys and no extraneous whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_audit_record_hash(
    previous_hash: str,
    sequence_number: int,
    event_type: str,
    timestamp_iso: str,
    payload: Dict[str, Any],
) -> str:
    """Computes SHA-256 hash committing to the entire state of the audit record."""
    payload_str = canonical_json(payload)
    message = f"{previous_hash}|{sequence_number}|{event_type}|{timestamp_iso}|{payload_str}"
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def verify_audit_chain(records: List[Dict[str, Any]]) -> ChainVerificationResult:
    """Traverses an ordered list of audit records and verifies cryptographic link integrity."""
    now = datetime.now(timezone.utc)
    if not records:
        return ChainVerificationResult(
            is_valid=True,
            status="CHAIN INTEGRITY: VERIFIED",
            total_records=0,
            verified_at=now,
        )

    expected_prev_hash = GENESIS_PREVIOUS_HASH

    for idx, rec in enumerate(records):
        prev_hash = rec.get("previous_hash", "")
        seq = rec.get("sequence_number", idx + 1)
        event_type = rec.get("event_type", "")
        ts = rec.get("created_at")
        ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
        payload = rec.get("payload", {})
        current_hash = rec.get("current_hash", "")

        # 1. Check link to previous hash
        if prev_hash != expected_prev_hash:
            return ChainVerificationResult(
                is_valid=False,
                status="CHAIN INTEGRITY: COMPROMISED",
                total_records=len(records),
                verified_at=now,
                broken_sequence_number=seq,
                expected_hash=expected_prev_hash,
                actual_hash=prev_hash,
            )

        # 2. Recompute current hash
        recomputed = compute_audit_record_hash(
            previous_hash=prev_hash,
            sequence_number=seq,
            event_type=event_type,
            timestamp_iso=ts_str,
            payload=payload,
        )

        if recomputed != current_hash:
            return ChainVerificationResult(
                is_valid=False,
                status="CHAIN INTEGRITY: COMPROMISED",
                total_records=len(records),
                verified_at=now,
                broken_sequence_number=seq,
                expected_hash=recomputed,
                actual_hash=current_hash,
            )

        expected_prev_hash = current_hash

    return ChainVerificationResult(
        is_valid=True,
        status="CHAIN INTEGRITY: VERIFIED",
        total_records=len(records),
        verified_at=now,
    )
