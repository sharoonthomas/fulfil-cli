"""Keyring-based storage for API keys."""

from __future__ import annotations

import contextlib

import keyring

SERVICE_NAME = "fulfil-cli"


def store_api_key(workspace: str, api_key: str) -> None:
    """Store an API key in the system keyring."""
    keyring.set_password(SERVICE_NAME, workspace, api_key)


def get_api_key(workspace: str) -> str | None:
    """Retrieve an API key from the system keyring."""
    return keyring.get_password(SERVICE_NAME, workspace)


def delete_api_key(workspace: str) -> None:
    """Delete an API key from the system keyring."""
    with contextlib.suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SERVICE_NAME, workspace)
