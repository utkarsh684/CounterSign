"""ApprovalDecision model."""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.base import UUIDMixin, utc_now


class ApprovalDecision(Base, UUIDMixin):
    __tablename__ = "approval_decisions"

    payment_request_id: Mapped[str] = mapped_column(String(36), ForeignKey("payment_requests.id"), nullable=False, unique=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # APPROVED, REJECTED

    # Exact human-confirmed details
    confirmed_recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    confirmed_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    confirmed_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    typed_amount_confirmation: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Scoped One-Time Exception Handling
    is_one_time_exception: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exception_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    payment_request: Mapped["PaymentRequest"] = relationship("PaymentRequest", back_populates="approval_decision")
    paypal_payout: Mapped[Optional["PayPalPayout"]] = relationship(
        "PayPalPayout", back_populates="approval_decision", uselist=False, cascade="all, delete-orphan"
    )
