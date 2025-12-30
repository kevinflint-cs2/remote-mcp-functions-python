# Auto-generated from function_app.py: function `get_snippet`
# NOTE: move any function-specific imports here if necessary
from typing import Any, TYPE_CHECKING

# Context can be a JSON string or a dict
ContextType = dict | str
import logging
import azure.functions as func

if TYPE_CHECKING:
    from function_app import app, _BLOB_PATH, tool_properties_get_snippets_json
else:
    try:
        from .function_app import app, _BLOB_PATH, tool_properties_get_snippets_json
    except Exception:
        from function_app import app, _BLOB_PATH, tool_properties_get_snippets_json


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
def get_snippet(file: func.InputStream, context: ContextType) -> str:
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
