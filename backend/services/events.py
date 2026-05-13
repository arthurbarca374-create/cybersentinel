import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, channel: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(channel, []).append(q)
        return q

    def unsubscribe(self, channel: str, q: asyncio.Queue):
        subs = self._subscribers.get(channel, [])
        if q in subs:
            subs.remove(q)

    async def publish(self, channel: str, data: Any):
        subs = self._subscribers.get(channel, [])
        for q in subs:
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass

    def get_subscriber_count(self, channel: str) -> int:
        return len(self._subscribers.get(channel, []))


event_bus = EventBus()


async def publish_scan_progress(scan_id: int, progress: float, status: str, message: str = ""):
    await event_bus.publish(f"scan:{scan_id}", {
        "type": "scan_progress",
        "scan_id": scan_id,
        "progress": progress,
        "status": status,
        "message": message,
    })
