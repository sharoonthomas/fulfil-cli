"""Tests for CLI app commands."""

from __future__ import annotations

from typer.testing import CliRunner

from fulfil_cli.cli.app import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "fulfil-cli" in result.output


def test_version_json():
    result = runner.invoke(app, ["version", "--json"])
    assert result.exit_code == 0
    assert '"version"' in result.output


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "fulfil" in result.output.lower()


def test_auth_help():
    result = runner.invoke(app, ["auth", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output


def test_config_help():
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "set" in result.output


def test_dynamic_model_subcommand_help():
    """Unknown subcommands should resolve as model names."""
    result = runner.invoke(app, ["sales_order", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "get" in result.output
    assert "create" in result.output
