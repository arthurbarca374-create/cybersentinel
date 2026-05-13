import asyncio
import os
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.scan import Scan, Finding, Target
from backend.db.database import SessionLocal
from backend.services.notifications import notify_scan_completed
from backend.services.events import publish_scan_progress

SCAN_TIMEOUT = int(os.getenv("SCAN_TIMEOUT", "300"))
STUCK_SCAN_THRESHOLD = int(os.getenv("STUCK_SCAN_THRESHOLD", "600"))

logger = logging.getLogger(__name__)

SCAN_TYPES = {
    "quick": "Fast port scan (common ports)",
    "full": "Full port scan (1-65535)",
    "service": "Service version detection",
    "vuln": "Vulnerability assessment",
    "web": "Web application scan",
}


def get_scan_types():
    return [{"id": k, "name": v} for k, v in SCAN_TYPES.items()]


def create_target(db: Session, user_id: int, name: str, host: str, **kwargs) -> Target:
    target = Target(user_id=user_id, name=name, host=host, **kwargs)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def get_targets(db: Session, user_id: int) -> list[Target]:
    return db.query(Target).filter(Target.user_id == user_id, Target.is_active == True).all()


def delete_target(db: Session, target_id: int, user_id: int) -> bool:
    target = db.query(Target).filter(Target.id == target_id, Target.user_id == user_id).first()
    if not target:
        return False
    target.is_active = False
    db.commit()
    return True


def create_scan(db: Session, user_id: int, target_id: int, scan_type: str, config: Optional[dict] = None) -> Scan:
    scan = Scan(
        user_id=user_id,
        target_id=target_id,
        scan_type=scan_type,
        status="pending",
        config=config or {},
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def get_scans(db: Session, user_id: int, limit: int = 50) -> list[Scan]:
    return db.query(Scan).filter(Scan.user_id == user_id).order_by(Scan.created_at.desc()).limit(limit).all()


def get_scan(db: Session, scan_id: int, user_id: int) -> Optional[Scan]:
    return db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user_id).first()


def get_findings(db: Session, scan_id: int) -> list[Finding]:
    return db.query(Finding).filter(Finding.scan_id == scan_id).order_by(Finding.severity.desc()).all()


def _validate_port(port: int) -> bool:
    return isinstance(port, int) and 1 <= port <= 65535


def _parse_ports(ports_str: str) -> list[int]:
    valid = []
    for p in ports_str.split(","):
        p = p.strip()
        try:
            port = int(p)
            if _validate_port(port):
                valid.append(port)
            else:
                logger.warning(f"Ignoring invalid port: {p}")
        except ValueError:
            logger.warning(f"Ignoring non-numeric port: {p}")
    return valid


async def run_scan(scan_id: int):
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        scan.status = "running"
        scan.started_at = datetime.utcnow()
        scan.progress = 0.0
        db.commit()

        await publish_scan_progress(scan.id, 0.0, "running", "Starting scan")

        target = db.query(Target).filter(Target.id == scan.target_id).first()
        if not target:
            scan.status = "failed"
            scan.error = "Target not found"
            db.commit()
            return

        host = target.host
        scan_type = scan.scan_type
        config = scan.config or {}

        async def _execute_scan():
            loop = asyncio.get_event_loop()

            if scan_type == "quick":
                ports = config.get("ports", "21,22,23,25,53,80,110,143,443,445,993,995,1433,1521,2049,3306,3389,5432,5900,6379,8080,8443,9090,27017")
                port_list = _parse_ports(ports)
                return await _tcp_scan(host, port_list, scan, db, loop)

            elif scan_type == "service":
                ports = config.get("ports", "22,80,443,3306,5432,8080")
                port_list = _parse_ports(ports)
                return await _service_scan(host, port_list, scan, db, loop)

            elif scan_type == "vuln":
                return await _vuln_check(host, scan, db, loop)

            elif scan_type == "web":
                return await _web_scan(host, scan, db)

            else:
                ports = config.get("ports", "80,443,8080")
                port_list = _parse_ports(ports)
                return await _tcp_scan(host, port_list, scan, db, loop)

        findings = await asyncio.wait_for(_execute_scan(), timeout=SCAN_TIMEOUT)

        severity_map = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.get("severity", "info")
            severity_map[sev] = severity_map.get(sev, 0) + 1

        scan.result_summary = {
            "total_findings": len(findings),
            "severity_counts": severity_map,
            "target": host,
        }
        scan.status = "completed"
        scan.progress = 100.0
        scan.completed_at = datetime.utcnow()
        db.commit()

        await publish_scan_progress(scan.id, 100.0, "completed", f"Found {len(findings)} issues")

        _update_trial_scan(db, scan)

        asyncio.create_task(notify_scan_completed(
            scan_id=scan.id,
            target=host,
            scan_type=scan_type,
            total_findings=len(findings),
            severity_counts=severity_map,
        ))

    except asyncio.TimeoutError:
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = "failed"
                scan.error = f"Scan timed out after {SCAN_TIMEOUT}s"
                db.commit()
                asyncio.create_task(publish_scan_progress(scan_id, 0, "failed", f"Timed out after {SCAN_TIMEOUT}s"))
        except Exception as db_e:
            logger.error(f"Failed to mark timed-out scan {scan_id}: {db_e}")
    except Exception as e:
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = "failed"
                scan.error = str(e)
                db.commit()
                asyncio.create_task(publish_scan_progress(scan_id, 0, "failed", str(e)))
        except Exception as db_e:
            logger.error(f"Failed to mark scan {scan_id} as failed: {db_e}")
    finally:
        db.close()


