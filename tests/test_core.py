"""Tests for core modules."""

import pytest
from vcsx.core.context import ProjectContext
from vcsx.core.inference import (
    infer_language,
    infer_framework,
    infer_test_framework,
    infer_formatter,
    infer_linter,
)
from vcsx.core.validators import validate_project_name, sanitize_input


class TestProjectContext:
    def test_defaults(self):
        ctx = ProjectContext()
        assert ctx.project_type == ""
        assert ctx.lang == "tr"
        assert ctx.auth_needed is False

    def test_custom(self):
        ctx = ProjectContext(project_name="test", language="python")
        assert ctx.project_name == "test"
        assert ctx.language == "python"


class TestInference:
    def test_typescript_language(self):
        assert infer_language("React, Node.js, TypeScript") == "typescript"

    def test_python_language(self):
        assert infer_language("Python, FastAPI") == "python"

    def test_go_language(self):
        assert infer_language("Go, Gin") == "go"

    def test_default_language(self):
        assert infer_language("") == "typescript"

    def test_framework_inference(self):
        assert infer_framework("Next.js, React") == "Next.js"
        assert infer_framework("FastAPI") == "FastAPI"
        assert infer_framework("") == ""

    def test_test_framework(self):
        assert infer_test_framework("python") == "pytest"
        assert infer_test_framework("typescript") == "vitest"
        assert infer_test_framework("go") == "go test"

    def test_formatter(self):
        assert infer_formatter("python") == "ruff format"
        assert infer_formatter("typescript") == "prettier"

    def test_linter(self):
        assert infer_linter("python") == "ruff check"
        assert infer_linter("typescript") == "eslint"


class TestValidators:
    def test_valid_project_name(self):
        assert validate_project_name("my-project") is True
        assert validate_project_name("my_project") is True
        assert validate_project_name("myproject123") is True

    def test_invalid_project_name(self):
        assert validate_project_name("My Project") is False
        assert validate_project_name("my/project") is False

    def test_sanitize_input(self):
        assert sanitize_input("  hello  ") == "hello"
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""
