"""Tests for report output rendering logic."""

from __future__ import annotations

from fulfil_cli.output.report import _flatten_tree, _format_report_value


class TestFormatReportValue:
    def test_none(self):
        assert _format_report_value(None) == ""

    def test_string(self):
        assert _format_report_value("hello") == "hello"

    def test_int(self):
        assert _format_report_value(42) == "42"

    def test_float(self):
        assert _format_report_value(1234.5) == "1,234.50"

    def test_dict(self):
        assert _format_report_value({"a": 1}) == "{'a': 1}"


class TestFlattenTree:
    def _cols(self, *names):
        return [{"name": n} for n in names]

    def test_empty(self):
        assert _flatten_tree([], self._cols("a")) == []

    def test_flat_rows(self):
        nodes = [{"name": "Row 1"}, {"name": "Row 2"}]
        rows = _flatten_tree(nodes, self._cols("name"))
        assert len(rows) == 2
        assert rows[0][0].plain == "Row 1"
        assert rows[1][0].plain == "Row 2"

    def test_nested_children_indented(self):
        nodes = [
            {
                "name": "Parent",
                "children": [{"name": "Child"}],
            }
        ]
        rows = _flatten_tree(nodes, self._cols("name"))
        assert len(rows) == 2
        assert rows[0][0].plain == "Parent"
        assert rows[1][0].plain == "  Child"  # indented

    def test_bold_style(self):
        nodes = [{"name": "Total", "style": {"font_weight": "bold"}}]
        rows = _flatten_tree(nodes, self._cols("name"))
        assert "bold" in str(rows[0][0]._spans[0].style)

    def test_border_top_separator(self):
        """Bold row with border-top gets a separator row before it."""
        nodes = [
            {"name": "Regular"},
            {"name": "Total", "style": {"font_weight": "bold", "border-top": "1px"}},
        ]
        rows = _flatten_tree(nodes, self._cols("name"))
        # Regular, separator, Total
        assert len(rows) == 3
        assert rows[1] == [""]  # separator row

    def test_border_bottom_separator(self):
        nodes = [{"name": "Section", "style": {"border-bottom": "1px"}}]
        rows = _flatten_tree(nodes, self._cols("name"))
        assert len(rows) == 2  # row + separator

    def test_multiple_columns(self):
        nodes = [{"name": "Item", "amount": 99.5}]
        rows = _flatten_tree(nodes, self._cols("name", "amount"))
        assert len(rows) == 1
        assert rows[0][0].plain == "Item"
        assert rows[0][1].plain == "99.50"