def cleanup_stuck_scans():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow()
        stuck = db.query(Scan).filter(
            Scan.status == "running",
            Scan.started_at < cutoff,
        ).all()
        for s in stuck:
            elapsed = (cutoff - s.started_at).total_seconds() if s.started_at else 0
            if elapsed > STUCK_SCAN_THRESHOLD:
                s.status = "failed"
                s.error = f"Stuck scan auto-cleaned after {elapsed:.0f}s"
                logger.warning(f"Cleaned stuck scan {s.id} (ran for {elapsed:.0f}s)")
        db.commit()
    except Exception as e:
        logger.error(f"Stuck scan cleanup error: {e}")
    finally:
        db.close()


async def _check_port(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError):
        return False


async def _grab_banner(host: str, port: int, timeout: float = 2) -> str:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.write(b"HEAD / HTTP/1.0\r\n\r\n")
        await writer.drain()
        banner = await asyncio.wait_for(reader.read(1024), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return banner.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


async def _tcp_scan(host: str, ports: list[int], scan: Scan, db: Session, loop: asyncio.AbstractEventLoop) -> list[dict]:
    findings = []
    findings_batch = []
    total = len(ports)

    for i, port in enumerate(ports):
        if total > 0 and i % 10 == 0:
            scan.progress = round((i / total) * 100, 1)
            db.commit()

        try:
            if await _check_port(host, port):
                service = _guess_service(port)
                findings_batch.append({
                    "scan_id": scan.id,
                    "finding_type": "open_port",
                    "severity": "medium",
                    "title": f"Open port {port}/{service}",
                    "description": f"Port {port} ({service}) is open on {host}",
                    "port": port,
                    "protocol": "tcp",
                    "evidence": {"service": service},
                })
                findings.append({"port": port, "service": service, "severity": "medium"})
        except Exception:
            continue

    _bulk_create_findings(db, findings_batch)
    scan.progress = 100.0
    db.commit()
    return findings


async def _service_scan(host: str, ports: list[int], scan: Scan, db: Session, loop: asyncio.AbstractEventLoop) -> list[dict]:
    findings = []
    findings_batch = []
    for i, port in enumerate(ports):
        if i % 10 == 0:
            scan.progress = round((i / len(ports)) * 100, 1)
            db.commit()
        try:
            if await _check_port(host, port, timeout=2):
                banner = await _grab_banner(host, port)
                service = _guess_service(port)
                findings_batch.append({
                    "scan_id": scan.id,
                    "finding_type": "service_detection",
                    "severity": "info",
                    "title": f"Service on port {port}: {service}",
                    "description": f"Detected {service} on {host}:{port}",
                    "port": port,
                    "protocol": "tcp",
                    "evidence": {"banner": banner[:500], "service": service},
                })
                findings.append({"port": port, "service": service, "banner": banner[:100]})
        except Exception:
            continue
    _bulk_create_findings(db, findings_batch)
    scan.progress = 100.0
    db.commit()
    return findings


async def _vuln_check(host: str, scan: Scan, db: Session, loop: asyncio.AbstractEventLoop) -> list[dict]:
    findings = []
    findings_batch = []
    checks = [
        ("open-ssh", 22, "SSH", "SSH service exposed - check for weak credentials"),
        ("open-http", 80, "HTTP", "HTTP service - check for web vulnerabilities"),
        ("open-https", 443, "HTTPS", "HTTPS service - verify TLS configuration"),
        ("open-mysql", 3306, "MySQL", "Database port exposed to internet"),
        ("open-pgsql", 5432, "PostgreSQL", "Database port exposed to internet"),
    ]
    for i, (vuln_id, port, service, desc) in enumerate(checks):
        scan.progress = round((i / len(checks)) * 100, 1)
        db.commit()
        try:
            if await _check_port(host, port, timeout=1):
                findings_batch.append({
                    "scan_id": scan.id,
                    "finding_type": vuln_id,
                    "severity": "high" if port in [3306, 5432] else "medium",
                    "title": f"Exposed {service} (port {port})",
                    "description": desc,
                    "port": port,
                    "protocol": "tcp",
                    "recommendation": f"Restrict access to port {port} using a firewall",
                })
                findings.append({"vuln_id": vuln_id, "port": port, "severity": "high" if port in [3306, 5432] else "medium"})
        except Exception:
            continue
    _bulk_create_findings(db, findings_batch)
    scan.progress = 100.0
    db.commit()
    return findings


async def _web_scan(host: str, scan: Scan, db: Session) -> list[dict]:
    findings = []
    findings_batch = []
    import httpx
    protocols = ["https", "http"]
    for i, proto in enumerate(protocols):
        scan.progress = round((i / len(protocols)) * 50, 1)
        db.commit()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{proto}://{host}")
                headers = {k.lower(): v for k, v in resp.headers.items()}

                findings_batch.append({
                    "scan_id": scan.id,
                    "finding_type": "web_access",
                    "severity": "info",
                    "title": f"Web server accessible via {proto.upper()}",
                    "description": f"{host} responds on {proto.upper()} with status {resp.status_code}",
                    "evidence": {"status_code": resp.status_code, "server": headers.get("server", "")},
                })
                findings.append({"protocol": proto, "status": resp.status_code})

                if headers.get("x-frame-options", "").lower() not in ("deny", "sameorigin"):
                    findings_batch.append({
                        "scan_id": scan.id,
                        "finding_type": "missing_header",
                        "severity": "low",
                        "title": "Missing X-Frame-Options header",
                        "description": f"{proto.upper()}://{host} is missing clickjacking protection",
                        "recommendation": "Add X-Frame-Options: DENY or SAMEORIGIN",
                    })
                    findings.append({"header": "X-Frame-Options", "severity": "low"})

        except httpx.ConnectError:
            scan.progress += 50
            db.commit()
        except Exception:
            continue
    _bulk_create_findings(db, findings_batch)
    scan.progress = 100.0
    db.commit()
    return findings


def _bulk_create_findings(db: Session, batch: list[dict]):
    if not batch:
        return
    for item in batch:
        finding = Finding(
            scan_id=item["scan_id"],
            type=item["finding_type"],
            severity=item["severity"],
            title=item["title"],
            description=item.get("description"),
            recommendation=item.get("recommendation"),
            port=item.get("port"),
            protocol=item.get("protocol"),
            evidence=item.get("evidence"),
        )
        db.add(finding)
    db.commit()


def _guess_service(port: int) -> str:
    common = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
        443: "HTTPS", 993: "IMAPS", 995: "POP3S",
        1433: "MSSQL", 1521: "Oracle", 2049: "NFS",
        3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
        5900: "VNC", 6379: "Redis", 8080: "HTTP-Alt",
        8443: "HTTPS-Alt", 9090: "HTTP-Alt2", 27017: "MongoDB",
    }
    return common.get(port, "unknown")


def _update_trial_scan(db: Session, scan: Scan):
    from backend.models.user import User
    user = db.query(User).filter(User.id == scan.user_id).first()
    if not user:
        logger.warning(f"Trial update failed: user {scan.user_id} not found for scan {scan.id}")
        return
    user.trial_scans_used += 1
    db.commit()
