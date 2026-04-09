from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.user import User
from app.service import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class RequestClientContext:
    user_agent: str | None
    ip_address: str | None


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_request_client_context(request: Request) -> RequestClientContext:
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else None)
    return RequestClientContext(
        user_agent=request.headers.get("User-Agent"),
        ip_address=ip_address,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_access_token(db, credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_internal_api_key(x_internal_api_key: Annotated[str | None, Header(alias="X-Internal-API-Key")] = None) -> str:
    settings = get_settings()
    if not x_internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal API key.")
    return x_internal_api_key
