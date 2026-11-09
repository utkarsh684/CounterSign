"""PaymentRequest, PolicyEvaluation, and AIVerification models."""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.base import UUIDMixin, TimestampMixin, utc_now


class PaymentRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_requests"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    invoice_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=True, index=True)
    payee_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("payees.id"), nullable=True, index=True)
    mandate_version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("mandate_versions.id"), nullable=True, index=True)

    agent_id: Mapped[str] = mapped_column(String(64), default="COUNTERSIGN_OPS_AGENT", nullable=False)
    agent_mode: Mapped[str] = mapped_column(String(32), default="LIVE", nullable=False)  # LIVE, SCRIPTED_COMPROMISED
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    overall_decision: Mapped[str] = mapped_column(String(32), default="EVALUATED", nullable=False)  # READY_FOR_APPROVAL, ESCALATE, DENY
    decision_reasons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="EVALUATED", nullable=False)  # EVALUATED, AWAITING_APPROVAL, APPROVED, REJECTED, EXECUTED, BLOCKED
    is_simulated_attack: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="payment_requests")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="payment_requests")
    payee: Mapped[Optional["Payee"]] = relationship("Payee", back_populates="payment_requests")
    policy_evaluation: Mapped[Optional["PolicyEvaluation"]] = relationship(
        "PolicyEvaluation", back_populates="payment_request", uselist=False, cascade="all, delete-orphan"
    )
    ai_verification: Mapped[Optional["AIVerification"]] = relationship(
        "AIVerification", back_populates="payment_request", uselist=False, cascade="all, delete-orphan"
    )
    approval_decision: Mapped[Optional["ApprovalDecision"]] = relationship(
        "ApprovalDecision", back_populates="payment_request", uselist=False, cascade="all, delete-orphan"
    )


class PolicyEvaluation(Base, UUIDMixin):
    __tablename__ = "policy_evaluations"

    payment_request_id: Mapped[str] = mapped_column(String(36), ForeignKey("payment_requests.id"), nullable=False, unique=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)  # READY_FOR_APPROVAL, ESCALATE, DENY
    rules_evaluated: Mapped[int] = mapped_column(Integer, nullable=False)
    rules_passed: Mapped[int] = mapped_column(Integer, nullable=False)
    rules_failed: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    payment_request: Mapped["PaymentRequest"] = relationship("PaymentRequest", back_populates="policy_evaluation")


class AIVerification(Base, UUIDMixin):
    __tablename__ = "ai_verifications"

    payment_request_id: Mapped[str] = mapped_column(String(36), ForeignKey("payment_requests.id"), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    recommendation: Mapped[str] = mapped_column(String(32), nullable=False)  # CLEAR, ESCALATE, DENY
    injection_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason_codes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    evidence_references: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    raw_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    payment_request: Mapped["PaymentRequest"] = relationship("PaymentRequest", back_populates="ai_verification")
