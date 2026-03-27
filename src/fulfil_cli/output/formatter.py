"""Output routing — JSON, table, CSV, NDJSON based on format."""

from __future__ import annotations

import csv
import io
import sys
from typing import Any

import orjson
from rich.console import Console
from rich.rule import Rule

from fulfil_cli.output.describe import print_model_describe
from fulfil_cli.output.json_output import print_json, print_ndjson
from fulfil_cli.output.report import print_report, print_schema
from fulfil_cli.output.table import print_record, print_table


def print_csv(data: list[dict[str, Any]]) -> None:
    """Print a list of dicts as CSV to stdout."""
    if not data:
        return
    flat_rows = []
    for row in data:
        flat: dict[str, Any] = {}
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                flat[k] = orjson.dumps(v, option=orjson.OPT_NON_STR_KEYS).decode()
            elif v is None:
                flat[k] = ""
            else:
                flat[k] = v
        flat_rows.append(flat)

    fieldnames = list(flat_rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(flat_rows)
    sys.stdout.write(buf.getvalue())


def _has_nested_dicts(record: dict) -> bool:
    """Check if a record has nested dict values (indicating rich sub-records)."""
    return any(isinstance(v, dict) for v in record.values())


def output(data: Any, *, fmt: str = "table", title: str | None = None) -> None:
    """Route output to the appropriate format renderer."""
    if fmt == "json":
        print_json(data)
        return

    if fmt == "ndjson":
        if isinstance(data, list):
            print_ndjson(data)
        elif isinstance(data, dict):
            print_ndjson([data])
        else:
            print_ndjson([{"value": data}])
        return

    if fmt == "csv":
        if isinstance(data, list) and data and isinstance(data[0], dict):
            print_csv(data)
        elif isinstance(data, dict):
            print_csv([data])
        else:
            print_json(data)
        return

    # table format
    if isinstance(data, list) and data and isinstance(data[0], dict):
        if _has_nested_dicts(data[0]):
            console = Console(stderr=False)
            for i, record in enumerate(data):
                if i > 0:
                    console.print(Rule(style="dim"))
                print_record(record, title=title)
        else:
            print_table(data, title=title)
    elif isinstance(data, dict):
        print_record(data, title=title)
    else:
        print_json(data)


def output_report(data: Any, *, fmt: str = "table") -> None:
    """Route report output to the appropriate renderer."""
    if fmt != "table":
        output(data, fmt=fmt)
        return

    if isinstance(data, dict) and "columns" in data and "data" in data:
        print_report(data)
    else:
        output(data, fmt=fmt)


def output_describe(data: Any, *, fmt: str = "table", title: str | None = None) -> None:
    """Route describe output to the appropriate renderer."""
    if fmt != "table":
        output(data, fmt=fmt, title=title)
        return

    if isinstance(data, dict) and "params_schema" in data:
        schema = data["params_schema"]
        print_schema(schema, title=title or data.get("report_name"))
    elif isinstance(data, dict) and "properties" in data:
        print_schema(data, title=title)
    else:
        output(data, fmt=fmt, title=title)


def output_model_describe(data: Any, *, fmt: str = "table") -> None:
    """Route model describe output to the appropriate renderer."""
    if fmt != "table":
        output(data, fmt=fmt)
        return

    if isinstance(data, dict) and "fields" in data:
        print_model_describe(data)
    else:
        output(data, fmt=fmt)
