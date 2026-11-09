"""Mandate and MandateVersion models."""

from typing import List, Optional
from datetime import datetime, time
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.base import UUIDMixin, TimestampMixin, utc_now


class Mandate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "mandates"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    natural_language_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)  # DRAFT, ACTIVE, REVOKED, EXPIRED
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="mandates")
    versions: Mapped[List["MandateVersion"]] = relationship(
        "MandateVersion",
        back_populates="mandate",
        cascade="all, delete-orphan",
        order_by="MandateVersion.version.desc()",
    )


class MandateVersion(Base, UUIDMixin):
    __tablename__ = "mandate_versions"

    mandate_id: Mapped[str] = mapped_column(String(36), ForeignKey("mandates.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Core Financial Policy Constraints (Integer Minor Units)
    currency_allowlist: Mapped[list] = mapped_column(JSON, default=lambda: ["USD"], nullable=False)
    per_transaction_limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    daily_limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    weekly_limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Operational Boundaries
    allowed_weekdays: Mapped[list] = mapped_column(JSON, default=lambda: [1, 2, 3, 4, 5], nullable=False)  # Mon-Fri
    operating_hours_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    operating_hours_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Payee & Evidence Governance
    allow_existing_payees_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unknown_payee_action: Mapped[str] = mapped_column(String(32), default="ESCALATE", nullable=False)
    third_party_evidence_limit_minor: Mapped[int] = mapped_column(BigInteger, default=10000, nullable=False)
    human_confirmation_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # AI Compiler Explanations & Lineage
    compiler_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    compiler_rules_breakdown: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Tamper-Evident HMAC Signature
    hmac_signature: Mapped[str] = mapped_column(String(64), nullable=False)
    authorized_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    mandate: Mapped["Mandate"] = relationship("Mandate", back_populates="versions")
