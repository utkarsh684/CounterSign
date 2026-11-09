"""Domain exceptions for Countersign."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class CountersignException(Exception):
    """Base exception for all Countersign domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PolicyViolationException(CountersignException):
    """Raised when a transaction violates deterministic financial policy."""
    pass


class KillSwitchActiveException(CountersignException):
    """Raised when an operation is blocked because the kill switch is enabled."""
    pass


class PayeeTamperException(CountersignException):
    """Raised when an existing payee's payout email has been tampered with."""
    pass


class PayPalIntegrationException(CountersignException):
    """Raised on PayPal communication, authorization, or payout failures."""
    pass


class MandateIntegrityException(CountersignException):
    """Raised when mandate HMAC signature or version verification fails."""
    pass


class AuditLedgerTamperException(CountersignException):
    """Raised when hash-chain integrity verification detects a broken or modified link."""
    pass
