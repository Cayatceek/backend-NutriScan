from __future__ import annotations

from app.models.product import Product
from app.schemas.history import HistoryProductSummary
from app.schemas.open_food_facts import (
    OpenFoodFactsBarcodeResponse,
    OpenFoodFactsIngredient,
    OpenFoodFactsProduct,
    OpenFoodFactsSearchResponse,
)
from app.schemas.product import ProductRead, ProductSummary


def product_ingredients(product: Product) -> list[OpenFoodFactsIngredient]:
    raw_ingredients = product.ingredients_json or []
    return [OpenFoodFactsIngredient.model_validate(item) for item in raw_ingredients]


def product_nutriments(product: Product):
    if not product.nutriments_json:
        return None
    return product.nutriments_json


def product_to_read(product: Product) -> ProductRead:
    return ProductRead(
        id=product.id,
        barcode=product.barcode,
        name=product.name,
        brand=product.brand,
        image_url=product.image_url,
        image_front_url=product.image_front_url,
        nutriscore_grade=product.nutriscore_grade,
        ingredients_text=product.ingredients_text,
        ingredients=product_ingredients(product),
        categories=product.categories,
        labels=product.labels,
        additives_tags=product.additives_tags_json or [],
        allergens=product.allergens,
        nutriments=product.nutriments_json,
        source=product.source,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def product_to_summary(product: Product, *, is_favorite: bool) -> ProductSummary:
    return ProductSummary(
        id=product.id,
        barcode=product.barcode,
        name=product.name,
        brand=product.brand,
        image_url=product.image_url or product.image_front_url,
        nutriscore_grade=product.nutriscore_grade,
        ingredients_text=product.ingredients_text,
        ingredients=product_ingredients(product),
        is_favorite=is_favorite,
    )


def product_to_history_summary(product: Product, *, is_favorite: bool) -> HistoryProductSummary:
    return HistoryProductSummary(
        id=product.id,
        barcode=product.barcode,
        name=product.name,
        brand=product.brand,
        image_url=product.image_url or product.image_front_url,
        nutriscore_grade=product.nutriscore_grade,
        ingredients_text=product.ingredients_text,
        ingredients=product_ingredients(product),
        is_favorite=is_favorite,
    )


def product_to_open_food_facts_product(product: Product) -> OpenFoodFactsProduct:
    return OpenFoodFactsProduct(
        code=product.barcode or str(product.id),
        product_name=product.name,
        brands=product.brand,
        ingredients_text=product.ingredients_text,
        ingredients=product_ingredients(product),
        nutriscore_grade=product.nutriscore_grade,
        nutriments=product.nutriments_json,
        image_url=product.image_url,
        image_front_url=product.image_front_url,
        categories=product.categories,
        labels=product.labels,
        additives_tags=product.additives_tags_json or [],
        allergens=product.allergens,
    )


def product_to_barcode_response(product: Product) -> OpenFoodFactsBarcodeResponse:
    return OpenFoodFactsBarcodeResponse(
        code=product.barcode or str(product.id),
        product=product_to_open_food_facts_product(product),
        status=1,
        status_verbose="product found in NutriScan backend",
    )


def products_to_search_response(
    *,
    products: list[Product],
    total: int,
    page: int,
    page_size: int,
    skip: int,
) -> OpenFoodFactsSearchResponse:
    page_count = ((total - 1) // page_size + 1) if total else 0
    return OpenFoodFactsSearchResponse(
        count=total,
        page=page,
        page_count=page_count,
        page_size=page_size,
        products=[product_to_open_food_facts_product(product) for product in products],
        skip=skip,
    )
