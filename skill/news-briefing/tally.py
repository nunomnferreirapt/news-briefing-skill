"""Fold the reader's taps into the preferences tables, and list recently covered topics.

Usage: python3 -I tally.py <feedback_dir> [--today YYYY-MM-DD]

<feedback_dir> holds the page's saved taps as one JSON file per row, as written by
ArtifactData `list` with `out_dir` (rows may be the bare row or {"id", "data", ...}).

Everything is recomputed from scratch on every run, so running it twice changes nothing.
It walks every story of every edition (an edition with "learn": false is skipped) and
matches it with its saved row, then scores two tables in state/preferences.md:
  Tags    what a story is about (nl-politics, chips ...)
  Angles  what kind of story it is (policy, deal, research ...)

Signals per story, strongest first:
  skipped    the reader tapped Skip
  discussed  they asked a question
  liked      they tapped Like
  dwell      seconds the story stayed open (30 s or more counts as reading)
  read       they tapped Read (alone it is weak: many readers tap it on everything)
  passed     they used that edition (tapped anything in it) but did nothing with this story
An edition they never touched teaches nothing: they were away, not uninterested.

Standing, from the last three stories of that tag or angle in editions they used:
  skipped   a Skip among them, or passed over twice
  cooling   passed over once
  engaged   the most recent one was read for real, liked or discussed, or half of them were
  neutral   otherwise
  new       never shown in an edition they used
Any later read, like or question lifts a tag again, because only the last three count.

"Worth reading" and "Career reading" pieces count like stories: under their voice tag
(reads-mollick ...) and the angle "essay", kept apart from the long view's "analysis".

Prints what changed, the Discuss messages, a long-view pick if any, past long views, the
stories covered in the last seven days (for the variety rule), the pieces already shown
(a piece is never shown twice) and any voice passed over five times running.
Standard library only.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFS = HERE / "state" / "preferences.md"
EDITIONS = HERE / "state" / "editions"
COLS = ["Shown", "Seen", "Opened", "Read", "Liked", "Discussed", "Skipped", "Passed", "Avg s"]
HEAD = ["Key", *COLS, "Last shown", "Standing"]
READ_SECONDS = 30
PICKS: list[tuple] = []


def load_rows(folder: Path) -> dict[tuple[str, str], dict]:
    rows = {}
    for f in sorted(folder.rglob("*.json")):
        try:
            d = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(d.get("data"), dict):
            d = d["data"]
        if d.get("story") == "next-question":
            if d.get("pick"):
                PICKS.append((d.get("updatedAt", ""), d.get("edition", ""), d.get("pick"), d.get("question")))
        elif d.get("edition") and d.get("story"):
            rows[(d["edition"], d["story"])] = d
    return rows


def load_editions() -> list[dict]:
    return [json.loads(f.read_text()) for f in sorted(EDITIONS.glob("*.json"))]


def items(ed: dict):
    """Every story of an edition, the long view and the reading pieces included, as (story_id, tags, angle, headline)."""
    for sec in ed.get("sections", []):
        for s in sec.get("stories", []):
            yield s["id"], s.get("tags", []), s.get("angle"), s.get("headline", "")
    lv = ed.get("long_view")
    if lv:
        yield "long-view", lv.get("tags", []), "analysis", lv.get("title", "")
    for p in pieces(ed):
        yield p["id"], p.get("tags", []), "essay", p.get("title", "")


def pieces(ed: dict) -> list[dict]:
    """The Worth reading and Career reading pieces of an edition."""
    return [*(ed.get("reads") or []), *(ed.get("career_reading") or [])]


def outcome(row: dict | None, used: bool) -> str:
    """What one story taught: skip, strong, weak, passed or none."""
    if not used:
        return "none"
    if not row:
        return "passed"
    if row.get("skipped"):
        return "skip"
    secs = row.get("seconds") or 0
    if row.get("liked") or row.get("discussed") or secs >= READ_SECONDS:
        return "strong"
    if row.get("read") and not secs:
        return "strong"  # a Read from before reading time was recorded
    if row.get("read") or row.get("opened"):
        return "weak"
    return "passed"


def standing(history: list[str]) -> str:
    seen = [h for h in history if h != "none"]
    if not seen:
        return "new"
    last3 = seen[-3:]
    if "skip" in last3 or last3.count("passed") >= 2:
        return "skipped"
    if last3[-1] == "strong" or last3.count("strong") * 2 >= len(last3):
        return "engaged"
    if "passed" in last3:
        return "cooling"
    return "neutral"


def parse_table(text: str, title: str) -> tuple[list[str], dict[str, dict]]:
    m = re.search(rf"## {title}\n(.*?)(?=\n## |\Z)", text, flags=re.S)
    order, table = [], {}
    if not m:
        return order, table
    header = None
    for line in m.group(1).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set(cells[0]) <= {"-"}:
            continue
        order.append(cells[0])
        table[cells[0]] = dict(zip(header, cells))
    return order, table


def render_table(order: list[str], stats: dict[str, dict]) -> list[str]:
    lines = ["| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
    for key in order:
        c = stats[key]
        lines.append(f"| {key} | " + " | ".join(str(c[k]) for k in COLS) + f" | {c['Last shown']} | {c['Standing']} |")
    return lines


def replace_table(text: str, title: str, lines: list[str], intro: str) -> str:
    block = "\n".join(lines) + "\n"
    m = re.search(rf"(## {title}\n)(.*?)(?=\n## |\Z)", text, flags=re.S)
    if not m:
        anchor = "## How the counts steer the next edition"
        return text.replace(anchor, f"## {title}\n\n{intro}\n\n{block}\n{anchor}", 1)
    body = m.group(2)
    table = re.search(r"(?:^\|.*\|\n?)+", body, flags=re.M)
    new_body = body[: table.start()] + block + body[table.end():] if table else body.rstrip("\n") + "\n\n" + block
    return text[: m.start(2)] + new_body + text[m.end(2):]


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    folder = Path(args[0])
    today = dt.date.fromisoformat(args[args.index("--today") + 1]) if "--today" in args else dt.date.today()

    rows = load_rows(folder) if folder.exists() else {}
    eds = load_editions()
    used = {e for (e, _) in rows}

    def blank():
        return {**{k: 0 for k in COLS}, "_secs": [], "_hist": [], "Last shown": ""}

    stats = {"Tags": defaultdict(blank), "Angles": defaultdict(blank)}
    for ed in eds:
        if ed.get("learn") is False:
            continue
        eid = ed["edition"]
        for sid, tags, angle, _ in items(ed):
            row = rows.get((eid, sid))
            out = outcome(row, eid in used)
            keys = [("Tags", t) for t in tags] + ([("Angles", angle)] if angle else [])
            for table, key in keys:
                c = stats[table][key]
                c["Shown"] += 1
                c["Last shown"] = max(c["Last shown"], eid[:10])
                c["_hist"].append(out)
                if eid not in used:
                    continue
                c["Seen"] += 1
                if row:
                    c["Opened"] += 1 if row.get("opened") else 0
                    c["Read"] += 1 if row.get("read") else 0
                    c["Liked"] += 1 if row.get("liked") else 0
                    c["Discussed"] += int(row.get("discussed") or 0)
                    c["Skipped"] += 1 if row.get("skipped") else 0
                    if row.get("seconds"):
                        c["_secs"].append(row["seconds"])
                c["Passed"] += 1 if out == "passed" else 0

    text = PREFS.read_text()
    changes = []
    intros = {
        "Tags": "What a story is about. Counts since the first edition; \"Seen\" counts only editions the reader used.",
        "Angles": "What kind of story it is, across topics: policy, decision, deal, money, markets, conflict, research, people, product, analysis (the long view), essay (Worth reading).",
    }
    for title in ("Tags", "Angles"):
        order, old = parse_table(text, title)
        st = stats[title]
        for key in st:
            if key not in order:
                order.append(key)
        for key in order:
            c = st[key]
            c["Avg s"] = round(sum(c["_secs"]) / len(c["_secs"])) if c["_secs"] else ""
            c["Standing"] = standing(c["_hist"])
            prev = old.get(key)
            if prev is None:
                changes.append(f"{title[:-1].lower()} {key}: new")
                continue
            diffs = [f"{k} {prev.get(k, '')}→{c[k]}" for k in COLS if str(c[k]) != prev.get(k, "")]
            if prev.get("Standing") != c["Standing"]:
                diffs.append(f"standing {prev.get('Standing')}→{c['Standing']}")
            if diffs:
                changes.append(f"{title[:-1].lower()} {key}: " + ", ".join(diffs))
        text = replace_table(text, title, render_table(order, st), intros[title])
    PREFS.write_text(text)

    questions = []
    for (eid, sid), r in sorted(rows.items()):
        for t in r.get("chat") or []:
            if t.get("role") == "user":
                questions.append(f"{eid} {sid}: {t.get('content', '')[:200]}")

    print("== CHANGES ==")
    print("\n".join(changes) or "none")
    print("\n== QUESTIONS ASKED IN DISCUSS ==")
    print("\n".join(questions) or "none")
    print("\n== NEXT LONG VIEW PICKED ==")
    if PICKS:
        _, ed_id, pid, question = sorted(PICKS)[-1]
        print(f"{ed_id} | {pid} | {question}")
    else:
        print("none")
    print("\n== PAST LONG VIEWS ==")
    for ed in eds:
        lv = ed.get("long_view")
        if lv:
            print(f"{ed['edition']} | {lv.get('title', '')} | question: {lv.get('question', '')}")
    print(f"\n== COVERED SINCE {today - dt.timedelta(days=7)} (variety: hold back unless something significant changed) ==")
    for ed in eds:
        if dt.date.fromisoformat(ed["edition"][:10]) >= today - dt.timedelta(days=7):
            for sec in ed.get("sections", []):
                for s in sec.get("stories", []):
                    print(f"{ed['edition']} | {s['id']} | {', '.join(s.get('tags', []))} | {s['headline']}")
                for b in sec.get("briefs", []):
                    print(f"{ed['edition']} | brief | {sec.get('id', '')} | {b.get('text', '')[:140]}")

    print("\n== WORTH READING: PIECES ALREADY SHOWN (never show a URL twice) ==")
    shown = [(ed["edition"], p) for ed in eds for p in pieces(ed)]
    for eid, p in shown:
        print(f"{eid} | {p.get('voice', '')} | {p.get('url', '')} | {p.get('title', '')}")
    if not shown:
        print("none")
    carried = [eid for eid, _ in shown]
    print("last edition that carried the section: " + (carried[-1] if carried else "none, look back 14 days"))

    print("\n== VOICES PASSED OVER FIVE TIMES RUNNING (tell the reader; never drop one on your own) ==")
    quiet = []
    for key, c in stats["Tags"].items():
        seen = [x for x in c["_hist"] if x != "none"]
        if key.startswith("reads-") and key != "reads-requested" and len(seen) >= 5 and all(x in ("passed", "skip") for x in seen[-5:]):
            quiet.append(key)
    print("\n".join(quiet) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
