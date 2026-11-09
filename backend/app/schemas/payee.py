"""Pydantic schemas for Payee Registry."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PayeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    paypal_email: EmailStr
    category: str = Field(default="Contractor", max_length=100)
    trust_status: str = Field(default="STANDARD")  # STANDARD, TRUSTED, SUSPICIOUS


class PayeeUpdate(BaseModel):
    name: Optional[str] = None
    paypal_email: Optional[EmailStr] = None  # Note: Modifying email triggers hard rejection if changed
    category: Optional[str] = None
    verification_status: Optional[str] = None  # UNVERIFIED, VERIFIED, BLOCKED
    trust_status: Optional[str] = None


class PayeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    paypal_email: str
    category: str
    verification_status: str
    trust_status: str
    total_paid_minor: int
    last_transaction_at: Optional[datetime] = None
    risk_flags: List[str]
    created_at: datetime
    updated_at: datetime
