#!/bin/zsh
# Remove the nightly launchd job that install.sh set up for this project folder. The briefing itself stays.
set -eu
PROJECT="${${0:A:h}:h:h}"
LABEL="local.news-briefing.$(basename "$PROJECT" | tr -c 'A-Za-z0-9\n' '-')"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2> /dev/null && echo "Stopped $LABEL." || echo "$LABEL was not loaded."
[[ -f "$PLIST" ]] && rm "$PLIST" && echo "Removed $PLIST."
exit 0
