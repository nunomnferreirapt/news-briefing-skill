#!/bin/zsh
# Install the nightly run as a macOS launchd job for the project folder it is run from
# (news-briefing-nightly-install, from the project root, the folder that holds news-briefing/).
# It saves the current PATH into the job, because launchd starts jobs with almost no PATH.
# What it does: copies run_nightly.sh into news-briefing/nightly/, writes
# ~/Library/LaunchAgents/<label>.plist and loads it. Nothing else: no sudo, no login item,
# no shell profile change. Undo with news-briefing-nightly-uninstall.
set -eu
PROJECT="$PWD"
TOOL="$PROJECT/news-briefing"
NIGHTLY="$TOOL/nightly"
[[ -f "$TOOL/settings.md" ]] || { echo "No news-briefing/settings.md here: run this from the project folder, after the first /news-briefing." >&2; exit 1; }
mkdir -p "$NIGHTLY"
cp "${0:A:h}/run_nightly.sh" "$NIGHTLY/run_nightly.sh"
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
echo "Remove it:  news-briefing-nightly-uninstall (from $PROJECT)"
