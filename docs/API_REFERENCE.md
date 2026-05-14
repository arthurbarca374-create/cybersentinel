# API Reference

Base URL: `http://localhost:8000/api`

Authentication: `Authorization: Bearer <jwt_or_api_key>` header.

## Health

### `GET /api/health`

Basic health check. No auth required.

```bash
curl http://localhost:8000/api/health
```

```json
{"status":"ok","service":"CyberSentinel","version":"0.2.0"}
```

### `GET /api/health/status`

Detailed service status showing which integrations are active.

```bash
curl http://localhost:8000/api/health/status
```

```json
{
  "status": "ok",
  "services": {
    "ai": {"has_ai": false},
    "threat_intel": {"has_threat_intel": false},
    "blockchain": {"bitcoin": true, "has_blockchain": true},
    "notifications": {"has_notifications": false},
    "auth": {"github_oauth": false, "email": true}
  }
}
```

---

## Auth

### `POST /api/auth/register`

Create a new account. Rate limited: 5 req/minute.

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "securepass123"
}
```

Returns JWT token and user object. New accounts get a 14-day trial with 10 scans.

### `POST /api/auth/login`

Authenticate with username and password. Rate limited: 10 req/minute.

```json
{
  "username": "alice",
  "password": "securepass123"
}
```

### `GET /api/auth/github`

Redirects to GitHub OAuth authorization page. Requires `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` configured.

### `GET /api/auth/github/callback`

OAuth callback — GitHub redirects here after authorization. Sets a `cs_token` cookie and redirects to the dashboard.

### `GET /api/auth/me`

Returns the authenticated user's profile.

```bash
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer <token>"
```

---

## Users

### `GET /api/users/trial/status`

Trial state and remaining scan credits.

```bash
curl http://localhost:8000/api/users/trial/status -H "Authorization: Bearer <token>"
```

### `POST /api/users/trial/use-scan`

Manually consume one scan credit.

```bash
curl -X POST http://localhost:8000/api/users/trial/use-scan -H "Authorization: Bearer <token>"
```

### `GET /api/users/community/members`

Public member directory. No auth required.

```bash
curl http://localhost:8000/api/users/community/members
```

---

## Scans

### `GET /api/scans/types`

List available scan types. No auth required.

```bash
curl http://localhost:8000/api/scans/types
```

### `POST /api/scans/targets`

Add a scan target.

```json
{
  "name": "My Server",
  "host": "10.0.0.1",
  "port": 443,
  "os_info": "Ubuntu 22.04",
  "notes": "Production",
  "tags": ["web"]
}
```

### `GET /api/scans/targets`

List your targets.

### `DELETE /api/scans/targets/{target_id}`

Soft-delete a target.

### `POST /api/scans/run`

Start a scan. Rate limited: 10 req/minute.

```json
{
  "target_id": 1,
  "scan_type": "quick",
  "config": {"ports": "80,443,22"},
  "schedule": null
}
```

For scheduled scans, use a cron expression:

```json
{
  "target_id": 1,
  "scan_type": "full",
  "schedule": "0 2 * * *"
}
```

### `GET /api/scans`

List your scans (most recent first, max 50).

### `GET /api/scans/{scan_id}`

Get scan details.

### `GET /api/scans/{scan_id}/findings`

Get findings for a completed scan.

---

## WebSocket

### `WS /api/ws/scan/{scan_id}?token={jwt}`

Real-time scan progress. Auth via query parameter `token`.

Messages:

```json
{"type": "progress", "percent": 45, "message": "Scanning port 443..."}
{"type": "finding", "severity": "medium", "title": "Open port 22", "detail": "SSH service on port 22"}
{"type": "complete", "scan_id": 42}
{"type": "error", "message": "Scan timed out"}
```

---

## AI Analysis

### `POST /api/ai/analyze`

Analyze completed scan findings with AI.

```json
{
  "scan_id": 42,
  "model": "claude"
}
```

Models: `default` (local), `claude`, `gpt4`

### `GET /api/ai/models`

List available AI models.

---

## Threat Intelligence

### `POST /api/threat/lookup`

Look up an IP, domain, hash, or URL.

```json
{
  "indicator": "8.8.8.8",
  "indicator_type": "ip"
}
```

### `GET /api/threat/lookup/{indicator_type}/{indicator}`

Path-based threat lookup.

### `GET /api/threat/feed`

Get recent threat intelligence feed.

Query params: `limit` (1-200, default 50)

### `GET /api/threat/stats`

Threat intel statistics.

### `GET /api/threat/reports`

List threat reports.

### `POST /api/threat/reports`

Create a threat report.

```json
{
  "title": "Campaign Name",
  "summary": "Description",
  "indicators": ["evil.com"],
  "mitre_techniques": ["T1566"],
  "tlp": "AMBER"
}
```

---

## Blockchain

### `POST /api/blockchain/analyze`

Analyze a blockchain address.

```json
{
  "chain": "btc",
  "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
}
```

### `GET /api/blockchain/analyze/{chain}/{address}`

Path-based analysis.

### `GET /api/blockchain/analyses`

Recent analyses for current user.

### `POST /api/blockchain/recover`

Start wallet recovery.

```json
{
  "chain": "btc",
  "method": "seed_phrase"
}
```

### `GET /api/blockchain/recoveries`

List wallet recoveries.

---

## Organizations & Teams

### `POST /api/orgs`

```json
{"name": "Acme Security"}
```

### `GET /api/orgs`

### `GET /api/orgs/{org_id}`

### `GET /api/orgs/{org_id}/members`

### `POST /api/orgs/{org_id}/teams`

```json
{"name": "Red Team"}
```

### `GET /api/orgs/{org_id}/teams`

---

## API Keys

### `POST /api/keys`

```json
{"name": "ci-pipeline"}
```

Returns the key value once — save it immediately.

### `GET /api/keys`

### `DELETE /api/keys/{key_id}`

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Description of the error"
}
```

Common HTTP status codes:

| Code | Meaning |
|---|---|
| 400 | Bad request (invalid input) |
| 401 | Missing or invalid auth token |
| 403 | Trial expired or no scans remaining |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
