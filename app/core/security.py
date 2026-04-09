from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16
TOKEN_BYTES = 32
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt}${encoded_digest}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        algorithm, iterations, salt, encoded_digest = encoded_password.split("$", maxsplit=3)
    except ValueError:
        return False

    if algorithm != PBKDF2_ALGORITHM:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    )
    recalculated = base64.urlsafe_b64encode(digest).decode("ascii")
    return hmac.compare_digest(recalculated, encoded_digest)


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def generate_opaque_token() -> str:
    return generate_token()


def hash_token(token: str, pepper: str) -> str:
    return hashlib.sha256(f"{pepper}:{token}".encode("utf-8")).hexdigest()


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign(value: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(signature)


def create_access_token(
    *,
    secret: str,
    issuer: str,
    user_id: int,
    session_id: int,
    expires_delta: timedelta,
) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "type": "access",
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = _sign(signing_input, secret)
    return f"{signing_input}.{signature}", expires_at


class JWTValidationError(ValueError):
    pass


def decode_access_token(token: str, *, secret: str, issuer: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, signature = token.split(".", maxsplit=2)
    except ValueError as exc:
        raise JWTValidationError("Malformed token.") from exc

    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = _sign(signing_input, secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise JWTValidationError("Invalid token signature.")

    try:
        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
    except (json.JSONDecodeError, ValueError) as exc:
        raise JWTValidationError("Malformed token payload.") from exc

    if header.get("alg") != JWT_ALGORITHM or payload.get("type") != "access":
        raise JWTValidationError("Unsupported token.")

    if payload.get("iss") != issuer:
        raise JWTValidationError("Invalid issuer.")

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp <= int(datetime.now(UTC).timestamp()):
        raise JWTValidationError("Token expired.")

    return payload
