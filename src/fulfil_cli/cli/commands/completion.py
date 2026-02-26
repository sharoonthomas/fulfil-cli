"""Shell completion install command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

console = Console()


def completion_install() -> None:
    """Install shell completion for the current shell."""
    shell = _detect_shell()
    if not shell:
        console.print("[red]Could not detect shell. Set $SHELL and try again.[/red]")
        raise typer.Exit(code=2)

    console.print(f"Detected shell: [bold]{shell}[/bold]")

    try:
        result = subprocess.run(
            [sys.argv[0], "--show-completion", shell],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            target = _completion_target(shell)
            console.print(f"[green]Completion installed for {shell}.[/green]")
            if target:
                console.print(f"[dim]Wrote to: {target}[/dim]")
            console.print("[dim]Restart your shell or source your profile to activate.[/dim]")
        else:
            console.print(f"[red]Failed to install completion: {result.stderr}[/red]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1) from None


def _detect_shell() -> str | None:
    """Detect the current shell."""
    shell_path = os.environ.get("SHELL", "")
    if "zsh" in shell_path:
        return "zsh"
    if "bash" in shell_path:
        return "bash"
    if "fish" in shell_path:
        return "fish"
    return None


def _completion_target(shell: str) -> str | None:
    """Return the typical completion file path for display."""
    home = Path.home()
    if shell == "zsh":
        return f"{home}/.zfunc/_fulfil"
    if shell == "bash":
        return f"{home}/.bash_completions/fulfil.bash"
    if shell == "fish":
        return f"{home}/.config/fish/completions/fulfil.fish"
    return None
