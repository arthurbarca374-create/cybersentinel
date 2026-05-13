# CyberSentinel Community Build - Free Trial Platform

## Quick Start Guide

Welcome to CyberSentinel! This guide helps you get started with our community-driven security platform featuring a **14-day free trial with 10 scan credits**.

## Getting Started

### 1. Sign Up (Choose Your Method)
```bash
# Option A: GitHub OAuth (Recommended)
Visit: http://localhost:8000
Click: "Login with GitHub"

# Option B: Email/Password
Visit: http://localhost:8000/register
Enter: Email, Password, Confirm Password
```

### 2. Your Free Trial Includes
- 14 days of full platform access
- 10 vulnerability scan credits
- Community member directory access
- Discord & Telegram alert integration
- Threat intelligence reports
- Honeypot attack data access

### 3. Run Your First Scan
```bash
# Via Web Interface
1. Navigate to Dashboard
2. Click "New Scan"
3. Enter target (domain or IP)
4. Select scan type: Quick (5min) | Standard (30min) | Deep (2hrs)
5. Click "Start Scan"

# Via API
curl -X POST http://localhost:8000/api/scan/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scan_type": "standard"
  }'
```

## Platform Architecture

### Backend (Python + FastAPI)
```
cybersentinel/
├── backend/
│   ├── api/routes/
│   │   ├── auth.py          # Login, register, GitHub OAuth
│   │   ├── users.py         # Trial status, scan credits
│   │   └── health.py        # Health checks
│   ├── core/
│   │   ├── config.py        # Settings (14-day trial, 10 scans)
│   │   └── security.py      # JWT, bcrypt
│   ├── db/
│   │   └── database.py      # SQLite setup
│   ├── models/
│   │   ├── user.py          # User ORM
│   │   └── schemas.py       # Pydantic models
│   └── services/
│       ├── auth.py          # Authentication logic
│       └── github_oauth.py  # OAuth flow
```

### Frontend (Vanilla HTML/CSS/JS)
```
frontend/
├── static/
│   ├── css/main.css
│   └── js/
│       ├── app.js
│       ├── auth.js          # Login/register
│       └── dashboard.js     # Scan management
└── templates/
    ├── index.html
    ├── login.html
    ├── register.html
    └── dashboard.html
```

## AI Agent System

### Agent Personas (Roles)
1. **Security Analyst** - Vulnerability assessment and reporting
2. **Threat Hunter** - Proactive threat detection via honeypots
3. **Vulnerability Scanner** - Automated scanning engine
4. **Community Manager** - User onboarding and engagement
5. **Blockchain Analyst** - Crypto/smart contract security

### Masterprompts (Systems)
1. **Security Operations** - 24/7 SOC automation
2. **Threat Intelligence** - IOC collection and enrichment
3. **Vulnerability Assessment** - Comprehensive scanning methodology

**Location**: `/cybersentinel/.opencode/agent/` (9 markdown files)

## API Reference

### Authentication
```bash
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
Response: {"access_token": "eyJ...", "token_type": "bearer"}

# GitHub OAuth
GET /api/auth/github  # Redirects to GitHub
GET /api/auth/github/callback  # Returns JWT

# Get Current User
GET /api/auth/me
Headers: Authorization: Bearer <token>
```

### Free Trial Management
```bash
# Check Trial Status
GET /api/users/trial/status
Headers: Authorization: Bearer <token>
Response: {
  "trial_active": true,
  "scans_remaining": 7,
  "trial_expires_at": "2026-05-27T12:00:00Z"
}

# Use Scan Credit
POST /api/users/trial/use-scan
Headers: Authorization: Bearer <token>
Response: {
  "scans_remaining": 6,
  "message": "Scan credit consumed"
}
```

### Community
```bash
# Public Member Directory
GET /api/users/community/members
Response: [
  {
    "username": "sec_researcher",
    "joined": "2026-05-01",
    "scans_completed": 47
  }
]
```

## Running the Platform

### Local Development
```bash
# 1. Clone repository
git clone https://github.com/arthurbarca374-create/cybersentinel.git
cd cybersentinel

# 2. Setup environment
cp .env.example .env
# Edit .env - add GitHub OAuth credentials

# 3. Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Run server
uvicorn main:app --reload

# 5. Open browser
http://localhost:8000
```

### Docker Deployment
```bash
# Build and run
docker-compose up --build

# Access
http://localhost:8000

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Community Features

### Discord Integration
```yaml
Channels:
  - #general: Community chat
  - #support: Technical help
  - #threat-intel: Share IOCs and findings
  - #showcase: Demo your projects
  - #announcements: Platform updates

Bot Commands:
  - /scan-status <scan_id>: Check scan progress
  - /trial-status: View remaining credits
  - /leaderboard: Top contributors
```

### Telegram Alerts
```yaml
Features:
  - Real-time scan completion alerts
  - Critical vulnerability notifications
  - Daily threat intelligence digest
  - Community announcements

Setup:
  1. Message @CyberSentinel_bot
  2. Send /start
  3. Link account with code from dashboard
