#!/bin/zsh
# Remove the nightly launchd job that news-briefing-nightly-install set up for the project folder it is
# run from. The briefing itself stays.
set -eu
PROJECT="$PWD"
LABEL="local.news-briefing.$(basename "$PROJECT" | tr -c 'A-Za-z0-9\n' '-')"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2> /dev/null && echo "Stopped $LABEL." || echo "$LABEL was not loaded."
[[ -f "$PLIST" ]] && rm "$PLIST" && echo "Removed $PLIST."
exit 0
