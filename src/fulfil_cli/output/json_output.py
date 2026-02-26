"""JSON and NDJSON output formatting using orjson."""

from __future__ import annotations

import sys
from typing import Any

import orjson


def dumps(data: Any, *, pretty: bool = False) -> str:
    """Serialize data to JSON string."""
    opts = orjson.OPT_NON_STR_KEYS
    if pretty:
        opts |= orjson.OPT_INDENT_2
    return orjson.dumps(data, option=opts).decode()


def print_json(data: Any, *, file: Any = None) -> None:
    """Print data as formatted JSON."""
    file = file or sys.stdout
    print(dumps(data, pretty=True), file=file)


def print_ndjson(records: list[dict[str, Any]], *, file: Any = None) -> None:
    """Print records as newline-delimited JSON (one per line)."""
    file = file or sys.stdout
    for record in records:
        print(dumps(record), file=file)
