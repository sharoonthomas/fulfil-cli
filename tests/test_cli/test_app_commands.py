"""Tests for top-level app commands: whoami, models, reports."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from fulfil_cli.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset global state before each test."""
    from fulfil_cli.cli import state

    state.set_globals()
    yield
    state.set_globals()


class TestWhoami:
    def test_happy_path(self, httpx_mock, cli_env, jsonrpc_success):
        whoami_data = {"user": "admin@test.com", "workspace": "test.fulfil.io"}
        httpx_mock.add_response(json=jsonrpc_success(whoami_data))

        result = runner.invoke(app, ["whoami", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["user"] == "admin@test.com"

        body = json.loads(httpx_mock.get_request().content)
        assert body["method"] == "system.whoami"

    def test_auth_error(self, httpx_mock, cli_env):
        httpx_mock.add_response(status_code=401, json={"error": "unauthorized"})

        result = runner.invoke(app, ["whoami", "--json"])
        assert result.exit_code == 4


class TestModels:
    def test_list_models(self, httpx_mock, cli_env, jsonrpc_success):
        models = [
            {
                "model_name": "sale_order",
                "description": "Sale Order",
                "category": "Sales",
                "access": {"read": True, "create": True, "update": True, "delete": False},
            },
        ]
        httpx_mock.add_response(json=jsonrpc_success(models))

        result = runner.invoke(app, ["models", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert data[0]["model_name"] == "sale_order"

        body = json.loads(httpx_mock.get_request().content)
        assert body["method"] == "system.list_models"

    def test_list_models_with_search(self, httpx_mock, cli_env, jsonrpc_success):
        models = [
            {
                "model_name": "sale_order",
                "description": "Sale Order",
                "category": "Sales",
                "access": {},
            },
            {
                "model_name": "product",
                "description": "Product",
                "category": "Products",
                "access": {},
            },
        ]
        httpx_mock.add_response(json=jsonrpc_success(models))

        result = runner.invoke(app, ["models", "--search", "sale", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["model_name"] == "sale_order"

    def test_models_list_subcommand(self, httpx_mock, cli_env, jsonrpc_success):
        httpx_mock.add_response(json=jsonrpc_success([]))

        result = runner.invoke(app, ["models", "list", "--json"])
        assert result.exit_code == 0


class TestReports:
    def test_list_reports(self, httpx_mock, cli_env, jsonrpc_success):
        reports = [{"name": "sales_report", "description": "Sales Report"}]
        httpx_mock.add_response(json=jsonrpc_success(reports))

        result = runner.invoke(app, ["reports", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data[0]["name"] == "sales_report"

        body = json.loads(httpx_mock.get_request().content)
        assert body["method"] == "system.list_reports"

    def test_reports_list_subcommand(self, httpx_mock, cli_env, jsonrpc_success):
        httpx_mock.add_response(json=jsonrpc_success([]))

        result = runner.invoke(app, ["reports", "list", "--json"])
        assert result.exit_code == 0
