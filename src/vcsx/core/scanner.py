"""Project scanner — auto-detects tech stack, language, framework from project files."""

from pathlib import Path


def scan_project(project_dir: str) -> dict:
    """Scan a project directory and return detected tech stack info.

    Returns a dict with:
    - language: detected primary language
    - framework: detected framework
    - tech_stack: comma-separated stack string
    - project_type: detected project type
    - test_framework: detected test framework
    - has_docker: bool
    - has_ci: bool
    - project_name: from directory name or package name
    """
    root = Path(project_dir).resolve()
    result = {
        "language": "",
        "framework": "",
        "tech_stack": "",
        "project_type": "web",
        "test_framework": "",
        "has_docker": False,
        "has_ci": False,
        "project_name": root.name,
        "description": "",
    }

    # Detect language from config files
    if (root / "pyproject.toml").exists():
        result["language"] = "python"
        _scan_pyproject(root, result)
    elif (root / "requirements.txt").exists() or (root / "setup.py").exists():
        result["language"] = "python"
        _scan_python_files(root, result)
    elif (root / "package.json").exists():
        _scan_package_json(root, result)
    elif (root / "go.mod").exists():
        result["language"] = "go"
        _scan_go_mod(root, result)
    elif (root / "Cargo.toml").exists():
        result["language"] = "rust"
        _scan_cargo_toml(root, result)
    elif (root / "pom.xml").exists() or (root / "build.gradle").exists():
        result["language"] = "java"
        result["project_type"] = "api"
    elif (root / "pubspec.yaml").exists():
        result["language"] = "dart"
        result["framework"] = "Flutter"
        result["project_type"] = "mobile"

    # Detect Docker
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        result["has_docker"] = True

    # Detect CI
    if (root / ".github" / "workflows").exists() or (root / ".gitlab-ci.yml").exists():
        result["has_ci"] = True

    # Detect project type from directory structure
    if not result.get("project_type") or result["project_type"] == "web":
        result["project_type"] = _infer_project_type(root, result["language"])

    # Build tech stack string
    stack_parts = []
    if result["language"]:
        stack_parts.append(result["language"].title())
    if result["framework"]:
        stack_parts.append(result["framework"])
    result["tech_stack"] = ", ".join(stack_parts) if stack_parts else result["language"]

    return result


def _scan_pyproject(root: Path, result: dict) -> None:
    """Parse pyproject.toml for project info."""
    try:
        content = (root / "pyproject.toml").read_text(encoding="utf-8")

        # Extract project name
        for line in content.splitlines():
            if line.strip().startswith("name ="):
                name = line.split("=", 1)[1].strip().strip("\"'")
                if name:
                    result["project_name"] = name
                break

        # Extract description
        for line in content.splitlines():
            if line.strip().startswith("description ="):
                desc = line.split("=", 1)[1].strip().strip("\"'")
                if desc:
                    result["description"] = desc
                break

        # Detect framework from dependencies
        deps_lower = content.lower()
        result["framework"] = _detect_python_framework(deps_lower)
        result["test_framework"] = "pytest" if "pytest" in deps_lower else "pytest"

    except Exception:
        pass


def _scan_python_files(root: Path, result: dict) -> None:
    """Scan Python project files."""
    try:
        req_file = root / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text(encoding="utf-8").lower()
            result["framework"] = _detect_python_framework(content)
            result["test_framework"] = "pytest"
    except Exception:
        pass


def _detect_python_framework(deps_lower: str) -> str:
    """Detect Python framework from dependency string."""
    if "fastapi" in deps_lower:
        return "FastAPI"
    if "django" in deps_lower:
        return "Django"
    if "flask" in deps_lower:
        return "Flask"
    if "starlette" in deps_lower:
        return "Starlette"
    if "tornado" in deps_lower:
        return "Tornado"
    if "pandas" in deps_lower or "numpy" in deps_lower or "sklearn" in deps_lower:
        return "Data Science"
    if "scrapy" in deps_lower:
        return "Scrapy"
    return ""


