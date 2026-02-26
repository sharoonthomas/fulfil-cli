"""XDG-compliant paths for config and data storage."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "fulfil"
APP_AUTHOR = "fulfil"


def config_dir() -> Path:
    """Return the config directory (~/.config/fulfil on Linux/macOS)."""
    path = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    """Return the data directory (~/.local/share/fulfil on Linux/macOS)."""
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_file() -> Path:
    """Return path to the main config TOML file."""
    return config_dir() / "config.toml"
