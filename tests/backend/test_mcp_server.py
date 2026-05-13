import os
import pytest

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

from mcp_server import TOOL_CONFIGS, TOOL_HANDLERS, get_tool_definitions


def test_tool_configs_present():
    names = {t["name"] for t in TOOL_CONFIGS}
    assert "run_scan" in names
    assert "threat_lookup" in names
    assert "analyze_blockchain" in names
    assert "scan_findings" in names


def test_tool_handlers_present():
    assert "run_scan" in TOOL_HANDLERS
    assert "threat_lookup" in TOOL_HANDLERS
    assert "analyze_blockchain" in TOOL_HANDLERS
    assert "scan_findings" in TOOL_HANDLERS


def test_tool_input_schemas():
    for cfg in TOOL_CONFIGS:
        assert "inputSchema" in cfg
        schema = cfg["inputSchema"]
        assert "properties" in schema
        assert "required" in schema


def test_get_tool_definitions_fallback():
    tools = get_tool_definitions()
    assert len(tools) == 4
    assert isinstance(tools[0], dict)


@pytest.mark.asyncio
async def test_handle_scan_findings_not_found():
    result = await TOOL_HANDLERS["scan_findings"](scan_id=99999)
    assert "not found" in result
