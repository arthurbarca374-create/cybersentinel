import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.models.scan import Scan, ScanSchedule
from backend.services.scan_engine import run_scan, cleanup_stuck_scans

logger = logging.getLogger(__name__)


async def process_pending_scans():
    db = SessionLocal()
    try:
        pending = db.query(Scan).filter(Scan.status == "pending").limit(5).all()
        for scan in pending:
            logger.info(f"Starting scan {scan.id} ({scan.scan_type}) on target {scan.target_id}")
            await run_scan(scan.id)
    finally:
        db.close()


async def check_scheduled_scans():
    db = SessionLocal()
    try:
        from croniter import croniter
        now = datetime.utcnow()
        schedules = db.query(ScanSchedule).filter(
            ScanSchedule.is_active == True,
            ScanSchedule.next_run <= now,
        ).all()

        for sched in schedules:
            scan = Scan(
                user_id=sched.user_id,
                target_id=sched.target_id,
                scan_type=sched.scan_type,
                status="pending",
                config=sched.config,
            )
            db.add(scan)
            db.commit()

            sched.last_run = now
            cron = croniter(sched.cron_expression, now)
            sched.next_run = cron.get_next(datetime)
            db.commit()

            logger.info(f"Scheduled scan {scan.id} created from schedule {sched.id}")
    except ImportError:
        logger.warning("croniter not installed - scheduled scans disabled")
    finally:
        db.close()


async def run_scheduler_loop(interval: int = 10):
    cycle = 0
    while True:
        try:
            await process_pending_scans()
            await check_scheduled_scans()
            cycle += 1
            if cycle % (60 // interval) == 0:
                cleanup_stuck_scans()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(interval)
