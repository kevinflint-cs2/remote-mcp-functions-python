import json
import os
import sys
from unittest.mock import Mock

import pytest

# Ensure the `src` package directory is importable when tests run from `src/`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from functions.abuseipdb import (
    abuseipdb_check_ip,
    abuseipdb_report_ip,
    check_ip,
    report_ip,
)


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ABUSEIPDB_API_KEY", "test-key")


def test_check_ip_wrapper_success(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {"data": {"ipAddress": "1.2.3.4", "abuseConfidenceScore": 5}}
    fake = Mock(ok=True, json=Mock(return_value=response))
    monkeypatch.setattr("functions.abuseipdb.requests.get", Mock(return_value=fake))

    ctx = json.dumps({"arguments": {"ip": "1.2.3.4"}})
    result = abuseipdb_check_ip(ctx)
    assert json.loads(result) == response


def test_check_ip_wrapper_missing_ip() -> None:
    ctx = json.dumps({"arguments": {}})
    result = abuseipdb_check_ip(ctx)
    assert result == "No ip provided"


def test_report_ip_wrapper_success(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {"data": {"ipAddress": "1.2.3.4", "reported": True}}
    fake = Mock(ok=True, json=Mock(return_value=response))
    monkeypatch.setattr("functions.abuseipdb.requests.post", Mock(return_value=fake))

    ctx = json.dumps(
        {
            "arguments": {
                "ip": "1.2.3.4",
                "categories": "14,18",
                "comment": "Brute force",
            }
        }
    )
    result = abuseipdb_report_ip(ctx)
    assert json.loads(result) == response


def test_report_ip_wrapper_missing_fields() -> None:
    ctx = json.dumps({"arguments": {"ip": "1.2.3.4", "categories": "14"}})
    result = abuseipdb_report_ip(ctx)
    assert result == "No comment provided"


def test_check_ip_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        check_ip("1.2.3.4")


def test_report_ip_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = Mock(ok=False, status_code=500, text="boom")
    monkeypatch.setattr("functions.abuseipdb.requests.post", Mock(return_value=fake))
    with pytest.raises(RuntimeError):
        report_ip("1.2.3.4", "14", "Bad actor")
