#!/usr/bin/env bash
# File an issue and put it on the project board in the same call.
#
# This exists because `gh issue create --project` cannot be the whole answer on
# its own. It resolves the board *before* creating anything and exits non-zero
# when the title matches nothing, so a shipped config naming a board that a
# repository does not have would lose that repository the ability to file issues
# at all — a worse failure than the gap being closed. The lookup below is what
# lets `--project` be passed only once the board is known to exist.
#
# Board membership is not decoration here. `opening-a-change` Step 5 makes a
# pull request's membership a step that can be observed as unfinished, and an
# issue had no equivalent at any point in its life; on 2026-09-06 that asymmetry
# had left 23 of 65 open issues off the board (#232). So a *named* board that
# refuses the issue is an error and exits non-zero with nothing filed, while
# *no* board is an ordinary outcome, reported and carried past. The two are told
# apart by the lookup and never by matching gh's error text, so that a board
# outage cannot read as a board that was never configured.
#
# Called as argv tokens from `.agents/trackers/github.json` — never through a
# shell — so a title carrying `$(...)` or quotes reaches `gh` inert.
#
# Requires a `gh` token carrying the `project` scope, which `gh auth login` does
# not grant by default: `gh auth refresh -s project`. Without it the lookup
# fails rather than answering "no board", which is why that case gets its own
# line below: the issue is still filed, and the reason it landed nowhere is on
# screen instead of being inferred.
set -uo pipefail

title=${1:-}
body=${2:-}
board=${3:-}

if [[ -z "$title" ]]; then
  echo "usage: github-issue-create.sh <title> <body> [board]" >&2
  exit 2
fi

args=(--title "$title" --body "$body")

if [[ -n "$board" ]]; then
  owner=$(gh repo view --json owner --jq '.owner.login') || exit 1
  # The board title reaches jq through the environment rather than the filter
  # text: `gh --jq` takes no `--arg`, and splicing a config value into a jq
  # program is the same class of mistake this file avoids with argv.
  if ! found=$(WFCTL_BOARD="$board" gh project list --owner "$owner" \
        --format json \
        --jq '[.projects[] | select(.title == env.WFCTL_BOARD)] | length'); then
    echo "ℹ could not read $owner's projects — filing without a board"
  elif [[ "$found" == "0" ]]; then
    echo "ℹ no project titled '$board' — filing without a board"
  else
    args+=(--project "$board")
  fi
fi

gh issue create "${args[@]}"
