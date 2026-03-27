"""Raw JSON-RPC call command."""

from __future__ import annotations

import json
import sys

import typer
from rich.console import Console

from fulfil_cli.cli.commands.common import handle_error
from fulfil_cli.cli.state import AppContext
from fulfil_cli.client.errors import EXIT_USAGE, EXIT_VALIDATION, FulfilError
from fulfil_cli.output.formatter import output

console = Console(stderr=True)


def api_cmd(
    ctx: typer.Context,
    output_format: str | None = typer.Option(
        None, "--format", help="Output format: table, json, csv, ndjson"
    ),
    payload: str = typer.Argument(
        ...,
        help=(
            "JSON-RPC request body (or '-' to read from stdin). "
            'Must contain a "method" key and optional "params" object. '
            """Example: '{"method": "system.version", "params": {}}'"""
        ),
    ),
) -> None:
    """Send a raw JSON-RPC request to the Fulfil API.

    \b
    Examples:
      fulfil api '{"method": "system.version", "params": {}}'
      fulfil api '{"method": "model.sale_order.find", "params": {"where": {"state": "confirmed"}}}'
      echo '{"method": "system.version", "params": {}}' | fulfil api -
    """
    app_ctx: AppContext = ctx.obj

    if payload == "-":
        payload = sys.stdin.read()

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON: {exc}[/red]")
        raise typer.Exit(code=EXIT_VALIDATION) from None

    if "method" not in data:
        console.print("[red]JSON must contain a 'method' key.[/red]")
        raise typer.Exit(code=EXIT_USAGE)

    method = data["method"]
    params = data.get("params", {})

    try:
        client = app_ctx.get_client()
        result = client.call(method, **params)
    except FulfilError as exc:
        handle_error(exc)

    output(result, fmt=app_ctx.get_effective_format(output_format))
