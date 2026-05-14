from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import os

try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False

from backend.core.config import get_settings
from backend.core.limiter import limiter
from backend.core.csrf import SecurityHeadersMiddleware
from backend.db.database import Base, engine
from backend.api.routes import auth, users, health
from backend.api.routes import scans, teams, threat, ai, blockchain, ws, api_keys
from backend.services.scheduler import run_scheduler_loop

ON_VERCEL = os.getenv("VERCEL", "").lower() == "1"

settings = get_settings()
logger = logging.getLogger(__name__)


def _log_capabilities():
    enabled = []
    disabled = []

    if settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY or settings.LLM_API_URL:
        enabled.append("AI analysis")
    else:
        disabled.append("AI analysis (set ANTHROPIC_API_KEY, OPENAI_API_KEY, or LLM_API_URL)")

    if settings.VIRUSTOTAL_API_KEY or settings.SHODAN_API_KEY or settings.ABUSEIPDB_API_KEY:
        enabled.append("threat intel")
    else:
        disabled.append("threat intel (set VIRUSTOTAL_API_KEY, SHODAN_API_KEY, or ABUSEIPDB_API_KEY)")

    if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
        enabled.append("GitHub OAuth")
    else:
        disabled.append("GitHub OAuth (set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)")

    if settings.ETHERSCAN_API_KEY:
        enabled.append("Ethereum blockchain analysis")
    else:
        disabled.append("Ethereum blockchain analysis (set ETHERSCAN_API_KEY)")

    if settings.DISCORD_WEBHOOK_URL or (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID):
        enabled.append("notifications")

    logger.info(f"Enabled: {', '.join(enabled) if enabled else 'none'}")
    if disabled:
        logger.info(f"Disabled: {', '.join(disabled)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_capabilities()
    scheduler_task = None
    if not ON_VERCEL:
        scheduler_task = asyncio.create_task(run_scheduler_loop(interval=15))
        logger.info("Background scheduler started (interval=15s)")
    else:
        logger.info("Skipping background scheduler (Vercel serverless)")
    yield
    if scheduler_task:
        scheduler_task.cancel()
        logger.info("Background scheduler stopped")


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    max_request_size=1024 * 1024,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
from backend.core.limiter import HAS_LIMITER
if HAS_LIMITER:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(scans.router)
app.include_router(teams.router)
app.include_router(threat.router)
app.include_router(ai.router)
app.include_router(blockchain.router)
app.include_router(ws.router)
app.include_router(api_keys.router)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    if full_path == "login":
        return FileResponse("frontend/templates/login.html")
    if full_path == "register":
        return FileResponse("frontend/templates/register.html")
    return FileResponse("frontend/templates/index.html")
