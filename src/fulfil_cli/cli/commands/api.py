"""Raw JSON-RPC call command."""

from __future__ import annotations

import json
import sys

import typer
from rich.console import Console

from fulfil_cli.cli.state import AppContext
from fulfil_cli.client.errors import FulfilError
from fulfil_cli.output.formatter import output
from fulfil_cli.output.json_output import print_json

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
        raise typer.Exit(code=7) from None

    # Extract method and params from JSON-RPC envelope or shorthand
    if "method" in data:
        method = data["method"]
        params = data.get("params", {})
    else:
        console.print("[red]JSON must contain a 'method' key.[/red]")
        raise typer.Exit(code=2)

    try:
        client = app_ctx.get_client()
        result = client.call(method, **params)
    except FulfilError as exc:
        fmt = app_ctx.get_effective_format(output_format)
        if fmt != "table":
            print_json(exc.to_dict(), file=sys.stderr)
        else:
            console.print(f"[red]Error: {exc}[/red]")
            if exc.hint:
                console.print(f"[dim]Hint: {exc.hint}[/dim]")
        raise typer.Exit(code=exc.exit_code) from None

    output(result, fmt=app_ctx.get_effective_format(output_format))
