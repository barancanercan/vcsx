"""Tests for templates/engine.py — render_template, render_template_file, validate_template."""

import tempfile
import os
import pytest

from vcsx.templates.engine import render_template, render_template_file, validate_template


class TestRenderTemplate:
    def test_simple_substitution(self):
        result = render_template("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_variables(self):
        result = render_template("{{greeting}} {{name}}!", {"greeting": "Hi", "name": "Baran"})
        assert result == "Hi Baran!"

    def test_missing_variable_kept(self):
        result = render_template("Hello {{missing}}!", {})
        assert result == "Hello {{missing}}!"

    def test_none_value_becomes_empty(self):
        result = render_template("Hello {{name}}!", {"name": None})
        assert result == "Hello !"

    def test_integer_value(self):
        result = render_template("Count: {{n}}", {"n": 42})
        assert result == "Count: 42"

    def test_empty_template(self):
        result = render_template("", {"foo": "bar"})
        assert result == ""

    def test_no_variables(self):
        result = render_template("plain text", {"foo": "bar"})
        assert result == "plain text"

    def test_repeated_variable(self):
        result = render_template("{{x}} and {{x}}", {"x": "hello"})
        assert result == "hello and hello"

    def test_partial_match_not_replaced(self):
        # Single braces should not be affected
        result = render_template("{single} {{double}}", {"double": "ok"})
        assert result == "{single} ok"


class TestRenderTemplateFile:
    def test_basic_file_render(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("Project: {{name}}\nLang: {{lang}}")
            path = f.name
        try:
            result = render_template_file(path, {"name": "vcsx", "lang": "Python"})
            assert result == "Project: vcsx\nLang: Python"
        finally:
            os.unlink(path)

    def test_missing_variable_in_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("Hello {{missing}}")
            path = f.name
        try:
            result = render_template_file(path, {})
            assert "{{missing}}" in result
        finally:
            os.unlink(path)


class TestValidateTemplate:
    def test_finds_variables(self):
        variables = validate_template("Hello {{name}}, you have {{count}} messages.")
        assert set(variables) == {"name", "count"}

    def test_empty_template(self):
        assert validate_template("") == []

    def test_no_variables(self):
        assert validate_template("plain text") == []

    def test_single_variable(self):
        result = validate_template("{{only_one}}")
        assert result == ["only_one"]

    def test_duplicate_variables_deduplicated(self):
        result = validate_template("{{x}} {{x}} {{y}}")
        assert set(result) == {"x", "y"}
