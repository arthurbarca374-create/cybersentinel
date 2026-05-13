import os
import pytest
from unittest.mock import patch, AsyncMock

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

from backend.services.notifications import (
    send_discord, send_telegram, notify_all,
    notify_scan_completed, notify_threat_alert,
)


@pytest.mark.asyncio
async def test_send_discord_no_webhook():
    result = await send_discord("test", webhook_url="")
    assert result is False


@pytest.mark.asyncio
async def test_send_telegram_no_config():
    result = await send_telegram("test", bot_token="", chat_id="")
    assert result is False


@pytest.mark.asyncio
async def test_notify_all_no_config():
    result = await notify_all("test")
    assert result == {}


@pytest.mark.asyncio
async def test_notify_scan_completed_no_config():
    result = await notify_scan_completed(1, "192.168.1.1", "quick", 5)
    assert result == {}


@pytest.mark.asyncio
async def test_notify_threat_alert_no_config():
    result = await notify_threat_alert("8.8.8.8", "malicious", 85.0, ["virustotal"])
    assert result == {}
