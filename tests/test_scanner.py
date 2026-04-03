"""Tests for the project scanner module."""

import json
import tempfile
from pathlib import Path

import pytest

from vcsx.core.scanner import scan_project, format_scan_summary, _infer_project_type


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestScanProjectPython:
    def test_detects_python_from_pyproject(self, tmp_dir):
        (Path(tmp_dir) / "pyproject.toml").write_text(
            '[project]\nname = "my-api"\ndescription = "A FastAPI app"\n'
            '[project.dependencies]\nfastapi = ">=0.100"\npytest = ">=7.0"\n'
        )
        result = scan_project(tmp_dir)
        assert result["language"] == "python"

    def test_detects_fastapi_framework(self, tmp_dir):
        (Path(tmp_dir) / "pyproject.toml").write_text(
            '[project]\nname = "my-api"\n[project.dependencies]\nfastapi = ">=0.100"\n'
        )
        result = scan_project(tmp_dir)
        assert result["framework"] == "FastAPI"

    def test_detects_django_framework(self, tmp_dir):
        (Path(tmp_dir) / "requirements.txt").write_text("django>=4.0\ndjangorestframework\n")
        result = scan_project(tmp_dir)
        assert result["framework"] == "Django"

    def test_detects_flask_framework(self, tmp_dir):
        (Path(tmp_dir) / "requirements.txt").write_text("flask>=2.0\n")
        result = scan_project(tmp_dir)
        assert result["framework"] == "Flask"

    def test_detects_project_name_from_pyproject(self, tmp_dir):
        (Path(tmp_dir) / "pyproject.toml").write_text(
            '[project]\nname = "my-cool-project"\ndescription = "Cool"\n'
        )
        result = scan_project(tmp_dir)
        assert result["project_name"] == "my-cool-project"

    def test_detects_description_from_pyproject(self, tmp_dir):
        (Path(tmp_dir) / "pyproject.toml").write_text(
            '[project]\nname = "proj"\ndescription = "A great project"\n'
        )
        result = scan_project(tmp_dir)
        assert result["description"] == "A great project"

    def test_pytest_test_framework(self, tmp_dir):
        (Path(tmp_dir) / "requirements.txt").write_text("fastapi\npytest\n")
        result = scan_project(tmp_dir)
        assert result["test_framework"] == "pytest"


