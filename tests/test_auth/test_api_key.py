"""Tests for API key and workspace resolution."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from fulfil_cli.auth.api_key import _normalize_workspace, resolve_api_key, resolve_workspace
from fulfil_cli.client.errors import AuthError


class TestResolveApiKey:
    def test_flag_takes_priority(self, monkeypatch):
        monkeypatch.setenv("FULFIL_API_KEY", "env_key")
        result = resolve_api_key(token_flag="flag_key", workspace="acme.fulfil.io")
        assert result == "flag_key"

    def test_env_var(self, monkeypatch):
        monkeypatch.setenv("FULFIL_API_KEY", "env_key")
        result = resolve_api_key(workspace="acme.fulfil.io")
        assert result == "env_key"

    def test_keyring_fallback(self, monkeypatch):
        monkeypatch.delenv("FULFIL_API_KEY", raising=False)
        with patch("fulfil_cli.auth.api_key.get_api_key", return_value="kr_key"):
            result = resolve_api_key(workspace="acme.fulfil.io")
        assert result == "kr_key"

    def test_keyring_returns_none_raises(self, monkeypatch):
        monkeypatch.delenv("FULFIL_API_KEY", raising=False)
        with patch("fulfil_cli.auth.api_key.get_api_key", return_value=None):
            with pytest.raises(AuthError, match="No API key"):
                resolve_api_key(workspace="acme.fulfil.io")

    def test_no_workspace_no_keyring(self, monkeypatch):
        monkeypatch.delenv("FULFIL_API_KEY", raising=False)
        with pytest.raises(AuthError, match="No API key"):
            resolve_api_key(workspace=None)

    def test_env_takes_priority_over_keyring(self, monkeypatch):
        monkeypatch.setenv("FULFIL_API_KEY", "env_key")
        with patch("fulfil_cli.auth.api_key.get_api_key", return_value="kr_key"):
            result = resolve_api_key(workspace="acme.fulfil.io")
        assert result == "env_key"


class TestResolveWorkspace:
    def test_flag_takes_priority(self, monkeypatch):
        monkeypatch.setenv("FULFIL_WORKSPACE", "env_ws.fulfil.io")
        result = resolve_workspace(
            workspace_flag="flag_ws", config_workspace="cfg.fulfil.io"
        )
        assert result == "flag_ws.fulfil.io"

    def test_env_var(self, monkeypatch):
        monkeypatch.setenv("FULFIL_WORKSPACE", "env_ws.fulfil.io")
        result = resolve_workspace(config_workspace="cfg.fulfil.io")
        assert result == "env_ws.fulfil.io"

    def test_config_fallback(self, monkeypatch):
        monkeypatch.delenv("FULFIL_WORKSPACE", raising=False)
        result = resolve_workspace(config_workspace="cfg.fulfil.io")
        assert result == "cfg.fulfil.io"

    def test_nothing_configured_raises(self, monkeypatch):
        monkeypatch.delenv("FULFIL_WORKSPACE", raising=False)
        with pytest.raises(AuthError, match="No workspace"):
            resolve_workspace()

    def test_slug_normalized(self, monkeypatch):
        monkeypatch.delenv("FULFIL_WORKSPACE", raising=False)
        result = resolve_workspace(workspace_flag="acme")
        assert result == "acme.fulfil.io"


class TestNormalizeWorkspace:
    def test_slug(self):
        assert _normalize_workspace("acme") == "acme.fulfil.io"

    def test_full_domain_fulfil_io(self):
        assert _normalize_workspace("acme.fulfil.io") == "acme.fulfil.io"

    def test_full_domain_fulfil_app(self):
        assert _normalize_workspace("acme.fulfil.app") == "acme.fulfil.app"
