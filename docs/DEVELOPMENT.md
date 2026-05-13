# Development Guide

## Setup

```bash
git clone https://github.com/arthurbarca374-create/cybersentinel.git
cd cybersentinel
cp .env.example .env
# Set SECRET_KEY in .env
pip install -r requirements.txt
pip install -r requirements-mcp.txt
```

## Running in Development

```bash
# API server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Background worker (separate terminal)
python worker.py

# MCP server (separate terminal)
python mcp_server.py
```

## Project Structure

```
cybersentinel/
├── backend/
│   ├── api/routes/       # HTTP route handlers (10 modules)
│   │   ├── ai.py         # AI analysis endpoints
│   │   ├── api_keys.py   # API key management
│   │   ├── auth.py       # Login/register/OAuth
│   │   ├── blockchain.py # Blockchain analysis
│   │   ├── health.py     # Health checks
│   │   ├── scans.py      # Scan management
│   │   ├── teams.py      # Org/team management
│   │   ├── threat.py     # Threat intelligence
│   │   ├── users.py      # User profiles/trial
│   │   └── ws.py         # WebSocket scan progress
│   ├── core/             # Config, security, middleware
│   ├── db/               # Database engine + session
│   ├── models/           # SQLAlchemy models + Pydantic schemas
│   └── services/         # Business logic (12 modules)
├── frontend/
│   ├── static/css/       # Stylesheets
│   ├── static/js/        # Client-side JavaScript
│   └── templates/        # Jinja2 HTML templates
├── tests/backend/        # Pytest test suite
├── scripts/              # Setup, run, backup utilities
├── main.py               # FastAPI entry point
├── worker.py             # Background worker
├── mcp_server.py         # MCP AI protocol server
├── cybersentinel_app.py  # Gunicorn WSGI wrapper
└── docker-compose.yml    # Docker deployment
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
coverage run -m pytest
coverage report

# Run specific test file
pytest tests/backend/test_scan_engine.py -v

# Run with verbose output
pytest -v

# Run tests matching a keyword
pytest -k "blockchain"
```

## Code Quality

The project uses `pyproject.toml` for tool configuration:

```bash
# Type checking
mypy backend/

# Lint (ruff)
ruff check backend/

# Security scan
bandit -r backend/
```

## Adding a New API Route

1. Create a route file in `backend/api/routes/`
2. Use the `APIRouter` pattern:
   ```python
   from fastapi import APIRouter, Depends
   router = APIRouter(prefix="/api/example", tags=["example"])

   @router.get("/items")
   def list_items(db=Depends(get_db)):
       return {"items": []}
   ```
3. Register the router in `main.py`:
   ```python
   from backend.api.routes import example
   app.include_router(example.router)
   ```

## Adding a New Service

1. Create a service module in `backend/services/`
2. Import the database session and models
3. Use dependency injection for the service in route handlers
4. Write tests in `tests/backend/test_{service}.py`

## Adding a New Database Model

1. Create a model file in `backend/models/` using SQLAlchemy declarative base
2. Add Pydantic schemas in `backend/models/schemas.py`
3. Tables are auto-created on startup via `Base.metadata.create_all()`

## Database Migrations

The project uses SQLAlchemy's `create_all()` for schema management. In production with PostgreSQL, use Alembic for migrations:

```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

There is no existing Alembic setup — configure it if you need migration management.

## CI/CD Pipeline

Defined in `.github/workflows/ci.yml`:
- Lint with ruff
- Type check with mypy
- Security scan with bandit
- Run pytest suite
- Build Docker image
- Run Docker smoke test

## WebSocket Client Example

```javascript
const ws = new WebSocket(`ws://localhost:8000/api/ws/scan/${scanId}?token=${jwt}`);
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'progress') {
        console.log(`${data.percent}%: ${data.message}`);
    } else if (data.type === 'complete') {
        console.log('Scan finished:', data.scan_id);
    }
};
```

## API Key Usage

```bash
# Generate an API key (returns once)
curl -X POST http://localhost:8000/api/keys \
  -H "Authorization: Bearer <jwt>"

# Use API key
curl http://localhost:8000/api/scans \
  -H "Authorization: Bearer <api_key>"
```
