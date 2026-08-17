#!/usr/bin/env bash
# Common functions for the speckit runtime scripts.
#
# ADAPTED FOR wfctl: branch → spec-dir resolution is delegated to
# `wfctl feature-paths`, the single source of truth. That honors the active
# tracker's key_pattern (e.g. PFHB-\d+) and an exact `specs/<branch>` match,
# instead of the upstream spec-kit numeric-only `^[0-9]{1,7}-` regex — so
# non-numeric issue keys are not rejected here. Do not reintroduce a branch-key
# regex in this file; change it in wfctl (_paths.resolve_spec_dir) instead.

get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

get_current_branch() {
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then echo "$SPECIFY_FEATURE"; return; fi
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD; return
    fi
    echo "main"
}

has_git() { git rev-parse --show-toplevel >/dev/null 2>&1; }

# Branch validation is owned by wfctl (key_pattern-aware). A missing feature dir
# is caught downstream by check-prerequisites, so this stays permissive: it must
# not reject non-numeric tracker keys.
check_feature_branch() {
    local has_git_repo="$2"
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
    fi
    return 0
}

# Delegate all path resolution to wfctl — the single source of truth for
# branch → spec-dir. Prints eval-able REPO_ROOT/CURRENT_BRANCH/HAS_GIT/
# FEATURE_DIR/FEATURE_SPEC/IMPL_PLAN/TASKS/RESEARCH/DATA_MODEL/QUICKSTART/
# CONTRACTS_DIR assignments.
get_feature_paths() {
    wfctl feature-paths
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
