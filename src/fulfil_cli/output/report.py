"""Report-specific Rich table renderer for hierarchical report data."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text


def print_report(data: dict[str, Any]) -> None:
    """Render a Fulfil report as a Rich table with headers and indented rows.

    Expected structure:
        title: str
        subtitle: str
        company: {name: str}
        columns: [{name, display_name, type, invisible}, ...]
        data: [{<col_name>: value, children: [...], style: {...}}, ...]
    """
    console = Console()

    # Print report header
    title = data.get("title", "")
    subtitle = data.get("subtitle", "")
    company = data.get("company", {})
    company_name = company.get("name", "") if isinstance(company, dict) else ""

    if company_name:
        console.print(Text(company_name, style="bold"))
    if title:
        console.print(Text(title, style="bold cyan"))
    if subtitle:
        console.print(Text(subtitle, style="dim"))
    if title or subtitle or company_name:
        console.print()

    # Build visible columns
    columns = data.get("columns", [])
    visible_cols = [c for c in columns if not c.get("invisible")]

    if not visible_cols:
        console.print("[dim]No columns defined.[/dim]")
        return

    # Create table
    table = Table(show_header=True, show_lines=False, pad_edge=True)

    for col in visible_cols:
        col_type = (col.get("type") or "").lower()
        justify = "right" if col_type in _NUMERIC_TYPES else "left"
        table.add_column(col.get("display_name", col["name"]), justify=justify)

    # Flatten tree and add rows
    rows = _flatten_tree(data.get("data", []), visible_cols)
    for row in rows:
        table.add_row(*row)

    console.print(table)


def print_schema(data: dict[str, Any], *, title: str | None = None) -> None:
    """Render a report schema as a Rich table of parameters.

    Expected JSON Schema-style structure:
        title: str
        type: "object"
        properties: {param_name: {title, type, required, default, enum, format, ...}, ...}
    """
    console = Console()

    schema_title = title or data.get("title", "")
    if schema_title:
        console.print(Text(f"{schema_title} schema", style="bold cyan"))
        console.print()

    properties = data.get("properties", {})
    if not properties:
        console.print("[dim]No parameters defined.[/dim]")
        return

    table = Table(show_header=True, show_lines=False, pad_edge=True)
    table.add_column("Parameter", style="bold")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Required")
    table.add_column("Default")
    table.add_column("Description")

    for name, prop in properties.items():
        param_title = prop.get("title", name)
        param_type = prop.get("type", "")
        if prop.get("format"):
            param_type = f"{param_type} ({prop['format']})"
        if prop.get("enum"):
            choices = ", ".join(str(v) for v in prop["enum"] if v is not None)
            if choices:
                param_type = f"{param_type} [{choices}]"

        required = "yes" if prop.get("required") else ""
        default = str(prop["default"]) if prop.get("default") is not None else ""
        description = prop.get("description", "")
        if prop.get("relation"):
            relation = f"relation: {prop['relation']}"
            description = f"{relation} — {description}" if description else relation

        table.add_row(param_title, name, param_type, required, default, description)

    console.print(table)


_NUMERIC_TYPES = frozenset(
    {
        "numeric",
        "float",
        "integer",
        "int",
        "number",
        "money",
        "amount",
        "decimal",
        "currency",
    }
)


def _flatten_tree(
    nodes: list[dict[str, Any]],
    columns: list[dict[str, str]],
    depth: int = 0,
) -> list[list[str | Text]]:
    """Recursively flatten tree nodes into table rows."""
    rows: list[list[str | Text]] = []

    for node in nodes:
        style = node.get("style", {}) or {}
        is_bold = style.get("font_weight") == "bold"
        has_border_top = style.get("border-top")
        has_border_bottom = style.get("border-bottom")

        cells: list[str | Text] = []
        for i, col in enumerate(columns):
            raw = node.get(col["name"])
            formatted = _format_report_value(raw)

            # Indent the first column based on depth
            if i == 0 and depth > 0:
                formatted = "  " * depth + formatted

            text = Text(formatted)
            if is_bold:
                text.stylize("bold")
            if has_border_top:
                text.stylize("underline")

            cells.append(text)

        # Add a separator row before if border-top on a bold/total row
        if has_border_top and is_bold and rows:
            rows.append([""] * len(columns))

        rows.append(cells)

        # Recurse into children
        children = node.get("children", [])
        if children:
            rows.extend(_flatten_tree(children, columns, depth + 1))

        # Add separator after if border-bottom
        if has_border_bottom:
            rows.append([""] * len(columns))

    return rows


def _format_report_value(value: Any) -> str:
    """Format a report cell value for display."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            return f"{value:,.2f}"
        return str(value)
    if isinstance(value, dict):
        return str(value)
    return str(value)
