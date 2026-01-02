import json
import os
from typing import Any, TYPE_CHECKING, cast

import requests

from function_app import (
    _ABUSEIPDB_CATEGORIES_PROPERTY_NAME,
    _ABUSEIPDB_COMMENT_PROPERTY_NAME,
    _ABUSEIPDB_IP_PROPERTY_NAME,
    app,
    tool_properties_abuseipdb_check_ip_json,
    tool_properties_abuseipdb_report_ip_json,
)

# Context arrives as a JSON string; annotate as str for worker compatibility
ContextType = str

if TYPE_CHECKING:
    pass  # pragma: no cover


def _require_api_key() -> str:
    api_key = os.getenv("ABUSEIPDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AbuseIPDB API key not set in environment variable 'ABUSEIPDB_API_KEY'."
        )
    return api_key


def check_ip(ip: str) -> dict[str, Any]:
    """Query the AbuseIPDB 'check' endpoint for information about an IP address."""

    api_key = _require_api_key()
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": api_key, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": "90"}
    response = requests.get(url, headers=headers, params=params, timeout=10)
    if not response.ok:
        raise RuntimeError(
            f"AbuseIPDB check failed: {response.status_code} {response.text}"
        )
    return cast(dict[str, Any], response.json())


def report_ip(ip: str, categories: str, comment: str) -> dict[str, Any]:
    """Report an IP address to AbuseIPDB using the 'report' endpoint."""

    api_key = _require_api_key()
    url = "https://api.abuseipdb.com/api/v2/report"
    headers = {"Key": api_key, "Accept": "application/json"}
    data = {"ip": ip, "categories": categories, "comment": comment}
    response = requests.post(url, headers=headers, data=data, timeout=10)
    if not response.ok:
        raise RuntimeError(
            f"AbuseIPDB report failed: {response.status_code} {response.text}"
        )
    return cast(dict[str, Any], response.json())


def _parse_context(context: ContextType) -> dict[str, Any] | None:
    if isinstance(context, str):
        try:
            payload = json.loads(context)
        except json.JSONDecodeError:
            return None
    elif isinstance(context, dict):
        payload = context
    else:
        return None

    arguments = payload.get("arguments")
    if not isinstance(arguments, dict):
        return None
    return arguments


def _json_response(data: Any) -> str:
    return json.dumps(data)


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="abuseipdb_check_ip",
    description="Check an IP reputation via AbuseIPDB.",
    toolProperties=tool_properties_abuseipdb_check_ip_json,
)
def abuseipdb_check_ip(context: ContextType) -> str:
    args = _parse_context(context)
    if args is None:
        return "Invalid arguments"

    ip = args.get(_ABUSEIPDB_IP_PROPERTY_NAME)
    if not ip:
        return "No ip provided"

    try:
        result = check_ip(ip)
        return _json_response(result)
    except Exception as exc:  # pragma: no cover - exercised in tests
        return f"Error checking IP: {exc}"


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="abuseipdb_report_ip",
    description="Report an IP to AbuseIPDB.",
    toolProperties=tool_properties_abuseipdb_report_ip_json,
)
def abuseipdb_report_ip(context: ContextType) -> str:
    args = _parse_context(context)
    if args is None:
        return "Invalid arguments"

    ip = args.get(_ABUSEIPDB_IP_PROPERTY_NAME)
    categories = args.get(_ABUSEIPDB_CATEGORIES_PROPERTY_NAME)
    comment = args.get(_ABUSEIPDB_COMMENT_PROPERTY_NAME)

    if not ip:
        return "No ip provided"
    if not categories:
        return "No categories provided"
    if not comment:
        return "No comment provided"

    try:
        result = report_ip(ip, categories, comment)
        return _json_response(result)
    except Exception as exc:  # pragma: no cover - exercised in tests
        return f"Error reporting IP: {exc}"
