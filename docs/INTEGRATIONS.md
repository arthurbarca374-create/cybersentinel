# Integrations Guide

- [AI Analysis](#ai-analysis)
- [Threat Intelligence](#threat-intelligence)
- [Blockchain Analysis](#blockchain-analysis)
- [Notifications](#notifications)
- [Community Member Directory](#community-member-directory)

---

## AI Analysis

After a scan completes, send its findings to an AI model for analysis and remediation suggestions.

### Setup

Set one of these in `.env`:

| Variable | Provider | Model |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude (Anthropic) | Claude 3 Haiku |
| `OPENAI_API_KEY` | OpenAI | GPT-4o Mini |
| `LLM_API_URL` + `LLM_MODEL` | Any OpenAI-compatible API | Configurable |

No API key required for the "local" fallback mode — it returns a template analysis using scan findings directly.

### Usage

```bash
curl -X POST http://localhost:8000/api/ai/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": 42,
    "model": "claude"
  }'
```

Available models:

```bash
curl http://localhost:8000/api/ai/models
```

```json
{
  "models": [
    {"id": "default", "name": "Local analysis (no API key required)"},
    {"id": "claude",   "name": "Claude 3 Haiku (Anthropic)"},
    {"id": "gpt4",     "name": "GPT-4o Mini (OpenAI)"}
  ]
}
```

### Response

```json
{
  "scan_id": 42,
  "model_used": "claude",
  "summary": "2 high-severity issues found on ports 22 and 443",
  "findings_analysis": [
    {
      "finding": "Open SSH port 22",
      "risk": "high",
      "remediation": "Restrict SSH access by IP, disable password auth, use key-based auth only"
    }
  ],
  "recommendations": [
    "Move SSH to a non-standard port",
    "Enable fail2ban",
    "Set up a WAF for the web server"
  ]
}
```

---

## Threat Intelligence

Look up IP addresses, domains, file hashes, and URLs against multiple threat intel feeds.

### Setup

Configure at least one source in `.env`:

| Variable | Provider | Free Tier |
|---|---|---|
| `VIRUSTOTAL_API_KEY` | VirusTotal | 500 req/day, 4 req/min |
| `SHODAN_API_KEY` | Shodan | 1M results/mo (Educational) |
| `ABUSEIPDB_API_KEY` | AbuseIPDB | 1000 req/day |

If none are configured, the service returns cached/stored results.

### Lookup an indicator

```bash
curl -X POST http://localhost:8000/api/threat/lookup \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "indicator": "8.8.8.8",
    "indicator_type": "ip"
  }'
```

Supported indicator types: `ip`, `domain`, `hash`, `url`

Or use path-based lookup:

```bash
curl http://localhost:8000/api/threat/lookup/ip/8.8.8.8 \
  -H "Authorization: Bearer <token>"
```

### Threat feed

```bash
curl http://localhost:8000/api/threat/feed?limit=50 \
  -H "Authorization: Bearer <token>"
```

### Stats

```bash
curl http://localhost:8000/api/threat/stats \
  -H "Authorization: Bearer <token>"
```

### Reports

Create and share threat intelligence reports:

```bash
curl -X POST http://localhost:8000/api/threat/reports \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Phishing Campaign Q2",
    "summary": "Observed phishing infrastructure targeting...",
    "indicators": ["malicious.com", "192.0.2.1"],
    "mitre_techniques": ["T1566", "T1059"],
    "tlp": "AMBER"
  }'
```

TLP values: `WHITE`, `GREEN`, `AMBER`, `RED`

List reports:

```bash
curl http://localhost:8000/api/threat/reports \
  -H "Authorization: Bearer <token>"
```

---

## Blockchain Analysis

Analyze cryptocurrency wallet addresses for risk indicators.

### Setup

| Variable | Purpose | Free Tier |
|---|---|---|
| `ETHERSCAN_API_KEY` | Ethereum analysis | 5 req/sec, 100K req/day |

Bitcoin and Monero analysis work without any API key.

### Analyze an address

```bash
curl -X POST http://localhost:8000/api/blockchain/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "btc",
    "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
  }'
```

Path-based:

```bash
curl http://localhost:8000/api/blockchain/analyze/btc/1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa \
  -H "Authorization: Bearer <token>"
```

Supported chains: `btc`, `eth`, `xmr`

### Response

```json
{
  "chain": "btc",
  "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
  "valid_format": true,
  "risk_score": 12,
  "risk_level": "low",
  "tags": ["known_exchange"],
  "transaction_count": 29876,
  "first_seen": "2009-01-03"
}
```

### Recent analyses

```bash
curl http://localhost:8000/api/blockchain/analyses \
  -H "Authorization: Bearer <token>"
```

### Wallet recovery

Start a wallet recovery process (placeholder for future automated recovery):

```bash
curl -X POST http://localhost:8000/api/blockchain/recover \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "btc",
    "method": "seed_phrase"
  }'
```

---

## Notifications

Get notified when scans complete or security events occur.

### Discord

1. Create a webhook in your Discord channel: Channel Settings → Integrations → Webhooks
2. Set `DISCORD_WEBHOOK_URL` in `.env`

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456/abc-def
```

### Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get your chat ID (message @userinfobot)
3. Set in `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234...
TELEGRAM_CHAT_ID=123456789
```

Messages use Markdown formatting and include scan summaries with severity highlights.

### Testing notifications

The background worker sends notifications automatically on scan completion. To test manually:

```python
# Using the API directly via Python
import httpx
resp = httpx.get("http://localhost:8000/api/health/status")
print(resp.json()["services"]["notifications"])
```

---

## Community Member Directory

View public member count and recent signups:

```bash
curl http://localhost:8000/api/users/community/members
```

```json
{
  "total_members": 42,
  "recent_members": [
    {
      "username": "alice",
      "avatar_url": null,
      "joined": "2026-05-13T12:00:00"
    }
  ]
}
```

This endpoint is public and requires no authentication.
