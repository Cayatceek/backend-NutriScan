from pydantic import BaseModel, ConfigDict, Field


class OpenFoodFactsIngredient(BaseModel):
    id: str | None = None
    text: str | None = None
    percent_estimate: float | None = None
    vegan: str | None = None
    vegetarian: str | None = None


class OpenFoodFactsNutriments(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    energy_kcal_100g: float | None = Field(default=None, alias="energy-kcal_100g")
    energy_100g: float | None = None
    proteins_100g: float | None = None
    carbohydrates_100g: float | None = None
    sugars_100g: float | None = None
    fat_100g: float | None = None
    saturated_fat_100g: float | None = Field(default=None, alias="saturated-fat_100g")
    fiber_100g: float | None = None
    sodium_100g: float | None = None
    salt_100g: float | None = None


class OpenFoodFactsProduct(BaseModel):
    code: str | None = None
    product_name: str | None = None
    brands: str | None = None
    ingredients_text: str | None = None
    ingredients: list[OpenFoodFactsIngredient] | None = None
    nutriscore_grade: str | None = None
    nutriments: OpenFoodFactsNutriments | None = None
    image_url: str | None = None
    image_front_url: str | None = None
    categories: str | None = None
    labels: str | None = None
    additives_tags: list[str] | None = None
    allergens: str | None = None


class OpenFoodFactsBarcodeResponse(BaseModel):
    code: str | None = None
    product: OpenFoodFactsProduct | None = None
    status: int
    status_verbose: str


class OpenFoodFactsSearchResponse(BaseModel):
    count: int
    page: int
    page_count: int
    page_size: int
    products: list[OpenFoodFactsProduct]
    skip: int
