"""Tests for config subcommands: set, get, list."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from fulfil_cli.cli.app import app
from fulfil_cli.cli.commands.config import _flatten
from fulfil_cli.config.manager import ConfigManager

runner = CliRunner()


@pytest.fixture
def tmp_config(tmp_path):
    return ConfigManager(tmp_path / "config.toml")


def _patch_config(tmp_config):
    return patch(
        "fulfil_cli.cli.commands.config.ConfigManager",
        return_value=tmp_config,
    )


class TestFlatten:
    def test_flat(self):
        assert _flatten({"a": "1", "b": "2"}) == [("a", "1"), ("b", "2")]

    def test_nested(self):
        assert _flatten({"auth": {"workspace": "acme"}}) == [("auth.workspace", "acme")]


class TestConfigSet:
    def test_set(self, tmp_config):
        with _patch_config(tmp_config):
            result = runner.invoke(app, ["config", "set", "foo", "bar"])
        assert result.exit_code == 0
        assert tmp_config.get("foo") == "bar"


class TestConfigGet:
    def test_get_existing(self, tmp_config):
        tmp_config.set("foo", "bar")
        with _patch_config(tmp_config):
            result = runner.invoke(app, ["config", "get", "foo"])
        assert result.exit_code == 0
        assert "bar" in result.stdout

    def test_get_missing(self, tmp_config):
        with _patch_config(tmp_config):
            result = runner.invoke(app, ["config", "get", "missing"])
        assert result.exit_code == 1

    def test_get_json(self, tmp_config):
        tmp_config.set("foo", "bar")
        with _patch_config(tmp_config):
            result = runner.invoke(app, ["config", "get", "foo", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == {"foo": "bar"}


class TestConfigList:
    def test_list_empty(self, tmp_config):
        with _patch_config(tmp_config):
            result = runner.invoke(app, ["config", "list"])
        assert result.exit_code == 0
        assert "No configuration" in result.stdout

    def test_list_with_data(self, tmp_config):
        tmp_config.set("foo", "bar")
        tmp_config.set("baz", "qux")
        with _patch_config(tmp_config):
            result = runner.invoke(app, ["config", "list"])
        assert result.exit_code == 0
        assert "foo = bar" in result.stdout
        assert "baz = qux" in result.stdout

    def test_list_json(self, tmp_config):
        tmp_config.set("foo", "bar")
        with _patch_config(tmp_config):
            result = runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["foo"] == "bar"
