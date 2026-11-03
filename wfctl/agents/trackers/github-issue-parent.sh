#!/usr/bin/env bash
# Print a GitHub issue's parent as one line, `#<number> <title>`, or nothing when
# it has none.
#
# `wfctl status --session` prints this line under `Parent:` and never parses it.
# A script rather than one argv in the config for the reason the state script
# gives: `{owner}/{repo}` is gh's own placeholder, and wfctl would read it as its
# own and reject it.
#
# GitHub answers an issue with no parent with HTTP 404 and the message "No
# parent issue found". It also answers 404 for a repository the token can't
# read, and printing nothing then would report "no parent" for a lookup that
# never reached the issue. So a 404 is read as no parent only when that message
# is present, and anything else exits non-zero, which the report prints as
# `Parent: failed`.
#
# On a failed call `gh api` prints the JSON error body to stdout as well as the
# status to stderr, so both are kept and searched for the message.
set -uo pipefail

id=${1:-}
if [[ -z "$id" ]]; then
  echo "usage: github-issue-parent.sh <issue-number>" >&2
  exit 2
fi

err=$(mktemp)
trap 'rm -f "$err"' EXIT

if out=$(gh api "repos/{owner}/{repo}/issues/$id/parent" \
      --jq '"#\(.number) \(.title)"' 2>"$err"); then
  echo "$out"
  exit 0
fi

if grep -q 'HTTP 404' "$err" && { grep -q 'No parent issue found' "$err" || [[ "$out" == *"No parent issue found"* ]]; }; then
  exit 0
fi

cat "$err" >&2
exit 1
