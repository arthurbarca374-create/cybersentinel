from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CyberSentinel"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = False

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = "sqlite:///./cybersentinel.db"

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"

    FREE_TRIAL_DAYS: int = 14
    FREE_TRIAL_SCANS: int = 10

    FRONTEND_URL: str = "http://localhost:8000"
    ALLOWED_HOSTS: list[str] = ["*"]

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_API_URL: str = ""
    LLM_MODEL: str = ""

    VIRUSTOTAL_API_KEY: str = ""
    SHODAN_API_KEY: str = ""
    ABUSEIPDB_API_KEY: str = ""

    ETHERSCAN_API_KEY: str = ""

    DISCORD_WEBHOOK_URL: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    if not s.SECRET_KEY or len(s.SECRET_KEY) < 16:
        raise ValueError(
            "SECRET_KEY must be at least 16 characters. "
            "Generate one with: openssl rand -hex 32"
        )
    return s
