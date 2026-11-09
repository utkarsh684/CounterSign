"""Audit Ledger and Evidence schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence_number: int
    event_type: str
    user_id: Optional[str] = None
    payment_request_id: Optional[str] = None
    paypal_payout_id: Optional[str] = None
    summary: str
    payload: Dict[str, Any]
    previous_hash: str
    current_hash: str
    created_at: datetime


class ChainVerificationResult(BaseModel):
    is_valid: bool
    status: str  # "CHAIN INTEGRITY: VERIFIED" or "CHAIN INTEGRITY: COMPROMISED"
    total_records: int
    verified_at: datetime
    broken_sequence_number: Optional[int] = None
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None


class EvidencePackage(BaseModel):
    package_id: str
    generated_at: datetime
    payment_request: Dict[str, Any]
    mandate_version: Dict[str, Any]
    invoice: Optional[Dict[str, Any]] = None
    policy_evaluation: Dict[str, Any]
    ai_verification: Dict[str, Any]
    approval_decision: Optional[Dict[str, Any]] = None
    paypal_payout: Optional[Dict[str, Any]] = None
    audit_events: List[Dict[str, Any]]
    chain_status: str
    tamper_proof_checksum: str
