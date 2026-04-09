# NutriScan Environment Variables

## Application

- `NUTRISCAN_APP_NAME`
  Default: `NutriScan API`

- `NUTRISCAN_APP_VERSION`
  Example: `1.0.0`

- `NUTRISCAN_DEBUG`
  Use `false` in production.

- `NUTRISCAN_ENVIRONMENT`
  Typical values:
  - `development`
  - `staging`
  - `production`

- `NUTRISCAN_API_V1_PREFIX`
  Default: `/api/v1`

## Database

- `NUTRISCAN_DATABASE_URL`
  Example:
  - `postgresql+psycopg://nutriscan_user:password@db:5432/nutriscan`

Related compose variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

## CORS

- `NUTRISCAN_ALLOWED_ORIGINS`
  JSON array or comma-separated string.

Examples:

```env
NUTRISCAN_ALLOWED_ORIGINS=["https://app.example.com","https://api.example.com"]
```

## JWT And Tokens

- `NUTRISCAN_JWT_SECRET`
  Required in production.

- `NUTRISCAN_JWT_ISSUER`
  Default: `nutriscan-backend`

- `NUTRISCAN_ACCESS_TOKEN_TTL_MINUTES`
  Default: `15`

- `NUTRISCAN_REFRESH_TOKEN_TTL_DAYS`
  Default: `30`

- `NUTRISCAN_REFRESH_TOKEN_PEPPER`
  Required in production.

- `NUTRISCAN_PASSWORD_RESET_TOKEN_PEPPER`
  Required in production.

- `NUTRISCAN_PASSWORD_RESET_TOKEN_TTL_MINUTES`
  Default: `30`

- `NUTRISCAN_DEBUG_PASSWORD_RESET_TOKENS`
  Keep `false` in production.

## Internal API

- `NUTRISCAN_INTERNAL_API_KEY`
  Used for internal catalog ingestion.

## Open Food Facts Compatibility

- `NUTRISCAN_OPEN_FOOD_FACTS_BASE_URL`
  Default: `https://world.openfoodfacts.org`

- `NUTRISCAN_OPEN_FOOD_FACTS_USER_AGENT`
  Default: `NutriScan/1.0 (Android)`

- `NUTRISCAN_REQUEST_TIMEOUT_SECONDS`
  Default: `30`

## Rate Limiting

- `NUTRISCAN_AUTH_RATE_LIMIT_COUNT`
- `NUTRISCAN_AUTH_RATE_LIMIT_WINDOW_SECONDS`
- `NUTRISCAN_OFF_RATE_LIMIT_COUNT`
- `NUTRISCAN_OFF_RATE_LIMIT_WINDOW_SECONDS`

Important:

- the current implementation is in-memory
- it is safe for one server instance
- for multi-instance production, move rate limiting to Redis or another shared backend

## Recommended Production Defaults

```env
NUTRISCAN_DEBUG=false
NUTRISCAN_ENVIRONMENT=production
NUTRISCAN_ACCESS_TOKEN_TTL_MINUTES=15
NUTRISCAN_REFRESH_TOKEN_TTL_DAYS=30
NUTRISCAN_DEBUG_PASSWORD_RESET_TOKENS=false
```
