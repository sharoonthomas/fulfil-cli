"""Output routing — JSON vs Rich table based on context."""

from __future__ import annotations

import os
import sys
from typing import Any

from rich.console import Console
from rich.rule import Rule

from fulfil_cli.output.describe import print_model_describe
from fulfil_cli.output.json_output import print_json, print_ndjson
from fulfil_cli.output.report import print_report, print_schema
from fulfil_cli.output.table import print_record, print_table


def should_use_json() -> bool:
    """Determine if output should be JSON.

    JSON is used when:
    - --json flag is set (via FULFIL_JSON env or passed through)
    - stdout is not a TTY (piped to another command)
    - CI environment variable is set
    """
    if os.environ.get("FULFIL_JSON", "").lower() in ("1", "true", "yes"):
        return True
    if not sys.stdout.isatty():
        return True
    return bool(os.environ.get("CI"))


def output(
    data: Any,
    *,
    json_flag: bool = False,
    title: str | None = None,
) -> None:
    """Route output to JSON or Rich table."""
    use_json = json_flag or should_use_json()

    if use_json:
        print_json(data)
        return

    # For table display, data must be a list of dicts
    if isinstance(data, list) and data and isinstance(data[0], dict):
        # If records have nested dicts, render each as a detail view
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


def _has_nested_dicts(record: dict) -> bool:
    """Check if a record has nested dict values (indicating rich sub-records)."""
    return any(isinstance(v, dict) for v in record.values())


def output_report(
    data: Any,
    *,
    json_flag: bool = False,
) -> None:
    """Route report output to JSON or Rich report renderer."""
    use_json = json_flag or should_use_json()

    if use_json:
        print_json(data)
        return

    if isinstance(data, dict) and "columns" in data and "data" in data:
        print_report(data)
    else:
        output(data, json_flag=json_flag)


def output_describe(
    data: Any,
    *,
    json_flag: bool = False,
    title: str | None = None,
) -> None:
    """Route describe output to JSON or Rich schema renderer."""
    use_json = json_flag or should_use_json()

    if use_json:
        print_json(data)
        return

    if isinstance(data, dict) and "params_schema" in data:
        # describe endpoint wraps schema in {report_name, description, params_schema}
        schema = data["params_schema"]
        print_schema(schema, title=title or data.get("report_name"))
    elif isinstance(data, dict) and "properties" in data:
        print_schema(data, title=title)
    else:
        output(data, json_flag=json_flag, title=title)


def output_model_describe(
    data: Any,
    *,
    json_flag: bool = False,
) -> None:
    """Route model describe output to JSON or Rich renderer."""
    use_json = json_flag or should_use_json()

    if use_json:
        print_json(data)
        return

    if isinstance(data, dict) and "fields" in data:
        print_model_describe(data)
    else:
        output(data, json_flag=json_flag)


def output_ndjson(records: list[dict[str, Any]]) -> None:
    """Output records as NDJSON for streaming."""
    print_ndjson(records)
