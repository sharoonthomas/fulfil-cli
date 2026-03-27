"""Dynamic report subcommand actions: execute/describe."""

from __future__ import annotations

import json
import sys
from typing import Any

import click
import typer
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from fulfil_cli.cli.state import AppContext, format_option
from fulfil_cli.client.errors import FulfilError, ValidationError
from fulfil_cli.output.formatter import output_describe, output_report
from fulfil_cli.output.json_output import print_json

console = Console(stderr=True)


def _parse_json_arg(value: str, arg_name: str) -> Any:
    """Parse a JSON string argument."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for {arg_name}: {exc}[/red]")
        raise typer.Exit(code=7) from None


def _handle_error(exc: FulfilError) -> None:
    """Print error and exit with appropriate code."""
    ctx = click.get_current_context(silent=True)
    app_ctx: AppContext | None = ctx.obj if ctx else None
    if app_ctx and app_ctx.get_effective_format() != "table":
        print_json(exc.to_dict(), file=sys.stderr)
        raise typer.Exit(code=exc.exit_code)
    console.print(f"[red]Error: {exc}[/red]")
    if exc.hint:
        console.print(f"[dim]Hint: {exc.hint}[/dim]")
    raise typer.Exit(code=exc.exit_code)


def _extract_properties(describe: Any) -> dict[str, Any]:
    """Extract properties from a describe response.

    Handles both direct schema ``{"properties": ...}`` and the wrapped
    format ``{"params_schema": {"properties": ...}}``.
    """
    if not isinstance(describe, dict):
        return {}
    if "params_schema" in describe:
        schema = describe["params_schema"]
        return schema.get("properties", {}) if isinstance(schema, dict) else {}
    return describe.get("properties", {})


def _prompt_params(
    properties: dict[str, Any],
    parsed: dict[str, Any],
) -> dict[str, Any]:
    """Interactively prompt for report parameters.

    Iterates over the describe properties, skipping any already provided in
    ``parsed``, and prompts the user based on property metadata.
    """
    result = dict(parsed)

    for name, prop in properties.items():
        if name in result:
            continue

        label = prop.get("title", name)
        default = prop.get("default")

        if prop.get("enum"):
            choices = [str(v) for v in prop["enum"] if v is not None]
            value = Prompt.ask(
                label,
                choices=choices,
                default=str(default) if default is not None else None,
                console=console,
            )
        elif prop.get("type") == "integer":
            value = IntPrompt.ask(
                label,
                default=default,
                console=console,
            )
        elif prop.get("type") == "boolean":
            value = Confirm.ask(
                label,
                default=default if default is not None else False,
                console=console,
            )
        else:
            value = Prompt.ask(
                label,
                default=str(default) if default is not None else None,
                console=console,
            )

        result[name] = value

    return result


def create_report_group(report_name: str) -> click.Group:
    """Create a Click group for a report with execute and describe actions."""

    @click.group(
        name=report_name,
        help=f"Interact with {report_name} report.",
        invoke_without_command=True,
    )
    @click.option(
        "--params",
        default=None,
        help=(
            "Report parameters as a JSON object. "
            """Example: '{"date_from": "2024-01-01", "date_to": "2024-12-31", "warehouse": 1}'"""
        ),
    )
    @click.option(
        "-i",
        "--interactive",
        is_flag=True,
        default=False,
        help=(
            "Fetch the report schema and interactively prompt for each parameter. "
            "Use 'describe' subcommand to see the schema without executing."
        ),
    )
    @format_option
    @click.pass_context
    def report_group(
        ctx: click.Context,
        params: str | None,
        interactive: bool,
        output_format: str | None,
    ) -> None:
        if ctx.invoked_subcommand is None:
            ctx.invoke(
                execute_cmd, params=params, interactive=interactive, output_format=output_format
            )

    @report_group.command("execute")
    @click.option(
        "--params",
        default=None,
        help=(
            "Report parameters as a JSON object. "
            """Example: '{"date_from": "2024-01-01", "date_to": "2024-12-31"}'"""
        ),
    )
    @click.option(
        "-i",
        "--interactive",
        is_flag=True,
        default=False,
        help=(
            "Fetch the report schema and interactively prompt for each parameter. "
            "Use 'describe' subcommand to see the schema without executing."
        ),
    )
    @format_option
    @click.pass_context
    def execute_cmd(
        ctx: click.Context,
        params: str | None,
        interactive: bool,
        output_format: str | None,
    ) -> None:
        """Execute the report with given parameters."""
        app_ctx: AppContext = ctx.obj
        parsed: dict[str, Any] = {}
        if params:
            parsed = _parse_json_arg(params, "--params")

        client = app_ctx.get_client()

        # Interactive mode: fetch describe and prompt before executing
        if interactive and sys.stderr.isatty():
            try:
                describe = client.call(f"report.{report_name}.describe")
            except FulfilError as exc:
                _handle_error(exc)
            properties = _extract_properties(describe)
            if properties:
                parsed = _prompt_params(properties, parsed)

        try:
            result = client.call(f"report.{report_name}.execute", **parsed)
        except ValidationError as exc:
            # Reactive mode: on validation error, prompt and retry if TTY
            if sys.stderr.isatty():
                console.print(f"[yellow]Validation error: {exc}[/yellow]")
                try:
                    describe = client.call(f"report.{report_name}.describe")
                except FulfilError:
                    _handle_error(exc)
                properties = _extract_properties(describe)
                if properties:
                    console.print()
                    parsed = _prompt_params(properties, parsed)
                    try:
                        result = client.call(f"report.{report_name}.execute", **parsed)
                    except FulfilError as retry_exc:
                        _handle_error(retry_exc)
                else:
                    _handle_error(exc)
            else:
                _handle_error(exc)
        except FulfilError as exc:
            _handle_error(exc)

        output_report(result, fmt=app_ctx.get_effective_format(output_format))

    @report_group.command("describe")
    @format_option
    @click.pass_context
    def describe_cmd(ctx: click.Context, output_format: str | None) -> None:
        """Show the report's parameter description."""
        app_ctx: AppContext = ctx.obj

        try:
            client = app_ctx.get_client()
            result = client.call(f"report.{report_name}.describe")
        except FulfilError as exc:
            _handle_error(exc)

        output_describe(result, fmt=app_ctx.get_effective_format(output_format), title=report_name)

    return report_group
