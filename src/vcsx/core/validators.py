"""Input validation utilities."""

import re


def validate_project_name(name: str) -> bool:
    """Validate project name is safe for filesystem and URLs."""
    return bool(re.match(r"^[a-z0-9][a-z0-9_-]*$", name.lower()))


def sanitize_input(text: str | None) -> str:
    """Sanitize user input for safe file generation."""
    if not text:
        return ""
    return text.strip().replace("\r\n", "\n")


def validate_tech_stack(stack: str) -> list[str]:
    """Parse and validate tech stack string into list."""
    if not stack:
        return []
    return [item.strip() for item in stack.split(",") if item.strip()]


def validate_features(features: str) -> list[str]:
    """Parse and validate features string into list."""
    if not features:
        return []
    return [item.strip() for item in features.split(",") if item.strip()]
