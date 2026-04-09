from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.favorite_product import FavoriteProduct
from app.models.password_reset_token import PasswordResetToken
from app.models.product import Product
from app.models.scan_history import ScanHistory
from app.models.user import User
from app.models.user_session import UserSession
from app.models.user_settings import UserSettings
from app.schemas.product import InternalProductUpsertRequest


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str | None,
    password_hash: str,
) -> User:
    user = User(email=email, full_name=full_name, password_hash=password_hash)
    db.add(user)
    db.flush()
    db.add(UserSettings(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


def update_user_full_name(db: Session, *, user: User, full_name: str | None) -> User:
    user.full_name = full_name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_settings(db: Session, user_id: int) -> UserSettings | None:
    statement = select(UserSettings).where(UserSettings.user_id == user_id)
    return db.scalar(statement)


def get_or_create_user_settings(db: Session, user_id: int) -> UserSettings:
    settings = get_user_settings(db, user_id)
    if settings is not None:
        return settings

    settings = UserSettings(user_id=user_id)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_user_settings(db: Session, *, settings: UserSettings, payload: dict[str, object]) -> UserSettings:
    for field, value in payload.items():
        setattr(settings, field, value)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def create_user_session(
    db: Session,
    *,
    user_id: int,
    refresh_token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip_address: str | None,
) -> UserSession:
    session = UserSession(
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_session_by_id(db: Session, session_id: int) -> UserSession | None:
    statement = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(UserSession.id == session_id)
    )
    return db.scalar(statement)


def get_user_session_by_refresh_hash(db: Session, refresh_token_hash: str) -> UserSession | None:
    statement = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(UserSession.refresh_token_hash == refresh_token_hash)
    )
    return db.scalar(statement)


def revoke_user_session(db: Session, session: UserSession) -> UserSession:
    session.revoked_at = utc_now()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def touch_user_session(db: Session, session: UserSession) -> UserSession:
    session.last_used_at = utc_now()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def revoke_all_user_sessions(db: Session, user_id: int) -> None:
    statement = select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
    sessions = list(db.scalars(statement))
    if not sessions:
        return

    now = utc_now()
    for session in sessions:
        session.revoked_at = now
        db.add(session)
    db.commit()


def delete_expired_user_sessions(db: Session, before: datetime) -> None:
    statement = delete(UserSession).where(UserSession.expires_at <= before).execution_options(
        synchronize_session=False
    )
    db.execute(statement)
    db.commit()


def create_password_reset_token(
    db: Session,
    *,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> PasswordResetToken:
    token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_password_reset_token(db: Session, token_hash: str) -> PasswordResetToken | None:
    statement = (
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(PasswordResetToken.token_hash == token_hash)
    )
    return db.scalar(statement)


def mark_password_reset_token_used(db: Session, token: PasswordResetToken) -> PasswordResetToken:
    token.used_at = utc_now()
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def delete_expired_password_reset_tokens(db: Session, before: datetime) -> None:
    statement = delete(PasswordResetToken).where(
        or_(
            PasswordResetToken.expires_at <= before,
            PasswordResetToken.used_at.is_not(None),
        )
    ).execution_options(synchronize_session=False)
    db.execute(statement)
    db.commit()


def update_user_password(db: Session, *, user: User, password_hash: str) -> User:
    user.password_hash = password_hash
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_product_by_barcode(db: Session, barcode: str) -> Product | None:
    statement = select(Product).where(Product.barcode == barcode)
    return db.scalar(statement)


def _product_search_statement(query: str):
    normalized_query = f"%{query.strip()}%"
    return or_(
        Product.name.ilike(normalized_query),
        Product.brand.ilike(normalized_query),
        Product.barcode.ilike(normalized_query),
    )


def list_products(db: Session, *, limit: int, offset: int) -> list[Product]:
    statement = (
        select(Product)
        .order_by(Product.updated_at.desc(), Product.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement))


def search_products(db: Session, *, query: str, limit: int, offset: int) -> list[Product]:
    statement = (
        select(Product)
        .where(_product_search_statement(query))
        .order_by(Product.updated_at.desc(), Product.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement))


def count_products(db: Session, *, query: str | None = None) -> int:
    statement = select(func.count()).select_from(Product)
    if query and query.strip():
        statement = statement.where(_product_search_statement(query))
    return int(db.scalar(statement) or 0)


def upsert_product(db: Session, product_in: InternalProductUpsertRequest) -> Product:
    product = get_product_by_barcode(db, product_in.barcode) if product_in.barcode else None
    if product is None:
        product = Product()

    payload = product_in.model_dump()
    payload.pop("nutriments", None)
    payload.pop("ingredients", None)
    additives_tags = payload.pop("additives_tags", [])

    for field, value in payload.items():
        setattr(product, field, value)

    product.ingredients_json = [ingredient.model_dump() for ingredient in product_in.ingredients]
    product.additives_tags_json = additives_tags or None
    product.nutriments_json = (
        product_in.nutriments.model_dump(by_alias=True) if product_in.nutriments is not None else None
    )

    if product_in.nutriments is not None:
        product.calories = (
            int(product_in.nutriments.energy_kcal_100g)
            if product_in.nutriments.energy_kcal_100g is not None
            else None
        )
        product.protein = product_in.nutriments.proteins_100g
        product.fat = product_in.nutriments.fat_100g
        product.carbs = product_in.nutriments.carbohydrates_100g

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_favorite_products(db: Session, *, user_id: int, query: str | None, limit: int, offset: int) -> list[Product]:
    statement = (
        select(Product)
        .join(FavoriteProduct, FavoriteProduct.product_id == Product.id)
        .where(FavoriteProduct.user_id == user_id)
        .order_by(FavoriteProduct.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if query and query.strip():
        statement = statement.where(_product_search_statement(query))
    return list(db.scalars(statement))


def count_favorite_products(db: Session, *, user_id: int, query: str | None = None) -> int:
    statement = (
        select(func.count())
        .select_from(FavoriteProduct)
        .join(Product, Product.id == FavoriteProduct.product_id)
        .where(FavoriteProduct.user_id == user_id)
    )
    if query and query.strip():
        statement = statement.where(_product_search_statement(query))
    return int(db.scalar(statement) or 0)


def get_favorite_product(db: Session, *, user_id: int, product_id: int) -> FavoriteProduct | None:
    statement = select(FavoriteProduct).where(
        FavoriteProduct.user_id == user_id,
        FavoriteProduct.product_id == product_id,
    )
    return db.scalar(statement)


def add_favorite_product(db: Session, *, user_id: int, product_id: int) -> FavoriteProduct:
    favorite = FavoriteProduct(user_id=user_id, product_id=product_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite_product(db: Session, favorite: FavoriteProduct) -> None:
    db.delete(favorite)
    db.commit()


def favorite_product_ids_for_user(db: Session, *, user_id: int, product_ids: list[int]) -> set[int]:
    if not product_ids:
        return set()
    statement = select(FavoriteProduct.product_id).where(
        FavoriteProduct.user_id == user_id,
        FavoriteProduct.product_id.in_(product_ids),
    )
    return set(db.scalars(statement))


def create_scan_history(
    db: Session,
    *,
    scan_id: str,
    user_id: int,
    product_id: int,
    scanned_at: datetime,
    notes: str | None,
) -> ScanHistory:
    scan = ScanHistory(
        id=scan_id,
        user_id=user_id,
        product_id=product_id,
        scanned_at=scanned_at,
        notes=notes,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def list_scan_history(
    db: Session,
    *,
    user_id: int,
    query: str | None,
    favorites_only: bool,
    limit: int,
    offset: int,
) -> list[ScanHistory]:
    statement = (
        select(ScanHistory)
        .options(joinedload(ScanHistory.product))
        .join(Product, Product.id == ScanHistory.product_id)
        .where(ScanHistory.user_id == user_id)
        .order_by(ScanHistory.scanned_at.desc(), ScanHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if favorites_only:
        statement = statement.join(
            FavoriteProduct,
            (FavoriteProduct.product_id == ScanHistory.product_id) & (FavoriteProduct.user_id == user_id),
        )
    if query and query.strip():
        statement = statement.where(_product_search_statement(query))
    return list(db.scalars(statement).unique())


def count_scan_history(
    db: Session,
    *,
    user_id: int,
    query: str | None,
    favorites_only: bool,
) -> int:
    statement = (
        select(func.count())
        .select_from(ScanHistory)
        .join(Product, Product.id == ScanHistory.product_id)
        .where(ScanHistory.user_id == user_id)
    )
    if favorites_only:
        statement = statement.join(
            FavoriteProduct,
            (FavoriteProduct.product_id == ScanHistory.product_id) & (FavoriteProduct.user_id == user_id),
        )
    if query and query.strip():
        statement = statement.where(_product_search_statement(query))
    return int(db.scalar(statement) or 0)


def get_scan_history(db: Session, *, user_id: int, scan_id: str) -> ScanHistory | None:
    statement = (
        select(ScanHistory)
        .options(joinedload(ScanHistory.product))
        .where(ScanHistory.user_id == user_id, ScanHistory.id == scan_id)
    )
    return db.scalar(statement)


def delete_scan_history(db: Session, scan: ScanHistory) -> None:
    db.delete(scan)
    db.commit()


def delete_all_scan_history(db: Session, *, user_id: int) -> None:
    statement = delete(ScanHistory).where(ScanHistory.user_id == user_id)
    db.execute(statement)
    db.commit()
