from fastapi import APIRouter
from backend.core.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])
settings = get_settings()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/status")
def health_status():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "services": {
            "ai": {
                "anthropic": bool(settings.ANTHROPIC_API_KEY),
                "openai": bool(settings.OPENAI_API_KEY),
                "local_llm": bool(settings.LLM_API_URL),
                "has_ai": bool(settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY or settings.LLM_API_URL),
            },
            "threat_intel": {
                "virustotal": bool(settings.VIRUSTOTAL_API_KEY),
                "shodan": bool(settings.SHODAN_API_KEY),
                "abuseipdb": bool(settings.ABUSEIPDB_API_KEY),
                "has_threat_intel": bool(settings.VIRUSTOTAL_API_KEY or settings.SHODAN_API_KEY or settings.ABUSEIPDB_API_KEY),
            },
            "blockchain": {
                "etherscan": bool(settings.ETHERSCAN_API_KEY),
                "bitcoin": True,
                "has_blockchain": True,
            },
            "notifications": {
                "discord": bool(settings.DISCORD_WEBHOOK_URL),
                "telegram": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
                "has_notifications": bool(settings.DISCORD_WEBHOOK_URL or (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)),
            },
            "auth": {
                "github_oauth": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
                "email": True,
            },
        },
    }
