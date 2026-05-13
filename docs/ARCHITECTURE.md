# CyberSentinel Architecture

## Overview

CyberSentinel is a self-hostable security scanning platform with a modular monolith architecture. The backend is a FastAPI application serving both a REST API and a static frontend from a single process.

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│  HTML Templates (Jinja2) · Static JS/CSS · WebSocket Client │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     API Layer                               │
│  10 Route Modules · Rate Limiter · CORS · Security Headers  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Service Layer                             │
│  Auth · Scan Engine · AI Analysis · Threat Intel             │
│  Blockchain · Notifications · Teams · Scheduler · API Keys  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Data Layer                               │
│  SQLAlchemy ORM · SQLite/PostgreSQL · 6 Models + Pydantic   │
└─────────────────────────────────────────────────────────────┘
```

## Process Model

The application runs as three independent processes that can be deployed together or separately:

| Process | Entry Point | Role |
|---|---|---|
| **API Server** | `main.py` | FastAPI app serving REST endpoints + frontend + WebSocket |
| **Background Worker** | `worker.py` | Processes queued scans, cleanup tasks |
| **MCP Server** | `mcp_server.py` | AI tool protocol server for LLM integrations |

### API Server (`main.py`)

The primary process. On startup it:
1. Loads settings from `.env` via `pydantic-settings`
2. Creates all database tables (`Base.metadata.create_all`)
3. Initializes middleware stack: CORS, TrustedHost, GZip, SecurityHeaders, Rate Limiter
4. Registers 10 route modules under `/api/*`
5. Mounts static files at `/static`
6. Serves SPA frontend via catch-all route `/{full_path:path}`
7. Starts a background scheduler loop (interval: 15s) for cron-based scans

## Routing

```
/api/health          → health.py
/api/auth/*          → auth.py
/api/users/*         → users.py
/api/scans/*         → scans.py
/api/orgs/*          → teams.py
/api/threat/*        → threat.py
/api/ai/*            → ai.py
/api/blockchain/*    → blockchain.py
/api/ws/*            → ws.py (WebSocket)
/api/keys/*          → api_keys.py
/                    → frontend/templates/index.html
```

## Data Models

| Model | Table | Key Fields |
|---|---|---|
| `User` | `users` | id, email, password_hash, github_id, trial_start, trial_scans_used |
| `Scan` | `scans` | id, user_id, target_id, scan_type, status, started_at, completed_at |
| `ScanTarget` | `scan_targets` | id, user_id, name, host |
| `Team` | `teams` | id, org_id, name |
| `Organization` | `organizations` | id, name, owner_id |
| `ApiKey` | `api_keys` | id, user_id, key_hash, name, last_used_at |
| `BlockchainAnalysis` | `blockchain_analyses` | id, user_id, chain, address, risk_score |
| `ThreatReport` | `threat_reports` | id, user_id, title, severity, status |

## Authentication Flow

```
┌─────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  /login  │────▶│  verify  │
└─────────┘     └──────────┘     └──────────┘
                      │
              ┌───────┴───────┐
              ▼               ▼
        ┌──────────┐   ┌──────────┐
        │  JWT     │   │GitHub    │
        │ (email)  │   │ OAuth    │
        └──────────┘   └──────────┘
```

- Email/password: credentials verified with `passlib.sha256_crypt`, JWT issued via `python-jose`
- GitHub OAuth: redirect flow, profile fetched from GitHub API, local user created on first login
- API Key: Bearer token in `Authorization` header, validated against key hash in database
- Trial system: 14-day window with 10 scan credits, tracked per user

## Scan Engine

```
POST /api/scans/run
       │
       ▼
┌──────────────┐
│ Consume      │
│ scan credit  │
└──────┬───────┘
       ▼
┌──────────────┐
│ Create scan  │
│ record (PENDING)│
└──────┬───────┘
       ▼
┌──────────────┐
│  Run scan    │
│  (subprocess)│
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌──────────────────┐
│ Update scan  │──────▶│ WebSocket emit   │
│ (COMPLETED)  │      │ progress events  │
└──────────────┘      └──────────────────┘
```

Supported scan types:
- **quick** — Basic port/connectivity check
- **full** — Comprehensive port scan
- **service** — Service version detection
- **vuln** — Vulnerability check
- **web** — Web application scan

## WebSocket Protocol

Connect: `ws://host:8000/api/ws/scan/{scan_id}?token={jwt}`

Messages from server:
```json
{"type": "progress", "percent": 45, "message": "Scanning port 443..."}
{"type": "finding", "severity": "medium", "title": "Open port 22", "detail": "SSH service detected"}
{"type": "complete", "scan_id": 123}
{"type": "error", "message": "Scan timed out"}
```

## Service Integrations

### AI Analysis
- Supports Claude (Anthropic), GPT-4o mini (OpenAI), or any OpenAI-compatible local LLM
- Scan findings are sent as context, AI returns risk analysis with remediation steps

### Threat Intelligence
- VirusTotal: IP/domain/file hash lookup
- Shodan: service and vulnerability data
- AbuseIPDB: IP reputation reporting and checking

### Notifications
- Discord webhook: JSON payload to configured channel
- Telegram bot: message sent to configured chat ID

### Blockchain
- Bitcoin: address validation and risk scoring via blockchain APIs
- Ethereum: address analysis via Etherscan (when API key configured)
- Monero: basic address validation
