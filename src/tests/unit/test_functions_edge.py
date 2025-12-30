import os
import sys
import json

# Ensure the `src` package directory is importable when tests run from `src/`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

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


def test_save_snippet_invalid_json_returns_error() -> None:
    fake_out = FakeOut()
    res = save_snippet(fake_out, "not json")
    assert res == "Invalid request payload"


def test_save_snippet_arguments_not_dict_returns_error() -> None:
    fake_out = FakeOut()
    ctx = json.dumps({"arguments": "not a dict"})
    res = save_snippet(fake_out, ctx)
    assert res == "Invalid arguments"


def test_save_snippet_missing_content_returns_error() -> None:
    fake_out = FakeOut()
    ctx = json.dumps({"arguments": {"snippetname": "name", "snippet": ""}})
    res = save_snippet(fake_out, ctx)
    assert res == "No snippet content provided"


def test_save_snippet_invalid_context_type_returns_error() -> None:
    fake_out = FakeOut()
    res = save_snippet(fake_out, 12345)
    assert res == "Invalid request payload"


def test_get_snippet_invalid_utf8_raises_unicode_error() -> None:
    fake = FakeInputStream(b"\xff")
    import pytest

    with pytest.raises(UnicodeDecodeError):
        get_snippet(fake, None)
