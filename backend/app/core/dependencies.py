"""FastAPI security and context dependencies."""

from typing import Optional
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_access_token, hash_api_key
from app.database.session import get_db
from app.models.user import User, AgentApiKey

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Authenticates the user from a Bearer JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_current_owner(user: User = Depends(get_current_user)) -> User:
    """Ensures authenticated user is an account OWNER."""
    if user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner privileges required for this financial operation",
        )
    return user


def verify_agent_caller(
    x_agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db),
) -> str:
    """Authenticates the caller as an authorized AI agent or logged-in owner."""
    # Check direct Agent API Key header
    if x_agent_key:
        if x_agent_key == settings.AGENT_API_KEY:
            return "COUNTERSIGN_OPS_AGENT"
        key_hash = hash_api_key(x_agent_key)
        agent_key = db.query(AgentApiKey).filter(
            AgentApiKey.key_hash == key_hash,
            AgentApiKey.is_active == True,
        ).first()
        if agent_key:
            return agent_key.name
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Agent API Key",
        )

    # Alternatively allow authenticated owner session to trigger agent workflows
    if credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            if payload.get("sub"):
                return "OWNER_SESSION"
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid Agent API key or session",
    )
