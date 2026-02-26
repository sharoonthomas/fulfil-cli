"""API key resolution — env > flag > keyring."""

from __future__ import annotations

import os

from fulfil_cli.auth.keyring_store import get_api_key
from fulfil_cli.client.errors import AuthError


def resolve_api_key(
    *,
    token_flag: str | None = None,
    workspace: str | None = None,
) -> str:
    """Resolve API key from: --token flag > FULFIL_API_KEY env > keyring.

    Raises AuthError if no key can be found.
    """
    # 1. Explicit --token flag
    if token_flag:
        return token_flag

    # 2. Environment variable
    env_key = os.environ.get("FULFIL_API_KEY")
    if env_key:
        return env_key

    # 3. Keyring (requires workspace)
    if workspace:
        stored = get_api_key(workspace)
        if stored:
            return stored

    raise AuthError(
        message="No API key found",
        hint="Run 'fulfil auth login' or set FULFIL_API_KEY environment variable.",
    )


def resolve_workspace(
    *,
    workspace_flag: str | None = None,
    config_workspace: str | None = None,
) -> str:
    """Resolve workspace from: --workspace flag > FULFIL_WORKSPACE env > config.

    The workspace is the full domain (e.g. 'acme.fulfil.io').
    Raises AuthError if no workspace can be found.
    """
    if workspace_flag:
        return _normalize_workspace(workspace_flag)

    env_workspace = os.environ.get("FULFIL_WORKSPACE")
    if env_workspace:
        return _normalize_workspace(env_workspace)

    if config_workspace:
        return config_workspace

    raise AuthError(
        message="No workspace configured",
        hint="Run 'fulfil auth login' or set FULFIL_WORKSPACE environment variable.",
    )


def _normalize_workspace(value: str) -> str:
    """Normalize workspace input — accept slug or full domain.

    'acme' → 'acme.fulfil.io'
    'acme.fulfil.io' → 'acme.fulfil.io'
    'acme.fulfil.app' → 'acme.fulfil.app'
    """
    if "." in value:
        return value
    return f"{value}.fulfil.io"
