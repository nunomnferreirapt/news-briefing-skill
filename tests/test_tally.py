"""tally.py: how taps turn into standings, and a run against a temp state folder."""

import json

import tally
from conftest import SKILL


def test_outcome_needs_a_used_edition():
    assert tally.outcome(None, used=False) == "none"
    assert tally.outcome(None, used=True) == "passed"


def test_outcome_ranks_the_signals():
    assert tally.outcome({"skipped": True, "liked": True}, True) == "skip"
    assert tally.outcome({"liked": True}, True) == "strong"
    assert tally.outcome({"read": True, "seconds": 45}, True) == "strong"
    assert tally.outcome({"read": True, "seconds": 5}, True) == "weak"
    assert tally.outcome({"opened": True}, True) == "weak"


def test_standing_from_the_last_three():
    assert tally.standing([]) == "new"
    assert tally.standing(["none", "none"]) == "new"
    assert tally.standing(["strong", "strong", "skip"]) == "skipped"
    assert tally.standing(["passed", "weak", "passed"]) == "skipped"
    assert tally.standing(["weak", "weak", "strong"]) == "engaged"
    assert tally.standing(["strong", "passed", "weak"]) == "cooling"
    assert tally.standing(["skip", "weak", "weak", "weak"]) == "neutral"


def test_run_fills_the_empty_tables(tmp_path, monkeypatch, capsys):
    prefs = tmp_path / "preferences.md"
    prefs.write_text((SKILL / "state" / "preferences.md").read_text())
    editions = tmp_path / "editions"
    editions.mkdir()
    editions.joinpath("2026-11-23.json").write_text(json.dumps({"edition": "2026-11-23", "sections": [
        {"id": "world", "stories": [
            {"id": "a", "tags": ["eu-politics"], "angle": "policy", "headline": "A"},
            {"id": "b", "tags": ["economy"], "angle": "markets", "headline": "B"}]}]}))
    taps = tmp_path / "taps"
    taps.mkdir()
    taps.joinpath("1.json").write_text(json.dumps({"data": {"edition": "2026-11-23", "story": "a", "liked": True}}))
    monkeypatch.setattr(tally, "PREFS", prefs)
    monkeypatch.setattr(tally, "EDITIONS", editions)
    monkeypatch.setattr("sys.argv", ["tally.py", str(taps), "--today", "2026-11-24"])

    assert tally.main() == 0
    text = prefs.read_text()
    assert "| eu-politics | 1 | 1 | 0 | 0 | 1 |" in text and "| engaged |" in text
    assert "| economy |" in text and "| cooling |" in text  # passed over once in an edition the reader used
    out = capsys.readouterr().out
    assert "2026-11-23 | a | eu-politics | A" in out

    # running twice changes nothing
    tally.main()
    assert prefs.read_text() == text


def test_pieces_count_as_essays_and_are_listed_once_shown(tmp_path, monkeypatch, capsys):
    prefs = tmp_path / "preferences.md"
    prefs.write_text((SKILL / "state" / "preferences.md").read_text())
    editions = tmp_path / "editions"
    editions.mkdir()
    editions.joinpath("2026-11-23.json").write_text(json.dumps({"edition": "2026-11-23", "sections": [
        {"id": "world", "stories": [{"id": "a", "tags": ["eu-politics"], "angle": "policy", "headline": "A"}]}],
        "reads": [{"id": "read-x", "voice": "x", "url": "https://example.org/essay", "title": "An essay", "tags": ["reads-x"]}]}))
    taps = tmp_path / "taps"
    taps.mkdir()
    taps.joinpath("1.json").write_text(json.dumps({"data": {"edition": "2026-11-23", "story": "read-x", "liked": True}}))
    monkeypatch.setattr(tally, "PREFS", prefs)
    monkeypatch.setattr(tally, "EDITIONS", editions)
    monkeypatch.setattr("sys.argv", ["tally.py", str(taps), "--today", "2026-11-24"])
    assert tally.main() == 0
    text = prefs.read_text()
    assert "| reads-x |" in text and "| essay |" in text
    out = capsys.readouterr().out
    assert "2026-11-23 | x | https://example.org/essay | An essay" in out
    assert "last edition that carried the section: 2026-11-23" in out
