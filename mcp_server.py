import os
import asyncio
import logging

from backend.services.scan_engine import run_scan, create_scan, get_scan, get_findings
from backend.services.threat_intel import lookup_indicator
from backend.services.blockchain import analyze_address
from backend.db.database import SessionLocal

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "info").upper()))
logger = logging.getLogger("mcp-server")

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


TOOL_CONFIGS = [
    {
        "name": "run_scan",
        "description": "Run a security scan against a target host. Types: quick (common ports), full (1-65535), service (banner grab), vuln (vulnerability check), web (HTTP analysis)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_id": {"type": "integer", "description": "Database ID of the target"},
                "scan_type": {"type": "string", "description": "Scan type: quick, full, service, vuln, web", "default": "quick"},
            },
            "required": ["target_id"],
        },
    },
    {
        "name": "threat_lookup",
        "description": "Look up an IP address, domain, or file hash across VirusTotal, Shodan, and AbuseIPDB",
        "inputSchema": {
            "type": "object",
            "properties": {
                "indicator": {"type": "string", "description": "IP address, domain, or file hash"},
                "indicator_type": {"type": "string", "description": "Type: ip, domain, hash", "default": "ip"},
            },
            "required": ["indicator"],
        },
    },
    {
        "name": "analyze_blockchain",
        "description": "Analyze a blockchain wallet address (Bitcoin, Ethereum, Monero)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chain": {"type": "string", "description": "Blockchain: bitcoin, ethereum, monero"},
                "address": {"type": "string", "description": "Wallet address to analyze"},
            },
            "required": ["chain", "address"],
        },
    },
    {
        "name": "scan_findings",
        "description": "Get findings for a completed scan",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "integer", "description": "Scan ID"},
            },
            "required": ["scan_id"],
        },
    },
]


def get_tool_definitions():
    if HAS_MCP:
        return [Tool(**cfg) for cfg in TOOL_CONFIGS]
    return TOOL_CONFIGS


TOOL_HANDLERS = {
    "run_scan": lambda target_id, scan_type="quick": _handle_run_scan(target_id, scan_type),
    "threat_lookup": lambda indicator, indicator_type="ip": _handle_threat_lookup(indicator, indicator_type),
    "analyze_blockchain": lambda chain, address: _handle_blockchain_analysis(chain, address),
    "scan_findings": lambda scan_id: _handle_scan_findings(scan_id),
}


async def _handle_run_scan(target_id: int, scan_type: str = "quick") -> str:
    db = SessionLocal()
    try:
        scan = create_scan(db, user_id=0, target_id=target_id, scan_type=scan_type)
        asyncio.create_task(run_scan(scan.id))
        return f"Scan #{scan.id} started ({scan_type}) on target #{target_id}"
    except Exception as e:
        return f"Error: {e}"
    finally:
        db.close()


async def _handle_threat_lookup(indicator: str, indicator_type: str = "ip") -> str:
    result = await lookup_indicator(indicator, indicator_type)
    return str(result)


async def _handle_blockchain_analysis(chain: str, address: str) -> str:
    result = await analyze_address(chain, address)
    return str(result)


async def _handle_scan_findings(scan_id: int) -> str:
    db = SessionLocal()
    try:
        scan = get_scan(db, scan_id=scan_id, user_id=0)
        if not scan:
            return f"Scan #{scan_id} not found"
        findings = get_findings(db, scan.id)
        return str([{
            "severity": f.severity,
            "title": f.title,
            "description": f.description,
            "recommendation": f.recommendation,
            "port": f.port,
        } for f in findings])
    except Exception as e:
        return f"Error: {e}"
    finally:
        db.close()


async def serve_stdio():
    if not HAS_MCP:
        logger.error("mcp package not installed. Install with: pip install mcp")
        return

    server = Server("cybersentinel")

    @server.list_tools()
    async def list_tools():
        return get_tool_definitions()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        result = await handler(**arguments)
        return [TextContent(type="text", text=result)]

    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main():
    logger.info("CyberSentinel MCP Server starting...")
    asyncio.run(serve_stdio())


if __name__ == "__main__":
    main()
