#!/usr/bin/env bash
# Print whether a GitHub issue is open, in wfctl's words: open, closed or missing.
#
# `wfctl start` reads this in a linked worktree and refuses a session on closed
# and missing, so the one mistake this script must not make is a false
# `missing`. That is why it is a script rather than one argv in the config. A
# number GitHub has never issued and a request that never reached GitHub both
# make `gh` exit 1, and only the error text tells them apart: `HTTP 404` against
# `connection refused`. A verb is one argv with no shell, so it cannot read
# stderr. Anything this script cannot positively recognise exits non-zero, which
# wfctl reads as no answer and only warns about.
#
# The REST endpoint rather than `gh issue view`, because `issue view` reports a
# pull request number as an OPEN issue. The issues endpoint answers for pull
# requests too, and marks them with a `pull_request` key, which is mapped to
# `missing` here: a branch named for a pull request names no issue.
#
# `{owner}/{repo}` is gh's own placeholder, filled from the current repository.
# In the config's argv it would be read as wfctl's, and rejected as unknown.
#
# On a failed call `gh api` prints the JSON error body to stdout as well as the
# status to stderr, so stdout is discarded unless the call succeeded.
set -uo pipefail

id=${1:-}
if [[ -z "$id" ]]; then
  echo "usage: github-issue-state.sh <issue-number>" >&2
  exit 2
fi

err=$(mktemp)
trap 'rm -f "$err"' EXIT

if out=$(gh api "repos/{owner}/{repo}/issues/$id" \
      --jq 'if .pull_request then "missing" else .state end' 2>"$err"); then
  echo "$out"
  exit 0
fi

# 410 is an issue that existed and was deleted. Neither status alone proves the
# issue is missing, though: GitHub also answers 404 for a repository the token
# cannot see (the wrong `gh auth` account, a fine-grained token never granted
# this repo), and 410 for a repository with issues turned off. Printing
# `missing` in either of those cases would refuse every worktree on this
# repository, open issues included — the one mistake this script must not
# make. So a 404/410 on the issue is confirmed against the repository itself
# before it is trusted: readable, with issues on.
if grep -qE 'HTTP (404|410)' "$err"; then
  if repo=$(gh api "repos/{owner}/{repo}" --jq '.has_issues' 2>/dev/null) && [[ "$repo" == "true" ]]; then
    echo "missing"
    exit 0
  fi
  echo "repository is not readable, or has issues turned off" >&2
  exit 1
fi

cat "$err" >&2
exit 1
