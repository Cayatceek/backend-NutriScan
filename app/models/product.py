from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.favorite_product import FavoriteProduct
    from app.models.scan_history import ScanHistory
    from app.models.user import User


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    barcode: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
        index=True,
    )
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    image_front_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    nutriscore_grade: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    ingredients_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingredients_json: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    labels: Mapped[str | None] = mapped_column(Text, nullable=True)
    additives_tags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    allergens: Mapped[str | None] = mapped_column(Text, nullable=True)
    nutriments_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="api")
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner: Mapped[User | None] = relationship(back_populates="products")
    favorite_entries: Mapped[list[FavoriteProduct]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    scan_history_entries: Mapped[list[ScanHistory]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
