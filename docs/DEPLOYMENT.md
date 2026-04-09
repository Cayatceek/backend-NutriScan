# NutriScan Production Deployment Guide

## Assumptions

This guide assumes:

- Ubuntu 24.04 VPS
- one backend server
- Docker Engine + Docker Compose plugin
- Nginx on the host machine
- Let's Encrypt for TLS
- API domain like `api.example.com`
- project is deployed from repository checkout at `/opt/nutriscan-backend`

This is the recommended first production setup for the current project.

## Target Architecture

- `Nginx` on host terminates HTTPS
- `Nginx` proxies traffic to `127.0.0.1:8000`
- `Docker Compose` runs:
  - `api`
  - `postgres`
- `alembic` runs inside the API image before each rollout

## 1. Prepare Domain

In your DNS provider:

- create an `A` record for `api.example.com`
- point it to your VPS public IP

Wait until DNS resolves:

```bash
nslookup api.example.com
```

## 2. Prepare Server

Connect to the server:

```bash
ssh root@your-server-ip
```

Update packages:

```bash
apt update && apt upgrade -y
```

Install base packages:

```bash
apt install -y ca-certificates curl git nginx certbot python3-certbot-nginx ufw
```

Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

Open firewall:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 3. Upload Project To Server

Create project directory:

```bash
mkdir -p /opt/nutriscan-backend
cd /opt/nutriscan-backend
```

Clone the repository or upload the project files there.

Example:

```bash
git clone <your-repo-url> .
```

## 4. Prepare Production Env

Copy the production env template:

```bash
cp deploy/.env.production.example deploy/.env.production
```

Edit it:

```bash
nano deploy/.env.production
```

Set at minimum:

- strong `POSTGRES_PASSWORD`
- strong `NUTRISCAN_JWT_SECRET`
- strong `NUTRISCAN_REFRESH_TOKEN_PEPPER`
- strong `NUTRISCAN_PASSWORD_RESET_TOKEN_PEPPER`
- strong `NUTRISCAN_INTERNAL_API_KEY`
- correct `NUTRISCAN_ALLOWED_ORIGINS`
- `NUTRISCAN_ENVIRONMENT=production`
- `NUTRISCAN_DEBUG=false`

## 5. Start Containers

Build and start:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d --build
```

Run migrations:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production run --rm api alembic upgrade head
```

Check container status:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production ps
```

## 6. Configure Nginx

Copy the example config:

```bash
cp deploy/nginx/nutriscan.conf.example /etc/nginx/sites-available/nutriscan.conf
```

Edit the domain:

```bash
nano /etc/nginx/sites-available/nutriscan.conf
```

Replace:

- `api.example.com` with your real domain

Enable the site:

```bash
ln -s /etc/nginx/sites-available/nutriscan.conf /etc/nginx/sites-enabled/nutriscan.conf
nginx -t
systemctl reload nginx
```

## 7. Issue TLS Certificate

After DNS points to the server and Nginx is serving HTTP:

```bash
certbot --nginx -d api.example.com
```

Enable automatic renewal check:

```bash
systemctl status certbot.timer
```

## 8. Smoke Check

From the server:

```bash
curl http://127.0.0.1:8000/api/v1/health/ready
curl https://api.example.com/api/v1/health/ready
curl https://api.example.com/docs
```

Check logs:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production logs -f api
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production logs -f db
```

## 9. Update Procedure

On every deploy:

```bash
cd /opt/nutriscan-backend
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production build
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production run --rm api alembic upgrade head
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d
```

Smoke check again:

```bash
curl https://api.example.com/api/v1/health/ready
```

## 10. Rollback Plan

If a deploy fails:

1. Return to the previous commit.
2. Rebuild the old image.
3. Start the old containers.
4. Restore database only if the migration was destructive and rollback-safe.

Example:

```bash
git checkout <previous-stable-commit>
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production build
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d
```

Important:

- never downgrade production DB blindly without a tested rollback path
- take a backup before every schema-changing release

## 11. Backups

Create DB backup:

```bash
docker exec nutriscan_db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > nutriscan-$(date +%F-%H%M).sql
```

Recommended:

- daily backup via cron
- store copies outside the VPS
- test restore regularly

Restore backup:

```bash
cat backup.sql | docker exec -i nutriscan_db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## 12. Operational Warnings

- current rate limiting is in-memory and is suitable for one server instance
- password reset flow is secure, but production email delivery still needs a real provider
- internal catalog ingestion must be protected by a strong `NUTRISCAN_INTERNAL_API_KEY`
- DB port should not be exposed publicly in production unless there is a strict reason

## 13. Recommended Next Production Tasks

- add real email provider for password reset
- move rate limiting to Redis
- add centralized logs and monitoring
- add staging environment
- add CI/CD pipeline for tests and migrations
- add automated backups
