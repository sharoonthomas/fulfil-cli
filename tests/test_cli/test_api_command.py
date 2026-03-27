"""Tests for the raw JSON-RPC api command."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from fulfil_cli.cli.app import app

runner = CliRunner()


class TestApiCommand:
    def test_valid_request(self, httpx_mock, cli_env, jsonrpc_success):
        httpx_mock.add_response(json=jsonrpc_success({"version": "1.0"}))

        payload = json.dumps({"method": "system.version", "params": {}})
        result = runner.invoke(app, ["api", payload])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["version"] == "1.0"

        body = json.loads(httpx_mock.get_request().content)
        assert body["method"] == "system.version"

    def test_stdin_input(self, httpx_mock, cli_env, jsonrpc_success):
        httpx_mock.add_response(json=jsonrpc_success("ok"))

        payload = json.dumps({"method": "system.version", "params": {}})
        result = runner.invoke(app, ["api", "-"], input=payload)
        assert result.exit_code == 0

    def test_invalid_json(self, cli_env):
        result = runner.invoke(app, ["api", "not-valid-json"])
        assert result.exit_code == 7

    def test_missing_method_key(self, cli_env):
        result = runner.invoke(app, ["api", '{"params": {}}'])
        assert result.exit_code == 2

    def test_fulfil_error(self, httpx_mock, cli_env, jsonrpc_error):
        httpx_mock.add_response(json=jsonrpc_error(code=-32000, message="Auth failed"))

        payload = json.dumps({"method": "system.whoami", "params": {}})
        result = runner.invoke(app, ["api", payload])
        assert result.exit_code == 4
