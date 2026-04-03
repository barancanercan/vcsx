"""Template system for vcsx — starter templates and community templates."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemplateMetadata:
    """Template metadata container."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    tech_stack: dict[str, str] = field(default_factory=dict)
    ai_tools: list[str] = field(default_factory=list)


class Template:
    """Base class for vcsx templates."""

    def __init__(self, metadata: TemplateMetadata):
        self.metadata = metadata
        self._files: dict[str, str] = {}

    def add_file(self, path: str, content: str) -> None:
        """Add a file to the template."""
        self._files[path] = content

    def get_file(self, path: str) -> str | None:
        """Get a file content from the template."""
        return self._files.get(path)

    def list_files(self) -> list[str]:
        """List all files in the template."""
        return list(self._files.keys())

    def render(self, context: dict[str, Any]) -> "Template":
        """Render template with context variables."""
        from vcsx.templates.engine import render_template

        rendered = Template(self.metadata)
        for path, content in self._files.items():
            rendered.add_file(path, render_template(content, context))
        return rendered


class TemplateRegistry:
    """Registry for vcsx templates."""

    def __init__(self):
        self._templates: dict[str, Template] = {}

    def register(self, template: Template) -> None:
        """Register a template."""
        if template.metadata.name in self._templates:
            raise ValueError(f"Template already registered: {template.metadata.name}")
        self._templates[template.metadata.name] = template

    def unregister(self, name: str) -> None:
        """Unregister a template."""
        self._templates.pop(name, None)

    def get(self, name: str) -> Template | None:
        """Get a template by name."""
        return self._templates.get(name)

    def list_all(self) -> list[Template]:
        """List all registered templates."""
        return list(self._templates.values())

    def search(self, query: str) -> list[Template]:
        """Search templates by name, tags, or tech stack."""
        results = []
        query_lower = query.lower()
        for template in self._templates.values():
            if query_lower in template.metadata.name.lower():
                results.append(template)
            elif query_lower in template.metadata.description.lower():
                results.append(template)
            elif any(query_lower in tag.lower() for tag in template.metadata.tags):
                results.append(template)
        return results


_default_registry: TemplateRegistry | None = None


def get_template_registry() -> TemplateRegistry:
    """Get the default template registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = TemplateRegistry()
        _load_default_templates()
    return _default_registry


def _load_default_templates() -> None:
    """Load default vcsx templates."""
    registry = get_template_registry()

    registry.register(_create_fastapi_postgres_template())
    registry.register(_create_react_typescript_template())
    registry.register(_create_rust_cli_template())
    registry.register(_create_nextjs_template())
    registry.register(_create_go_api_template())
    registry.register(_create_django_api_template())
    registry.register(_create_flutter_app_template())
    registry.register(_create_saas_nextjs_template())
    registry.register(_create_python_cli_template())
    registry.register(_create_rust_api_template())


def _create_fastapi_postgres_template() -> Template:
    """Create FastAPI + PostgreSQL template."""
    metadata = TemplateMetadata(
        name="fastapi-postgres",
        version="1.0.0",
        description="FastAPI REST API with PostgreSQL database",
        author="vcsx",
        tags=["api", "python", "fastapi", "postgres", "sqlalchemy"],
        tech_stack={
            "language": "python",
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "orm": "SQLAlchemy",
        },
        ai_tools=["claude-code", "cursor", "aider"],
    )

    template = Template(metadata)

    template.add_file(
        "src/main.py",
        """from fastapi import FastAPI
from app.api import routes

