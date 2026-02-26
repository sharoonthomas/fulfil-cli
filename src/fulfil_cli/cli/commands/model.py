"""Dynamic model subcommand actions: list/get/create/update/delete/count/call/fields."""

from __future__ import annotations

import difflib
import json
import sys
from typing import Any

import click
from rich.console import Console

from fulfil_cli.cli.state import get_client, is_quiet
from fulfil_cli.client.errors import FulfilError, ValidationError
from fulfil_cli.output.formatter import output, output_model_describe, should_use_json

console = Console(stderr=True)


def _parse_json_arg(value: str, arg_name: str) -> Any:
    """Parse a JSON string argument."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for {arg_name}: {exc}[/red]")
        sys.exit(7)


def _parse_fields(value: str | None) -> list[str] | None:
    """Parse comma-separated field names."""
    if not value:
        return None
    return [f.strip() for f in value.split(",") if f.strip()]


def _parse_ids(value: str) -> list[int]:
    """Parse comma-separated IDs."""
    try:
        return [int(x.strip()) for x in value.split(",")]
    except ValueError:
        console.print("[red]IDs must be comma-separated integers.[/red]")
        sys.exit(2)


def _parse_order(value: str) -> dict[str, str]:
    """Parse order string like 'sale_date:desc,name:asc' into {"sale_date": "DESC", "name": "ASC"}.

    Each pair is field:direction where direction defaults to ASC if omitted.
    """
    result: dict[str, str] = {}
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            field, direction = part.split(":", 1)
            result[field.strip()] = direction.strip().upper()
        else:
            result[part] = "ASC"
    return result


def _handle_error(exc: FulfilError, *, model: str | None = None) -> None:
    """Print error with contextual hints and exit."""
    console.print(f"[red]Error ({model or 'fulfil'}): {exc}[/red]")
    if exc.hint:
        console.print(f"[dim]Hint: {exc.hint}[/dim]")
    elif not is_quiet() and model:
        if isinstance(exc, ValidationError):
            console.print(
                f"[dim]Hint: Run 'fulfil {model} describe' to see valid field names.[/dim]"
            )
    sys.exit(exc.exit_code)


def create_model_group(model_name: str) -> click.Group:
    """Create a Click group for a model with all standard actions."""

    @click.group(name=model_name, help=f"Interact with {model_name} records.")
    @click.pass_context
    def model_group(ctx: click.Context) -> None:
        ctx.ensure_object(dict)
        ctx.obj["model"] = model_name

    @model_group.command("list")
    @click.option(
        "--where",
        default=None,
        help=(
            "MongoDB-style JSON filter. "
            'Equality: \'{"state": "confirmed"}\'. '
            "Operators (gt, gte, lt, lte, ne, in, not_in, contains, startswith, endswith): "
            '\'{"total_amount": {"gte": 100}}\'. '
            'OR logic: \'{"or": [{"state": "draft"}, {"state": "confirmed"}]}\''
        ),
    )
    @click.option(
        "--fields",
        "fields_str",
        default=None,
        help="Comma-separated field names, e.g. name,state,sale_date",
    )
    @click.option(
        "--order",
        default=None,
        help=(
            "Sort order as field:direction pairs, comma-separated. "
            "Direction is ASC or DESC (default: ASC). "
            "Examples: sale_date:desc  or  sale_date:desc,name:asc  or  name"
        ),
    )
    @click.option(
        "--cursor",
        default=None,
        help="Opaque cursor for fetching the next page (from previous response).",
    )
    @click.option(
        "--page-size", "--limit", default=20, type=int, help="Records per page (default: 20)"
    )
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def list_cmd(
        ctx: click.Context,
        where: str | None,
        fields_str: str | None,
        order: str | None,
        cursor: str | None,
        page_size: int,
        json_flag: bool,
    ) -> None:
        """List records matching filters.

        Examples:

        \b
          fulfil sales_order list
          fulfil sales_order list --where '{"state": "confirmed"}' --fields name,state
          fulfil sales_order list --order sale_date:desc --limit 50
          fulfil sales_order list --cursor <token>
        """
        model = ctx.obj["model"]
        params: dict[str, Any] = {"page_size": page_size}

        if where:
            params["where"] = _parse_json_arg(where, "--where")
        if order:
            params["ordering"] = _parse_order(order)
        if fields_str:
            params["fields"] = _parse_fields(fields_str)
        if cursor:
            params["cursor"] = cursor

        client = get_client()

        try:
            result = client.call(f"model.{model}.find", **params)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        # Determine if output will be JSON (explicit flag or auto-detected)
        use_json = json_flag or should_use_json()

        # Handle envelope response: {"data": [...], "pagination": {...}}
        if isinstance(result, dict) and "data" in result and "pagination" in result:
            records = result["data"]
            pagination = result["pagination"]

            if use_json:
                output(result, json_flag=True)
            else:
                output(records, json_flag=False, title=model)
                if not is_quiet() and pagination:
                    count = len(records)
                    next_cursor = pagination.get("next_cursor")
                    has_more = pagination.get("has_more", next_cursor is not None)
                    if has_more:
                        console.print(f"[dim]{count} records (more available)[/dim]")
                        if next_cursor:
                            console.print(f"[dim]Next: --cursor {next_cursor}[/dim]")
                    else:
                        console.print(f"[dim]{count} records[/dim]")
        else:
            # Fallback for servers that still return bare arrays
            output(result, json_flag=json_flag, title=model)

    @model_group.command("get")
    @click.argument("ids", type=str)
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def get_cmd(
        ctx: click.Context,
        ids: str,
        json_flag: bool,
    ) -> None:
        """Get records by ID(s). IDS is one or more comma-separated integers (e.g. 123 or 1,2,3)."""
        model = ctx.obj["model"]
        parsed_ids = _parse_ids(ids)

        try:
            client = get_client()
            result = client.call(f"model.{model}.serialize", parsed_ids)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        # Single ID → single record output
        if len(parsed_ids) == 1 and isinstance(result, list) and len(result) == 1:
            result = result[0]

        output(result, json_flag=json_flag, title=model)

    @model_group.command("create")
    @click.option(
        "--data",
        required=True,
        help=(
            "Record data as a JSON object or array of objects. "
            'Example: \'{"name": "Test", "code": "T001"}\' or '
            '\'[{"name": "A"}, {"name": "B"}]\''
        ),
    )
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def create_cmd(
        ctx: click.Context,
        data: str,
        json_flag: bool,
    ) -> None:
        """Create new record(s). Returns the created record ID(s)."""
        model = ctx.obj["model"]
        parsed = _parse_json_arg(data, "--data")
        vlist = parsed if isinstance(parsed, list) else [parsed]

        try:
            client = get_client()
            result = client.call(f"model.{model}.create", vlist=vlist)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        output(result, json_flag=json_flag)

    @model_group.command("update")
    @click.argument("ids", type=str)
    @click.option(
        "--data",
        required=True,
        help=(
            "JSON object with fields to update. "
            'Example: \'{"state": "confirmed", "comment": "Approved"}\''
        ),
    )
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def update_cmd(
        ctx: click.Context,
        ids: str,
        data: str,
        json_flag: bool,
    ) -> None:
        """Update record(s) by ID.

        IDS is one or more comma-separated integers (e.g. 42 or 1,2,3).
        """
        model = ctx.obj["model"]
        parsed_ids = _parse_ids(ids)
        values = _parse_json_arg(data, "--data")

        try:
            client = get_client()
            result = client.call(f"model.{model}.update", ids=parsed_ids, values=values)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        output(result, json_flag=json_flag)

    @model_group.command("delete")
    @click.argument("ids", type=str)
    @click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
    @click.pass_context
    def delete_cmd(ctx: click.Context, ids: str, yes: bool) -> None:
        """Permanently delete record(s) by ID. This cannot be undone.

        IDS is one or more comma-separated integers.
        """
        model = ctx.obj["model"]
        parsed_ids = _parse_ids(ids)

        if not yes:
            if not sys.stdin.isatty():
                console.print(
                    "[red]Error: Delete requires confirmation. "
                    "Use --yes/-y to skip in non-interactive mode.[/red]"
                )
                sys.exit(2)
            id_list = ", ".join(str(i) for i in parsed_ids)
            if not click.confirm(f"Delete {len(parsed_ids)} record(s) from {model} ({id_list})?"):
                console.print("[dim]Aborted.[/dim]")
                sys.exit(0)

        try:
            client = get_client()
            client.call(f"model.{model}.delete", ids=parsed_ids)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        console.print(f"[green]Deleted {len(parsed_ids)} record(s).[/green]")

    @model_group.command("count")
    @click.option(
        "--where",
        default=None,
        help=(
            "MongoDB-style JSON filter (same syntax as list --where). "
            'Example: \'{"state": "confirmed"}\''
        ),
    )
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def count_cmd(
        ctx: click.Context,
        where: str | None,
        json_flag: bool,
    ) -> None:
        """Count records matching filters. Returns a single integer."""
        model = ctx.obj["model"]
        params: dict[str, Any] = {}
        if where:
            params["where"] = _parse_json_arg(where, "--where")

        try:
            client = get_client()
            result = client.call(f"model.{model}.count", **params)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        if json_flag:
            output({"count": result}, json_flag=True)
        else:
            console.print(str(result))

    @model_group.command("call")
    @click.argument("method_name", type=str)
    @click.option(
        "--ids",
        default=None,
        help="Comma-separated record IDs to pass to the method, e.g. 1,2,3",
    )
    @click.option(
        "--data",
        default=None,
        help=("Extra method arguments as a JSON object. Example: '{\"warehouse\": 1}'"),
    )
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def call_cmd(
        ctx: click.Context,
        method_name: str,
        ids: str | None,
        data: str | None,
        json_flag: bool,
    ) -> None:
        """Call a custom method on the model.

        METHOD_NAME is the method suffix (e.g. 'confirm', 'process', 'cancel').
        The full RPC method will be model.<model_name>.<METHOD_NAME>.

        \b
        Examples:
          fulfil sales_order call confirm --ids 1,2,3
          fulfil sales_order call process --ids 42
        """
        model = ctx.obj["model"]
        params: dict[str, Any] = {}
        if ids:
            params["ids"] = _parse_ids(ids)
        if data:
            extra = _parse_json_arg(data, "--data")
            if isinstance(extra, dict):
                params.update(extra)

        try:
            client = get_client()
            result = client.call(f"model.{model}.{method_name}", **params)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        output(result, json_flag=json_flag)

    @model_group.command("describe")
    @click.argument("endpoint_name", required=False, default=None)
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def describe_cmd(ctx: click.Context, endpoint_name: str | None, json_flag: bool) -> None:
        """Describe the model, or a specific endpoint.

        \b
          fulfil sales_order describe           # all fields and endpoints
          fulfil sales_order describe find       # details for the find endpoint
          fulfil sales_order describe confirm    # details for the confirm endpoint
        """
        model = ctx.obj["model"]
        try:
            client = get_client()
            result = client.call("system.describe_model", model=model)
        except FulfilError as exc:
            _handle_error(exc, model=model)

        if endpoint_name:
            _describe_endpoint(result, model, endpoint_name, json_flag)
        else:
            output_model_describe(result, json_flag=json_flag)

    @model_group.command("fields")
    @click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
    @click.pass_context
    def fields_cmd(ctx: click.Context, json_flag: bool) -> None:
        """Alias for 'describe'."""
        ctx.invoke(describe_cmd, endpoint_name=None, json_flag=json_flag)

    return model_group


def _describe_endpoint(model_data: dict, model: str, endpoint_name: str, json_flag: bool) -> None:
    """Show details for a specific endpoint, or error if not found."""
    from fulfil_cli.output.describe import print_endpoint_detail

    endpoints = model_data.get("endpoints", [])
    for ep in endpoints:
        if ep.get("rpc_name") == endpoint_name or ep.get("name") == endpoint_name:
            if json_flag:
                output(ep, json_flag=True)
            else:
                print_endpoint_detail(ep, model)
            return

    # Not found — show available endpoints
    names = [ep.get("rpc_name", ep.get("name", "")) for ep in endpoints]
    console.print(f"[red]Endpoint '{endpoint_name}' not found on {model}.[/red]")
    if names:
        matches = difflib.get_close_matches(endpoint_name, names, n=3, cutoff=0.4)
        if matches:
            console.print(f"[dim]Did you mean: {', '.join(matches)}?[/dim]")
        else:
            console.print(f"[dim]Available: {', '.join(sorted(names))}[/dim]")
    sys.exit(5)
