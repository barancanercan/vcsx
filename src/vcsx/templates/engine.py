"""Template rendering engine with variable substitution."""

import re
from typing import Any


def render_template(template: str, context: dict[str, Any]) -> str:
    """Render a template string with context variables.

    Variables are denoted with {{variable_name}} syntax.
    """
    result = template

    pattern = re.compile(r"\{\{(\w+)\}\}")

    def replace(match):
        key = match.group(1)
        if key in context:
            value = context[key]
            if value is None:
                return ""
            return str(value)
        return match.group(0)

    return pattern.sub(replace, result)


def render_template_file(template_path: str, context: dict[str, Any]) -> str:
    """Render a template file with context variables."""
    with open(template_path, encoding="utf-8") as f:
        template = f.read()
    return render_template(template, context)


def validate_template(template: str) -> list[str]:
    """Validate a template and return list of undefined variables."""
    pattern = re.compile(r"\{\{(\w+)\}\}")
    variables = set(pattern.findall(template))
    return list(variables)
