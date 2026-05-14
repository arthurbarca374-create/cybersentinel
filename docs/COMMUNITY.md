# Community Guide

## How to Contribute

CyberSentinel is a community-driven security platform. Contributions of all kinds are welcome — code, documentation, bug reports, feature ideas, and threat intel.

### Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/arthurbarca374-create/cybersentinel.git
cd cybersentinel

# Set up
cp .env.example .env
pip install -r requirements.txt
pip install -r requirements-mcp.txt

# Run tests
pytest -v

# Run locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### What to Work On

| Area | Description | Skill Level |
|---|---|---|
| **Scan engine** | Add new scan types, improve existing ones | Intermediate+ |
| **AI analysis** | Improve prompts, add new models | Intermediate |
| **Frontend** | UI/UX improvements, new dashboard features | Beginner+ |
| **Threat intel** | Add new data sources, improve parsing | Intermediate |
| **Blockchain** | Add chains, improve risk scoring | Advanced |
| **Documentation** | Guides, tutorials, API examples | Beginner |
| **Tests** | Increase coverage, add integration tests | Beginner+ |

### Coding Standards

- Python 3.11+ with type hints
- FastAPI patterns for routes
- SQLAlchemy ORM for data access
- Services layer for business logic
- pytest for tests (asyncio_mode = auto)

Run lint and type checking before submitting:

```bash
ruff check backend/
mypy backend/
bandit -r backend/
```

### Pull Request Process

1. Open an issue describing the change
2. Fork and create a feature branch
3. Write tests for new functionality
4. Run the full test suite: `pytest`
5. Submit a PR with a clear description

---

## Feature Requests

Have an idea? Open a [GitHub Discussion](https://github.com/arthurbarca374-create/cybersentinel/discussions) with the `idea` label. Popular requests include:

- **OAuth providers**: Google, GitLab, Discord login
- **Scan integrations**: Nmap scripts, Nuclei templates, OWASP ZAP
- **Reporting**: PDF/HTML report export
- **Dashboard**: Grafana integration, usage analytics
- **SIEM integration**: Splunk, Elastic, QRadar webhooks

---

## Reporting Bugs

1. Search existing [issues](https://github.com/arthurbarca374-create/cybersentinel/issues)
2. If new, create an issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, browser)
   - Logs from `/tmp/cybersentinel.log` if applicable

---

## Sharing Threat Intel

The threat intel feed is community-powered. When you find malicious indicators:

1. Use the API to create a report:

```bash
curl -X POST http://localhost:8000/api/threat/reports \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "C2 Infrastructure observed",
    "summary": "Observed C2 communication from...",
    "indicators": ["evil.com", "10.0.0.1"],
    "mitre_techniques": ["T1071"],
    "tlp": "GREEN"
  }'
```

2. Tag with appropriate TLP level
3. Each lookup is automatically stored and contributes to the feed

---

## Running a Community Instance

CyberSentinel is designed for community-hosted instances:

```bash
# Deploy with Docker
docker-compose up --build -d

# Or with systemd
# Create a service file at /etc/systemd/system/cybersentinel.service
```

Share your instance URL with the community by adding it to the [Community Deployments](https://github.com/arthurbarca374-create/cybersentinel/discussions) discussion.

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming, inclusive, and harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior:**
- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community

**Unacceptable behavior:**
- Harassment, trolling, or derogatory comments
- Personal or political attacks
- Publishing others' private information without consent
- Sexual language or imagery

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## License

CyberSentinel is MIT licensed. See [LICENSE](../LICENSE).
