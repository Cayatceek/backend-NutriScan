from datetime import datetime
from math import ceil

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.open_food_facts import OpenFoodFactsIngredient, OpenFoodFactsNutriments


class ProductBase(BaseModel):
    barcode: str | None = Field(default=None, min_length=3, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=255)
    image_url: str | None = Field(default=None, max_length=1024)
    image_front_url: str | None = Field(default=None, max_length=1024)
    nutriscore_grade: str | None = Field(default=None, max_length=8)
    ingredients_text: str | None = None
    ingredients: list[OpenFoodFactsIngredient] = Field(default_factory=list)
    categories: str | None = None
    labels: str | None = None
    additives_tags: list[str] = Field(default_factory=list)
    allergens: str | None = None
    nutriments: OpenFoodFactsNutriments | None = None
    source: str = Field(default="api", max_length=32)

    @field_validator("barcode")
    @classmethod
    def normalize_barcode(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductSummary(BaseModel):
    id: int
    barcode: str | None = None
    name: str
    brand: str | None = None
    image_url: str | None = None
    nutriscore_grade: str | None = None
    ingredients_text: str | None = None
    ingredients: list[OpenFoodFactsIngredient] = Field(default_factory=list)
    is_favorite: bool = False


class ProductListResponse(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int
    page_count: int

    @classmethod
    def build(
        cls,
        *,
        items: list[ProductRead],
        total: int,
        page: int,
        page_size: int,
    ) -> "ProductListResponse":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            page_count=ceil(total / page_size) if total else 0,
        )


class FavoriteProductListResponse(BaseModel):
    items: list[ProductSummary]
    total: int
    page: int
    page_size: int
    page_count: int

    @classmethod
    def build(
        cls,
        *,
        items: list[ProductSummary],
        total: int,
        page: int,
        page_size: int,
    ) -> "FavoriteProductListResponse":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            page_count=ceil(total / page_size) if total else 0,
        )


class InternalProductUpsertRequest(ProductBase):
    pass
