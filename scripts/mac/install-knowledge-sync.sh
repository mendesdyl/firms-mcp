#!/usr/bin/env bash
# Schedule the weekly FIRMS FAQ sync on this Mac (a per-user LaunchAgent; no admin rights).
#
#   scripts/mac/install-knowledge-sync.sh              install: Mondays 09:00 local time
#   scripts/mac/install-knowledge-sync.sh --uninstall  stop the weekly sync and remove it
#
# The runner is copied to ~/Library/Application Support/firms-mcp/, so it keeps working
# whatever branch the checkout is on; it always syncs from origin/main. If the Mac is asleep
# at 09:00, macOS runs it when the Mac wakes. Log: ~/Library/Logs/firms-mcp/knowledge-sync.log.
set -euo pipefail

LABEL="io.github.mendesdyl.firms-mcp.knowledge-sync"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
HOME_DIR="$HOME/Library/Application Support/firms-mcp"
LOG_DIR="$HOME/Library/Logs/firms-mcp"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

if [ "${1:-}" = "--uninstall" ]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST" "$HOME_DIR/knowledge-sync.sh"
  echo "Weekly FIRMS FAQ sync removed."
  exit 0
fi

mkdir -p "$HOME_DIR" "$LOG_DIR" "$(dirname "$PLIST")"
install -m 0755 "$REPO/scripts/mac/knowledge-sync.sh" "$HOME_DIR/knowledge-sync.sh"
PATH_FOR_JOB="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$HOME_DIR/knowledge-sync.sh</string></array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>FIRMS_MCP_REPO</key><string>$REPO</string>
    <key>PATH</key><string>$PATH_FOR_JOB</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$LOG_DIR/knowledge-sync.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/knowledge-sync.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Weekly FIRMS FAQ sync installed: Mondays 09:00 local time, syncing $REPO from origin/main."
echo "Run it now:  launchctl kickstart gui/$(id -u)/$LABEL"
echo "Remove it:   $0 --uninstall"
