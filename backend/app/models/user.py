"""User and Agent API Key models."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="OWNER", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    api_keys: Mapped[List["AgentApiKey"]] = relationship("AgentApiKey", back_populates="user", cascade="all, delete-orphan")
    mandates: Mapped[List["Mandate"]] = relationship("Mandate", back_populates="user")
    payees: Mapped[List["Payee"]] = relationship("Payee", back_populates="user")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="user")
    payment_requests: Mapped[List["PaymentRequest"]] = relationship("PaymentRequest", back_populates="user")


class AgentApiKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_api_keys"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    scopes: Mapped[list] = mapped_column(JSON, default=lambda: ["inbox:read", "payment:propose"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="api_keys")
