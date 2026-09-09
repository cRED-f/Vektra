"""Auth middleware — token-based authentication."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from server.core.config import get_settings
from server.core.errors import AuthError

_security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_security),
) -> str:
    """Verify the bearer token matches the configured API token."""
    settings = get_settings()

    # In dev mode, skip auth if no token is configured
    if settings.api_token == "dev-token-change-in-production" and credentials is None:
        return "dev"

    if credentials is None:
        raise HTTPException(status_code=401, detail="missing authorization token")

    if credentials.credentials != settings.api_token:
        raise HTTPException(status_code=403, detail="invalid token")

    return credentials.credentials
