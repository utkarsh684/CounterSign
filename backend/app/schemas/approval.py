"""Pydantic schemas for Human Payment Approval and Exception Handling."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ApprovalConfirmRequest(BaseModel):
    confirmed_recipient_email: EmailStr
    confirmed_amount_minor: int = Field(gt=0)
    confirmed_currency: str = Field(min_length=3, max_length=3)
    typed_amount_confirmation: Optional[str] = None
    is_one_time_exception: bool = False
    exception_reason: Optional[str] = None
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    reason: str = Field(min_length=5)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    payment_request_id: str
    user_id: str
    decision: str  # APPROVED, REJECTED
    confirmed_recipient_email: str
    confirmed_amount_minor: int
    confirmed_currency: str
    is_one_time_exception: bool
    exception_reason: Optional[str] = None
    notes: Optional[str] = None
    decided_at: datetime
    paypal_payout: Optional["PayPalPayoutResponse"] = None


class PayPalPayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender_batch_id: str
    paypal_batch_id: Optional[str] = None
    paypal_payout_item_id: Optional[str] = None
    recipient_email: str
    amount_minor: int
    currency: str
    batch_status: str
    item_status: str
    environment: str
    submitted_at: datetime
    reconciled_at: Optional[datetime] = None
