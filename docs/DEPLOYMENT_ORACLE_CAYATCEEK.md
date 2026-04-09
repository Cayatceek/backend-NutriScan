# NutriScan Deployment: Oracle Ubuntu + api-nutriscan.cayatceek.uz

## Current State

Server:

- provider: Oracle Cloud Ubuntu server
- public IP: `92.5.52.247`

API domain:

- `https://api-nutriscan.cayatceek.uz`

Important DNS note:

- on **April 9, 2026**, `api-nutriscan.cayatceek.uz` resolves to `188.114.96.1` and `188.114.97.1`
- that means the hostname is currently proxied by Cloudflare
- your origin server is still Oracle, but public clients hit Cloudflare first

Because of that, the cleanest setup is:

- Oracle VPS as origin
- Cloudflare proxy enabled
- Cloudflare SSL mode set to `Full (strict)`
- HTTPS on the origin via either:
  - Let’s Encrypt on the Oracle server
  - or Cloudflare Origin CA certificate

For your current setup, I recommend:

- **Option A (Recommended): Cloudflare Origin CA + Full (strict)**

This is the most natural setup because your hostname is already proxied by Cloudflare.

## Final Architecture

- Browser/mobile client -> Cloudflare -> Oracle Ubuntu server -> Nginx -> Docker API container
- PostgreSQL stays private inside Docker
- API container listens on `127.0.0.1:8000` through host mapping
- Nginx serves the public hostname `api-nutriscan.cayatceek.uz`

## 1. Oracle Cloud Network Rules

In OCI, open ingress to the instance for:

- `22/tcp`
- `80/tcp`
- `443/tcp`

Do this in the instance subnet security rules.

Recommended in OCI:

- use a **Network Security Group (NSG)** if available
- if you use Security Lists instead, make sure the subnet allows the same ports

Also remember:

- OCI images can still have local firewall rules on the VM, so both OCI rules and host firewall rules must allow the traffic

## 2. Connect To Server

```bash
ssh ubuntu@92.5.52.247
```

If your Oracle image uses another user, replace `ubuntu`.

## 3. Prepare Ubuntu Server

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl git nginx ufw
```

Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

Log out and back in once if you want Docker without `sudo`.

Host firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## 4. Upload Project

```bash
sudo mkdir -p /opt/nutriscan-backend
sudo chown -R $USER:$USER /opt/nutriscan-backend
cd /opt/nutriscan-backend
git clone <YOUR_REPO_URL> .
```

## 5. Prepare Production Environment

```bash
cp deploy/.env.production.example deploy/.env.production
nano deploy/.env.production
```

Use values like:

```env
POSTGRES_DB=nutriscan
POSTGRES_USER=nutriscan_user
POSTGRES_PASSWORD=<strong-db-password>

