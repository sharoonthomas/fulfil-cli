"""Config commands: get, set, list."""

from __future__ import annotations

import typer
from rich.console import Console

from fulfil_cli.config.manager import ConfigManager
from fulfil_cli.output.formatter import output

app = typer.Typer(help="Manage CLI configuration.")
console = Console()


@app.command("set")
def config_set(
    key: str = typer.Argument(help="Config key (e.g. 'merchant')"),
    value: str = typer.Argument(help="Value to set"),
) -> None:
    """Set a configuration value."""
    config = ConfigManager()
    config.set(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")


@app.command("get")
def config_get(
    key: str = typer.Argument(help="Config key"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get a configuration value."""
    config = ConfigManager()
    value = config.get(key)
    if value is None:
        console.print(f"[yellow]Key '{key}' is not set.[/yellow]")
        raise typer.Exit(code=1)
    if json:
        output({key: value}, json_flag=True)
    else:
        print(value)


@app.command("list")
def config_list(
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all configuration values."""
    config = ConfigManager()
    data = config.all()
    if json:
        output(data, json_flag=True)
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
