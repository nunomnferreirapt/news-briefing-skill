"""second.sh: the second editor's command runs with a numeric turn limit only."""

import shutil
import subprocess

import pytest

from conftest import SCRIPTS


@pytest.fixture
def project(tmp_path):
    (tmp_path / "news-briefing").mkdir()
    (tmp_path / "news-briefing" / "settings.md").write_text("command: echo turns={turns}\n")
    (tmp_path / "p.md").write_text("x")
    return tmp_path


def run(project, turns):
    return subprocess.run(["/bin/bash", str(SCRIPTS / "second.sh"), "p.md", turns], cwd=project, capture_output=True, text=True)


def test_turns_must_be_a_number(project):
    result = run(project, "3; echo INJECTED")
    assert result.returncode == 2
    assert "INJECTED" not in result.stdout


def test_a_number_goes_through(project):
    result = run(project, "12")
    assert result.returncode == 0
    assert result.stdout.strip() == "turns=12"
