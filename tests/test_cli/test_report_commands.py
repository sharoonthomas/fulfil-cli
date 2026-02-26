"""Tests for report subcommands: execute and describe."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from fulfil_cli.cli.app import app
from fulfil_cli.cli.commands.report import _extract_properties

runner = CliRunner()


@pytest.fixture(autouse=True)
def _reset_state():
    from fulfil_cli.cli import state

    state.set_globals()
    yield
    state.set_globals()


class TestExtractProperties:
    def test_direct_schema(self):
        data = {"properties": {"date": {"type": "string"}}}
        assert _extract_properties(data) == {"date": {"type": "string"}}

    def test_wrapped_schema(self):
        data = {"params_schema": {"properties": {"date": {"type": "string"}}}}
        assert _extract_properties(data) == {"date": {"type": "string"}}

    def test_not_a_dict(self):
        assert _extract_properties("garbage") == {}

    def test_empty_dict(self):
        assert _extract_properties({}) == {}

    def test_params_schema_not_dict(self):
        assert _extract_properties({"params_schema": "bad"}) == {}


class TestReportExecute:
    def test_execute_with_params(self, httpx_mock, cli_env, jsonrpc_success):
        report_data = {"columns": [{"name": "total"}], "data": [{"total": 100}]}
        httpx_mock.add_response(json=jsonrpc_success(report_data))

        result = runner.invoke(
            app,
            ["reports", "sales_report", "execute", "--params", '{"year": 2024}', "--json"],
        )
        assert result.exit_code == 0

        body = json.loads(httpx_mock.get_request().content)
        assert body["method"] == "report.sales_report.execute"
        assert body["params"]["year"] == 2024

    def test_execute_no_params(self, httpx_mock, cli_env, jsonrpc_success):
        httpx_mock.add_response(json=jsonrpc_success({"columns": [], "data": []}))

        result = runner.invoke(
            app, ["reports", "sales_report", "execute", "--json"]
        )
        assert result.exit_code == 0

    def test_execute_invalid_json(self, cli_env):
        result = runner.invoke(
            app, ["reports", "sales_report", "execute", "--params", "bad"]
        )
        assert result.exit_code == 7

    def test_execute_server_error(self, httpx_mock, cli_env, jsonrpc_error):
        httpx_mock.add_response(json=jsonrpc_error(code=-32603, message="Report failed"))

        result = runner.invoke(
            app, ["reports", "sales_report", "execute", "--json"]
        )
        assert result.exit_code == 9

    def test_default_action_is_execute(self, httpx_mock, cli_env, jsonrpc_success):
        """Invoking a report group without subcommand defaults to execute."""
        httpx_mock.add_response(json=jsonrpc_success({"columns": [], "data": []}))

        result = runner.invoke(
            app, ["reports", "sales_report", "--params", '{"year": 2024}', "--json"]
        )
        assert result.exit_code == 0

        body = json.loads(httpx_mock.get_request().content)
        assert body["method"] == "report.sales_report.execute"


class TestReportDescribe:
    def test_describe(self, httpx_mock, cli_env, jsonrpc_success):
        schema = {
            "report_name": "sales_report",
            "params_schema": {
                "properties": {"year": {"type": "integer", "title": "Year"}},
            },
        }
        httpx_mock.add_response(json=jsonrpc_success(schema))

        result = runner.invoke(
            app, ["reports", "sales_report", "describe", "--json"]
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["report_name"] == "sales_report"

        body = json.loads(httpx_mock.get_request().content)
        assert body["method"] == "report.sales_report.describe"
