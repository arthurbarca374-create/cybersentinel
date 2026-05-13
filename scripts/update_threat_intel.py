import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.db.database import SessionLocal
from backend.models.threat import ThreatIntel
from backend.services.threat_intel import lookup_indicator, store_intel
from backend.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("threat-intel-update")

settings = get_settings()

DEFAULT_FEEDS = [
    ("ip", "8.8.8.8"),
    ("ip", "1.1.1.1"),
    ("ip", "9.9.9.9"),
]


async def update_indicator(indicator: str, indicator_type: str = "ip") -> dict:
    result = await lookup_indicator(indicator, indicator_type)
    db = SessionLocal()
    try:
        for source_name, source_data in result.get("sources", {}).items():
            if "error" not in source_data:
                store_intel(db, source=source_name, indicator=indicator,
                            indicator_type=indicator_type, data={"reputation": result.get("reputation", {})})
        logger.info(f"Updated threat intel for {indicator}: {result.get('reputation', {})}")
        return result
    except Exception as e:
        logger.error(f"Failed to update {indicator}: {e}")
        return {"error": str(e)}
    finally:
        db.close()


async def refresh_feeds():
    logger.info("Refreshing threat intel feeds...")
    for ind_type, indicator in DEFAULT_FEEDS:
        await update_indicator(indicator, ind_type)


def main():
    parser = argparse.ArgumentParser(description="CyberSentinel Threat Intel Update Cron Job")
    parser.add_argument("--indicator", type=str, help="Single indicator to look up")
    parser.add_argument("--type", dest="indicator_type", default="ip",
                        choices=["ip", "domain", "hash"],
                        help="Indicator type")
    parser.add_argument("--refresh-feeds", action="store_true", help="Refresh default threat feeds")
    args = parser.parse_args()

    if args.indicator:
        asyncio.run(update_indicator(args.indicator, args.indicator_type))
    elif args.refresh_feeds:
        asyncio.run(refresh_feeds())
    else:
        asyncio.run(refresh_feeds())


if __name__ == "__main__":
    main()
