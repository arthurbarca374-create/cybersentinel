import logging
from typing import Optional

from backend.core.config import get_settings
from backend.core.http_client import create_client

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_discord(
    message: str,
    webhook_url: Optional[str] = None,
    username: str = "CyberSentinel",
) -> bool:
    url = webhook_url or settings.DISCORD_WEBHOOK_URL
    if not url:
        logger.debug("Discord webhook URL not configured, skipping")
        return False
    try:
        async with create_client(timeout=10) as client:
            resp = await client.post(url, json={"content": message, "username": username})
            if resp.status_code == 204:
                return True
            logger.warning(f"Discord webhook returned {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Discord webhook request failed: {e}")
        return False


async def send_telegram(
    message: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    cid = chat_id or settings.TELEGRAM_CHAT_ID
    if not token or not cid:
        logger.debug("Telegram bot token or chat ID not configured, skipping")
        return False
    try:
        async with create_client(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": cid, "text": message, "parse_mode": "Markdown"},
            )
            if resp.status_code == 200:
                return True
            logger.warning(f"Telegram API returned {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram request failed: {e}")
        return False


async def notify_all(message: str) -> dict[str, bool]:
    results = {}
    if settings.DISCORD_WEBHOOK_URL:
        results["discord"] = await send_discord(message)
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        results["telegram"] = await send_telegram(message)
    return results


async def notify_scan_completed(
    scan_id: int,
    target: str,
    scan_type: str,
    total_findings: int,
    severity_counts: Optional[dict] = None,
) -> dict[str, bool]:
    sev = severity_counts or {}
    msg = (
        f"\U0001f6e1\ufe0f **Scan Complete** \U0001f6e1\ufe0f\n"
        f"**ID**: `#{scan_id}`\n"
        f"**Target**: `{target}`\n"
        f"**Type**: `{scan_type}`\n"
        f"**Findings**: {total_findings}\n"
        f"**Severity**: "
        f"\U0001f534{sev.get('critical', 0)} "
        f"\U0001f7e0{sev.get('high', 0)} "
        f"\U0001f7e1{sev.get('medium', 0)} "
        f"\U0001f535{sev.get('low', 0)}"
    )
    return await notify_all(msg)


async def notify_threat_alert(
    indicator: str,
    severity: str,
    confidence: float,
    sources: Optional[list[str]] = None,
) -> dict[str, bool]:
    sources_str = ", ".join(sources or ["unknown"])
    icon = "\U0001f534" if severity == "malicious" else "\U0001f7e1"
    msg = (
        f"{icon} **Threat Alert** {icon}\n"
        f"**Indicator**: `{indicator}`\n"
        f"**Severity**: `{severity}`\n"
        f"**Confidence**: `{confidence}%`\n"
        f"**Sources**: `{sources_str}`"
    )
    return await notify_all(msg)


async def notify_error(service: str, error: str) -> dict[str, bool]:
    msg = (
        f"\u26a0\ufe0f **CyberSentinel Error** \u26a0\ufe0f\n"
        f"**Service**: `{service}`\n"
        f"**Error**: `{error}`"
    )
    return await notify_all(msg)
