#!/bin/bash
# Install or update the news-briefing skill in a project folder (default: ~/news-briefing).
#   ./install.sh                 install into ~/news-briefing
#   ./install.sh ~/somewhere     install into another folder
# On an update it replaces the skill's steps, scripts, prompts and page, and never touches what is yours:
# news-briefing/settings.md, news-briefing/sources.md and news-briefing/state/.
# It copies files and nothing else: no sudo, no global packages, no scheduled job (see the README for that).
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
SRC="$REPO/skill"
DEST="${1:-$HOME/news-briefing}"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"
if [[ "$DEST" == "$REPO" || "$DEST" == "$REPO"/* ]]; then
  echo "Choose a folder outside this clone (for example ~/news-briefing)." >&2
  exit 1
fi

if [[ -f "$DEST/news-briefing/settings.md" ]]; then
  echo "Updating $DEST (your settings, sources and state are kept)"
  KEEP=1
else
  echo "Installing into $DEST"
  KEEP=0
fi

mkdir -p "$DEST/.claude/skills/news-briefing" "$DEST/news-briefing"
cp "$SRC/.claude/skills/news-briefing/SKILL.md" "$DEST/.claude/skills/news-briefing/SKILL.md"
for item in build.py tally.py check_render.js second.sh page prompts nightly; do
  rm -rf "$DEST/news-briefing/$item"
  cp -R "$SRC/news-briefing/$item" "$DEST/news-briefing/$item"
done
if [[ $KEEP -eq 0 ]]; then
  cp "$SRC/news-briefing/settings.md" "$SRC/news-briefing/sources.md" "$DEST/news-briefing/"
  cp -R "$SRC/news-briefing/state" "$DEST/news-briefing/state"
fi
chmod +x "$DEST/news-briefing/second.sh" "$DEST/news-briefing/nightly/"*.sh

missing=""
command -v claude > /dev/null || missing="$missing claude"
command -v python3 > /dev/null || missing="$missing python3"
command -v node > /dev/null || missing="$missing node"
[[ -z "$missing" ]] || echo "Not found on this PATH:$missing (see Requirements in the README)."
echo "Done. Next: cd $DEST && claude, then type /news-briefing"
