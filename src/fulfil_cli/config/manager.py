"""Configuration manager using TOML files."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import tomli_w

from fulfil_cli.config.paths import config_file

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class ConfigManager:
    """Read/write configuration from TOML file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or config_file()
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            with open(self._path, "rb") as f:
                self._data = tomllib.load(f)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "wb") as f:
            tomli_w.dump(self._data, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value. Supports dotted keys like 'auth.workspace'."""
        parts = key.split(".")
        obj = self._data
        for part in parts:
            if not isinstance(obj, dict):
                return default
            obj = obj.get(part)
            if obj is None:
                return default
        return obj

    def set(self, key: str, value: Any) -> None:
        """Set a config value. Supports dotted keys."""
        parts = key.split(".")
        obj = self._data
        for part in parts[:-1]:
            if part not in obj or not isinstance(obj[part], dict):
                obj[part] = {}
            obj = obj[part]
        obj[parts[-1]] = value
        self._save()

    def delete(self, key: str) -> bool:
        """Delete a config value. Returns True if it existed."""
        parts = key.split(".")
        obj = self._data
        for part in parts[:-1]:
            if not isinstance(obj, dict) or part not in obj:
                return False
            obj = obj[part]
        if isinstance(obj, dict) and parts[-1] in obj:
            del obj[parts[-1]]
            self._save()
            return True
        return False

    def all(self) -> dict[str, Any]:
        """Return all config data."""
        return dict(self._data)

    # --- Workspace management ---

    @property
    def workspace(self) -> str | None:
        """Get the active workspace domain."""
        return self.get("workspace")

    @workspace.setter
    def workspace(self, value: str | None) -> None:
        if value is None:
            self.delete("workspace")
        else:
            self.set("workspace", value)

    @property
    def workspaces(self) -> list[str]:
        """Get all known workspace domains."""
        return self.get("workspaces", [])

    def add_workspace(self, workspace: str) -> None:
        """Add a workspace to the known list (if not already present)."""
        ws_list = self.workspaces
        if workspace not in ws_list:
            ws_list.append(workspace)
            self.set("workspaces", ws_list)

    def remove_workspace(self, workspace: str) -> None:
        """Remove a workspace from the known list."""
        ws_list = self.workspaces
        if workspace in ws_list:
            ws_list.remove(workspace)
            self.set("workspaces", ws_list)

    def clear_workspaces(self) -> None:
        """Remove all workspaces and clear the active workspace."""
        self.set("workspaces", [])
        self.delete("workspace")
