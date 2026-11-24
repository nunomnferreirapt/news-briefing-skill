import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skill" / "news-briefing"
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "2026-11-23.json"
sys.path.insert(0, str(SKILL))