app = FastAPI(title="{{project_name}}")
app.include_router(routes.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
""",
    )

    template.add_file("src/app/api/__init__.py", "")
    template.add_file("src/app/models/__init__.py", "")

    return template


def _create_react_typescript_template() -> Template:
    """Create React + TypeScript template."""
    metadata = TemplateMetadata(
        name="react-typescript",
        version="1.0.0",
        description="React SPA with TypeScript and Vite",
        author="vcsx",
        tags=["frontend", "react", "typescript", "vite"],
        tech_stack={
            "language": "typescript",
            "framework": "React",
            "bundler": "Vite",
        },
        ai_tools=["claude-code", "cursor", "windsurf", "bolt"],
    )

    template = Template(metadata)
    template.add_file(
        "src/App.tsx",
        """function App() {
  return <h1>{{project_name}}</h1>
}
export default App
""",
    )

    return template


def _create_rust_cli_template() -> Template:
    """Create Rust CLI template."""
    metadata = TemplateMetadata(
        name="rust-cli",
        version="1.0.0",
        description="Rust command-line application with Clap",
        author="vcsx",
        tags=["cli", "rust", "command-line"],
        tech_stack={
            "language": "rust",
            "framework": "Clap",
        },
        ai_tools=["claude-code", "cursor"],
    )

    template = Template(metadata)
    template.add_file(
        "src/main.rs",
        """use clap::Parser;

#[derive(Parser, Debug)]
struct Args {
    name: String,
}

fn main() {
    let args = Args::parse();
    println!("Hello, {}!", args.name);
}
""",
    )

    return template


def _create_nextjs_template() -> Template:
    """Create Next.js + TypeScript template."""
    metadata = TemplateMetadata(
        name="nextjs",
        version="1.0.0",
        description="Next.js full-stack application with App Router",
        author="vcsx",
        tags=["frontend", "fullstack", "nextjs", "typescript"],
        tech_stack={
            "language": "typescript",
            "framework": "Next.js",
        },
        ai_tools=["claude-code", "cursor", "windsurf", "bolt"],
    )

    template = Template(metadata)
    template.add_file(
        "app/page.tsx",
        """export default function Home() {
  return <h1>{{project_name}}</h1>
}
""",
    )

    return template


def _create_go_api_template() -> Template:
    """Create Go REST API template."""
    metadata = TemplateMetadata(
        name="go-api",
        version="1.0.0",
        description="Go REST API with Gin framework",
        author="vcsx",
        tags=["api", "go", "gin"],
        tech_stack={
            "language": "go",
            "framework": "Gin",
        },
        ai_tools=["claude-code", "cursor", "aider"],
    )

    template = Template(metadata)
    template.add_file(
        "main.go",
        """package main

import (
    "github.com/gin-gonic/gin"
)

func main() {
    r := gin.Default()
    r.GET("/health", func(c *gin.Context) {
        c.JSON(200, gin.H{"status": "ok"})
    })
    r.Run()
}
""",
    )

    return template


def _create_django_api_template() -> Template:
    """Django REST Framework API template."""
    metadata = TemplateMetadata(
        name="django-api",
        version="1.0.0",
        description="Django REST Framework API with PostgreSQL",
        author="vcsx",
        tags=["api", "python", "django", "drf", "postgres"],
        tech_stack={"language": "python", "framework": "Django", "type": "api"},
        ai_tools=["claude-code", "cursor"],
    )
    template = Template(metadata)
    template.add_file(
        "requirements.txt",
        "django>=5.0\ndjangorestframework>=3.15\npsycopg2-binary\npython-dotenv\n",
    )
    template.add_file(
        "manage.py",
        "#!/usr/bin/env python\nimport sys\nfrom django.core.management import execute_from_command_line\nif __name__ == '__main__':\n    execute_from_command_line(sys.argv)\n",
    )
    template.add_file(
        "README.md",
        "# Django REST API\n\n## Setup\n```bash\npip install -r requirements.txt\npython manage.py migrate\npython manage.py runserver\n```\n\n## Test\n```bash\npytest\n```\n",
    )
    template.add_file(
        ".env.example",
        "DEBUG=True\nDATABASE_URL=postgres://user:pass@localhost/dbname\nSECRET_KEY=your-secret-key\n",
    )
    return template


def _create_flutter_app_template() -> Template:
    """Flutter mobile app template."""
    metadata = TemplateMetadata(
        name="flutter-app",
        version="1.0.0",
        description="Flutter mobile app with Dart",
        author="vcsx",
        tags=["mobile", "dart", "flutter", "ios", "android"],
        tech_stack={"language": "dart", "framework": "Flutter", "type": "mobile"},
        ai_tools=["claude-code", "cursor"],
    )
    template = Template(metadata)
    template.add_file(
        "pubspec.yaml",
        "name: my_app\ndescription: A Flutter application\nversion: 1.0.0+1\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\nflutter:\n  uses-material-design: true\n",
    )
    template.add_file(
        "README.md",
        "# Flutter App\n\n## Setup\n```bash\nflutter pub get\n```\n\n## Run\n```bash\nflutter run\n```\n\n## Test\n```bash\nflutter test\n```\n",
    )
    template.add_file(
        "lib/main.dart",
        "import 'package:flutter/material.dart';\n\nvoid main() {\n  runApp(const MyApp());\n}\n\nclass MyApp extends StatelessWidget {\n  const MyApp({super.key});\n\n  @override\n  Widget build(BuildContext context) {\n    return MaterialApp(\n      title: 'My App',\n      home: Scaffold(\n        appBar: AppBar(title: const Text('Home')),\n        body: const Center(child: Text('Hello, World!')),\n      ),\n    );\n  }\n}\n",
    )
    return template


def _create_saas_nextjs_template() -> Template:
    """SaaS starter with Next.js, Tailwind, Prisma."""
    metadata = TemplateMetadata(
        name="saas-nextjs",
        version="1.0.0",
        description="SaaS starter: Next.js + Tailwind + Prisma + Auth",
        author="vcsx",
        tags=["saas", "nextjs", "typescript", "tailwind", "prisma", "auth"],
        tech_stack={"language": "typescript", "framework": "Next.js", "type": "web"},
        ai_tools=["claude-code", "cursor", "copilot"],
    )
    template = Template(metadata)
    template.add_file(
        "package.json",
        '{\n  "name": "saas-starter",\n  "version": "0.1.0",\n  "scripts": {\n    "dev": "next dev",\n    "build": "next build",\n    "test": "vitest run",\n    "lint": "eslint .",\n    "db:push": "prisma db push",\n    "db:generate": "prisma generate"\n  },\n  "dependencies": {\n    "next": "^15.0.0",\n    "@prisma/client": "^5.0.0",\n    "next-auth": "^5.0.0",\n    "tailwindcss": "^3.4.0"\n  }\n}\n',
    )
    template.add_file(
        "README.md",
        "# SaaS Starter\n\nNext.js + Tailwind + Prisma + Auth\n\n## Setup\n```bash\nnpm install\nnpx prisma db push\nnpm run dev\n```\n\n## Test\n```bash\nnpm test\n```\n",
    )
    template.add_file(
        ".env.example",
        "DATABASE_URL=postgresql://user:pass@localhost/dbname\nNEXTAUTH_SECRET=your-secret\nNEXTAUTH_URL=http://localhost:3000\n",
    )
    return template


def _create_python_cli_template() -> Template:
    """Python CLI app with Click and Rich."""
    metadata = TemplateMetadata(
        name="python-cli",
        version="1.0.0",
        description="Python CLI app with Click and Rich",
        author="vcsx",
        tags=["cli", "python", "click", "rich"],
        tech_stack={"language": "python", "framework": "Click", "type": "cli"},
        ai_tools=["claude-code", "aider"],
    )
    template = Template(metadata)
    template.add_file(
        "pyproject.toml",
        '[build-system]\nrequires = ["setuptools>=68"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "my-cli"\nversion = "0.1.0"\ndependencies = ["click>=8.1", "rich>=13.0"]\n\n[project.scripts]\nmy-cli = "my_cli.cli:main"\n\n[project.optional-dependencies]\ndev = ["pytest>=7.0", "ruff>=0.1.0"]\n',
    )
    template.add_file(
        "src/my_cli/cli.py",
        'import click\nfrom rich.console import Console\n\nconsole = Console()\n\n@click.group()\ndef main():\n    """My CLI tool."""\n    pass\n\n@main.command()\n@click.argument("name")\ndef hello(name: str):\n    """Say hello."""\n    console.print(f"Hello, [bold]{name}[/]!")\n',
    )
    template.add_file(
        "tests/test_cli.py",
        'from click.testing import CliRunner\nfrom my_cli.cli import main\n\ndef test_hello():\n    runner = CliRunner()\n    result = runner.invoke(main, ["hello", "World"])\n    assert result.exit_code == 0\n    assert "Hello" in result.output\n',
    )
    template.add_file(
        "README.md",
        "# My CLI\n\n## Install\n```bash\npip install -e '.[dev]'\n```\n\n## Use\n```bash\nmy-cli hello World\n```\n\n## Test\n```bash\npytest\n```\n",
    )
    return template


def _create_rust_api_template() -> Template:
    """Rust REST API with Axum."""
    metadata = TemplateMetadata(
        name="rust-api",
        version="1.0.0",
        description="Rust REST API with Axum and Tokio",
        author="vcsx",
        tags=["api", "rust", "axum", "tokio"],
        tech_stack={"language": "rust", "framework": "Axum", "type": "api"},
        ai_tools=["claude-code", "cursor"],
    )
    template = Template(metadata)
    template.add_file(
        "Cargo.toml",
        '[package]\nname = "my-api"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\naxum = "0.7"\ntokio = { version = "1", features = ["full"] }\nserde = { version = "1", features = ["derive"] }\nserde_json = "1"\n',
    )
    template.add_file(
        "src/main.rs",
        'use axum::{routing::get, Json, Router};\nuse serde::Serialize;\n\n#[derive(Serialize)]\nstruct Health { status: &\'static str }\n\nasync fn health() -> Json<Health> {\n    Json(Health { status: "ok" })\n}\n\n#[tokio::main]\nasync fn main() {\n    let app = Router::new().route("/health", get(health));\n    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();\n    axum::serve(listener, app).await.unwrap();\n}\n',
    )
    template.add_file(
        "README.md",
        "# Rust API (Axum)\n\n## Run\n```bash\ncargo run\n```\n\n## Test\n```bash\ncargo test\n```\n\n## Build\n```bash\ncargo build --release\n```\n",
    )
    return template


def list_official_templates() -> list[TemplateMetadata]:
    """List all official templates."""
    registry = get_template_registry()
    return [t.metadata for t in registry.list_all()]


def search_templates(query: str) -> list[TemplateMetadata]:
    """Search templates."""
    registry = get_template_registry()
    return [t.metadata for t in registry.search(query)]
