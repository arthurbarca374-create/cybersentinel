import pytest
from unittest.mock import patch, AsyncMock
from backend.services.scan_engine import (
    SCAN_TYPES, get_scan_types, _validate_port, _parse_ports, _guess_service
)


def test_get_scan_types():
    types = get_scan_types()
    assert len(types) == 5
    assert {t["id"] for t in types} == {"quick", "full", "service", "vuln", "web"}


def test_scan_types_dict():
    assert "quick" in SCAN_TYPES
    assert "full" in SCAN_TYPES
    assert "service" in SCAN_TYPES
    assert "vuln" in SCAN_TYPES
    assert "web" in SCAN_TYPES


def test_validate_port():
    assert _validate_port(1) is True
    assert _validate_port(65535) is True
    assert _validate_port(80) is True
    assert _validate_port(0) is False
    assert _validate_port(65536) is False
    assert _validate_port(-1) is False


def test_parse_ports():
    assert _parse_ports("80,443,8080") == [80, 443, 8080]
    assert _parse_ports("80") == [80]
    assert _parse_ports("") == []
    assert _parse_ports("invalid,80") == [80]


def test_parse_ports_ignores_out_of_range():
    assert _parse_ports("0,80,99999") == [80]


def test_guess_service():
    assert _guess_service(22) == "SSH"
    assert _guess_service(80) == "HTTP"
    assert _guess_service(443) == "HTTPS"
    assert _guess_service(3306) == "MySQL"
    assert _guess_service(99999) == "unknown"
    assert _guess_service(0) == "unknown"
