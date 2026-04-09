from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.favorite_product import FavoriteProduct
    from app.models.password_reset_token import PasswordResetToken
    from app.models.product import Product
    from app.models.scan_history import ScanHistory
    from app.models.user_session import UserSession
    from app.models.user_settings import UserSettings


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    products: Mapped[list[Product]] = relationship(back_populates="owner")
    favorite_products: Mapped[list[FavoriteProduct]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    scan_history_entries: Mapped[list[ScanHistory]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    settings: Mapped[UserSettings | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
