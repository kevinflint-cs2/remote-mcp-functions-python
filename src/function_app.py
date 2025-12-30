import json
from dataclasses import dataclass
from typing import Dict, List

import azure.functions as func

# Use importlib and helper names to dynamically import the functions package in a way that
# is robust at runtime and acceptable to static checkers (imports kept at module top).
import importlib

_pkg = __package__ or ""
_try_names = [f"{_pkg}.functions"] if _pkg else []
_try_names.append("functions")

_functions = None
for _name in _try_names:
    try:
        _functions = importlib.import_module(_name)
        break
    except Exception:
        _functions = None

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Constants for the Azure Blob Storage container, file, and blob path
_SNIPPET_NAME_PROPERTY_NAME = "snippetname"
_SNIPPET_PROPERTY_NAME = "snippet"
_BLOB_PATH = "snippets/{mcptoolargs." + _SNIPPET_NAME_PROPERTY_NAME + "}.json"


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

# Convert the tool properties to JSON
tool_properties_save_snippets_json = json.dumps(
    [prop.to_dict() for prop in tool_properties_save_snippets_object]
)

# Note: the trigger context may come in different shapes; we accept Any here.
tool_properties_get_snippets_json = json.dumps(
    [prop.to_dict() for prop in tool_properties_get_snippets_object]
)


# Functions package is dynamically imported at module top to register decorated handlers

# FUNCTION `hello_mcp` moved to `src/functions/hello_mcp.py`


# FUNCTION `get_snippet` moved to `src/functions/get_snippet.py`


# FUNCTION `save_snippet` moved to `src/functions/save_snippet.py`
