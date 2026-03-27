"""JSON and NDJSON output formatting using orjson."""

from __future__ import annotations

import sys
from typing import IO, Any

import orjson


def dumps(data: Any, *, pretty: bool = False) -> str:
    """Serialize data to JSON string."""
    opts = orjson.OPT_NON_STR_KEYS
    if pretty:
        opts |= orjson.OPT_INDENT_2
    return orjson.dumps(data, option=opts).decode()


def print_json(data: Any, *, file: IO[str] | None = None) -> None:
    """Print data as formatted JSON."""
    print(dumps(data, pretty=True), file=file or sys.stdout)


def print_ndjson(records: list[dict[str, Any]], *, file: IO[str] | None = None) -> None:
    """Print records as newline-delimited JSON (one per line)."""
    out = file or sys.stdout
    for record in records:
        print(dumps(record), file=out)
