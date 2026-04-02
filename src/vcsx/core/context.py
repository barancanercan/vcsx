"""Project context dataclass — holds all discovered project information."""

from dataclasses import dataclass, field


@dataclass
class ProjectContext:
    """Holds all discovered project information."""

    # Project basics
    project_type: str = ""
    project_name: str = ""
    description: str = ""
    tech_stack: str = ""
    language: str = ""
    framework: str = ""

    # MVP & scope
    mvp_features: str = ""
    future_phases: str = ""
    target_users: str = ""

    # Technical preferences
    hosting: str = ""
    auth_needed: bool = False
    auth_method: str = ""
    external_services: str = ""
    monorepo: bool = False

    # Development standards
    test_level: str = ""
    test_framework: str = ""
    ci_cd: bool = False
    code_style: str = ""
    formatter: str = ""
    linter: str = ""

    # Claude Code preferences
    recurring_tasks: str = ""
    forbidden_actions: str = ""
    automations: str = ""

    # Metadata
    lang: str = "tr"
    answers: dict = field(default_factory=dict)