class TestScanProjectTypeScript:
    def test_detects_typescript_from_package_json(self, tmp_dir):
        pkg = {"name": "my-app", "dependencies": {"react": "^18.0.0"}, "devDependencies": {"typescript": "^5.0.0"}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = scan_project(tmp_dir)
        assert result["language"] == "typescript"

    def test_detects_react_framework(self, tmp_dir):
        pkg = {"name": "my-app", "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = scan_project(tmp_dir)
        assert result["framework"] == "React"

    def test_detects_nextjs_framework(self, tmp_dir):
        pkg = {"name": "my-app", "dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = scan_project(tmp_dir)
        assert result["framework"] == "Next.js"

    def test_detects_express_framework(self, tmp_dir):
        pkg = {"name": "my-api", "dependencies": {"express": "^4.0.0"}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = scan_project(tmp_dir)
        assert result["framework"] == "Express"
        assert result["project_type"] == "api"

    def test_detects_vitest(self, tmp_dir):
        pkg = {"name": "my-app", "devDependencies": {"vitest": "^1.0.0"}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = scan_project(tmp_dir)
        assert result["test_framework"] == "vitest"

    def test_detects_vue(self, tmp_dir):
        pkg = {"name": "my-app", "dependencies": {"vue": "^3.0.0"}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = scan_project(tmp_dir)
        assert result["framework"] == "Vue"

    def test_detects_pnpm(self, tmp_dir):
        pkg = {"name": "my-app", "dependencies": {}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        (Path(tmp_dir) / "pnpm-lock.yaml").write_text("")
        result = scan_project(tmp_dir)
        assert result.get("package_manager") == "pnpm"

    def test_detects_project_name_from_package_json(self, tmp_dir):
        pkg = {"name": "awesome-project", "dependencies": {}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = scan_project(tmp_dir)
        assert result["project_name"] == "awesome-project"


class TestScanProjectGo:
    def test_detects_go_from_gomod(self, tmp_dir):
        (Path(tmp_dir) / "go.mod").write_text("module github.com/user/my-api\n\ngo 1.21\n")
        result = scan_project(tmp_dir)
        assert result["language"] == "go"

    def test_detects_gin_framework(self, tmp_dir):
        (Path(tmp_dir) / "go.mod").write_text(
            "module github.com/user/my-api\n\nrequire github.com/gin-gonic/gin v1.9.0\n"
        )
        result = scan_project(tmp_dir)
        assert result["framework"] == "Gin"
        assert result["project_type"] == "api"

    def test_detects_go_test_framework(self, tmp_dir):
        (Path(tmp_dir) / "go.mod").write_text("module my-app\n\ngo 1.21\n")
        result = scan_project(tmp_dir)
        assert result["test_framework"] == "go test"

    def test_extracts_module_name(self, tmp_dir):
        (Path(tmp_dir) / "go.mod").write_text("module github.com/myorg/my-service\n\ngo 1.21\n")
        result = scan_project(tmp_dir)
        assert result["project_name"] == "my-service"


class TestScanProjectRust:
    def test_detects_rust_from_cargo(self, tmp_dir):
        (Path(tmp_dir) / "Cargo.toml").write_text('[package]\nname = "my-cli"\nversion = "0.1.0"\n')
        result = scan_project(tmp_dir)
        assert result["language"] == "rust"

    def test_detects_axum_framework(self, tmp_dir):
        (Path(tmp_dir) / "Cargo.toml").write_text(
            '[package]\nname = "my-api"\n\n[dependencies]\naxum = "0.7"\n'
        )
        result = scan_project(tmp_dir)
        assert result["framework"] == "Axum"
        assert result["project_type"] == "api"

    def test_detects_clap_cli_type(self, tmp_dir):
        (Path(tmp_dir) / "Cargo.toml").write_text(
            '[package]\nname = "my-cli"\n\n[dependencies]\nclap = "4.0"\n'
        )
        result = scan_project(tmp_dir)
        assert result["project_type"] == "cli"

    def test_extracts_package_name(self, tmp_dir):
        (Path(tmp_dir) / "Cargo.toml").write_text('[package]\nname = "awesome-tool"\n')
        result = scan_project(tmp_dir)
        assert result["project_name"] == "awesome-tool"


class TestScanDocker:
    def test_detects_dockerfile(self, tmp_dir):
        (Path(tmp_dir) / "Dockerfile").write_text("FROM python:3.12\n")
        result = scan_project(tmp_dir)
        assert result["has_docker"] is True

    def test_detects_docker_compose(self, tmp_dir):
        (Path(tmp_dir) / "docker-compose.yml").write_text("version: '3'\n")
        result = scan_project(tmp_dir)
        assert result["has_docker"] is True

    def test_no_docker(self, tmp_dir):
        result = scan_project(tmp_dir)
        assert result["has_docker"] is False


class TestScanCI:
    def test_detects_github_actions(self, tmp_dir):
        workflows = Path(tmp_dir) / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text("name: CI\n")
        result = scan_project(tmp_dir)
        assert result["has_ci"] is True

    def test_detects_gitlab_ci(self, tmp_dir):
        (Path(tmp_dir) / ".gitlab-ci.yml").write_text("test:\n  script: pytest\n")
        result = scan_project(tmp_dir)
        assert result["has_ci"] is True


class TestInferProjectType:
    def test_infers_api_from_routes_dir(self, tmp_dir):
        (Path(tmp_dir) / "src" / "routes").mkdir(parents=True)
        assert _infer_project_type(Path(tmp_dir), "python") == "api"

    def test_infers_cli_from_commands_dir(self, tmp_dir):
        (Path(tmp_dir) / "src" / "commands").mkdir(parents=True)
        assert _infer_project_type(Path(tmp_dir), "python") == "cli"

    def test_infers_data_pipeline_from_scrapers(self, tmp_dir):
        (Path(tmp_dir) / "scrapers").mkdir()
        assert _infer_project_type(Path(tmp_dir), "python") == "data-pipeline"

    def test_defaults_to_web(self, tmp_dir):
        assert _infer_project_type(Path(tmp_dir), "typescript") == "web"


class TestFormatScanSummary:
    def test_formats_full_scan(self):
        scan = {
            "language": "python",
            "framework": "FastAPI",
            "project_type": "api",
            "test_framework": "pytest",
            "has_docker": True,
            "has_ci": True,
        }
        summary = format_scan_summary(scan)
        assert "python" in summary.lower()
        assert "FastAPI" in summary
        assert "pytest" in summary

    def test_formats_empty_scan(self):
        summary = format_scan_summary({})
        assert "No stack" in summary

    def test_formats_partial_scan(self):
        scan = {"language": "go", "framework": ""}
        summary = format_scan_summary(scan)
        assert "go" in summary.lower()