```

### Gamification & Rewards
```yaml
Reputation Points:
  - Complete first scan: +10 points
  - Submit verified IOC: +25 points
  - Discover new CVE: +100 points
  - Write tutorial: +50 points
  - Help community member: +15 points

Leaderboards:
  - Weekly top scanners
  - Monthly threat hunters
  - All-time contributors

Badges:
  - First Scan
  - Threat Hunter (10 IOC submissions)
  - Community Helper (50 support responses)
  - Security Champion (100+ scans)
  - CVE Discoverer
```

## Security Features

### Platform Security
```yaml
Authentication:
  - JWT with 24-hour expiration
  - bcrypt password hashing
  - GitHub OAuth support
  - Rate limiting on auth endpoints

Data Protection:
  - TLS 1.3 encryption in transit
  - SQLite with encrypted fields
  - No credit card storage (free tier)
  - Anonymized threat intel sharing

Abuse Prevention:
  - 10 scans per 14-day trial
  - Target validation (no private IPs)
  - CAPTCHA on suspicious signups
  - API rate limiting
```

### Scanning Features
```yaml
Vulnerability Detection:
  - OWASP Top 10 comprehensive testing
  - CVE database correlation (NVD)
  - CVSS v3.1 risk scoring
  - Safe PoC validation
  - No destructive actions

Scan Types:
  - Quick: 5-10 minutes (surface-level)
  - Standard: 30-45 minutes (comprehensive)
  - Deep: 2+ hours (exhaustive)

Output Formats:
  - Interactive HTML report
  - JSON (API integration)
  - PDF (executive summary)
  - CSV (vulnerability list)
```

## Deployment Guide

### GitHub OAuth Setup
```bash
1. Go to: https://github.com/settings/developers
2. Click: "New OAuth App"
3. Fill in:
   - App name: CyberSentinel
   - Homepage: http://localhost:8000
   - Callback: http://localhost:8000/api/auth/github/callback
4. Copy Client ID and Secret to .env
```

### Environment Variables
```bash
# .env file
SECRET_KEY=<generate with: openssl rand -hex 32>
GITHUB_CLIENT_ID=<from GitHub OAuth app>
GITHUB_CLIENT_SECRET=<from GitHub OAuth app>
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback
DATABASE_URL=sqlite:///./cybersentinel.db
FRONTEND_URL=http://localhost:8000

# Optional: External APIs
VIRUSTOTAL_API_KEY=<your_key>
SHODAN_API_KEY=<your_key>
ABUSEIPDB_API_KEY=<your_key>
```

### Production Checklist
```bash
- [ ] Change SECRET_KEY to production value
- [ ] Update FRONTEND_URL to production domain
- [ ] Update GitHub OAuth callback URL
- [ ] Enable HTTPS (Let's Encrypt)
- [ ] Set up database backups
- [ ] Configure monitoring (Sentry, DataDog)
- [ ] Set up log aggregation
- [ ] Deploy rate limiting
- [ ] Configure CDN for static assets
- [ ] Set up CI/CD pipeline (GitHub Actions)
```

## Roadmap

### Phase 1: Free Community (Current)
- ✅ Email/password registration
- ✅ GitHub OAuth login
- ✅ 14-day free trial with 10 scans
- ✅ Basic vulnerability scanning
- ✅ Community member directory

### Phase 2: Enhanced Features (Next 1-3 months)
- 🔜 AI-powered scan analysis
- 🔜 Custom scan templates
- 🔜 API access for automation
- 🔜 Discord/Telegram bot
- 🔜 Advanced threat intelligence
- 🔜 Honeypot attack visualization

### Phase 3: Paid Tiers (3-6 months)
- 🔜 Unlimited scans
- 🔜 Team accounts (5-50 users)
- 🔜 Enterprise SSO
- 🔜 SLA support
- 🔜 White-label options
- 🔜 Custom integrations

## Contributing

We welcome community contributions!

```bash
# 1. Fork the repository
# 2. Create feature branch
git checkout -b feat/my-feature

# 3. Make changes and test
pytest tests/

# 4. Commit and push
git add .
git commit -m "Add: My awesome feature"
git push origin feat/my-feature

# 5. Open Pull Request
```

## Support

### Community Channels
- GitHub Discussions: Q&A, ideas, threat intel
- Discord: Real-time chat and support
- Telegram: Alerts and announcements
- Email: [email protected]

### Documentation
- API Docs: http://localhost:8000/api/docs (Swagger)
- Agent Personas: `/cybersentinel/.opencode/agent/README.md`
- GitHub Wiki: Project documentation
- Blog: Security tutorials and case studies

## License

MIT License - Free to use, modify, and distribute.

---

**Built by the community, for the community.**  
**Join us in making the internet more secure.** 🛡️

**Version**: 0.1.0  
**Last Updated**: May 13, 2026  
**Contributors**: CyberSentinel Team + Community

---

*"Security, amplified by community. Welcome to CyberSentinel."*
