# NutriScan Operations Runbook

## Useful Commands

Project root on server:

```bash
cd /opt/nutriscan-backend
```

Start services:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d
```

Stop services:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production down
```

Restart API only:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production restart api
```

## Logs

API logs:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production logs -f api
```

Database logs:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production logs -f db
```

## Health Checks

Local container check:

```bash
curl http://127.0.0.1:8000/api/v1/health/live
curl http://127.0.0.1:8000/api/v1/health/ready
```

Public domain check:

```bash
curl https://api.example.com/api/v1/health/ready
```

## Database

Open SQL shell:

```bash
docker exec -it nutriscan_db psql -U nutriscan_user -d nutriscan
```

Run migrations:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production run --rm api alembic upgrade head
```

Check migration version:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production run --rm api alembic current
```

## Rotation Tasks

### Rotate internal API key

1. Generate a new key.
2. Replace `NUTRISCAN_INTERNAL_API_KEY` in `deploy/.env.production`.
3. Restart API:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d
```

4. Update all trusted internal clients.

### Rotate JWT and token peppers

This will invalidate active sessions and password reset tokens.

1. Update:
   - `NUTRISCAN_JWT_SECRET`
   - `NUTRISCAN_REFRESH_TOKEN_PEPPER`
   - `NUTRISCAN_PASSWORD_RESET_TOKEN_PEPPER`
2. Restart API.

## Incident Checklist

If API returns `502/503`:

1. Check Nginx status:

```bash
systemctl status nginx
```

2. Check compose services:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production ps
```

3. Check API health locally:

```bash
curl http://127.0.0.1:8000/api/v1/health/ready
```

4. Check logs.
5. Check DB health.

If DB is down:

1. Check disk usage:

```bash
df -h
```

2. Check Postgres container logs.
3. Restore from the latest healthy backup if needed.

## Pre-release Checklist

- `python -m pytest -q` passed locally
- `alembic upgrade head` tested on a clean DB
- backup created before production rollout
- `deploy/.env.production` reviewed
- domain and TLS active
- healthcheck returns `200`
