from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings


BASE = "pipeline.management.commands.archive"


def _make_private_repo(tmp_path):
    private_dir = tmp_path / "private_data"
    (private_dir / ".git").mkdir(parents=True)
    return private_dir


def test_pull_runs_git_pull_in_private_data_dir(tmp_path):
    private_dir = _make_private_repo(tmp_path)
    calls = []

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        calls.append((cmd, cwd))
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    with override_settings(PIPELINE_PRIVATE_DATA_DIR=private_dir), patch(f"{BASE}.subprocess.run", fake_run):
        call_command("archive", pull=True)

    assert calls == [(["git", "pull", "origin", "main"], private_dir)]


def test_push_skips_clean_private_data_repo(tmp_path):
    private_dir = _make_private_repo(tmp_path)
    calls = []

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        calls.append((cmd, cwd))
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    with override_settings(PIPELINE_PRIVATE_DATA_DIR=private_dir), patch(f"{BASE}.subprocess.run", fake_run):
        call_command("archive", push=True)

    assert calls == [
        (["git", "add", "."], private_dir),
        (["git", "diff", "--cached", "--name-only"], private_dir),
    ]


def test_push_commits_and_pushes_staged_private_data(tmp_path):
    private_dir = _make_private_repo(tmp_path)
    calls = []

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        calls.append((cmd, cwd))
        stdout = "product.jsonl\n" if cmd == ["git", "diff", "--cached", "--name-only"] else ""
        return type("Result", (), {"returncode": 0, "stdout": stdout, "stderr": ""})()

    with override_settings(PIPELINE_PRIVATE_DATA_DIR=private_dir), patch(f"{BASE}.subprocess.run", fake_run):
        call_command("archive", push=True)

    assert calls == [
        (["git", "add", "."], private_dir),
        (["git", "diff", "--cached", "--name-only"], private_dir),
        (["git", "commit", "-m", "update archive"], private_dir),
        (["git", "push", "origin", "main"], private_dir),
    ]


def test_archive_errors_when_private_data_is_not_git_repo(tmp_path):
    private_dir = tmp_path / "private_data"
    private_dir.mkdir()

    with override_settings(PIPELINE_PRIVATE_DATA_DIR=private_dir), pytest.raises(CommandError):
        call_command("archive", pull=True)
