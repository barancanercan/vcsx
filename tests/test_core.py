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


class TestValidatorsExtended:
    def test_validate_project_name_numbers(self):
        assert validate_project_name("project123") is True

    def test_validate_project_name_hyphen(self):
        assert validate_project_name("my-project") is True

    def test_validate_project_name_with_slash_fails(self):
        assert validate_project_name("my/project") is False

    def test_validate_project_name_space_fails(self):
        assert validate_project_name("my project") is False

    def test_sanitize_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_sanitize_none_returns_empty(self):
        assert sanitize_input(None) == ""

    def test_sanitize_empty_returns_empty(self):
        assert sanitize_input("") == ""

    def test_validate_tech_stack_parses(self):
        from vcsx.core.validators import validate_tech_stack

        result = validate_tech_stack("Python, FastAPI, PostgreSQL")
        assert "Python" in result
        assert "FastAPI" in result
        assert len(result) == 3

    def test_validate_tech_stack_empty(self):
        from vcsx.core.validators import validate_tech_stack

        assert validate_tech_stack("") == []

    def test_validate_features_parses(self):
        from vcsx.core.validators import validate_features

        result = validate_features("auth, CRUD, dashboard")
        assert len(result) == 3
        assert "auth" in result


class TestInferenceEdgeCases:
    """Test inference edge cases for 88% → 95%."""

    def test_infer_language_empty_returns_typescript(self):
        assert infer_language("") == "typescript"

    def test_infer_language_none_stack(self):
        # Test with unknown stack falls back to typescript
        assert infer_language("cobol, mainframe") == "typescript"

    def test_infer_framework_empty(self):
        assert infer_framework("") == ""

    def test_infer_framework_no_match(self):
        assert infer_framework("python, unknown-framework-xyz") == ""

    def test_infer_test_framework_unknown_lang(self):
        # Falls back to pytest for unknown
        assert infer_test_framework("cobol") == "pytest"

    def test_infer_formatter_unknown_lang(self):
        assert infer_formatter("cobol") == "prettier"

    def test_infer_linter_unknown_lang(self):
        assert infer_linter("cobol") == "eslint"

    def test_infer_framework_gin(self):
        assert infer_framework("Go, Gin framework") == "Gin"

    def test_infer_framework_echo(self):
        assert infer_framework("Go, Echo") == "Echo"

    def test_infer_kotlin_test_fw(self):
        assert infer_test_framework("kotlin") == "junit"

    def test_infer_dart_formatter(self):
        assert infer_formatter("dart") == "dart format"

    def test_infer_csharp_linter(self):
        assert infer_linter("csharp") == "roslyn"


class TestInferenceExtended:
    """Test new language support in inference engine."""

    def test_kotlin(self):
        assert infer_language("Kotlin, Ktor, Coroutines") == "kotlin"

    def test_swift(self):
        assert infer_language("Swift, SwiftUI, iOS") == "swift"

    def test_dart_flutter(self):
        assert infer_language("Dart, Flutter") == "dart"

    def test_csharp(self):
        assert infer_language("C#, ASP.NET Core") == "csharp"

    def test_php_laravel(self):
        assert infer_language("PHP, Laravel") == "php"

    def test_ruby_rails(self):
        assert infer_language("Ruby, Rails") == "ruby"

    def test_kotlin_test_framework(self):
        assert infer_test_framework("kotlin") == "junit"

    def test_swift_test_framework(self):
        assert infer_test_framework("swift") == "xctest"

    def test_dart_formatter(self):
        assert infer_formatter("dart") == "dart format"

    def test_ruby_linter(self):
        assert infer_linter("ruby") == "rubocop"

    def test_kotlin_framework(self):
        assert infer_framework("Kotlin, Ktor API") == "Ktor"

    def test_swift_framework(self):
        assert infer_framework("SwiftUI app") == "SwiftUI"


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
