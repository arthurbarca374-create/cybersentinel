import asyncio
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from backend.models.threat import ThreatIntel, IntelReport
from backend.core.config import get_settings
from backend.core.http_client import create_client
from backend.services.notifications import notify_threat_alert

settings = get_settings()


async def lookup_indicator(indicator: str, indicator_type: str = "ip") -> dict:
    results = {"indicator": indicator, "type": indicator_type, "sources": {}}

    if settings.VIRUSTOTAL_API_KEY:
        results["sources"]["virustotal"] = await _check_virustotal(indicator)
    if settings.SHODAN_API_KEY and indicator_type == "ip":
        results["sources"]["shodan"] = await _check_shodan(indicator)
    if settings.ABUSEIPDB_API_KEY and indicator_type == "ip":
        results["sources"]["abuseipdb"] = await _check_abuseipdb(indicator)

    results["reputation"] = _calculate_reputation(results["sources"])

    rep = results["reputation"]
    if rep.get("severity") in ("malicious", "suspicious"):
        source_names = [s for s in results["sources"] if "error" not in results["sources"][s]]
        asyncio.create_task(notify_threat_alert(
            indicator=indicator,
            severity=rep["severity"],
            confidence=rep["confidence"],
            sources=source_names,
        ))

    return results


async def _check_virustotal(indicator: str) -> dict:
    async with create_client(timeout=15) as client:
        resp = await client.get(
            f"https://www.virustotal.com/api/v3/search?query={indicator}",
            headers={"x-apikey": settings.VIRUSTOTAL_API_KEY},
        )
        if resp.status_code == 200:
            data = resp.json()
            stats = data.get("data", [{}])[0].get("attributes", {}).get("last_analysis_stats", {})
            return {"malicious": stats.get("malicious", 0), "suspicious": stats.get("suspicious", 0), "harmless": stats.get("harmless", 0), "undetected": stats.get("undetected", 0)}
        return {"error": f"VT API error: {resp.status_code}"}


async def _check_shodan(indicator: str) -> dict:
    async with create_client(timeout=15) as client:
        resp = await client.get(
            f"https://api.shodan.io/shodan/host/{indicator}",
            params={"key": settings.SHODAN_API_KEY},
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "ports": data.get("ports", []),
                "org": data.get("org", ""),
                "os": data.get("os", ""),
                "hostnames": data.get("hostnames", []),
                "vulns": data.get("vulns", []),
            }
        return {"error": f"Shodan error: {resp.status_code}"}


async def _check_abuseipdb(indicator: str) -> dict:
    async with create_client(timeout=15) as client:
        resp = await client.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={"Key": settings.ABUSEIPDB_API_KEY, "Accept": "application/json"},
            params={"ipAddress": indicator, "maxAgeInDays": 90},
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return {
                "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0),
                "last_reported_at": data.get("lastReportedAt"),
                "country": data.get("countryCode", ""),
                "isp": data.get("isp", ""),
                "domain": data.get("domain", ""),
                "usage_type": data.get("usageType", ""),
            }
        return {"error": f"AbuseIPDB error: {resp.status_code}"}


def _calculate_reputation(sources: dict) -> dict:
    score = 0
    max_score = 0
    details = []

    for source, data in sources.items():
        if "malicious" in data:
            max_score += 100
            score += min(data["malicious"] * 20, 100)
            if data["malicious"] > 0:
                details.append(f"Flagged by {data['malicious']} VT engines")
        if "abuse_confidence_score" in data:
            max_score += 100
            score += data["abuse_confidence_score"]
            if data["abuse_confidence_score"] > 0:
                details.append(f"AbuseIPDB confidence: {data['abuse_confidence_score']}%")
        if "ports" in data:
            details.append(f"Exposed ports: {len(data['ports'])}")

    confidence = round((score / max_score) * 100, 1) if max_score > 0 else 0
    severity = "safe"
    if confidence > 75:
        severity = "malicious"
    elif confidence > 50:
        severity = "suspicious"
    elif confidence > 25:
        severity = "unusual"

    return {"confidence": confidence, "severity": severity, "details": details}


def store_intel(db: Session, source: str, indicator: str, indicator_type: str, data: dict) -> ThreatIntel:
    existing = db.query(ThreatIntel).filter(
        ThreatIntel.source == source, ThreatIntel.indicator == indicator
    ).first()

    if existing:
        existing.last_seen = datetime.utcnow()
        existing.raw_data = data
        db.commit()
        return existing

    intel = ThreatIntel(
        source=source,
        indicator=indicator,
        indicator_type=indicator_type,
        severity=data.get("reputation", {}).get("severity", "unknown"),
        confidence=data.get("reputation", {}).get("confidence", 0.0),
        raw_data=data,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
    )
    db.add(intel)
    db.commit()
    db.refresh(intel)
    return intel


def get_threat_feed(db: Session, limit: int = 100) -> list[ThreatIntel]:
    return db.query(ThreatIntel).order_by(ThreatIntel.last_seen.desc().nullslast()).limit(limit).all()


def get_threat_stats(db: Session) -> dict:
    total = db.query(sql_func.count(ThreatIntel.id)).scalar() or 0
    by_severity = db.query(
        ThreatIntel.severity, sql_func.count(ThreatIntel.id)
    ).group_by(ThreatIntel.severity).all()
    return {
        "total_indicators": total,
        "by_severity": {s: c for s, c in by_severity},
    }


def create_intel_report(db: Session, user_id: Optional[int], title: str, **kwargs) -> IntelReport:
    report = IntelReport(user_id=user_id, title=title, **kwargs)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_intel_reports(db: Session, limit: int = 20) -> list[IntelReport]:
    return db.query(IntelReport).order_by(IntelReport.created_at.desc()).limit(limit).all()
