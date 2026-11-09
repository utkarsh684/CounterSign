"""PayPalPayout and PayPalWebhookEvent models."""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.base import UUIDMixin, utc_now


class PayPalPayout(Base, UUIDMixin):
    __tablename__ = "paypal_payouts"

    approval_decision_id: Mapped[str] = mapped_column(String(36), ForeignKey("approval_decisions.id"), nullable=False, unique=True)
    sender_batch_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    paypal_batch_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    paypal_payout_item_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)

    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    fee_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    batch_status: Mapped[str] = mapped_column(String(64), default="SUBMITTED", nullable=False)  # SUBMITTED, PROCESSING, SUCCESS, DENIED
    item_status: Mapped[str] = mapped_column(String(64), default="SUBMITTED", nullable=False)  # SUBMITTED, SUCCESS, FAILED, UNCLAIMED, BLOCKED, RETURNED
    environment: Mapped[str] = mapped_column(String(16), default="SANDBOX", nullable=False)

    raw_paypal_response: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    approval_decision: Mapped["ApprovalDecision"] = relationship("ApprovalDecision", back_populates="paypal_payout")


class PayPalWebhookEvent(Base, UUIDMixin):
    __tablename__ = "paypal_webhook_events"

    paypal_event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="VERIFIED", nullable=False)  # VERIFIED, UNVERIFIED, PROCESSED, DUPLICATE, FAILED

    transmission_id: Mapped[str] = mapped_column(String(128), nullable=False)
    transmission_time: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_verification_status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)

    raw_headers: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_webhook_type_event", "event_type", "paypal_event_id"),
    )
