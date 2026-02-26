"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def tmp_config(tmp_path: Path):
    """Provide a temporary config file path."""
    return tmp_path / "config.toml"


@pytest.fixture
def jsonrpc_success():
    """Factory for JSON-RPC success responses."""

    def _make(result: Any, request_id: int = 1) -> dict:
        return {"jsonrpc": "2.0", "result": result, "id": request_id}

    return _make


@pytest.fixture
def jsonrpc_error():
    """Factory for JSON-RPC error responses."""

    def _make(
        code: int = -32603,
        message: str = "Internal error",
        data: dict | None = None,
        request_id: int = 1,
    ) -> dict:
        error: dict[str, Any] = {"code": code, "message": message}
        if data:
            error["data"] = data
        return {"jsonrpc": "2.0", "error": error, "id": request_id}

    return _make
