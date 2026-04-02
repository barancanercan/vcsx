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


def list_official_templates() -> list[TemplateMetadata]:
    """List all official templates."""
    registry = get_template_registry()
    return [t.metadata for t in registry.list_all()]


def search_templates(query: str) -> list[TemplateMetadata]:
    """Search templates."""
    registry = get_template_registry()
    return [t.metadata for t in registry.search(query)]
