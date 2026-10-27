#!/bin/sh
# Install (or reinstall) a launchd agent that runs keepalive.py every 2 minutes.
# Extra arguments are passed to keepalive.py, e.g.
#   ./install-launchd.sh --device "My Nest Hub" --start 7 --end 22
# Uninstall: ./install-launchd.sh --uninstall
set -eu

LABEL=com.nullaware.nest-fishtank
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/nest-fishtank.log"
DIR=$(cd "$(dirname "$0")" && pwd)
PY="$(uv tool dir)/catt/bin/python"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--uninstall" ]; then
  rm -f "$PLIST"
  echo "Uninstalled $LABEL"
  exit 0
fi

[ -x "$PY" ] || { echo "catt not installed: run 'uv tool install catt'"; exit 1; }

args=""
for a in "$@"; do args="$args<string>$a</string>"; done

mkdir -p "$(dirname "$PLIST")"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$DIR/keepalive.py</string>$args</array>
  <key>StartInterval</key><integer>120</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
EOF

launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL; log: $LOG"