def _scan_package_json(root: Path, result: dict) -> None:
    """Parse package.json for JS/TS project info."""
    try:
        import json

        data = json.loads((root / "package.json").read_text(encoding="utf-8"))

        result["project_name"] = data.get("name", root.name)
        result["description"] = data.get("description", "")

        all_deps = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))
        deps_lower = " ".join(all_deps.keys()).lower()

        # Language: TypeScript or JavaScript
        if "typescript" in all_deps or (root / "tsconfig.json").exists():
            result["language"] = "typescript"
        else:
            result["language"] = "javascript"

        # Framework detection
        if "next" in all_deps:
            result["framework"] = "Next.js"
            result["project_type"] = "web"
        elif "react" in all_deps:
            result["framework"] = "React"
            result["project_type"] = "web"
        elif "vue" in all_deps:
            result["framework"] = "Vue"
            result["project_type"] = "web"
        elif "svelte" in all_deps:
            result["framework"] = "Svelte"
            result["project_type"] = "web"
        elif "express" in all_deps or "fastify" in all_deps or "hono" in all_deps:
            result["framework"] = "Express" if "express" in all_deps else "Fastify"
            result["project_type"] = "api"
        elif "nestjs" in deps_lower or "@nestjs/core" in all_deps:
            result["framework"] = "NestJS"
            result["project_type"] = "api"

        # Test framework
        if "vitest" in all_deps:
            result["test_framework"] = "vitest"
        elif "jest" in all_deps:
            result["test_framework"] = "jest"

        # Package manager
        if (root / "pnpm-lock.yaml").exists():
            result["package_manager"] = "pnpm"
        elif (root / "yarn.lock").exists():
            result["package_manager"] = "yarn"
        else:
            result["package_manager"] = "npm"

    except Exception:
        pass


def _scan_go_mod(root: Path, result: dict) -> None:
    """Parse go.mod for Go project info."""
    try:
        content = (root / "go.mod").read_text(encoding="utf-8")
        lines = content.splitlines()
        if lines:
            # module name is on first line
            module_line = lines[0]
            if "module " in module_line:
                module_name = module_line.split("module ", 1)[1].strip()
                result["project_name"] = module_name.split("/")[-1]

        # Detect framework from go.mod
        if "github.com/gin-gonic/gin" in content:
            result["framework"] = "Gin"
            result["project_type"] = "api"
        elif "github.com/labstack/echo" in content:
            result["framework"] = "Echo"
            result["project_type"] = "api"
        elif "github.com/gofiber/fiber" in content:
            result["framework"] = "Fiber"
            result["project_type"] = "api"

        result["test_framework"] = "go test"
    except Exception:
        pass


def _scan_cargo_toml(root: Path, result: dict) -> None:
    """Parse Cargo.toml for Rust project info."""
    try:
        content = (root / "Cargo.toml").read_text(encoding="utf-8")

        for line in content.splitlines():
            if line.strip().startswith("name ="):
                name = line.split("=", 1)[1].strip().strip("\"'")
                if name:
                    result["project_name"] = name
                break

        if "axum" in content:
            result["framework"] = "Axum"
            result["project_type"] = "api"
        elif "actix-web" in content:
            result["framework"] = "Actix"
            result["project_type"] = "api"
        elif "clap" in content:
            result["project_type"] = "cli"

        result["test_framework"] = "cargo test"
    except Exception:
        pass


def _infer_project_type(root: Path, language: str) -> str:
    """Infer project type from directory structure."""
    # API indicators
    if any((root / d).exists() for d in ["src/api", "src/routes", "src/controllers", "app/api"]):
        return "api"

    # CLI indicators
    if any((root / d).exists() for d in ["src/commands", "src/cmd", "cmd"]):
        return "cli"

    # Data pipeline indicators
    if any((root / d).exists() for d in ["scrapers", "pipelines", "data/raw", "notebooks"]):
        return "data-pipeline"

    # Library indicators
    if language == "python":
        if (
            any((root / f).exists() for f in ["setup.py", "setup.cfg"])
            and not (root / "main.py").exists()
        ):
            return "library"

    return "web"


def format_scan_summary(scan: dict) -> str:
    """Format scan results for display."""
    lines = []
    if scan.get("language"):
        lines.append(f"Language: {scan['language']}")
    if scan.get("framework"):
        lines.append(f"Framework: {scan['framework']}")
    if scan.get("project_type"):
        lines.append(f"Type: {scan['project_type']}")
    if scan.get("test_framework"):
        lines.append(f"Tests: {scan['test_framework']}")
    if scan.get("has_docker"):
        lines.append("Docker: ✓")
    if scan.get("has_ci"):
        lines.append("CI/CD: ✓")
    return " | ".join(lines) if lines else "No stack detected"
