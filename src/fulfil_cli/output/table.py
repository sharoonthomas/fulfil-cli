"""Rich table output formatting."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table


def print_table(records: list[dict[str, Any]], *, title: str | None = None) -> None:
    """Print records as a Rich table."""
    if not records:
        console = Console()
        console.print("[dim]No records found.[/dim]")
        return

    table = Table(title=title, show_lines=False)

    # Use keys from first record as columns
    columns = list(records[0].keys())
    for col in columns:
        table.add_column(col, overflow="fold")

    for record in records:
        table.add_row(*[_format_value(record.get(col)) for col in columns])

    console = Console()
    console.print(table)


def _format_value(value: Any) -> str:
    """Format a value for table display."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "[green]✓[/green]" if value else "[red]✗[/red]"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return str(value)
    return str(value)
