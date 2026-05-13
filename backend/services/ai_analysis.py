from typing import Optional
from sqlalchemy.orm import Session
from backend.models.scan import Scan, Finding
from backend.core.config import get_settings
from backend.core.http_client import create_client

settings = get_settings()


async def analyze_scan(db: Session, scan_id: int, model: str = "default") -> dict:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        return {"error": "Scan not found"}

    findings = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    summary = scan.result_summary or {}

    prompt = _build_analysis_prompt(scan, findings, summary)

    actual_model = "local"
    if model == "claude" and settings.ANTHROPIC_API_KEY:
        analysis = await _call_anthropic(prompt)
        actual_model = "claude-3-haiku"
    elif model in ("gpt4", "default") and settings.OPENAI_API_KEY:
        analysis = await _call_openai(prompt)
        actual_model = "gpt-4o-mini"
    elif settings.LLM_API_URL:
        analysis = await _call_llm_api(prompt)
        actual_model = f"llm:{settings.LLM_MODEL or 'default'}"
    else:
        analysis = _local_analysis(scan, findings, summary)

    recommendations = _extract_recommendations(findings)

    return {
        "scan_id": scan_id,
        "analysis": analysis,
        "model_used": actual_model,
        "findings_summary": summary,
        "recommendations": recommendations,
    }


def _build_analysis_prompt(scan: Scan, findings: list[Finding], summary: dict) -> str:
    target_info = scan.result_summary.get("target", "unknown") if scan.result_summary else "unknown"
    lines = [
        f"Analyze the following security scan results for target: {target_info}",
        f"Scan type: {scan.scan_type}",
        f"Total findings: {summary.get('total_findings', 0)}",
        "",
        "Findings:",
    ]
    for f in findings:
        lines.append(f"- [{f.severity.upper()}] {f.title}: {f.description or ''}")
        if f.recommendation:
            lines.append(f"  Recommendation: {f.recommendation}")
    lines.extend([
        "",
        "Please provide:",
        "1. Overall risk assessment",
        "2. Most critical issues to address first",
        "3. Suggested remediation steps",
        "4. Any additional checks recommended",
    ])
    return "\n".join(lines)


async def _call_anthropic(prompt: str) -> str:
    async with create_client(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"]
        return f"AI analysis failed: {resp.text}"


async def _call_openai(prompt: str) -> str:
    async with create_client(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
            },
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"AI analysis failed: {resp.text}"


async def _call_llm_api(prompt: str) -> str:
    async with create_client(timeout=60) as client:
        resp = await client.post(
            f"{settings.LLM_API_URL}/v1/chat/completions",
            json={
                "model": settings.LLM_MODEL or "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"AI analysis failed: {resp.text}"


def _local_analysis(scan: Scan, findings: list[Finding], summary: dict) -> str:
    if not findings:
        return "No findings to analyze. The target appears clean for the scan performed."

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 99))

    critical = [f for f in findings if f.severity == "critical"]
    high = [f for f in findings if f.severity == "high"]
    medium = [f for f in findings if f.severity == "medium"]

    lines = ["## Local Analysis Results", ""]
    if critical:
        lines.append(f"**CRITICAL**: {len(critical)} critical issues found - immediate action required!")
    if high:
        lines.append(f"**HIGH**: {len(high)} high severity issues detected.")
    if medium:
        lines.append(f"**MEDIUM**: {len(medium)} medium severity items to review.")
    lines.append("")

    for f in sorted_findings[:10]:
        lines.append(f"### [{f.severity.upper()}] {f.title}")
        if f.description:
            lines.append(f"  {f.description}")
        if f.recommendation:
            lines.append(f"  **Fix**: {f.recommendation}")
        lines.append("")

    if len(findings) > 10:
        lines.append(f"... and {len(findings) - 10} more findings")

    return "\n".join(lines)


def _extract_recommendations(findings: list[Finding]) -> list:
    seen = set()
    recs = []
    for f in findings:
        if f.recommendation and f.recommendation not in seen:
            seen.add(f.recommendation)
            recs.append({
                "finding": f.title,
                "severity": f.severity,
                "recommendation": f.recommendation,
            })
    return recs
