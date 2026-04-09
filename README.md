# NutriScan Backend

Backend для проекта NutriScan на `FastAPI + SQLAlchemy + Alembic`.

## Документация

- [API reference](/C:/Users/kurba/OneDrive/Desktop/MyProjects/Nutriscan_backend/docs/API.md)
- [Environment variables](/C:/Users/kurba/OneDrive/Desktop/MyProjects/Nutriscan_backend/docs/ENVIRONMENT.md)
- [Production deployment](/C:/Users/kurba/OneDrive/Desktop/MyProjects/Nutriscan_backend/docs/DEPLOYMENT.md)
- [Oracle + cayatceek.uz deployment](/C:/Users/kurba/OneDrive/Desktop/MyProjects/Nutriscan_backend/docs/DEPLOYMENT_ORACLE_CAYATCEEK.md)
- [Operations runbook](/C:/Users/kurba/OneDrive/Desktop/MyProjects/Nutriscan_backend/docs/OPERATIONS.md)

## Что уже есть

- конфиг через `.env`
- PostgreSQL по умолчанию для локальной разработки
- миграции через `Alembic`
- `backend-first JWT auth` с refresh rotation
- расширенный product catalog с OFF-compatible сериализацией
- сущности `history`, `favorites`, `profile`, `settings`
- совместимые endpoints для `Open Food Facts`
- internal catalog write endpoint через API key
- rate limiting и readiness/live health endpoints
- smoke-тесты на основные сценарии

## Структура

```text
app/
  api/
    endpoints/
  core/
  db/
  models/
  schemas/
  service/
tests/
```

## Совместимые endpoints

Для Android-клиента реализованы пути с тем же контрактом, который раньше ходил в `world.openfoodfacts.org`:

- `GET /api/v0/product/{barcode}.json`
- `GET /cgi/search.pl`

Если upstream Open Food Facts недоступен, backend пытается отдать ответ из локальной базы NutriScan.

## Основные endpoints

Public:

- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/products/`
- `GET /api/v1/products/{product_id}`
- `GET /api/v1/products/barcode/{barcode}`
- `GET /api/v0/product/{barcode}.json`
- `GET /cgi/search.pl`

Auth:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`

User-only:

- `GET /api/v1/history`
- `POST /api/v1/history`
- `DELETE /api/v1/history/{scan_id}`
- `DELETE /api/v1/history`
- `GET /api/v1/products/favorites`
- `PUT /api/v1/products/{product_id}/favorite`
- `DELETE /api/v1/products/{product_id}/favorite`
- `GET /api/v1/profile`
- `PATCH /api/v1/profile`
- `GET /api/v1/settings`
- `PUT /api/v1/settings`

Internal:

- `POST /api/v1/internal/products/upsert`

## Локальный запуск

```bash
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Документация после старта:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## PostgreSQL через Docker

```bash
docker compose -f app/db/docker-compose.yml up -d
```

Вход в `psql` после старта контейнера:

```powershell
./app/db/connect-psql.ps1
```

## Миграции

Применить все миграции:

```bash
alembic upgrade head
```

Посмотреть текущую ревизию:

```bash
alembic current
```

## Тесты

```bash
python -m pytest -q
```
