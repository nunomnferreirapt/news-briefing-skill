"""build.py: schema notes, and a full build of the example edition without the network."""

import json
import shutil
import subprocess

import pytest

import build
from conftest import EXAMPLE


def test_check_passes_the_example():
    assert build.check(json.loads(EXAMPLE.read_text())) == []


def test_check_reports_missing_fields_and_duplicates():
    edition = {"edition": "x", "title": "t", "lead": [], "sections": [
        {"id": "a", "stories": [{"id": "s1", "headline": "h", "summary": "s", "sources": [1], "tags": ["t"]},
                                {"id": "s1", "headline": "h"}]}]}
    problems = build.check(edition)
    assert "duplicate story id s1" in problems
    assert "s1: missing summary" in problems


def test_check_wants_both_sides_of_a_split():
    edition = {"edition": "x", "title": "t", "lead": [], "sections": [{"id": "a", "stories": [
        {"id": "s", "headline": "h", "summary": "s", "sources": [1], "tags": ["t"],
         "coverage": {"split": {"a": {"source": "A", "says": "1"}}}}]}]}
    assert "s: split needs a and b" in build.check(edition)


@pytest.fixture
def offline_build(tmp_path, monkeypatch):
    """Point build.py at a temp folder and drop the photos, so nothing is fetched."""
    monkeypatch.setattr(build, "SITE", tmp_path / "site")
    monkeypatch.setattr(build, "OUT", tmp_path / "site" / "briefing.html")
    monkeypatch.setattr(build, "CACHE", tmp_path / "cache")
    edition = json.loads(EXAMPLE.read_text())
    for sec in edition["sections"]:
        for s in sec["stories"]:
            s["photo"] = None
    path = tmp_path / "edition.json"
    path.write_text(json.dumps(edition))
    return path, tmp_path / "site" / "briefing.html"


def test_build_writes_the_page(offline_build, monkeypatch):
    path, out = offline_build
    monkeypatch.setattr("sys.argv", ["build.py", str(path)])
    assert build.main() == 0
    html = out.read_text()
    assert "__EDITION_JSON__" not in html
    assert "Lego picks Estarreja" in html


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_render_check_opens_every_story(offline_build, monkeypatch):
    path, out = offline_build
    monkeypatch.setattr("sys.argv", ["build.py", str(path)])
    build.main()
    result = subprocess.run(["node", str(build.HERE / "check_render.js"), str(out)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
    assert "RESULT: ok" in result.stdout
    assert "sheets opened: 10 of 10" in result.stdout
