import json
from dataclasses import dataclass
from typing import Dict, List, TYPE_CHECKING

import azure.functions as func


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Constants for the Azure Blob Storage container, file, and blob path
_SNIPPET_NAME_PROPERTY_NAME = "snippetname"
_SNIPPET_PROPERTY_NAME = "snippet"
_BLOB_PATH = "snippets/{mcptoolargs." + _SNIPPET_NAME_PROPERTY_NAME + "}.json"

# AbuseIPDB tool property names
_ABUSEIPDB_IP_PROPERTY_NAME = "ip"
_ABUSEIPDB_CATEGORIES_PROPERTY_NAME = "categories"
_ABUSEIPDB_COMMENT_PROPERTY_NAME = "comment"


@dataclass
class ToolProperty:
    propertyName: str
    propertyType: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


# Define the tool properties using the ToolProperty class
tool_properties_save_snippets_object: List[ToolProperty] = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The content of the snippet."),
]

tool_properties_get_snippets_object: List[ToolProperty] = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet.")
]

tool_properties_abuseipdb_check_ip_object: List[ToolProperty] = [
    ToolProperty(
        _ABUSEIPDB_IP_PROPERTY_NAME, "string", "IPv4 or IPv6 address to check."
    ),
]

tool_properties_abuseipdb_report_ip_object: List[ToolProperty] = [
    ToolProperty(
        _ABUSEIPDB_IP_PROPERTY_NAME, "string", "IPv4 or IPv6 address to report."
    ),
    ToolProperty(
        _ABUSEIPDB_CATEGORIES_PROPERTY_NAME,
        "string",
        "Comma-separated AbuseIPDB category IDs.",
    ),
    ToolProperty(
        _ABUSEIPDB_COMMENT_PROPERTY_NAME, "string", "Description of the abuse."
    ),
]

# Convert the tool properties to JSON
tool_properties_save_snippets_json = json.dumps(
    [prop.to_dict() for prop in tool_properties_save_snippets_object]
)

# Note: the trigger context may come in different shapes; we accept Any here.
tool_properties_get_snippets_json = json.dumps(
    [prop.to_dict() for prop in tool_properties_get_snippets_object]
)

tool_properties_abuseipdb_check_ip_json = json.dumps(
    [prop.to_dict() for prop in tool_properties_abuseipdb_check_ip_object]
)

tool_properties_abuseipdb_report_ip_json = json.dumps(
    [prop.to_dict() for prop in tool_properties_abuseipdb_report_ip_object]
)


# Import specific function modules so static analysis / pack tooling can discover decorated functions
if TYPE_CHECKING:
    from functions import (
        abuseipdb,
        get_snippet,
        hello_mcp,
        save_snippet,
    )  # pragma: no cover
else:
    from functions import abuseipdb, get_snippet, hello_mcp, save_snippet  # noqa: F401

# FUNCTION `hello_mcp` moved to `src/functions/hello_mcp.py`


# FUNCTION `get_snippet` moved to `src/functions/get_snippet.py`


# FUNCTION `save_snippet` moved to `src/functions/save_snippet.py`
