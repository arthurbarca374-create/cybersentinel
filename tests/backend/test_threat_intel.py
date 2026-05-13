import os
import pytest
from unittest.mock import patch, AsyncMock

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

from backend.services.threat_intel import _calculate_reputation


def test_calculate_reputation_safe():
    rep = _calculate_reputation({})
    assert rep["severity"] == "safe"
    assert rep["confidence"] == 0.0


def test_calculate_reputation_malicious_vt():
    sources = {
        "virustotal": {"malicious": 5, "suspicious": 2, "harmless": 0, "undetected": 0}
    }
    rep = _calculate_reputation(sources)
    assert rep["confidence"] > 75
    assert rep["severity"] == "malicious"


def test_calculate_reputation_abuseipdb():
    sources = {
        "abuseipdb": {
            "abuse_confidence_score": 80,
            "total_reports": 10,
            "last_reported_at": "2024-01-01",
        }
    }
    rep = _calculate_reputation(sources)
    assert rep["severity"] in ("malicious", "suspicious")


def test_calculate_reputation_shodan_ports():
    sources = {
        "shodan": {"ports": [22, 80, 443], "hostnames": []}
    }
    rep = _calculate_reputation(sources)
    assert "Exposed ports" in str(rep["details"])
