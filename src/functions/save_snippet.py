# Auto-generated from function_app.py: function `save_snippet`
# NOTE: move any function-specific imports here if necessary
from typing import TYPE_CHECKING
import json
import logging
import azure.functions as func

# Context arrives as a JSON string; annotate as str for worker compatibility
ContextType = str

if TYPE_CHECKING:
    from function_app import (
        app,
        _BLOB_PATH,
        tool_properties_save_snippets_json,
        _SNIPPET_NAME_PROPERTY_NAME,
        _SNIPPET_PROPERTY_NAME,
    )
else:
    try:
        from .function_app import (
            app,
            _BLOB_PATH,
            tool_properties_save_snippets_json,
            _SNIPPET_NAME_PROPERTY_NAME,
            _SNIPPET_PROPERTY_NAME,
        )
    except Exception:
        from function_app import (
            app,
            _BLOB_PATH,
            tool_properties_save_snippets_json,
            _SNIPPET_NAME_PROPERTY_NAME,
            _SNIPPET_PROPERTY_NAME,
        )


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
def save_snippet(file: func.Out[str], context: ContextType) -> str:
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
