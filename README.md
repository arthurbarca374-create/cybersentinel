# CyberSentinel

> Community-driven security platform — free to join, open to all.

[![CI](https://github.com/arthurbarca374-create/cybersentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/arthurbarca374-create/cybersentinel/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/arthurbarca374-create/cybersentinel)

CyberSentinel is a self-hostable, open-source security scanning platform with a community portal. Users can sign up (or log in with GitHub), get a **14-day free trial with 10 scans**, and connect with a growing security community.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Usage Guide](docs/USAGE.md) | Authentication, scans, API keys, WebSocket, teams |
| [API Reference](docs/API_REFERENCE.md) | Complete API endpoint reference with examples |
| [Integrations](docs/INTEGRATIONS.md) | AI analysis, threat intel, blockchain, notifications |
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, component relationships |
| [Deployment](docs/DEPLOYMENT.md) | Docker, production, reverse proxy, Terraform |
| [Development](docs/DEVELOPMENT.md) | Setup, testing, code quality, adding features |
| [Community Guide](docs/COMMUNITY.md) | Contributing, bug reports, feature requests, code of conduct |

---

## Features

| Feature | Status |
|---------|--------|
| GitHub OAuth login | ✅ |
| Email/password registration | ✅ |
| 14-day free trial with 10 scans | ✅ |
| JWT session management | ✅ |
| Community member directory | ✅ |
| Vulnerability scan engine (quick/full/service/vuln/web) | ✅ |
| AI-assisted analysis (Claude/OpenAI/local LLM) | ✅ |
| Team / org support with invitations | ✅ |
| Threat intel (VirusTotal, Shodan, AbuseIPDB) | ✅ |
| Blockchain wallet analysis (BTC/ETH/XMR) | ✅ |
| Scheduled scans (cron expression) | ✅ |
| Real-time scan progress (WebSocket) | ✅ |
| API key management (programmatic access) | ✅ |
| Notifications (Discord webhook / Telegram bot) | ✅ |
| Rate limiting & security headers | ✅ |
| MCP server (AI tool protocol) | ✅ |
| Background worker (scan queue, cleanup) | ✅ |
| Docker deployment | ✅ |

---

## Stack (all free tools)

- **Backend**: Python 3.11 · FastAPI · SQLAlchemy · SQLite
- **Auth**: GitHub OAuth · JWT (python-jose) · sha256_crypt
- **Frontend**: Vanilla HTML/CSS/JS — no paid frameworks
- **CI/CD**: GitHub Actions (lint, type check, security scan, test, Docker smoke test)
- **Container**: Docker + docker-compose
- **APS**: MCP protocol, WebSocket, slowapi rate limiting

---

## Quick Start

### 1. Clone & configure
```bash
git clone https://github.com/arthurbarca374-create/cybersentinel.git
cd cybersentinel
cp .env.example .env
# Edit .env — add SECRET_KEY (openssl rand -hex 32) and any API keys
```

### 2. Run with Docker (easiest)
```bash
docker-compose up --build
```
Open http://localhost:8000

### 3. Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Deploy on Vercel (serverless)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/arthurbarca374-create/cybersentinel)

Requires PostgreSQL. See [Deployment Guide](docs/DEPLOYMENT.md#vercel-serverless) for details.

### 5. Or run individual components
```bash
python scripts/run.sh api     # API server only
python scripts/run.sh worker  # Background worker only
python mcp_server.py          # MCP AI tool server
```

---

## Project Structure

```
cybersentinel/
├── backend/
│   ├── api/routes/       # 10 route modules (all API endpoints)
│   ├── core/             # config, security, limiter, csrf, http_client
│   ├── db/               # SQLAlchemy engine + session
│   ├── models/           # 6 ORM models + Pydantic schemas
│   └── services/         # 12 service modules (business logic)
├── frontend/
│   ├── static/           # CSS, JS
│   └── templates/        # HTML pages
├── tests/backend/        # 46 pytest tests
├── scripts/              # run.sh, backup.sh, setup.sh, cron jobs
├── .github/workflows/    # CI pipeline with lint/test/Docker
├── main.py               # FastAPI app entry point
├── vercel_app.py         # Vercel serverless ASGI entry point
├── vercel.json           # Vercel deployment configuration
├── worker.py             # Background worker process
├── mcp_server.py         # MCP AI tool protocol server
├── requirements.txt
├── requirements-mcp.txt
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml        # pytest, mypy, bandit, coverage config
└── .env.example          # All config vars documented
```

---

## API Reference

Interactive docs at `/api/docs` (Swagger) and `/api/redoc`.

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | — | Register email/password |
| POST | `/api/auth/login` | — | Login, receive JWT |
| GET | `/api/auth/github` | — | GitHub OAuth login |
| GET | `/api/auth/github/callback` | — | OAuth callback |
| GET | `/api/auth/me` | JWT/API key | Current user profile |

### User & Trial
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/users/trial/status` | JWT/API key | Trial status & remaining scans |
| POST | `/api/users/trial/use-scan` | JWT/API key | Consume 1 scan credit |
| GET | `/api/users/community/members` | — | Public member directory |

### Scans
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/scans/types` | — | Available scan types |
| POST | `/api/scans/targets` | JWT/API key | Add scan target (name, host) |
| GET | `/api/scans/targets` | JWT/API key | List my targets |
| DELETE | `/api/scans/targets/{id}` | JWT/API key | Remove target |
| POST | `/api/scans/run` | JWT/API key | Start scan (uses 1 credit) |
| GET | `/api/scans` | JWT/API key | List my scans |
| GET | `/api/scans/{id}` | JWT/API key | Scan details |
| GET | `/api/scans/{id}/findings` | JWT/API key | Scan findings |

### WebSocket
| Pattern | Auth | Description |
|---------|------|-------------|
| WS `/api/ws/scan/{id}?token=` | JWT query | Real-time scan progress |

### AI Analysis
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/ai/analyze` | JWT/API key | AI analysis of completed scan |
| GET | `/api/ai/models` | — | Available AI models |

### Organizations & Teams
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/orgs` | JWT/API key | Create org |
| GET | `/api/orgs` | JWT/API key | List my orgs |
| GET | `/api/orgs/{id}` | JWT/API key | Org details |
| GET | `/api/orgs/{id}/members` | JWT/API key | Org members |
| POST | `/api/orgs/{id}/teams` | JWT/API key | Create team |
| GET | `/api/orgs/{id}/teams` | JWT/API key | List teams |

### Threat Intelligence
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/threat/lookup` | JWT/API key | Lookup IP/domain/hash |
| GET | `/api/threat/feed` | JWT/API key | Threat intel feed |
| GET | `/api/threat/stats` | JWT/API key | Intel statistics |
| POST | `/api/threat/reports` | JWT/API key | Create threat report |
| GET | `/api/threat/reports` | JWT/API key | List reports |

### Blockchain
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/blockchain/analyze` | JWT/API key | Analyze BTC/ETH/XMR address |
| GET | `/api/blockchain/analyze/{chain}/{address}` | JWT/API key | Analyze by path |
| GET | `/api/blockchain/analyses` | JWT/API key | Recent analyses |
| POST | `/api/blockchain/recover` | JWT/API key | Start wallet recovery |

### API Keys
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/keys` | JWT | Generate API key (returns once) |
| GET | `/api/keys` | JWT/API key | List my API keys |
| DELETE | `/api/keys/{id}` | JWT/API key | Revoke API key |

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | — | Basic health check |
| GET | `/api/health/status` | — | Detailed service status |

---

## Environment Variables

See `.env.example` for all 25+ config vars. Key ones:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **Yes** | — | 32+ char hex (openssl rand -hex 32) |
| `GITHUB_CLIENT_ID` | No | — | GitHub OAuth login |
| `GITHUB_CLIENT_SECRET` | No | — | GitHub OAuth login |
| `ANTHROPIC_API_KEY` | No | — | Claude AI analysis |
| `OPENAI_API_KEY` | No | — | GPT-4o mini analysis |
| `VIRUSTOTAL_API_KEY` | No | — | Threat intel |
| `SHODAN_API_KEY` | No | — | Threat intel |
| `ABUSEIPDB_API_KEY` | No | — | Threat intel |
| `ETHERSCAN_API_KEY` | No | — | ETH blockchain data |
| `DISCORD_WEBHOOK_URL` | No | — | Alert notifications |
| `TELEGRAM_BOT_TOKEN` | No | — | Alert notifications |
| `TELEGRAM_CHAT_ID` | No | — | Alert notifications |

---

## Deployment

### Docker (single server)
```bash
docker-compose up --build -d
```

### Production (AWS ECS / Render / Railway)
- Full Terraform infra in `cybersentinel-read-and-deploy/`
- Render config in `cybersentinel-infra/render.yaml`
- Railway config in `cybersentinel-infra/railway.json`

---

## Community

- [GitHub Discussions](https://github.com/arthurbarca374-create/cybersentinel/discussions) — questions, ideas, threat intel
- [Report a Bug](https://github.com/arthurbarca374-create/cybersentinel/issues/new)

---

## License

MIT — see [LICENSE](LICENSE)
