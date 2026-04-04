"""Tests for __main__.py entry point."""

import subprocess
import sys


def test_main_module_runs():
    """python -m vcsx --help should exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "vcsx", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "vcsx" in result.stdout.lower()


def test_main_module_version():
    """python -m vcsx --version should print version."""
    result = subprocess.run(
        [sys.executable, "-m", "vcsx", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
