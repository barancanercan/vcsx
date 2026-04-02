# vcsx Template System

vcsx includes 5 built-in templates and supports community templates.

## Official Templates

### fastapi-postgres
FastAPI REST API with PostgreSQL database.
- **Tech Stack**: Python, FastAPI, PostgreSQL, SQLAlchemy
- **AI Tools**: Claude Code, Cursor, Aider

### react-typescript
React SPA with TypeScript and Vite.
- **Tech Stack**: TypeScript, React, Vite
- **AI Tools**: Claude Code, Cursor, Windsurf, Bolt

### rust-cli
Rust CLI application with Clap.
- **Tech Stack**: Rust, Clap
- **AI Tools**: Claude Code, Cursor

### nextjs
Next.js full-stack with App Router.
- **Tech Stack**: TypeScript, Next.js
- **AI Tools**: Claude Code, Cursor, Windsurf, Bolt

### go-api
Go REST API with Gin framework.
- **Tech Stack**: Go, Gin
- **AI Tools**: Claude Code, Cursor, Aider

## Using Templates

### List templates
```bash
vcsx templates
```

### Search templates
```bash
vcsx templates search react
```

### Install template
```bash
vcsx templates:install fastapi-postgres
```

## Creating Custom Templates

Create a template directory with template files:

```
my-template/
├── template.yaml       # Template metadata
├── src/main.py        # Template files
├── src/models.py
└── tests/test_main.py
```

Use `{{variable}}` syntax for variables:

```python
# src/main.py
def hello():
    return "{{project_name}}"
```

## Template Metadata

```yaml
name: my-template
version: 1.0.0
description: My custom template
author: your-username
tags:
  - api
  - python
tech_stack:
  language: python
  framework: fastapi
ai_tools:
  - claude-code
  - cursor
```
