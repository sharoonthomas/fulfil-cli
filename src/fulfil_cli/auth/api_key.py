"""Credential resolution — flag > env > keyring, with workspace normalization."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from fulfil_cli.auth.keyring_store import get_api_key, get_oauth_tokens, store_oauth_tokens
from fulfil_cli.auth.oauth import OAuthTokens, discover_oidc, refresh_access_token
from fulfil_cli.client.errors import AuthError


@dataclass
class Credentials:
    """Resolved authentication credentials."""

    method: Literal["api_key", "oauth"]
    api_key: str | None = None
    access_token: str | None = None
    workspace: str | None = None


def resolve_credentials(
    *,
    token_flag: str | None = None,
    workspace: str | None = None,
    auth_method: str = "api_key",
) -> Credentials:
    """Resolve credentials, supporting both API key and OAuth.

    Priority: --token flag > FULFIL_API_KEY env > check auth method > keyring.
    """
    if token_flag:
        return Credentials(method="api_key", api_key=token_flag)

    env_key = os.environ.get("FULFIL_API_KEY")
    if env_key:
        return Credentials(method="api_key", api_key=env_key)

    if auth_method == "oauth" and workspace:
        tokens_json = get_oauth_tokens(workspace)
        if tokens_json:
            tokens = OAuthTokens.from_json(tokens_json)
            if tokens.is_expired and tokens.refresh_token:
                oidc = discover_oidc(workspace)
                tokens = refresh_access_token(oidc["token_endpoint"], tokens.refresh_token)
                store_oauth_tokens(workspace, tokens.to_json().decode())
            return Credentials(
                method="oauth",
                access_token=tokens.access_token,
                workspace=workspace,
            )

    if workspace:
        stored = get_api_key(workspace)
        if stored:
            return Credentials(method="api_key", api_key=stored)

    raise AuthError(
        message="No credentials found",
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
        return normalize_workspace(workspace_flag)

    env_workspace = os.environ.get("FULFIL_WORKSPACE")
    if env_workspace:
        return normalize_workspace(env_workspace)

    if config_workspace:
        return config_workspace

    raise AuthError(
        message="No workspace configured",
        hint="Run 'fulfil auth login' or set FULFIL_WORKSPACE environment variable.",
    )


def normalize_workspace(value: str) -> str:
    """Normalize workspace input — accept slug or full domain.

    'acme' → 'acme.fulfil.io'
    'acme.fulfil.io' → 'acme.fulfil.io'
    'acme.fulfil.app' → 'acme.fulfil.app'
    """
    if "." in value:
        return value
    return f"{value}.fulfil.io"
