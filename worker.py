import os
import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from backend.db.database import SessionLocal
from backend.models.scan import Scan, ScanSchedule
from backend.models.user import User
from backend.services.scan_engine import run_scan
from backend.services.scheduler import check_scheduled_scans

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "info").upper()))
logger = logging.getLogger("cybersentinel-worker")

POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "10"))
MAX_CONCURRENT = int(os.getenv("WORKER_CONCURRENCY", "4"))
CLEANUP_DAYS = int(os.getenv("WORKER_CLEANUP_DAYS", "90"))


async def process_scan_queue():
    db = SessionLocal()
    try:
        pending = db.query(Scan).filter(Scan.status == "pending").limit(MAX_CONCURRENT).all()
        for scan in pending:
            logger.info(f"Worker processing scan {scan.id} ({scan.scan_type})")
            try:
                await run_scan(scan.id)
            except Exception as e:
                logger.error(f"Scan {scan.id} failed: {e}")
                scan.status = "failed"
                scan.error = str(e)
                db.commit()
    finally:
        db.close()


async def process_scheduled_scans():
    await check_scheduled_scans()


async def cleanup_old_data():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=CLEANUP_DAYS)
        old_scans = db.query(Scan).filter(
            Scan.created_at < cutoff,
            Scan.status.in_(["completed", "failed"]),
        ).count()
        old_schedules = db.query(ScanSchedule).filter(
            ScanSchedule.created_at < cutoff,
            ScanSchedule.is_active == False,
        ).count()

        if old_scans:
            db.query(Scan).filter(
                Scan.created_at < cutoff,
                Scan.status.in_(["completed", "failed"]),
            ).delete(synchronize_session=False)
        if old_schedules:
            db.query(ScanSchedule).filter(
                ScanSchedule.created_at < cutoff,
                ScanSchedule.is_active == False,
            ).delete(synchronize_session=False)

        if old_scans or old_schedules:
            db.commit()
            logger.info(f"Cleaned up {old_scans} scans, {old_schedules} schedules older than {CLEANUP_DAYS}d")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
    finally:
        db.close()


async def worker_loop():
    logger.info(f"Worker started (concurrency={MAX_CONCURRENT}, poll={POLL_INTERVAL}s, cleanup={CLEANUP_DAYS}d)")
    cycle = 0
    while True:
        try:
            await process_scan_queue()
            await process_scheduled_scans()

            cycle += 1
            if cycle % (3600 // POLL_INTERVAL) == 0:
                await cleanup_old_data()
                cycle = 0

        except Exception as e:
            logger.error(f"Worker cycle error: {e}")
        await asyncio.sleep(POLL_INTERVAL)


def main():
    logger.info("CyberSentinel Worker starting...")
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
