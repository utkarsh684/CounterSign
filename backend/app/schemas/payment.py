"""Pydantic schemas for Payment Requests, Policy Evaluations, and AI Verifications."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PaymentRequestCreate(BaseModel):
    invoice_id: Optional[str] = None
    recipient_email: EmailStr
    amount_minor: int = Field(gt=0, description="Payment amount in integer minor units")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=8, max_length=128)
    agent_id: str = Field(default="COUNTERSIGN_OPS_AGENT")
    agent_mode: str = Field(default="LIVE")  # LIVE or SCRIPTED_COMPROMISED
    is_simulated_attack: bool = False


class RuleResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    rule_name: str
    passed: bool
    decision: str  # PASS, ESCALATE, DENY
    reason: str
    parameter_checked: Optional[str] = None
    actual_value: Optional[Any] = None
    allowed_value: Optional[Any] = None


class PolicyEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outcome: str  # READY_FOR_APPROVAL, ESCALATE, DENY
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    rule_results: List[Any]
    latency_ms: int
    evaluated_at: datetime


class AIVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    model: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendation: str  # CLEAR, ESCALATE, DENY
    injection_detected: bool
    reason_codes: List[str]
    evidence_references: List[str]
    explanation: str
    latency_ms: int
    created_at: datetime


class PaymentRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: Optional[str] = None
    payee_id: Optional[str] = None
    agent_id: str
    agent_mode: str
    idempotency_key: str
    recipient_email: str
    amount_minor: int
    currency: str
    overall_decision: str  # READY_FOR_APPROVAL, ESCALATE, DENY
    decision_reasons: List[str]
    status: str
    is_simulated_attack: bool
    created_at: datetime
    policy_evaluation: Optional[PolicyEvaluationResponse] = None
    ai_verification: Optional[AIVerificationResponse] = None
    approval_decision: Optional[Dict[str, Any]] = None
