#!/bin/zsh
# The news briefing, unattended. news-briefing-nightly-install copies this file into the project's
# news-briefing/nightly/ and starts it from launchd at the time in settings.md;
# by hand: `zsh news-briefing/nightly/run_nightly.sh` from the project folder.
# It builds the edition into news-briefing/site/ and stops: a run that launchd starts has no page tools,
# so the next /news-briefing at the keyboard publishes it. Rules for the run: SKILL.md, "Mode: unattended".
# Guards: skips until setup is done or when today's edition exists; a lock so two runs never overlap;
# a cut-off; every failure is one line in news-briefing/state/nightly-runs.md, which the next run reads.
set -u
NIGHTLY="${0:A:h}"
TOOL="${NIGHTLY:h}"
PROJECT="${TOOL:h}"
cd "$PROJECT" || exit 1
mkdir -p "$TOOL/out/second"
LOG="$TOOL/out/nightly.log"
LOCK="$TOOL/out/nightly.lock"
RUNS="$TOOL/state/nightly-runs.md"
TODAY=$(date +%F)
CUTOFF=${NEWS_BRIEFING_CUTOFF:-6600}   # seconds; a run takes 25 to 75 minutes
say() { echo "$(date '+%F %T') $1" >> "$LOG"; }
fail() {
  say "FAIL: $1"
  echo "- $(date '+%F %H:%M') FAIL: $1 (log: news-briefing/out/nightly.log)" >> "$RUNS"
  rm -f "$LOCK"
  exit 1
}

say "start"
if grep -q '^setup: not done' "$TOOL/settings.md"; then
  echo "- $(date '+%F %H:%M') SKIPPED: setup is not done; type /news-briefing once at the keyboard first" >> "$RUNS"
  say "skip: setup not done"; exit 0
fi
command -v claude > /dev/null || fail "claude is not on the PATH launchd gives (run news-briefing-nightly-install again from Claude Code)"
if [[ -f "$LOCK" ]]; then
  OTHER=$(awk '{print $3}' "$LOCK")
  if kill -0 "$OTHER" 2> /dev/null; then say "skip: another run holds the lock ($(cat "$LOCK"))"; exit 0; fi
  say "stale lock removed ($(cat "$LOCK"))"
fi
echo "$(date '+%F %T') $$" > "$LOCK"
trap 'rm -f "$LOCK"' EXIT
if [[ -f "$TOOL/state/editions/$TODAY.json" ]]; then say "skip: edition $TODAY already exists"; exit 0; fi

T="news-briefing"
PROMPT="/news-briefing:news-briefing Unattended run. Today is $TODAY; the edition id is $TODAY. Follow the skill with its section 'Mode: unattended'. Nobody is there to answer a question."

# Only these tools; --permission-mode dontAsk refuses everything else without asking.
# The run reads the open web with nobody watching, so it may read only the briefing folder and the plugin
# (nothing else on the Mac), and write only in state/ and out/: never the
# settings or this runner (deny rules win over allow rules, as a second guard). The scripts it runs are
# the plugin's bin/ commands, which live in Claude Code's plugin cache, outside the project.
caffeinate -i claude -p "$PROMPT" --permission-mode dontAsk --allowedTools \
  "Skill" "ToolSearch" "Agent" "WebSearch" "WebFetch" "TodoWrite" \
  "Read($T/**)" "Read(~/.claude/plugins/**)" \
  "Edit($T/state/**)" "Write($T/state/**)" "Edit($T/out/**)" "Write($T/out/**)" \
  "Bash(news-briefing-tally:*)" "Bash(news-briefing-build:*)" "Bash(news-briefing-render:*)" "Bash(news-briefing-second:*)" \
  "Bash(ls:*)" "Bash(mkdir -p $T/out:*)" \
  --disallowedTools \
  "Edit($T/settings.md)" "Write($T/settings.md)" "Edit($T/sources.md)" "Write($T/sources.md)" \
  "Edit($T/nightly/**)" "Write($T/nightly/**)" "Edit(.claude/**)" "Write(.claude/**)" \
  < /dev/null >> "$LOG" 2>&1 &
PID=$!
( sleep "$CUTOFF"; kill $PID 2> /dev/null ) &
WATCHDOG=$!
wait $PID
RC=$?
kill $WATCHDOG 2> /dev/null

[[ $RC -eq 0 ]] || fail "the run stopped (exit $RC; 143 means the cut-off)"
[[ -f "$TOOL/state/editions/$TODAY.json" ]] || fail "no edition file for $TODAY"
grep -q "\"$TODAY\"" "$TOOL/site/briefing.html" 2> /dev/null || fail "edition $TODAY written but the page was not built (see the log)"
say "done: edition $TODAY built, waiting to be published"
