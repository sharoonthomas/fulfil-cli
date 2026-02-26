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


# Fields to skip everywhere (noisy metadata)
_SKIP_FIELDS = {"rec_name", "created_at", "updated_at"}


def print_record(data: dict[str, Any], *, title: str | None = None) -> None:
    """Print a single record as a vertical key-value layout with indented sub-records."""
    console = Console()

    # Separate fields into scalar, sub-records, and sub-lists
    scalar_fields: list[tuple[str, Any]] = []
    sub_records: list[tuple[str, dict]] = []
    sub_lists: list[tuple[str, list[dict]]] = []

    for key, value in data.items():
        if key in _SKIP_FIELDS:
            continue
        if isinstance(value, dict):
            sub_records.append((key, value))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            sub_lists.append((key, value))
        elif isinstance(value, list) and not value:
            # Skip empty lists
            continue
        else:
            scalar_fields.append((key, value))

    # Main key-value table for scalar fields and sub-records
    table = Table(title=title, show_header=False, show_lines=False, pad_edge=False)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")

    for key, value in scalar_fields:
        table.add_row(key, _format_value(value))

    for key, value in sub_records:
        _add_sub_record(table, key, value)

    console.print(table)

    # Sub-lists rendered as separate tables
    for key, items in sub_lists:
        console.print()
        _print_sub_table(console, key, items)


def _print_sub_table(console: Console, key: str, items: list[dict[str, Any]]) -> None:
    """Render a list of sub-records as a compact table."""
    # Collect columns from all items, skipping noisy metadata
    columns = [col for col in items[0] if col not in _SKIP_FIELDS and col != "id"]

    count = len(items)
    label = "record" if count == 1 else "records"

    table = Table(
        title=f"{key} ({count} {label})",
        title_style="bold cyan",
        show_lines=False,
        pad_edge=True,
        min_width=len(key) + 20,  # prevent title wrapping
    )
    for col in columns:
        table.add_column(col, overflow="fold")

    for item in items:
        row: list[str] = []
        for col in columns:
            val = item.get(col)
            if isinstance(val, dict):
                row.append(_sub_record_label(val))
            else:
                row.append(_format_value(val))
        table.add_row(*row)

    console.print(table)


def _sub_record_label(value: dict[str, Any]) -> str:
    """Build a single-line display label for a nested record."""
    label = value.get("name") or value.get("code") or ""
    # Clean up multiline rec_name (addresses etc.) — use name field instead
    if not label:
        rec = value.get("rec_name", "")
        label = rec.split("\n")[0].split("\r")[0] if rec else ""
    if label and "id" in value:
        return f"{label} [dim](#{value['id']})[/dim]"
    if label:
        return str(label)
    return ""


def _add_sub_record(table: Table, key: str, value: dict[str, Any]) -> None:
    """Add a nested record as a header row + indented child fields."""
    label = _sub_record_label(value)
    table.add_row(key, label)

    for sub_key, sub_value in value.items():
        if sub_key in _SKIP_FIELDS or sub_key == "id":
            continue
        # Skip if the value was already used as the label
        if sub_key in ("name", "code") and str(sub_value) in str(label):
            continue
        if isinstance(sub_value, dict):
            nested_label = _sub_record_label(sub_value)
            table.add_row(f"  {sub_key}", nested_label or _format_value(sub_value))
        elif isinstance(sub_value, list) and sub_value and isinstance(sub_value[0], dict):
            items = []
            for item in sub_value:
                il = item.get("name") or item.get("code") or item.get("rec_name", "")
                items.append(str(il) if il else str(item))
            table.add_row(f"  {sub_key}", ", ".join(items))
        elif isinstance(sub_value, list) and not sub_value:
            continue  # skip empty lists
        else:
            formatted = _format_value(sub_value)
            if formatted:
                table.add_row(f"  {sub_key}", formatted)


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
