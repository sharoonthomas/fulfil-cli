"""Config commands: get, set, list."""

from __future__ import annotations

import typer
from rich.console import Console

from fulfil_cli.cli.state import AppContext
from fulfil_cli.config.manager import ConfigManager
from fulfil_cli.output.formatter import output

app = typer.Typer(help="Manage CLI configuration.")
console = Console()


@app.command("set")
def config_set(
    ctx: typer.Context,
    key: str = typer.Argument(help="Config key (e.g. 'merchant')"),
    value: str = typer.Argument(help="Value to set"),
) -> None:
    """Set a configuration value."""
    app_ctx: AppContext = ctx.obj
    config = ConfigManager()
    config.set(key, value)
    if not app_ctx.quiet:
        console.print(f"[green]Set {key} = {value}[/green]")


@app.command("get")
def config_get(
    ctx: typer.Context,
    key: str = typer.Argument(help="Config key"),
) -> None:
    """Get a configuration value."""
    app_ctx: AppContext = ctx.obj
    config = ConfigManager()
    value = config.get(key)
    if value is None:
        console.print(f"[yellow]Key '{key}' is not set.[/yellow]")
        raise typer.Exit(code=1)
    fmt = app_ctx.get_effective_format()
    if fmt != "table":
        output({key: value}, fmt=fmt)
    else:
        print(value)


@app.command("list")
def config_list(ctx: typer.Context) -> None:
    """List all configuration values."""
    app_ctx: AppContext = ctx.obj
    config = ConfigManager()
    data = config.all()
    fmt = app_ctx.get_effective_format()
    if fmt != "table":
        output(data, fmt=fmt)
    elif not data:
        console.print("[dim]No configuration set.[/dim]")
    else:
        for key, value in _flatten(data):
            console.print(f"{key} = {value}")


def _flatten(data: dict, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten nested dict to dotted key-value pairs."""
    items: list[tuple[str, str]] = []
    for key, value in data.items():
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            items.extend(_flatten(value, full_key))
        else:
            items.append((full_key, str(value)))
    return items
