"""Tests for Rich table output."""

from __future__ import annotations

from fulfil_cli.output.table import _format_value, print_table


class TestPrintTable:
    def test_empty_list(self, capsys):
        print_table([])
        captured = capsys.readouterr()
        assert "No records found" in captured.out

    def test_list_of_dicts(self, capsys):
        records = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        print_table(records)
        captured = capsys.readouterr()
        assert "Alice" in captured.out
        assert "Bob" in captured.out

    def test_with_title(self, capsys):
        records = [{"id": 1}]
        print_table(records, title="Test Title")
        captured = capsys.readouterr()
        # Rich may wrap the title across lines; check both words are present
        assert "Test" in captured.out
        assert "Title" in captured.out

    def test_single_record(self, capsys):
        records = [{"key": "value"}]
        print_table(records)
        captured = capsys.readouterr()
        assert "value" in captured.out


class TestFormatValue:
    def test_none(self):
        assert _format_value(None) == ""

    def test_bool_true(self):
        result = _format_value(True)
        assert "✓" in result

    def test_bool_false(self):
        result = _format_value(False)
        assert "✗" in result

    def test_list(self):
        assert _format_value([1, 2, 3]) == "1, 2, 3"

    def test_dict(self):
        result = _format_value({"a": 1})
        assert "a" in result

    def test_string(self):
        assert _format_value("hello") == "hello"

    def test_integer(self):
        assert _format_value(42) == "42"
