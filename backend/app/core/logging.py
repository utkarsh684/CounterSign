"""Structured logging with automatic sensitive data redaction."""

import logging
import re
from typing import Any

SENSITIVE_PATTERNS = [
    (re.compile(r"(client_secret=)[^\s&]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(access_token=)[^\s&]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(password=)[^\s&]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9\-_.]+", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(api_key=)[^\s&]+", re.IGNORECASE), r"\1[REDACTED]"),
]


class RedactingFormatter(logging.Formatter):
    """Custom logging formatter that strips API keys, passwords, and bearer tokens."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern, replacement in SENSITIVE_PATTERNS:
            msg = pattern.sub(replacement, msg)
        return msg


def setup_logging():
    handler = logging.StreamHandler()
    formatter = RedactingFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Clear existing handlers to avoid duplicates
    root.handlers = [handler]
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("countersign")
