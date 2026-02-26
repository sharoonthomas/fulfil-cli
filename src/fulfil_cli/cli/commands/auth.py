"""Auth commands: login, logout, status, token, workspaces, use."""

from __future__ import annotations

import os
import sys

import typer
from rich.console import Console

from fulfil_cli.auth.api_key import resolve_api_key, resolve_workspace
from fulfil_cli.auth.keyring_store import delete_api_key, get_api_key, store_api_key
from fulfil_cli.client.errors import AuthError, FulfilError
from fulfil_cli.client.http import FulfilClient
from fulfil_cli.config.manager import ConfigManager

app = typer.Typer(help="Manage authentication.")
console = Console()


@app.command()
def login(
    workspace: str | None = typer.Option(None, help="Workspace domain (e.g. 'acme.fulfil.io')"),
    api_key: str | None = typer.Option(None, "--api-key", help="API key"),
) -> None:
    """Authenticate with a Fulfil workspace."""
    config = ConfigManager()

    if not workspace:
        workspace = typer.prompt("Workspace domain (e.g. acme.fulfil.io)")
    if not api_key:
        api_key = typer.prompt("API key", hide_input=True)

    # Normalize workspace — accept slug or full domain
    if "." not in workspace:
        workspace = f"{workspace}.fulfil.io"

    # Validate the credentials
    console.print(f"[dim]Validating credentials for {workspace}...[/dim]")
    try:
        client = FulfilClient(workspace=workspace, api_key=api_key)
        client.call("system.version")
    except FulfilError as exc:
        console.print(f"[red]Authentication failed: {exc}[/red]")
        raise typer.Exit(code=exc.exit_code)
    except Exception:
        # If the v3 endpoint doesn't exist yet, store anyway with a warning
        console.print(
            "[yellow]Warning: Could not validate credentials "
            "(v3 API may not be deployed yet).[/yellow]"
        )

    # Store credentials
    store_api_key(workspace, api_key)
    config.add_workspace(workspace)
    config.workspace = workspace
    console.print(f"[green]Logged in to workspace '{workspace}'.[/green]")


@app.command()
def logout(
    workspace: str | None = typer.Argument(
        None, help="Workspace to log out from (default: current)"
    ),
    all_workspaces: bool = typer.Option(False, "--all", help="Log out from all workspaces"),
) -> None:
    """Remove stored credentials."""
    config = ConfigManager()

    if all_workspaces:
        for ws in config.workspaces:
            delete_api_key(ws)
        config.clear_workspaces()
        console.print("[green]Logged out from all workspaces.[/green]")
        return

    target = workspace or config.workspace
    if target:
        delete_api_key(target)
        config.remove_workspace(target)
        if config.workspace == target:
            # Switch to another workspace if available, or clear
            remaining = config.workspaces
            config.workspace = remaining[0] if remaining else None
        console.print(f"[green]Logged out from '{target}'.[/green]")
    else:
        console.print("[dim]Not logged in.[/dim]")


@app.command()
def status() -> None:
    """Show current authentication status."""
    config = ConfigManager()
    workspace = config.workspace
    if not workspace:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("[dim]Run 'fulfil auth login' to authenticate.[/dim]")
        raise typer.Exit(code=3)

    has_key = get_api_key(workspace) is not None
    env_key = "FULFIL_API_KEY" in os.environ

    console.print(f"Workspace: [bold]{workspace}[/bold]")
    if env_key:
        console.print("API Key:   [green]set via FULFIL_API_KEY[/green]")
    elif has_key:
        console.print("API Key:   [green]stored in keyring[/green]")
    else:
        console.print("API Key:   [red]not found[/red]")

    all_ws = config.workspaces
    if len(all_ws) > 1:
        console.print(f"\nAll workspaces ({len(all_ws)}):")
        for ws in all_ws:
            marker = " [bold green]*[/bold green]" if ws == workspace else ""
            console.print(f"  {ws}{marker}")


@app.command()
def token() -> None:
    """Print the current API key to stdout (for piping)."""
    config = ConfigManager()
    try:
        workspace = resolve_workspace(config_workspace=config.workspace)
        key = resolve_api_key(workspace=workspace)
    except AuthError as exc:
        console.print(f"[red]{exc}[/red]", file=sys.stderr)
        raise typer.Exit(code=exc.exit_code)
    print(key)


@app.command()
def workspaces() -> None:
    """List all stored workspaces."""
    config = ConfigManager()
    all_ws = config.workspaces
    current = config.workspace

    if not all_ws:
        console.print("[dim]No workspaces configured. Run 'fulfil auth login'.[/dim]")
        return

    for ws in all_ws:
        if ws == current:
            console.print(f"  [bold green]*[/bold green] {ws} [dim](current)[/dim]")
        else:
            console.print(f"    {ws}")


@app.command()
def use(
    workspace: str = typer.Argument(help="Workspace to switch to"),
) -> None:
    """Switch the active workspace."""
    config = ConfigManager()

    # Normalize
    if "." not in workspace:
        workspace = f"{workspace}.fulfil.io"

    if workspace not in config.workspaces:
        console.print(f"[red]Workspace '{workspace}' not found.[/red]")
        console.print("[dim]Run 'fulfil auth login' to add it first.[/dim]")
        raise typer.Exit(code=3)

    config.workspace = workspace
    console.print(f"[green]Switched to workspace '{workspace}'.[/green]")
