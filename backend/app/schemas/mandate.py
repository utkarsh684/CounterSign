"""Pydantic schemas for AI Mandates."""

from datetime import datetime, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MandateSpec(BaseModel):
    """Structured financial mandate compiled from natural language."""
    currency_allowlist: List[str] = Field(default=["USD"], description="Permitted ISO 4217 currencies")
    per_transaction_limit_minor: int = Field(gt=0, description="Max amount per payment in cents")
    daily_limit_minor: int = Field(gt=0, description="Max daily spend in cents")
    weekly_limit_minor: int = Field(gt=0, description="Max weekly spend in cents")
    allowed_weekdays: List[int] = Field(default=[1, 2, 3, 4, 5], description="1=Monday ... 7=Sunday")
    operating_hours_start: Optional[str] = Field(default="09:00", description="HH:MM UTC")
    operating_hours_end: Optional[str] = Field(default="18:00", description="HH:MM UTC")
    allow_existing_payees_only: bool = Field(default=True)
    unknown_payee_action: str = Field(default="ESCALATE")  # ESCALATE, DENY
    third_party_evidence_limit_minor: int = Field(default=10000, description="Threshold above which third-party evidence triggers escalation")
    human_confirmation_required: bool = Field(default=True)


class RuleExplanation(BaseModel):
    rule: str
    parameter: str
    value: str
    rationale: str


class MandateCompileRequest(BaseModel):
    prompt: str = Field(min_length=10, description="Natural language spending policy instructions")
    title: Optional[str] = Field(default="Corporate AP Mandate")


class MandateCompileResponse(BaseModel):
    spec: MandateSpec
    explanation: str
    rules_breakdown: List[RuleExplanation]
    missing_or_ambiguous_conditions: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)


class MandateActivateRequest(BaseModel):
    title: str
    natural_language_prompt: str
    spec: MandateSpec
    explanation: str
    rules_breakdown: List[RuleExplanation]


class MandateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    currency_allowlist: List[str]
    per_transaction_limit_minor: int
    daily_limit_minor: int
    weekly_limit_minor: int
    allowed_weekdays: List[int]
    operating_hours_start: Optional[time] = None
    operating_hours_end: Optional[time] = None
    allow_existing_payees_only: bool
    unknown_payee_action: str
    third_party_evidence_limit_minor: int
    human_confirmation_required: bool
    compiler_explanation: str
    compiler_rules_breakdown: list
    hmac_signature: str
    created_at: datetime


class MandateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    natural_language_prompt: str
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime
    active_version: Optional[MandateVersionResponse] = None
