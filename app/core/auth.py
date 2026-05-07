"""JWT transport, strategy, and FastAPI Users ``UserManager`` wiring."""

import uuid

from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from app.core.config import get_settings
from app.models.users import User


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = get_settings().secret_key
    verification_token_secret = get_settings().secret_key


def _secrets() -> tuple[str, int]:
    s = get_settings()
    return s.secret_key, s.jwt_lifetime_seconds


def get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
    secret, lifetime = _secrets()
    return JWTStrategy[User, uuid.UUID](secret=secret, lifetime_seconds=lifetime)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