NUTRISCAN_APP_NAME=NutriScan API
NUTRISCAN_APP_VERSION=1.0.0
NUTRISCAN_DEBUG=false
NUTRISCAN_ENVIRONMENT=production
NUTRISCAN_API_V1_PREFIX=/api/v1
NUTRISCAN_ALLOWED_ORIGINS=["https://api-nutriscan.cayatceek.uz"]
NUTRISCAN_JWT_SECRET=<strong-jwt-secret>
NUTRISCAN_JWT_ISSUER=nutriscan-backend
NUTRISCAN_ACCESS_TOKEN_TTL_MINUTES=15
NUTRISCAN_REFRESH_TOKEN_TTL_DAYS=30
NUTRISCAN_REFRESH_TOKEN_PEPPER=<strong-refresh-pepper>
NUTRISCAN_PASSWORD_RESET_TOKEN_PEPPER=<strong-reset-pepper>
NUTRISCAN_INTERNAL_API_KEY=<strong-internal-api-key>
NUTRISCAN_OPEN_FOOD_FACTS_BASE_URL=https://world.openfoodfacts.org
NUTRISCAN_OPEN_FOOD_FACTS_USER_AGENT=NutriScan/1.0 (Android)
NUTRISCAN_REQUEST_TIMEOUT_SECONDS=30
NUTRISCAN_PASSWORD_RESET_TOKEN_TTL_MINUTES=30
NUTRISCAN_DEBUG_PASSWORD_RESET_TOKENS=false
NUTRISCAN_AUTH_RATE_LIMIT_COUNT=10
NUTRISCAN_AUTH_RATE_LIMIT_WINDOW_SECONDS=60
NUTRISCAN_OFF_RATE_LIMIT_COUNT=60
NUTRISCAN_OFF_RATE_LIMIT_WINDOW_SECONDS=60
```

If you later add a web frontend on another domain, add that frontend origin to `NUTRISCAN_ALLOWED_ORIGINS`.

## 6. Start Containers

```bash
cd /opt/nutriscan-backend
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d --build
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production run --rm api alembic upgrade head
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production ps
```

## 7. Configure Nginx On Oracle Server

Copy the ready file from the repository:

```bash
sudo cp deploy/nginx/api-nutriscan.cayatceek.uz.conf /etc/nginx/sites-available/api-nutriscan.cayatceek.uz.conf
sudo ln -s /etc/nginx/sites-available/api-nutriscan.cayatceek.uz.conf /etc/nginx/sites-enabled/api-nutriscan.cayatceek.uz.conf
sudo nginx -t
sudo systemctl reload nginx
```

At this point HTTP on port 80 should proxy to your API.

## 8. Cloudflare Setup

In Cloudflare DNS:

- keep the record for `api-nutriscan.cayatceek.uz`
- origin should point to `92.5.52.247`
- proxy can stay enabled

In Cloudflare SSL/TLS:

- set encryption mode to **Full (strict)**

## 9. TLS On Origin: Recommended Variant

### Option A: Cloudflare Origin CA (Recommended)

Because the hostname is already proxied by Cloudflare, this is the cleanest route.

In Cloudflare dashboard:

1. Go to `SSL/TLS` -> `Origin Server`
2. Create an Origin Certificate for `api-nutriscan.cayatceek.uz`
3. Save:
   - certificate
   - private key

On the Oracle server:

```bash
sudo mkdir -p /etc/ssl/nutriscan
sudo nano /etc/ssl/nutriscan/origin.crt
sudo nano /etc/ssl/nutriscan/origin.key
sudo chmod 600 /etc/ssl/nutriscan/origin.key
```

Then switch Nginx config to HTTPS:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name api-nutriscan.cayatceek.uz;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api-nutriscan.cayatceek.uz;

    ssl_certificate /etc/ssl/nutriscan/origin.crt;
    ssl_certificate_key /etc/ssl/nutriscan/origin.key;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
    }
}
```

Then:

```bash
sudo cp deploy/nginx/api-nutriscan.cayatceek.uz.ssl.conf.example /etc/nginx/sites-available/api-nutriscan.cayatceek.uz.conf
sudo nginx -t
sudo systemctl reload nginx
```

### Option B: Let’s Encrypt On Origin

If you prefer a public CA certificate directly on the origin:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api-nutriscan.cayatceek.uz
```

This also works with Cloudflare, but for your current proxied setup, Origin CA is usually simpler and more aligned.

## 10. Smoke Checks

From the Oracle server:

```bash
curl http://127.0.0.1:8000/api/v1/health/ready
curl -I http://api-nutriscan.cayatceek.uz
curl -I https://api-nutriscan.cayatceek.uz
curl https://api-nutriscan.cayatceek.uz/api/v1/health/ready
```

Expected result:

- local readiness returns `200`
- public HTTPS returns `200`

## 11. Logs

```bash
cd /opt/nutriscan-backend
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production logs -f api
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production logs -f db
sudo journalctl -u nginx -f
```

## 12. Update Procedure

```bash
cd /opt/nutriscan-backend
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production build
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production run --rm api alembic upgrade head
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d
curl https://api-nutriscan.cayatceek.uz/api/v1/health/ready
```

## 13. Backup

```bash
cd /opt/nutriscan-backend
docker exec nutriscan_db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > nutriscan-$(date +%F-%H%M).sql
```

## 14. Recommended Hardening After First Deploy

- restrict origin access to Cloudflare traffic only
- add Authenticated Origin Pulls in Cloudflare
- move rate limiting to Redis
- add real email provider for password reset
- add automated backups and off-server storage

## 15. The Fastest Path For You

If you want the least painful path for this exact setup:

1. Open OCI ingress for `22/80/443`
2. Deploy Docker stack on `92.5.52.247`
3. Put Nginx in front
4. Use **Cloudflare Origin CA**
5. Set Cloudflare SSL mode to **Full (strict)**
6. Smoke test `https://api-nutriscan.cayatceek.uz/api/v1/health/ready`
