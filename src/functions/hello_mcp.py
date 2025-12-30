# Auto-generated from function_app.py: function `hello_mcp`
# NOTE: move any function-specific imports here if necessary
from typing import Any, TYPE_CHECKING

# For decorated trigger parameter typing, annotate context as a dict or str to satisfy worker validation
ContextType = dict | str

if TYPE_CHECKING:
    # For type checkers, import the symbols from the top-level module
    from function_app import app
else:
    try:
        from .function_app import app
    except Exception:
        from function_app import app


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="hello_mcp",
    description="Hello world.",
    toolProperties="[]",
)
def hello_mcp(context: ContextType) -> str:
    """A simple function that returns a greeting message.

    Args:
        context: The trigger context (not used in this function).

    Returns:
        str: A greeting message.
    """
    return "Hello I am MCPTool!"
