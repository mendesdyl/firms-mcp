#!/usr/bin/env bash
# Weekly FIRMS FAQ sync, run from the owner's Mac (ADR-0011 §6; integration issue II-28: the
# FAQ page refuses GitHub's runners with HTTP 403). It does what the Knowledge sync workflow
# did: sync the FAQ and the missing-data table, run every check, and open or update one review
# pull request from the `knowledge-sync` branch. Nothing reaches `main` without the owner's
# review.
#
# It works in its own git worktree made from origin/main, so the owner's checkout (whatever
# branch, whatever uncommitted work) is never touched. The commit is signed like every other
# commit: 1Password asks for approval. If that approval does not come, the run stops, shows a
# notification, and can simply be run again.
#
#   scripts/mac/knowledge-sync.sh            run now
#   scripts/mac/install-knowledge-sync.sh    schedule it weekly (see that file)
set -euo pipefail

REPO="${FIRMS_MCP_REPO:?set FIRMS_MCP_REPO to the firms-mcp checkout}"
WORK="${FIRMS_MCP_SYNC_WORKTREE:-$HOME/Library/Caches/firms-mcp/knowledge-sync}"
BRANCH="knowledge-sync"

notify() {
  osascript -e "display notification \"$1\" with title \"FIRMS FAQ sync\"" >/dev/null 2>&1 || true
  echo "$1"
}
fail() {
  notify "$1"
  exit 1
}

echo "=== $(date -u +%FT%TZ) FIRMS FAQ sync"
cd "$REPO"
git fetch --quiet origin main || fail "Could not reach GitHub (git fetch failed)."
if git worktree list --porcelain | grep -qx "worktree $WORK"; then
  git worktree remove --force "$WORK"
fi
git worktree prune
mkdir -p "$(dirname "$WORK")"
git worktree add --quiet --force -B "$BRANCH" "$WORK" origin/main
cd "$WORK"

npm ci --silent --no-audit --no-fund
npm run --silent knowledge -- sync || fail "Sync refused or failed; nothing was changed. See ~/Library/Logs/firms-mcp/knowledge-sync.log."
missing=success
npm run --silent knowledge -- missing-data || missing=failed

if [ -z "$(git status --porcelain -- knowledge)" ]; then
  echo "No changes to the FAQ or the missing-data table."
  cd "$REPO" && git worktree remove --force "$WORK"
  exit 0
fi

npm run --silent check || fail "Checks failed on the synced content; no pull request opened. See the log."

day=$(date -u +%F)
git add knowledge
git commit --quiet -m "chore(knowledge): FIRMS FAQ sync $day" \
  || fail "Commit not signed (1Password approval needed). Run the sync again when you are at the Mac."
git push --quiet --force -u origin "$BRANCH" || fail "Could not push the $BRANCH branch."

npm run --silent knowledge -- pr-body --missing "$missing" --base origin/main > "$WORK/.pr-body.md"
if gh pr view "$BRANCH" --json state --jq .state 2>/dev/null | grep -q OPEN; then
  gh pr edit "$BRANCH" --title "chore(knowledge): FIRMS FAQ sync $day" --body-file "$WORK/.pr-body.md" >/dev/null
  url=$(gh pr view "$BRANCH" --json url --jq .url)
else
  url=$(gh pr create --base main --head "$BRANCH" --title "chore(knowledge): FIRMS FAQ sync $day" \
    --body-file "$WORK/.pr-body.md")
fi
cd "$REPO" && git worktree remove --force "$WORK"
notify "FIRMS FAQ changed: review pull request ready. $url"
