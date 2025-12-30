import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import azure.functions as func

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


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="hello_mcp",
    description="Hello world.",
    toolProperties="[]",
)
def hello_mcp(context: Any) -> str:
    """A simple function that returns a greeting message.

    Args:
        context: The trigger context (not used in this function).

    Returns:
        str: A greeting message.
    """
    return "Hello I am MCPTool!"


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_snippet",
    description="Retrieve a snippet by name.",
    toolProperties=tool_properties_get_snippets_json,
)
@app.generic_input_binding(
    arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH
)
def get_snippet(file: func.InputStream, context: Any) -> str:
    """Retrieves a snippet by name from Azure Blob Storage.

    Args:
        file (func.InputStream): The input binding to read the snippet from Azure Blob Storage.
        context: The trigger context containing the input arguments.

    Returns:
        str: The content of the snippet or an error message.
    """
    snippet_content = file.read().decode("utf-8")
    logging.info(f"Retrieved snippet: {snippet_content}")
    return snippet_content


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="save_snippet",
    description="Save a snippet with a name.",
    toolProperties=tool_properties_save_snippets_json,
)
@app.generic_output_binding(
    arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH
)
def save_snippet(file: func.Out[str], context: Any) -> str:
    """Save snippet content into blob storage using the provided arguments in `context`.

    Args:
        file: Output blob binding.
        context: Trigger context (expected to be a JSON string or dict with an "arguments" mapping).

    Returns:
        A success or error message string.
    """
    if isinstance(context, str):
        try:
            content = json.loads(context)
        except json.JSONDecodeError:
            logging.exception("Failed to decode context as JSON")
            return "Invalid request payload"
    elif isinstance(context, dict):
        content = context
    else:
        return "Invalid request payload"

    arguments = content.get("arguments")
    if not isinstance(arguments, dict):
        return "Invalid arguments"

    snippet_name_from_args = arguments.get(_SNIPPET_NAME_PROPERTY_NAME)
    snippet_content_from_args = arguments.get(_SNIPPET_PROPERTY_NAME)

    if not snippet_name_from_args:
        return "No snippet name provided"

    if not snippet_content_from_args:
        return "No snippet content provided"

    file.set(snippet_content_from_args)
    logging.info(f"Saved snippet: {snippet_content_from_args}")
    return f"Snippet '{snippet_content_from_args}' saved successfully"
