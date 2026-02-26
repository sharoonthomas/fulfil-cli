"""Global CLI state — resolves client from config/env/flags."""

from __future__ import annotations

from fulfil_cli.auth.api_key import resolve_api_key, resolve_workspace
from fulfil_cli.client.http import FulfilClient
from fulfil_cli.config.manager import ConfigManager

# Module-level state set by the root callback
_token: str | None = None
_workspace_flag: str | None = None
_base_url: str | None = None
_debug: bool = False
_quiet: bool = False

# Cached client
_client: FulfilClient | None = None


def set_globals(
    *,
    token: str | None = None,
    workspace: str | None = None,
    base_url: str | None = None,
    debug: bool = False,
    quiet: bool = False,
) -> None:
    """Set global state from root CLI callback."""
    global _token, _workspace_flag, _base_url, _debug, _quiet, _client
    _token = token
    _workspace_flag = workspace
    _base_url = base_url
    _debug = debug
    _quiet = quiet
    _client = None  # Reset cached client


def is_debug() -> bool:
    """Return whether debug mode is enabled."""
    return _debug


def is_quiet() -> bool:
    """Return whether quiet mode is enabled."""
    return _quiet


def get_client() -> FulfilClient:
    """Get or create the FulfilClient from resolved credentials."""
    global _client
    if _client is not None:
        return _client

    config = ConfigManager()
    workspace = resolve_workspace(
        workspace_flag=_workspace_flag,
        config_workspace=config.workspace,
    )
    api_key = resolve_api_key(token_flag=_token, workspace=workspace)
    _client = FulfilClient(workspace=workspace, api_key=api_key, base_url=_base_url)
    return _client
