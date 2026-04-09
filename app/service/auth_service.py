from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.config import get_settings
from app.core.security import (
    JWTValidationError,
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db import crud
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest


@dataclass
class SessionBundle:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    user: User
    session: UserSession


def normalize_email(email: str) -> str:
    return email.strip().lower()


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _refresh_expires_at() -> datetime:
    settings = get_settings()
    return utc_now() + timedelta(days=settings.refresh_token_ttl_days)


def _build_session_bundle(
    db: Session,
    *,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
) -> SessionBundle:
    settings = get_settings()
    crud.delete_expired_user_sessions(db, before=utc_now())

    refresh_token = generate_opaque_token()
    refresh_expires_at = _refresh_expires_at()
    session = crud.create_user_session(
        db,
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token, settings.refresh_token_pepper),
        expires_at=refresh_expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    access_token, access_expires_at = create_access_token(
        secret=settings.jwt_secret,
        issuer=settings.jwt_issuer,
        user_id=user.id,
        session_id=session.id,
        expires_delta=timedelta(minutes=settings.access_token_ttl_minutes),
    )
    audit_log("auth.session.created", user_id=user.id, session_id=session.id, ip_address=ip_address)
    return SessionBundle(
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
        user=user,
        session=session,
    )


def register_user(
    db: Session,
    auth_in: AuthRegisterRequest,
    *,
    user_agent: str | None,
    ip_address: str | None,
) -> SessionBundle:
    email = normalize_email(str(auth_in.email))
    if crud.get_user_by_email(db, email):
        raise ValueError("User with this email already exists.")

    user = crud.create_user(
        db,
        email=email,
        full_name=auth_in.full_name,
        password_hash=hash_password(auth_in.password),
    )
    audit_log("auth.register.success", user_id=user.id, email=email, ip_address=ip_address)
    return _build_session_bundle(db, user=user, user_agent=user_agent, ip_address=ip_address)


def login_user(
    db: Session,
    auth_in: AuthLoginRequest,
    *,
    user_agent: str | None,
    ip_address: str | None,
) -> SessionBundle:
    email = normalize_email(str(auth_in.email))
    user = crud.get_user_by_email(db, email)
    if user is None or not verify_password(auth_in.password, user.password_hash):
        audit_log("auth.login.failed", email=email, ip_address=ip_address)
        raise PermissionError("Invalid email or password.")
    if not user.is_active:
        raise PermissionError("User is inactive.")

    audit_log("auth.login.success", user_id=user.id, email=email, ip_address=ip_address)
    return _build_session_bundle(db, user=user, user_agent=user_agent, ip_address=ip_address)


def _validate_session(session: UserSession | None) -> UserSession | None:
    if session is None:
        return None
    if session.revoked_at is not None:
        return None
    if ensure_utc(session.expires_at) <= utc_now():
        return None
    return session


def get_user_by_access_token(db: Session, token: str) -> User | None:
    settings = get_settings()
    try:
        payload = decode_access_token(token, secret=settings.jwt_secret, issuer=settings.jwt_issuer)
    except JWTValidationError:
        return None

    session = _validate_session(crud.get_user_session_by_id(db, int(payload["sid"])))
    if session is None or session.user_id != int(payload["sub"]):
        return None
    if not session.user.is_active:
        return None
    return session.user


def refresh_auth_session(
    db: Session,
    *,
    refresh_token: str,
    user_agent: str | None,
    ip_address: str | None,
) -> SessionBundle:
    settings = get_settings()
    refresh_hash = hash_token(refresh_token, settings.refresh_token_pepper)
    session = _validate_session(crud.get_user_session_by_refresh_hash(db, refresh_hash))
    if session is None:
        raise PermissionError("Invalid or expired refresh token.")

    crud.touch_user_session(db, session)
    crud.revoke_user_session(db, session)
    audit_log("auth.refresh.success", user_id=session.user_id, session_id=session.id, ip_address=ip_address)
    return _build_session_bundle(db, user=session.user, user_agent=user_agent, ip_address=ip_address)


def logout_user(db: Session, *, refresh_token: str, ip_address: str | None) -> None:
    settings = get_settings()
    refresh_hash = hash_token(refresh_token, settings.refresh_token_pepper)
    session = _validate_session(crud.get_user_session_by_refresh_hash(db, refresh_hash))
    if session is None:
        raise PermissionError("Invalid or expired refresh token.")

    crud.revoke_user_session(db, session)
    audit_log("auth.logout.success", user_id=session.user_id, session_id=session.id, ip_address=ip_address)


def create_password_reset_request(db: Session, email: str) -> str | None:
    user = crud.get_user_by_email(db, normalize_email(email))
    crud.delete_expired_password_reset_tokens(db, before=utc_now())
    if user is None:
        audit_log("auth.password_reset.request.accepted", email=normalize_email(email), user_exists=False)
        return None

    settings = get_settings()
    raw_token = generate_opaque_token()
    crud.create_password_reset_token(
        db,
        user_id=user.id,
        token_hash=hash_token(raw_token, settings.password_reset_token_pepper),
        expires_at=utc_now() + timedelta(minutes=settings.password_reset_token_ttl_minutes),
    )
    if settings.debug_password_reset_tokens:
        audit_log("auth.password_reset.debug_token", user_id=user.id, email=user.email, reset_token=raw_token)
    audit_log("auth.password_reset.request.accepted", user_id=user.id, email=user.email, user_exists=True)
    return raw_token


def confirm_password_reset(db: Session, *, token: str, new_password: str) -> User:
    settings = get_settings()
    token_hash = hash_token(token, settings.password_reset_token_pepper)
    reset_token = crud.get_password_reset_token(db, token_hash)
    if (
        reset_token is None
        or reset_token.used_at is not None
        or ensure_utc(reset_token.expires_at) <= utc_now()
    ):
        raise LookupError("Reset token is invalid or expired.")

    user = crud.update_user_password(db, user=reset_token.user, password_hash=hash_password(new_password))
    crud.mark_password_reset_token_used(db, reset_token)
    crud.revoke_all_user_sessions(db, user.id)
    audit_log("auth.password_reset.confirmed", user_id=user.id)
    return user
