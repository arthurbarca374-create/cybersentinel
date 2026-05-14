import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

NUCLEI_BIN = os.getenv("NUCLEI_BIN", "nuclei")
NUCLEI_TEMPLATES = os.getenv("NUCLEI_TEMPLATES", "")

SEVERITY_MAP = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
    "unknown": 0,
}


def _findings_from_nuclei_output(raw: str, scan_id: int) -> list[dict]:
    findings = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            continue

        severity = result.get("info", {}).get("severity", "unknown").lower()
        finding = {
            "scan_id": scan_id,
            "title": result.get("info", {}).get("name", "Unknown finding"),
            "severity": severity,
            "severity_id": SEVERITY_MAP.get(severity, 0),
            "detail": result.get("info", {}).get("description", ""),
            "port": result.get("port", 0),
            "protocol": result.get("protocol", ""),
            "matched": result.get("matched-at", ""),
            "curl_command": result.get("curl-command", ""),
            "cve_ids": result.get("info", {}).get("classification", {}).get("cve-id", []),
            "cwe_ids": result.get("info", {}).get("classification", {}).get("cwe-id", []),
            "remediation": result.get("info", {}).get("remediation", ""),
            "tags": result.get("info", {}).get("tags", []),
            "raw_result": result,
        }
        findings.append(finding)

    return findings


def _build_nuclei_args(
    target: str,
    scan_type: str,
    ports: Optional[list[int]] = None,
    config: Optional[dict] = None,
) -> list[str]:
    args = [
        NUCLEI_BIN,
        "-target", target,
        "-json",
        "-silent",
        "-stats",
        "-disable-update-check",
    ]

    if NUCLEI_TEMPLATES:
        args.extend(["-templates", NUCLEI_TEMPLATES])

    severity_filter = {
        "nuclei-critical": "critical",
        "nuclei-high": "critical,high",
        "nuclei-medium": "critical,high,medium",
        "nuclei-all": "critical,high,medium,low,info",
    }

    if scan_type in severity_filter:
        args.extend(["-severity", severity_filter[scan_type]])

    if ports:
        args.extend(["-ports", ",".join(str(p) for p in ports)])

    if config:
        if config.get("tags"):
            args.extend(["-tags", ",".join(config["tags"])])
        if config.get("exclude"):
            args.extend(["-exclude", ",".join(config["exclude"])])
        if config.get("timeout"):
            args.extend(["-timeout", str(config["timeout"])])
        if config.get("concurrency"):
            args.extend(["-concurrency", str(config["concurrency"])])
        if config.get("rate-limit"):
            args.extend(["-rate-limit", str(config["rate-limit"])])

    return args


async def run_nuclei_scan(
    target: str,
    scan_id: int,
    scan_type: str = "nuclei-medium",
    ports: Optional[list[int]] = None,
    config: Optional[dict] = None,
    timeout: int = 300,
) -> tuple[str, list[dict]]:
    args = _build_nuclei_args(target, scan_type, ports, config)
    logger.info(f"Running nuclei scan {scan_id}: {' '.join(args)}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            logger.warning(f"Nuclei scan {scan_id} timed out after {timeout}s")
            return "timeout", []

        raw_out = stdout.decode("utf-8", errors="replace")
        err_out = stderr.decode("utf-8", errors="replace")

        if proc.returncode != 0 and not raw_out.strip():
            logger.error(f"Nuclei scan {scan_id} failed (code {proc.returncode}): {err_out[:500]}")
            return f"error: {err_out[:200]}", []

        findings = _findings_from_nuclei_output(raw_out, scan_id)
        logger.info(f"Nuclei scan {scan_id} complete: {len(findings)} findings")
        return "completed", findings

    except FileNotFoundError:
        logger.error("nuclei binary not found — install with: apt-get install nuclei")
        return "error: nuclei binary not found", []
    except Exception as e:
        logger.error(f"Nuclei scan {scan_id} exception: {e}")
        return f"error: {e}", []


NUCLEI_SCAN_TYPES = {
    "nuclei-critical": "Critical severity Nuclei scan (CVE detection, high-risk only)",
    "nuclei-high": "High+ severity Nuclei scan",
    "nuclei-medium": "Medium+ severity Nuclei scan (recommended)",
    "nuclei-all": "Full Nuclei scan — all severities (slowest, most thorough)",
}
