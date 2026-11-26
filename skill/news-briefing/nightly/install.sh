#!/bin/zsh
# Install the nightly run as a macOS launchd job for this project folder.
# Run it from a terminal where `claude`, `node` and `python3` work: it saves that PATH into the job,
# because launchd starts jobs with almost no PATH.
# What it does: writes ~/Library/LaunchAgents/<label>.plist and loads it. Nothing else: no sudo,
# no login item, no shell profile change. Undo with uninstall.sh.
set -eu
NIGHTLY="${0:A:h}"
TOOL="${NIGHTLY:h}"
PROJECT="${TOOL:h}"
LABEL="local.news-briefing.$(basename "$PROJECT" | tr -c 'A-Za-z0-9\n' '-')"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
TIME=$(grep -m1 '^nightly:' "$TOOL/settings.md" | awk '{print $2}')
TIME=${TIME:-06:00}
HOUR=$((10#${TIME%%:*})); MINUTE=$((10#${TIME##*:}))

for tool in claude node python3; do
  command -v $tool > /dev/null || { echo "$tool is not on this terminal's PATH; install it or open a terminal where it works, then run this again." >&2; exit 1; }
done
grep -q '^setup: not done' "$TOOL/settings.md" && echo "Note: setup is not done yet. Type /news-briefing once in Claude Code first; until then the nightly run skips."

mkdir -p "$HOME/Library/LaunchAgents" "$TOOL/out"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/zsh</string><string>$NIGHTLY/run_nightly.sh</string></array>
  <key>WorkingDirectory</key><string>$PROJECT</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$PATH</string><key>HOME</key><string>$HOME</string></dict>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MINUTE</integer></dict>
  <key>StandardOutPath</key><string>$TOOL/out/launchd.out</string>
  <key>StandardErrorPath</key><string>$TOOL/out/launchd.out</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/$LABEL" 2> /dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL: every day at $(printf '%02d:%02d' $HOUR $MINUTE)."
echo "Check it:   launchctl print gui/$(id -u)/$LABEL | grep -E 'state|last exit'"
echo "Run it now: launchctl kickstart gui/$(id -u)/$LABEL"
echo "Its log:    $TOOL/out/nightly.log"
echo "Remove it:  zsh $NIGHTLY/uninstall.sh"
