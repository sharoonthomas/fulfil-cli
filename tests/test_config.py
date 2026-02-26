"""Tests for config manager."""

from __future__ import annotations

from pathlib import Path

from fulfil_cli.config.manager import ConfigManager


def test_set_and_get(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    config.set("foo", "bar")
    assert config.get("foo") == "bar"


def test_dotted_keys(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    config.set("auth.workspace", "acme.fulfil.io")
    assert config.get("auth.workspace") == "acme.fulfil.io"


def test_delete(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    config.set("key", "value")
    assert config.delete("key") is True
    assert config.get("key") is None


def test_delete_nonexistent(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    assert config.delete("nonexistent") is False


def test_get_default(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    assert config.get("missing", "default") == "default"


def test_workspace_property(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    config.workspace = "acme.fulfil.io"
    assert config.workspace == "acme.fulfil.io"


def test_workspace_list(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    assert config.workspaces == []

    config.add_workspace("acme.fulfil.io")
    config.add_workspace("beta.fulfil.app")
    assert config.workspaces == ["acme.fulfil.io", "beta.fulfil.app"]

    # No duplicates
    config.add_workspace("acme.fulfil.io")
    assert config.workspaces == ["acme.fulfil.io", "beta.fulfil.app"]

    config.remove_workspace("acme.fulfil.io")
    assert config.workspaces == ["beta.fulfil.app"]


def test_clear_workspaces(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    config.add_workspace("acme.fulfil.io")
    config.workspace = "acme.fulfil.io"
    config.clear_workspaces()
    assert config.workspaces == []
    assert config.workspace is None


def test_persistence(tmp_path: Path):
    path = tmp_path / "config.toml"
    config1 = ConfigManager(path)
    config1.set("key", "value")

    # Reload from same file
    config2 = ConfigManager(path)
    assert config2.get("key") == "value"


def test_all(tmp_path: Path):
    config = ConfigManager(tmp_path / "config.toml")
    config.set("a", "1")
    config.set("b", "2")
    data = config.all()
    assert data == {"a": "1", "b": "2"}
