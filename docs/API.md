# NutriScan Backend API

## Overview

Base API prefix:

- `public/user/internal API`: `/api/v1`
- `Open Food Facts compatibility`: `/api/v0` and `/cgi`

Authentication model:

- access token: JWT Bearer
- refresh token: opaque token in request body

Collection response format for non-compatibility endpoints:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "page_count": 0
}
```

## Public Endpoints

### Health

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/health`

### Product Catalog

- `GET /api/v1/products/`
  Query:
  - `query`
  - `page`
  - `page_size`

- `GET /api/v1/products/{product_id}`

- `GET /api/v1/products/barcode/{barcode}`

### Open Food Facts Compatibility

- `GET /api/v0/product/{barcode}.json`
- `GET /cgi/search.pl`
  Query:
  - `search_terms`
  - `page`
  - `page_size`
  - `json`
  - `fields`

These endpoints keep the Open Food Facts wire format expected by the current Android client.

## Auth Endpoints

### Register

- `POST /api/v1/auth/register`

Request:

```json
{
  "email": "user@example.com",
  "password": "supersecret123",
  "full_name": "Jane User"
}
```

Response:

```json
{
  "access_token": "jwt",
  "refresh_token": "opaque-token",
  "token_type": "bearer",
  "access_expires_at": "2026-04-09T12:00:00Z",
  "refresh_expires_at": "2026-05-09T11:45:00Z",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Jane User",
    "is_active": true,
    "created_at": "2026-04-09T11:45:00Z"
  }
}
```

### Login

- `POST /api/v1/auth/login`

### Refresh

- `POST /api/v1/auth/refresh`

Request:

```json
{
  "refresh_token": "opaque-token"
}
```

### Logout

- `POST /api/v1/auth/logout`

Request:

```json
{
  "refresh_token": "opaque-token"
}
```

### Current User

- `GET /api/v1/auth/me`
  Header:
  - `Authorization: Bearer <access_token>`

### Password Reset

- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`

Security note:

- reset request always returns the same `202` message
- reset token is never returned by the public API

## User-only Endpoints

All endpoints below require:

- `Authorization: Bearer <access_token>`

### Favorites

- `GET /api/v1/products/favorites`
- `PUT /api/v1/products/{product_id}/favorite`
- `DELETE /api/v1/products/{product_id}/favorite`

### History

- `GET /api/v1/history`
  Query:
  - `query`
  - `filter=all|favorites`
  - `page`
  - `page_size`

- `POST /api/v1/history`

Request:

```json
{
  "product_id": 123,
  "notes": "Scanned at home"
}
```

- `DELETE /api/v1/history/{scan_id}`
- `DELETE /api/v1/history`

### Profile

- `GET /api/v1/profile`
- `PATCH /api/v1/profile`

Request:

```json
{
  "full_name": "Updated Name"
}
```

### Settings

- `GET /api/v1/settings`
- `PUT /api/v1/settings`

Request:

```json
{
  "language": "ru",
  "is_language_manually_selected": true,
  "theme": "dark",
  "halal_mode_enabled": true,
  "healthy_mode_enabled": false,
  "vegan_mode_enabled": false,
  "notifications_enabled": true,
  "selected_allergens": ["MILK", "GLUTEN"],
  "onboarding_completed": true,
  "onboarding_shown": true
}
```

## Internal Endpoints

These endpoints are not for public clients.

- `POST /api/v1/internal/products/upsert`
  Header:
  - `X-Internal-API-Key: <internal_api_key>`

This route is intended for trusted backend ingestion jobs, admin tooling, or catalog sync pipelines.

## Error Semantics

Typical status codes:

- `200` success
- `201` created
- `202` accepted
- `400` validation or invalid reset token
- `401` missing or invalid authentication
- `404` entity not found
- `409` duplicate registration conflict
- `429` rate limit exceeded

## Current Limitations

- password reset delivery adapter is safe, but a real email provider still needs to be connected for production
- rate limiting currently uses in-memory storage and is suitable only for a single-instance deployment
- OFF-compatible endpoints are preserved to support Android migration, not as a long-term public contract
