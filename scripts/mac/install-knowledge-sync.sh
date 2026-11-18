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

# Prerequisites (Operations §4.2): stop with a clear message rather than install a job that
# fails every Monday.
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
problems=()
command -v node >/dev/null || problems+=("Node.js 24 or later is not installed (brew install node).")
if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 24 ]; then
  problems+=("Node.js $(node -v) is too old; version 24 or later is needed.")
fi
command -v gh >/dev/null || problems+=("The GitHub CLI is not installed (brew install gh).")
command -v gh >/dev/null && ! gh auth status >/dev/null 2>&1 && problems+=("The GitHub CLI is not signed in (gh auth login).")
git -C "$REPO" ls-remote --exit-code origin main >/dev/null 2>&1 || problems+=("This checkout cannot reach its GitHub remote (check SSH access to origin).")
if [ "$(git -C "$REPO" config --get commit.gpgsign || true)" != "true" ]; then
  problems+=("Commit signing is not on for this checkout; the sync's commits must be signed like every other commit.")
fi
if [ ${#problems[@]} -gt 0 ]; then
  printf 'Not installed:\n'
  printf '  - %s\n' "${problems[@]}"
  exit 1
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
