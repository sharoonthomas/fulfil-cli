"""Tests for the CLI state module."""

from __future__ import annotations

import pytest

from fulfil_cli.cli.state import AppContext
from fulfil_cli.client.errors import AuthError


class TestGetClient:
    def test_with_env_vars(self, monkeypatch):
        monkeypatch.setenv("FULFIL_API_KEY", "sk_test")
        monkeypatch.setenv("FULFIL_WORKSPACE", "acme.fulfil.io")

        ctx = AppContext()
        client = ctx.get_client()
        assert client.workspace == "acme.fulfil.io"
        assert client.url == "https://acme.fulfil.io/api/v3/jsonrpc"
        client.close()

    def test_with_token_flag(self, monkeypatch):
        monkeypatch.setenv("FULFIL_WORKSPACE", "acme.fulfil.io")

        ctx = AppContext(token="sk_flag_token")
        client = ctx.get_client()
        assert client.workspace == "acme.fulfil.io"
        client.close()

    def test_client_cached(self, monkeypatch):
        monkeypatch.setenv("FULFIL_API_KEY", "sk_test")
        monkeypatch.setenv("FULFIL_WORKSPACE", "acme.fulfil.io")

        ctx = AppContext()
        client1 = ctx.get_client()
        client2 = ctx.get_client()
        assert client1 is client2
        client1.close()

    def test_missing_workspace(self, monkeypatch):
        monkeypatch.setenv("FULFIL_API_KEY", "sk_test")
        monkeypatch.delenv("FULFIL_WORKSPACE", raising=False)
        monkeypatch.setattr(
            "fulfil_cli.config.manager.ConfigManager.workspace",
            property(lambda self: None),
        )

        ctx = AppContext()
        with pytest.raises(AuthError, match="No workspace"):
            ctx.get_client()

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.setenv("FULFIL_WORKSPACE", "acme.fulfil.io")
        monkeypatch.delenv("FULFIL_API_KEY", raising=False)

        ctx = AppContext()
        with pytest.raises(AuthError, match="No credentials found"):
            ctx.get_client()

    def test_debug_passed_to_client(self, monkeypatch):
        monkeypatch.setenv("FULFIL_API_KEY", "sk_test")
        monkeypatch.setenv("FULFIL_WORKSPACE", "acme.fulfil.io")

        ctx = AppContext(debug=True)
        client = ctx.get_client()
        assert client._debug is True
        client.close()
