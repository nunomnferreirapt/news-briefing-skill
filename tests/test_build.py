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
    """Point build.py at a temp folder and serve one stand-in image for every photo, so nothing is fetched."""
    monkeypatch.setattr(build, "SITE", tmp_path / "site")
    monkeypatch.setattr(build, "OUT", tmp_path / "site" / "briefing.html")
    monkeypatch.setattr(build, "CACHE", tmp_path / "cache")
    stand_in = tmp_path / "stand-in.jpg"
    stand_in.write_bytes(b"\xff\xd8\xff\xd9")
    monkeypatch.setattr(build, "thumb_file", lambda page: stand_in)
    edition = json.loads(EXAMPLE.read_text())
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
    result = subprocess.run(["node", str(build.SKILL / "scripts" / "check_render.js"), str(out)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
    assert "RESULT: ok" in result.stdout
    assert "sheets opened: 11 of 11" in result.stdout
    assert "worth reading: 1 pieces" in result.stdout


def test_pieces_need_their_fields_and_a_real_quote(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "DATA", tmp_path)
    monkeypatch.setattr(build, "READS", tmp_path)
    (tmp_path / "read-x.txt").write_text("The author wrote this sentence, word for word.")
    good = {"id": "read-x", "voice": "x", "title": "t", "author": "a", "url": "u", "summary": "s", "why_read": "w",
            "key_takeaway": "k", "takeaways": ["one", "two"], "quote": "this sentence, word for word", "open_if": "o", "tags": ["reads-x"]}
    assert build.check_pieces({"reads": [good]}, set()) == []
    bad = {**good, "quote": "a sentence nobody wrote", "takeaways": ["only one"], "why_read": ""}
    problems = build.check_pieces({"reads": [bad]}, set())
    assert "read-x: missing why_read" in problems
    assert "read-x: needs 2 to 5 takeaways" in problems
    assert any("quote not found" in x for x in problems)


def test_career_reading_needs_for_you(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "DATA", tmp_path)
    monkeypatch.setattr(build, "READS", tmp_path)
    piece = {"id": "read-c", "voice": "x", "title": "t", "author": "a", "url": "u", "summary": "s", "why_read": "w",
             "key_takeaway": "k", "takeaways": ["one", "two"], "quote": "q", "open_if": "o", "tags": ["reads-x"]}
    assert "read-c: a career piece needs for_you" in build.check_pieces({"career_reading": [piece]}, set())
    assert "read-c: for_you belongs to career_reading only" in build.check_pieces({"reads": [{**piece, "for_you": "f"}]}, set())


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_render_check_fails_a_story_without_an_image(offline_build, monkeypatch):
    path, out = offline_build
    edition = json.loads(path.read_text())
    edition["sections"][0]["stories"][0]["photo"] = None
    path.write_text(json.dumps(edition))
    monkeypatch.setattr("sys.argv", ["build.py", str(path)])
    build.main()
    result = subprocess.run(["node", str(build.SKILL / "scripts" / "check_render.js"), str(out)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "NO IMAGE on: eu-22nd-sanctions" in result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_local_section_carries_career_reading_after_worth_reading(offline_build, monkeypatch):
    path, out = offline_build
    edition = json.loads(path.read_text())
    local = {"id": "scene", "name": "Local tech", "stories": [], "briefs": [],
             "events": [{"date": "3 Dec", "name": "Meetup", "url": "https://example.org", "venue": "Hall"}]}
    edition["sections"].append(local)
    edition["local"] = "scene"
    career = {**edition["reads"][0], "id": "read-career", "for_you": "What it means for the search.", "tags": ["reads-latent-space"]}
    edition["career_reading"] = [career]
    path.write_text(json.dumps(edition))
    monkeypatch.setattr("sys.argv", ["build.py", str(path)])
    build.main()
    result = subprocess.run(["node", str(build.SKILL / "scripts" / "check_render.js"), str(out)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
    assert "career reading: 1 pieces" in result.stdout
