#!/bin/bash
# Run the second editor named in settings.md on one filled prompt and print its answer.
# Usage, from the project folder: news-briefing-second <prompt file> <turns>
# It runs from news-briefing/out/second/, so the other model never sees the rest of the folder.
# Exit 3 means no second editor is set: the skill then carries on with Claude alone.
set -euo pipefail
HERE="${NEWS_BRIEFING_DATA:-$PWD/news-briefing}"
[[ -f "$HERE/settings.md" ]] || { echo "no news-briefing/settings.md here: run from the project folder" >&2; exit 2; }
cmd="$(grep -m1 '^command:' "$HERE/settings.md" | sed 's/^command:[[:space:]]*//' || true)"
if [[ -z "$cmd" ]]; then
  echo "NO SECOND EDITOR: settings.md has no command" >&2
  exit 3
fi
[[ -f "${1:-}" ]] || { echo "usage: second.sh <prompt file> <turns>" >&2; exit 2; }
prompt="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
turns="${2:-3}"
# turns goes into a shell command: a number and nothing else
[[ "$turns" =~ ^[0-9]{1,3}$ ]] || { echo "turns must be a number" >&2; exit 2; }
cmd="${cmd//\{prompt\}/$(printf '%q' "$prompt")}"
cmd="${cmd//\{turns\}/$turns}"
mkdir -p "$HERE/out/second"
cd "$HERE/out/second"
exec /bin/bash -c "$cmd"
