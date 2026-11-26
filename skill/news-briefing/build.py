"""Build the briefing page from one edition file.

Usage: python3 -I build.py state/editions/2026-11-24.json
Writes site/briefing.html and site/thumbs/, plus site/files.json: the `files` map to
pass to the Artifact publish, its sources relative to this folder (publish with
`root` set to this folder). The nightly run builds site/ and stops; the next run at the
keyboard publishes it. Thumbnails: for every story whose
photo is {"page": <url>, "credit": ...}, take the page's og:image, shrink it to
640 px wide (with macOS sips when present; elsewhere the
original image is kept), and publish it as a file beside the page (artifact
pages cannot load images from other sites). A failed fetch drops the thumbnail and
is reported; it never stops the build. For each "Worth reading" or "Career reading"
piece it looks for the quote, word for word, in out/reads/<id>.txt (the text saved by
the run that read the piece) and prints a SCHEMA line when it is not there.
Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache" / "thumbs"
SITE = HERE / "site"
READS = HERE / "out" / "reads"
OUT = SITE / "briefing.html"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
MAX_BYTES = 8_000_000


def fetch(url: str, limit: int = MAX_BYTES) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,nl,pt"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(limit)


def og_image(page_url: str) -> str | None:
    html = fetch(page_url, 2_000_000).decode("utf-8", "replace")
    for tag in re.findall(r"<meta[^>]+>", html, flags=re.I):
        if re.search(r'(property|name)=["\'](og:image|twitter:image)["\']', tag, flags=re.I):
            m = re.search(r'content=["\']([^"\']+)["\']', tag, flags=re.I)
            if m:
                src = m.group(1).replace("&amp;", "&")
                return urllib.parse.urljoin(page_url, src)
    return None


def thumb_file(page_url: str) -> Path:
    """Return the cached, shrunk lead image of the page, fetching it if needed."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(page_url.encode()).hexdigest()[:20]
    cached = CACHE / f"{key}.jpg"
    if not cached.exists():
        img_url = og_image(page_url)
        if not img_url:
            raise ValueError("no og:image on the page")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.write_bytes(fetch(img_url))
            if shutil.which("sips"):
                subprocess.run(
                    ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "62",
                     "--resampleWidth", "640", str(src), "--out", str(cached)],
                    check=True, capture_output=True, timeout=60,
                )
            else:  # no resizer on this machine: keep the image as served
                shutil.copyfile(src, cached)
    return cached


def squash(text: str) -> str:
    """Lower-case, straight quotes, single spaces: so a quote matches whatever the page's typography."""
    for a, b in (("\u2018", "'"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u2013", "-"), ("\u2014", "-"), ("\u00a0", " ")):
        text = text.replace(a, b)
    return " ".join(text.lower().split())


def check_pieces(edition: dict, seen: set[str]) -> list[str]:
    """Checks on the Worth reading and Career reading pieces."""
    problems = []
    for key in ("reads", "career_reading"):
        pieces = edition.get(key) or []
        if key == "reads" and len(pieces) > 3:
            problems.append(f"reads: {len(pieces)} pieces, at most 3")
        voices = [p.get("voice") for p in pieces if not p.get("requested")]
        for v in {v for v in voices if v and v != "other" and voices.count(v) > 1}:
            problems.append(f"{key}: more than one piece by {v}")
        for p in pieces:
            pid = p.get("id", "?")
            if pid in seen:
                problems.append(f"duplicate id {pid}")
            seen.add(pid)
            for field in ("title", "author", "url", "summary", "why_read", "key_takeaway", "takeaways", "quote", "open_if", "tags"):
                if not p.get(field):
                    problems.append(f"{pid}: missing {field}")
            if not 2 <= len(p.get("takeaways") or []) <= 5:
                problems.append(f"{pid}: needs 2 to 5 takeaways")
            if key == "career_reading" and not p.get("for_you"):
                problems.append(f"{pid}: a career piece needs for_you")
            if key == "reads" and p.get("for_you"):
                problems.append(f"{pid}: for_you belongs to career_reading only")
            text = READS / f"{pid}.txt"
            if not text.exists():
                print(f"QUOTE: {pid}: not checked (no {text.relative_to(HERE)}; expected in the run that read the piece)")
            elif p.get("quote") and squash(p["quote"]).strip('"\' ') not in squash(text.read_text()):
                problems.append(f"{pid}: quote not found word for word in {text.relative_to(HERE)}")
    return problems


def check(edition: dict) -> list[str]:
    """Light checks against page/SCHEMA.md; returns problems, never raises."""
    problems = []
    for key in ("edition", "title", "sections", "lead"):
        if key not in edition:
            problems.append(f"missing {key}")
    seen = set()
    for sec in edition.get("sections", []):
        for s in sec.get("stories", []):
            sid = s.get("id", "?")
            if sid in seen:
                problems.append(f"duplicate story id {sid}")
            seen.add(sid)
            for key in ("headline", "summary", "sources", "tags"):
                if not s.get(key):
                    problems.append(f"{sid}: missing {key}")
            split = (s.get("coverage") or {}).get("split")
            if split and not (split.get("a") and split.get("b")):
                problems.append(f"{sid}: split needs a and b")
    problems += check_pieces(edition, seen)
    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    edition = json.loads(path.read_text())
    problems = check(edition)
    for p in problems:
        print("SCHEMA:", p)

    thumbs = 0
    files: dict[str, str] = {}
    if (SITE / "thumbs").exists():
        shutil.rmtree(SITE / "thumbs")
    (SITE / "thumbs").mkdir(parents=True)
    items = [s for sec in edition.get("sections", []) for s in sec.get("stories", [])]
    pieces = (edition.get("reads") or []) + (edition.get("career_reading") or [])
    for p in pieces:  # an essay's cover comes from its own page unless the edition names another
        if not p.get("photo") and p.get("url"):
            p["photo"] = {"page": p["url"], "credit": p.get("outlet")}
    for s in items + pieces:
        ph = s.get("photo") or {}
        if ph.get("page"):
            try:
                rel = f"thumbs/{edition['edition']}__{s['id']}.jpg"
                shutil.copyfile(thumb_file(ph["page"]), SITE / rel)
                ph["src"] = rel
                files[rel] = f"site/{rel}"
                thumbs += 1
            except Exception as e:  # report and carry on without the image
                print(f"PHOTO: {s.get('id')}: dropped ({e})")
                s["photo"] = None
    bare = [s["id"] for s in items + pieces if not (s.get("photo") or {}).get("src")]
    if bare:  # no story without an image
        print("NO IMAGE:", ", ".join(bare), "- find a page with a photo for each before publishing")

    template = (HERE / "page" / "template.html").read_text()
    payload = json.dumps(edition, ensure_ascii=False).replace("</", "<\\/")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(template.replace("__EDITION_JSON__", payload))
    (SITE / "files.json").write_text(json.dumps(files, indent=1))
    size = OUT.stat().st_size
    print(f"BUILT: {OUT} ({size / 1024:.0f} KB, {thumbs} thumbnails, {len(problems)} schema notes)")
    print(f"FILES: {SITE / 'files.json'} ({len(files)} files to publish beside the page)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
