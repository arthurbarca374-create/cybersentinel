import os
import pytest

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

from backend.services.ai_analysis import _local_analysis, _extract_recommendations, _build_analysis_prompt


class MockScan:
    id = 1
    scan_type = "quick"
    result_summary = {"target": "192.168.1.1", "total_findings": 2}


class MockFinding:
    severity = "high"
    title = "Open port 22/SSH"
    description = "SSH port is exposed"
    recommendation = "Restrict SSH access"


def test_local_analysis_no_findings():
    result = _local_analysis(MockScan(), [], {"total_findings": 0})
    assert "No findings" in result


def test_local_analysis_with_findings():
    result = _local_analysis(MockScan(), [MockFinding()], {"total_findings": 1})
    assert "HIGH" in result
    assert "Open port 22/SSH" in result
    assert "Restrict SSH access" in result


def test_extract_recommendations():
    finding1 = MockFinding()
    finding2 = MockFinding()
    finding2.title = "Open port 443/HTTPS"
    finding2.recommendation = "Restrict SSH access"
    recs = _extract_recommendations([finding1, finding2])
    assert len(recs) == 1
    assert recs[0]["finding"] == "Open port 22/SSH"


def test_extract_recommendations_multiple():
    finding1 = MockFinding()
    finding2 = MockFinding()
    finding2.title = "Open port 443/HTTPS"
    finding2.recommendation = "Enable HTTPS only"
    recs = _extract_recommendations([finding1, finding2])
    assert len(recs) == 2


def test_build_analysis_prompt():
    scan = MockScan()
    findings = [MockFinding()]
    prompt = _build_analysis_prompt(scan, findings, scan.result_summary)
    assert "192.168.1.1" in prompt
    assert "quick" in prompt
    assert "HIGH" in prompt
    assert "Restrict SSH access" in prompt
    assert "remediation" in prompt
