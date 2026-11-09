"""Core security utilities: Argon2id password hashing, JWT handling, HMAC signing."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from app.core.config import settings

ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hashes a raw password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a raw password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def hash_api_key(api_key: str) -> str:
    """Computes SHA-256 hash of an API key for safe database storage."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def compute_mandate_hmac(mandate_dict: Dict[str, Any]) -> str:
    """Computes HMAC-SHA256 of canonical JSON-serialized financial mandate."""
    canonical_json = json.dumps(mandate_dict, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        settings.MANDATE_HMAC_SECRET.encode("utf-8"),
        canonical_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_mandate_hmac(mandate_dict: Dict[str, Any], signature: str) -> bool:
    """Constant-time comparison for mandate HMAC verification."""
    expected = compute_mandate_hmac(mandate_dict)
    return hmac.compare_digest(expected, signature)
