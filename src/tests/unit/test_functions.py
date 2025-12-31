import os
import sys
import json

# Ensure the `src` package directory is importable when tests run from `src/`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from functions.hello_mcp import hello_mcp
from functions.get_snippet import get_snippet
from functions.save_snippet import save_snippet


class FakeInputStream:
    def __init__(self, data: bytes) -> None:
        self._data: bytes = data

    def read(self) -> bytes:
        return self._data


class FakeOut:
    def __init__(self) -> None:
        self.value: str | None = None

    def set(self, val: str) -> None:
        self.value = val


def test_hello_mcp_returns_greeting() -> None:
    assert hello_mcp(None) == "Hello I am MCPTool!"


def test_get_snippet_returns_blob_content() -> None:
    fake = FakeInputStream(b'{"foo": "bar"}')
    res = get_snippet(fake, None)
    assert res == '{"foo": "bar"}'


def test_save_snippet_with_string_context_sets_blob_and_returns_success() -> None:
    fake_out = FakeOut()
    ctx = json.dumps({"arguments": {"snippetname": "name", "snippet": "content"}})
    res = save_snippet(fake_out, ctx)
    assert res == "Snippet 'content' saved successfully"
    assert fake_out.value == "content"


def test_save_snippet_with_dict_context_sets_blob_and_returns_success() -> None:
    fake_out = FakeOut()
    ctx = {"arguments": {"snippetname": "name", "snippet": "content"}}
    res = save_snippet(fake_out, ctx)
    assert res == "Snippet 'content' saved successfully"
    assert fake_out.value == "content"


def test_save_snippet_missing_name_returns_error() -> None:
    fake_out = FakeOut()
    ctx = json.dumps({"arguments": {"snippet": "content"}})
    res = save_snippet(fake_out, ctx)
    assert res == "No snippet name provided"
