from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import RequestClientContext, get_current_user, get_db, get_request_client_context
from app.core.rate_limit import auth_policy, enforce_rate_limit
from app.models.user import User
from app.schemas.auth import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
)
from app.schemas.user import UserRead
from app.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[Session, Depends(get_db)]
ClientContextDep = Annotated[RequestClientContext, Depends(get_request_client_context)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
RegisterRateLimitDep = Annotated[None, Depends(enforce_rate_limit(auth_policy("auth-register")))]
LoginRateLimitDep = Annotated[None, Depends(enforce_rate_limit(auth_policy("auth-login")))]
ResetRateLimitDep = Annotated[None, Depends(enforce_rate_limit(auth_policy("auth-password-reset")))]


def _build_auth_response(bundle: auth_service.SessionBundle) -> AuthTokenResponse:
    return AuthTokenResponse(
        access_token=bundle.access_token,
        refresh_token=bundle.refresh_token,
        token_type="bearer",
        access_expires_at=bundle.access_expires_at,
        refresh_expires_at=bundle.refresh_expires_at,
        user=UserRead.model_validate(bundle.user),
    )


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    auth_in: AuthRegisterRequest,
    db: SessionDep,
    client_context: ClientContextDep,
    _: RegisterRateLimitDep,
) -> AuthTokenResponse:
    try:
        bundle = auth_service.register_user(
            db,
            auth_in,
            user_agent=client_context.user_agent,
            ip_address=client_context.ip_address,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _build_auth_response(bundle)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    auth_in: AuthLoginRequest,
    db: SessionDep,
    client_context: ClientContextDep,
    _: LoginRateLimitDep,
) -> AuthTokenResponse:
    try:
        bundle = auth_service.login_user(
            db,
            auth_in,
            user_agent=client_context.user_agent,
            ip_address=client_context.ip_address,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return _build_auth_response(bundle)


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh_access_token(
    payload: RefreshTokenRequest,
    db: SessionDep,
    client_context: ClientContextDep,
) -> AuthTokenResponse:
    try:
        bundle = auth_service.refresh_auth_session(
            db,
            refresh_token=payload.refresh_token,
            user_agent=client_context.user_agent,
            ip_address=client_context.ip_address,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return _build_auth_response(bundle)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, db: SessionDep, client_context: ClientContextDep) -> MessageResponse:
    try:
        auth_service.logout_user(db, refresh_token=payload.refresh_token, ip_address=client_context.ip_address)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/password-reset/request", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(payload: PasswordResetRequest, db: SessionDep, _: ResetRateLimitDep) -> MessageResponse:
    auth_service.create_password_reset_request(db, str(payload.email))
    return MessageResponse(message="If an account exists, password reset instructions will be sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirmRequest, db: SessionDep) -> MessageResponse:
    try:
        auth_service.confirm_password_reset(db, token=payload.token, new_password=payload.new_password)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message="Password has been updated.")
