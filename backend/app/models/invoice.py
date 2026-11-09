"""Invoice and EvidenceDocument models."""

from typing import List, Optional
from datetime import date
from sqlalchemy import BigInteger, Date, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class Invoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoices"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tax_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)  # PENDING, ANALYZED, PAYMENT_PROPOSED, PROCESSED, REJECTED
    extracted_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    security_findings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="invoices")
    evidence_documents: Mapped[List["EvidenceDocument"]] = relationship(
        "EvidenceDocument", back_populates="invoice", cascade="all, delete-orphan"
    )
    payment_requests: Mapped[List["PaymentRequest"]] = relationship("PaymentRequest", back_populates="invoice")


class EvidenceDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "evidence_documents"

    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(64), default="INVOICE_PDF", nullable=False)
    source_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    trust_level: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)  # HIGH, MEDIUM, UNTRUSTED_THIRD_PARTY
    extracted_snippets: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="evidence_documents")
