"""Tests for output formatting."""

from __future__ import annotations

import json

from fulfil_cli.output.json_output import print_json, print_ndjson


def test_print_json(capsys):
    print_json({"id": 1, "name": "Test"})
    output = capsys.readouterr().out
    data = json.loads(output)
    assert data == {"id": 1, "name": "Test"}


def test_print_json_list(capsys):
    print_json([{"id": 1}, {"id": 2}])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert len(data) == 2


def test_print_ndjson(capsys):
    records = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    print_ndjson(records)
    output = capsys.readouterr().out
    lines = output.strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"id": 1, "name": "A"}
    assert json.loads(lines[1]) == {"id": 2, "name": "B"}
