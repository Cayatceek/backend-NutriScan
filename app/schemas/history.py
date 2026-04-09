from datetime import datetime
from math import ceil

from pydantic import BaseModel, Field

from app.schemas.open_food_facts import OpenFoodFactsIngredient


class HistoryCreateRequest(BaseModel):
    product_id: int = Field(ge=1)
    notes: str | None = Field(default=None, max_length=2000)


class HistoryProductSummary(BaseModel):
    id: int
    barcode: str | None = None
    name: str
    brand: str | None = None
    image_url: str | None = None
    nutriscore_grade: str | None = None
    ingredients_text: str | None = None
    ingredients: list[OpenFoodFactsIngredient] = Field(default_factory=list)
    is_favorite: bool


class HistoryItemRead(BaseModel):
    id: str
    scanned_at: datetime
    created_at: datetime
    notes: str | None = None
    product: HistoryProductSummary


class HistoryListResponse(BaseModel):
    items: list[HistoryItemRead]
    total: int
    page: int
    page_size: int
    page_count: int

    @classmethod
    def build(
        cls,
        *,
        items: list[HistoryItemRead],
        total: int,
        page: int,
        page_size: int,
    ) -> "HistoryListResponse":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            page_count=ceil(total / page_size) if total else 0,
        )
