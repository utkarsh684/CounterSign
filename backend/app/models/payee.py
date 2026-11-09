"""Payee registry model."""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class Payee(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payees"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    paypal_email: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Contractor", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="VERIFIED", nullable=False)  # UNVERIFIED, VERIFIED, BLOCKED
    trust_status: Mapped[str] = mapped_column(String(32), default="STANDARD", nullable=False)  # STANDARD, TRUSTED, SUSPICIOUS
    total_paid_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_transaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="payees")
    payment_requests: Mapped[list["PaymentRequest"]] = relationship("PaymentRequest", back_populates="payee")

    __table_args__ = (
        Index("idx_payee_user_email", "user_id", "paypal_email"),
    )
