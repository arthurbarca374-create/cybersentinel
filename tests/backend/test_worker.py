import os
import pytest
from unittest.mock import patch, AsyncMock

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

from worker import process_scan_queue, cleanup_old_data


@pytest.mark.asyncio
async def test_process_scan_queue_empty():
    result = await process_scan_queue()
    assert result is None


@pytest.mark.asyncio
async def test_cleanup_old_data():
    result = await cleanup_old_data()
    assert result is None
