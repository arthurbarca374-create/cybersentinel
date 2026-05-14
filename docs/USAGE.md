# Usage Guide

## Table of Contents

- [Authentication](#authentication)
- [API Keys](#api-keys)
- [Scan Targets](#scan-targets)
- [Running Scans](#running-scans)
- [Scan Progress via WebSocket](#scan-progress-via-websocket)
- [Trial System](#trial-system)
- [Organizations & Teams](#organizations--teams)

---

## Authentication

### Register a new account

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "securepass123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "is_trial_active": true
  }
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "securepass123"}'
```

### GitHub OAuth

1. Register a GitHub OAuth app at https://github.com/settings/developers
2. Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `.env`
3. Navigate to `http://localhost:8000/api/auth/github`

### Get current user

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

---

## API Keys

Generate a persistent API key for programmatic access. The key is shown once and stored hashed.

```bash
# Generate key
curl -X POST http://localhost:8000/api/keys \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "ci-cd-pipeline"}'
```

Response:
```json
{
  "id": 1,
  "name": "ci-cd-pipeline",
  "key": "cs_abc123def456...",  // shown once — save it
  "created_at": "2026-05-13T..."
}
```

Use the API key anywhere you'd use a JWT:

```bash
curl http://localhost:8000/api/scans \
  -H "Authorization: Bearer cs_abc123def456..."
```

List and revoke keys:

```bash
# List keys
curl http://localhost:8000/api/keys \
  -H "Authorization: Bearer <token>"

# Revoke key
curl -X DELETE http://localhost:8000/api/keys/1 \
  -H "Authorization: Bearer <token>"
```

---

## Scan Targets

### List available scan types

```bash
curl http://localhost:8000/api/scans/types
```

```json
{
  "scan_types": [
    {"id": "quick", "name": "Fast port scan (common ports)"},
    {"id": "full", "name": "Full port scan (1-65535)"},
    {"id": "service", "name": "Service version detection"},
    {"id": "vuln", "name": "Vulnerability assessment"},
    {"id": "web", "name": "Web application scan"}
  ]
}
```

### Add a target

```bash
curl -X POST http://localhost:8000/api/scans/targets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Web Server",
    "host": "example.com",
    "port": 443,
    "os_info": "Ubuntu 22.04",
    "notes": "Production web server",
    "tags": ["web", "production"]
  }'
```

### List targets

```bash
curl http://localhost:8000/api/scans/targets \
  -H "Authorization: Bearer <token>"
```

### Remove a target

```bash
curl -X DELETE http://localhost:8000/api/scans/targets/1 \
  -H "Authorization: Bearer <token>"
```

---

## Running Scans

### Start a scan

```bash
curl -X POST http://localhost:8000/api/scans/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": 1,
    "scan_type": "quick",
    "config": {"ports": "80,443,22"},
    "schedule": null
  }'
```

Response:
```json
{
  "id": 42,
  "target_id": 1,
  "scan_type": "quick",
  "status": "pending",
  "created_at": "2026-05-13T12:00:00",
  "config": {"ports": "80,443,22"}
}
```

Scheduled scans use cron expressions:

```bash
curl -X POST http://localhost:8000/api/scans/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": 1,
    "scan_type": "quick",
    "schedule": "0 */6 * * *"
  }'
```

### List scans

```bash
curl http://localhost:8000/api/scans \
  -H "Authorization: Bearer <token>"
```

### Get scan details

```bash
curl http://localhost:8000/api/scans/42 \
  -H "Authorization: Bearer <token>"
```

### Get findings

```bash
curl http://localhost:8000/api/scans/42/findings \
  -H "Authorization: Bearer <token>"
```

---

## Scan Progress via WebSocket

Connect to receive real-time progress during a scan:

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/ws/scan/42?token=<jwt_or_api_key>`
);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    case "progress":
      console.log(`Scanning: ${msg.percent}% — ${msg.message}`);
      break;

    case "finding":
      console.log(`[${msg.severity.toUpperCase()}] ${msg.title}`);
      break;

    case "complete":
      console.log(`Scan ${msg.scan_id} finished`);
      ws.close();
      break;

    case "error":
      console.error(`Scan error: ${msg.message}`);
      break;
  }
};
```

Using wscat:

```bash
# Install: npm install -g wscat
wscat -c "ws://localhost:8000/api/ws/scan/42?token=<token>"
```

---

## Trial System

New accounts get a 14-day trial with 10 scans.

```bash
# Check trial status
curl http://localhost:8000/api/users/trial/status \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "is_active": true,
  "expires_at": "2026-05-27T12:00:00",
  "scans_used": 3,
  "scans_remaining": 7,
  "trial_days": 14,
  "max_scans": 10
}
```

Each scan call automatically consumes one credit. When `scans_remaining` reaches 0, the trial period still runs but no new scans can be started.

---

## Organizations & Teams

### Create organization

```bash
curl -X POST http://localhost:8000/api/orgs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Security"}'
```

### List organizations

```bash
curl http://localhost:8000/api/orgs \
  -H "Authorization: Bearer <token>"
```

### Create team

```bash
curl -X POST http://localhost:8000/api/orgs/1/teams \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Red Team"}'
```

### List teams

```bash
curl http://localhost:8000/api/orgs/1/teams \
  -H "Authorization: Bearer <token>"
```

---

## Health Checks

```bash
# Basic
curl http://localhost:8000/api/health

# Detailed
curl http://localhost:8000/api/health/status
```

## API Docs

Interactive documentation at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
