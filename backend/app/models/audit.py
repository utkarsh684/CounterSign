"""AuditEvent and SecurityAlert models."""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base
from app.models.base import UUIDMixin, TimestampMixin, utc_now


class AuditEvent(Base, UUIDMixin):
    __tablename__ = "audit_events"

    # Monotonically increasing sequence number for cryptographic chaining
    sequence_number: Mapped[int] = mapped_column(Integer, autoincrement=True, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    payment_request_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    paypal_payout_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)

    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # SHA-256 Tamper-Evident Chaining
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    timestamp_iso: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_audit_chain", "sequence_number", "previous_hash", "current_hash"),
    )


class SecurityAlert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "security_alerts"

    severity: Mapped[str] = mapped_column(String(16), default="WARNING", nullable=False)  # INFO, WARNING, CRITICAL
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)  # KILL_SWITCH, POLICY_ENGINE, AI_VERIFIER, WEBHOOK
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
