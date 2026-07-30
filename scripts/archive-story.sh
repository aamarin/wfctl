#!/usr/bin/env bash
# Archive a story's speckit artifacts before its worktree is deleted.
#
# specs/ and .agent/ are gitignored — deliberately, so the implementation is
# what ships and the repo doesn't accumulate every spec/plan/tasks tree. The
# consequence is that `workmux remove` destroys them. This copies them into
# wfctl's per-branch state dir, which already holds current.md and
# session-summary.md and outlives the worktree.
#
# Files are flattened and numbered in pipeline order, so the archive reads as
# the story of the branch rather than as a directory to dig through.
#
# Usage: scripts/archive-story.sh [worktree_path] [handle]
# Defaults come from workmux's pre_remove env, then from git.
set -uo pipefail

WORKTREE="${1:-${WM_WORKTREE_PATH:-$(git rev-parse --show-toplevel 2>/dev/null)}}"
HANDLE="${2:-${WM_HANDLE:-$(basename "$WORKTREE")}}"

[ -d "$WORKTREE" ] || { echo "⚠ no worktree at '$WORKTREE'" >&2; exit 0; }

DEST=$(cd "$WORKTREE" && wfctl state-dir 2>/dev/null)
[ -n "$DEST" ] || { echo "⚠ could not resolve state dir — nothing archived" >&2; exit 0; }
ARCHIVE="$DEST/archive"

SPECS="$WORKTREE/specs/$HANDLE"
DESIGN="$WORKTREE/.agent/spec.md"

if [ ! -d "$SPECS" ] && [ ! -f "$DESIGN" ]; then
    echo "ℹ no speckit artifacts for '$HANDLE' — nothing to archive"
    exit 0
fi

# A re-archive of the same branch should refresh, not accumulate. Any previous
# run is moved aside rather than deleted, so nothing is ever lost to a rerun.
if [ -d "$ARCHIVE" ]; then
    mv "$ARCHIVE" "$ARCHIVE-$(date -u +%Y%m%dT%H%M%SZ)"
fi
mkdir -p "$ARCHIVE"

# source path (relative to the worktree) -> archived name, in pipeline order.
copy() {
    local src="$1" dst="$2"
    [ -e "$WORKTREE/$src" ] || return 0
    cp -R "$WORKTREE/$src" "$ARCHIVE/$dst"
    echo "$dst|$src"
}

MAP=$(
    copy ".agent/spec.md"                       "1-design.md"
    copy "specs/$HANDLE/spec.md"                "2-spec.md"
    copy "specs/$HANDLE/checklists/requirements.md" "3-requirements-checklist.md"
    copy "specs/$HANDLE/plan.md"                "4-plan.md"
    copy "specs/$HANDLE/research.md"            "5-research.md"
    copy "specs/$HANDLE/data-model.md"          "6-data-model.md"
    copy "specs/$HANDLE/contracts/cli.md"       "7-contract-cli.md"
    copy "specs/$HANDLE/quickstart.md"          "8-quickstart.md"
    copy "specs/$HANDLE/tasks.md"               "9-tasks.md"
    copy "specs/$HANDLE/delivery.md"            "10-delivery.md"
    copy "specs/$HANDLE/checklists/analysis-report.md" "11-analysis-report.md"
)

# Anything the map didn't name still gets archived, so a new speckit artifact
# is never silently dropped just because this script hasn't heard of it.
if [ -d "$SPECS" ]; then
    while IFS= read -r extra; do
        rel="${extra#"$WORKTREE"/}"
        case "$MAP" in *"|$rel"*) continue ;; esac
        mkdir -p "$ARCHIVE/extra/$(dirname "${rel#specs/"$HANDLE"/}")"
        cp "$extra" "$ARCHIVE/extra/${rel#specs/"$HANDLE"/}"
        MAP="$MAP
extra/${rel#specs/"$HANDLE"/}|$rel"
    done < <(find "$SPECS" -type f)
fi

BRANCH=$(cd "$WORKTREE" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "$HANDLE")
COMMIT=$(cd "$WORKTREE" && git rev-parse --short HEAD 2>/dev/null || echo unknown)

{
    echo "# Story archive: $HANDLE"
    echo
    echo "| | |"
    echo "|---|---|"
    echo "| Branch | \`$BRANCH\` |"
    echo "| Last commit | \`$COMMIT\` |"
    echo "| Archived | $(date -u +%Y-%m-%dT%H:%M:%SZ) |"
    echo "| Source | \`$WORKTREE\` (removed) |"
    echo
    echo "Speckit artifacts, flattened and numbered in the order the pipeline"
    echo "produced them. Read top to bottom for the full story."
    echo
    echo "| File | Was |"
    echo "|---|---|"
    # No sort: MAP is already in pipeline order (the copy() calls above run in
    # that order, and extras append after). Sorting would be lexicographic, which
    # puts 10-delivery.md and 11-analysis-report.md ahead of 2-spec.md.
    echo "$MAP" | grep -v '^$' | while IFS='|' read -r dst src; do
        echo "| [$dst]($dst) | \`$src\` |"
    done
} > "$ARCHIVE/README.md"

echo "✓ archived $(echo "$MAP" | grep -cv '^$') artifact(s) → $ARCHIVE"
exit 0  # never block worktree removal
