# Deployment Guide

## Vercel (Serverless)

CyberSentinel can be deployed on Vercel's serverless platform. Note that WebSocket and background scheduler are skipped in this mode.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/arthurbarca374-create/cybersentinel)

### Prerequisites
- A PostgreSQL database (Vercel Postgres, Neon, Supabase, etc.)
- Vercel CLI: `npm i -g vercel`

### Setup

1. Set `DATABASE_URL` in your Vercel project environment variables to a PostgreSQL connection string
2. The app auto-detects Vercel via the `VERCEL` env var and skips background scheduler + WebSocket

```bash
vercel login
vercel --prod
```

### How it works

| Component | Vercel Behavior |
|---|---|
| **API** | Runs as serverless ASGI function via `vercel_app.py` |
| **Frontend** | Static files served from `frontend/static/` and `frontend/templates/` via Vercel CDN |
| **Database** | Use PostgreSQL via `DATABASE_URL`. SQLite will NOT persist on serverless |
| **WebSocket** | Not available on Vercel Functions; the route is registered but clients will receive an error |
| **Scheduler** | Skipped on Vercel (no long-running background tasks in serverless) |
| **Rate limiting** | Per-function memory; resets on cold starts |

### Limitations

- Scan runs are synchronous (no background worker)
- WebSocket progress updates are unavailable
- Scheduler/cron-based scans require an external cron service (e.g., cron-job.org)

---

## Quick Deploy (Single Server)

### Prerequisites
- Python 3.11+
- pip

```bash
git clone https://github.com/arthurbarca374-create/cybersentinel.git
cd cybersentinel
cp .env.example .env
# Edit .env — set SECRET_KEY (openssl rand -hex 32)
pip install -r requirements.txt
pip install -r requirements-mcp.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t cybersentinel .
docker run -d -p 8000:8000 --env-file .env -v $(pwd)/cybersentinel.db:/app/cybersentinel.db cybersentinel
```

### Docker Compose
```bash
docker compose up --build -d
```

## Production Deployments

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | 32+ char hex. Generate: `openssl rand -hex 32` |
| `DATABASE_URL` | No | Default: `sqlite:///./cybersentinel.db`. Use `postgresql://user:pass@host/db` for production |
| `GITHUB_CLIENT_ID` | No | For GitHub OAuth login |
| `GITHUB_CLIENT_SECRET` | No | For GitHub OAuth login |
| `ANTHROPIC_API_KEY` | No | Claude AI analysis |
| `OPENAI_API_KEY` | No | GPT-4o mini AI analysis |
| `VIRUSTOTAL_API_KEY` | No | Threat intel lookups |
| `SHODAN_API_KEY` | No | Threat intel lookups |
| `ABUSEIPDB_API_KEY` | No | Threat intel lookups |
| `DISCORD_WEBHOOK_URL` | No | Alert notifications |
| `TELEGRAM_BOT_TOKEN` | No | Alert notifications |
| `TELEGRAM_CHAT_ID` | No | Alert notifications |
| `ETHERSCAN_API_KEY` | No | Ethereum analysis |
| `FRONTEND_URL` | No | CORS origin. Update for custom domains |
| `ALLOWED_HOSTS` | No | Host header validation. Default: `["*"]` |
| `FREE_TRIAL_DAYS` | No | Trial duration. Default: `14` |
| `FREE_TRIAL_SCANS` | No | Free scan count. Default: `10` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | JWT lifetime. Default: `1440` (24h) |
| `DEBUG` | No | Enable debug mode. Default: `false` |

### Switching to PostgreSQL

1. Set `DATABASE_URL=postgresql://user:password@host:5432/cybersentinel`
2. Install psycopg2: `pip install psycopg2-binary`
3. Run migrations: tables are auto-created on startup

### Background Worker

For production, run the worker as a separate process:

```bash
python worker.py
```

The worker handles scan queue processing, stuck scan cleanup, and periodic threat intel updates.

### MCP Server (AI Tools)

Run alongside the API for AI agent integrations:

```bash
python mcp_server.py
```

### Running Behind a Reverse Proxy

Nginx example:

```nginx
server {
    listen 80;
    server_name sentinel.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Infrastructure as Code

### Render
Config in `cybersentinel-infra/render.yaml` — Web Service + Background Worker

### Railway
Config in `cybersentinel-infra/railway.json`

### Terraform
Full AWS ECS/Fargate deployment in `cybersentinel-read-and-deploy/terraform/`

## Health Checks

```bash
# Basic health
curl http://localhost:8000/api/health

# Detailed status
curl http://localhost:8000/api/health/status

# Docker healthcheck (built-in)
# Runs every 30s, 10s timeout, 3 retries
```

## Backup

Use the built-in backup script:

```bash
bash scripts/backup.sh
```

This creates a timestamped archive of the database and `.env` file.
