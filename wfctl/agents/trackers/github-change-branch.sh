#!/usr/bin/env bash
# Print a branch's open pull request as one line, or nothing when it has none:
#
#   #712 Session report · checks: failing · 2 unresolved review threads
#
# `wfctl status --session` prints this line under `PR:` and never parses it.
#
# One GraphQL query reads everything the line needs. `gh pr list` would take a
# second call for review threads, since it doesn't return their state. An
# unresolved thread is one whose `isResolved` is false, whether or not anyone
# has replied to it.
#
# GitHub matches a head branch by name alone, so a fork's PR from a branch with
# the same name matches too. `isCrossRepository` drops those. When more than one
# PR is still left, such as two from this branch into different bases, the most
# recently updated one is printed.
#
# `{owner}` and `{repo}` are gh's placeholders, filled from the current
# repository. A non-zero exit is any failure to get an answer, which the report
# prints as `PR: failed`.
set -uo pipefail

branch=${1:-}
if [[ -z "$branch" ]]; then
  echo "usage: github-change-branch.sh <branch>" >&2
  exit 2
fi

query='query($owner: String!, $name: String!, $branch: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(headRefName: $branch, states: OPEN, first: 20,
                 orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        isCrossRepository
        commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
        reviewThreads(first: 100) { nodes { isResolved } }
      }
    }
  }
}'

# The checks word is mapped here rather than in wfctl, which reads no tracker's
# vocabulary (`tracker-reads-report-failure`).
jq_line='
  [.data.repository.pullRequests.nodes[] | select(.isCrossRepository | not)] | first
  | if . == null then empty else
      (.commits.nodes[0].commit.statusCheckRollup.state // "NONE") as $s
      | ({SUCCESS: "passing", FAILURE: "failing", ERROR: "failing",
          PENDING: "pending", EXPECTED: "pending", NONE: "none"}[$s] // ($s | ascii_downcase)) as $checks
      | ([.reviewThreads.nodes[] | select(.isResolved | not)] | length) as $open
      | "#\(.number) \(.title) · checks: \($checks) · \($open) unresolved review thread\(if $open == 1 then "" else "s" end)"
    end'

gh api graphql -F owner='{owner}' -F name='{repo}' -f branch="$branch" \
  -f query="$query" --jq "$jq_line"
