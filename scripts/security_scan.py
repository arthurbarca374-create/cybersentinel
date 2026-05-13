import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.db.database import SessionLocal
from backend.models.scan import Target, Scan
from backend.services.scan_engine import run_scan, create_scan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("security-scan")


async def scan_target(target_id: int, scan_type: str = "quick", user_id: int = 0):
    db = SessionLocal()
    try:
        target = db.query(Target).filter(Target.id == target_id, Target.is_active == True).first()
        if not target:
            logger.error(f"Target {target_id} not found or inactive")
            return False

        scan = create_scan(db, user_id=user_id, target_id=target_id, scan_type=scan_type)
        db.commit()
        logger.info(f"Starting scan #{scan.id} ({scan_type}) on {target.host}")
        await run_scan(scan.id)
        logger.info(f"Scan #{scan.id} completed for {target.host}")
        return True
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return False
    finally:
        db.close()


async def scan_all_active(scan_type: str = "quick"):
    db = SessionLocal()
    try:
        targets = db.query(Target).filter(Target.is_active == True).all()
        if not targets:
            logger.info("No active targets found")
            return

        logger.info(f"Scanning {len(targets)} active targets ({scan_type})")
        for target in targets:
            scan = create_scan(db, user_id=target.user_id, target_id=target.id, scan_type=scan_type)
            db.commit()
            logger.info(f"Queued scan #{scan.id} for {target.host}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="CyberSentinel Security Scan Cron Job")
    parser.add_argument("--target", type=int, help="Target ID to scan (default: all active)")
    parser.add_argument("--type", dest="scan_type", default="quick",
                        choices=["quick", "full", "service", "vuln", "web"],
                        help="Scan type")
    parser.add_argument("--user", type=int, default=0, help="User ID to associate scans with")
    args = parser.parse_args()

    if args.target:
        asyncio.run(scan_target(args.target, args.scan_type, args.user))
    else:
        asyncio.run(scan_all_active(args.scan_type))


if __name__ == "__main__":
    main()
