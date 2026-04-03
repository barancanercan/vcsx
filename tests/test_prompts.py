"""Tests for utils/prompts.py."""

import os
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest import mock

import pytest

from vcsx.utils.prompts import (
    get_prompts,
    get_prompt_value,
    get_prompt_question,
    get_prompt_hint,
    get_prompt_placeholder,
    detect_platform,
    detect_ai_tool,
    detect_installed_ai_tools,
    get_intelligent_defaults,
    _is_cache_valid,
    _load_best_practices,
    _get_cache_dir,
    AI_TOOLS,
)


class TestGetPrompts:
    def test_returns_dict(self):
        result = get_prompts("tr")
        assert isinstance(result, dict)

    def test_turkish_prompts(self):
        result = get_prompts("tr")
        assert "purpose" in result
        assert "project_name" in result

    def test_english_prompts(self):
        result = get_prompts("en")
        assert isinstance(result, dict)
        assert "purpose" in result

    def test_normalized_structure(self):
        result = get_prompts("tr")
        for key, value in result.items():
            if key != "welcome":
                assert isinstance(value, dict)
                assert "question" in value


class TestGetPromptValue:
    def test_returns_field(self):
        prompts = {"key": {"question": "Q?", "hint": "H"}}
        assert get_prompt_value(prompts, "key", "hint") == "H"

    def test_missing_key_returns_default(self):
        prompts = {}
        assert get_prompt_value(prompts, "missing", "question", "default") == "default"

    def test_missing_field_returns_default(self):
        prompts = {"key": {"question": "Q?"}}
        assert get_prompt_value(prompts, "key", "hint", "fallback") == "fallback"

    def test_string_prompt_returns_default(self):
        prompts = {"key": "simple string"}
        assert get_prompt_value(prompts, "key", "question", "def") == "def"


class TestGetPromptQuestion:
    def test_returns_question(self):
        prompts = {"p": {"question": "What is this?"}}
        assert get_prompt_question(prompts, "p") == "What is this?"

    def test_missing_returns_default(self):
        assert get_prompt_question({}, "missing", "fallback") == "fallback"


class TestGetPromptHint:
    def test_returns_hint(self):
        prompts = {"p": {"question": "Q", "hint": "Use this"}}
        assert get_prompt_hint(prompts, "p") == "Use this"

    def test_missing_hint_returns_default(self):
        prompts = {"p": {"question": "Q"}}
        assert get_prompt_hint(prompts, "p", "no hint") == "no hint"


class TestGetPromptPlaceholder:
    def test_returns_placeholder(self):
        prompts = {"p": {"question": "Q", "placeholder": "e.g. foo"}}
        assert get_prompt_placeholder(prompts, "p") == "e.g. foo"

    def test_missing_returns_default(self):
        assert get_prompt_placeholder({}, "x", "default_ph") == "default_ph"


class TestDetectPlatform:
    def test_returns_string(self):
        result = detect_platform()
        assert isinstance(result, str)
        assert result in ("windows-powershell", "macos", "linux", "wsl")

    def test_wsl_detection(self):
        # WSL_DISTRO_NAME must contain "WSL" string for detection
        with mock.patch.dict(os.environ, {"WSL_DISTRO_NAME": "WSL2-Ubuntu"}):
            result = detect_platform()
            assert result == "wsl"

    def test_linux(self):
        with mock.patch("platform.system", return_value="Linux"):
            with mock.patch.dict(os.environ, {}, clear=True):
                result = detect_platform()
                assert result == "linux"

    def test_macos(self):
        with mock.patch("platform.system", return_value="Darwin"):
            with mock.patch.dict(os.environ, {}, clear=True):
                result = detect_platform()
                assert result == "macos"

    def test_windows(self):
        with mock.patch("platform.system", return_value="Windows"):
            with mock.patch.dict(os.environ, {}, clear=True):
                result = detect_platform()
                assert result == "windows-powershell"


class TestDetectAiTool:
    def test_returns_none_when_no_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = detect_ai_tool()
        assert result is None

    def test_detects_cursorrules(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".cursorrules").write_text("rules")
        result = detect_ai_tool()
        assert result == "cursor"

    def test_detects_claude_settings(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "settings.json").write_text("{}")
        result = detect_ai_tool()
        assert result == "claude-code"

    def test_detects_windsurfrules(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".windsurfrules").write_text("rules")
        result = detect_ai_tool()
        assert result == "windsurf"

    def test_detects_copilot(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "copilot-instructions.md").write_text("# Copilot")
        result = detect_ai_tool()
        assert result == "copilot"


class TestDetectInstalledAiTools:
    def test_returns_list(self):
        result = detect_installed_ai_tools()
        assert isinstance(result, list)

    def test_empty_when_nothing_installed(self):
        with mock.patch("shutil.which", return_value=None):
            result = detect_installed_ai_tools()
            assert result == []

    def test_detects_claude(self):
        def which_side(bin_name):
            return "/usr/bin/claude" if bin_name == "claude" else None
        with mock.patch("shutil.which", side_effect=which_side):
            result = detect_installed_ai_tools()
            assert "claude-code" in result


class TestIsCacheValid:
    def test_nonexistent_file(self, tmp_path):
        result = _is_cache_valid(tmp_path / "nonexistent.json")
        assert result is False

    def test_fresh_file_valid(self, tmp_path):
        f = tmp_path / "cache.json"
        f.write_text("{}")
        assert _is_cache_valid(f, max_age_days=7) is True

    def test_old_file_invalid(self, tmp_path):
        f = tmp_path / "cache.json"
        f.write_text("{}")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(str(f), (old_time, old_time))
        assert _is_cache_valid(f, max_age_days=7) is False


class TestLoadBestPractices:
    def test_returns_dict(self):
        result = _load_best_practices()
        assert isinstance(result, dict)
        assert "python" in result

    def test_returns_default_when_cache_invalid(self, tmp_path, monkeypatch):
        monkeypatch.setattr("vcsx.utils.prompts._get_cache_dir", lambda: tmp_path)
        result = _load_best_practices()
        assert isinstance(result, dict)

    def test_loads_valid_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("vcsx.utils.prompts._get_cache_dir", lambda: tmp_path)
        cache_data = {"custom": {"api": {"recurring_tasks": ["task1"]}}}
        (tmp_path / "best_practices.json").write_text(json.dumps(cache_data))
        result = _load_best_practices()
        assert "custom" in result


class TestGetIntelligentDefaults:
    def test_python_cli(self):
        result = get_intelligent_defaults("python", "cli")
        assert isinstance(result, dict)
        assert "recurring_tasks" in result
        assert "automations" in result
        assert "forbidden_actions" in result

    def test_unknown_lang_has_forbidden_defaults(self):
        result = get_intelligent_defaults("cobol", "mainframe")
        assert "rm -rf" in result["forbidden_actions"]

    def test_typescript_web(self):
        result = get_intelligent_defaults("typescript", "web")
        assert isinstance(result["recurring_tasks"], str)

    def test_rust_cli(self):
        result = get_intelligent_defaults("rust", "cli")
        assert "rm -rf" in result["forbidden_actions"]


class TestAiTools:
    def test_ai_tools_list_nonempty(self):
        assert len(AI_TOOLS) > 5
        assert "claude-code" in AI_TOOLS
        assert "cursor" in AI_TOOLS
