#!/usr/bin/env bash
# File an issue, then put it on the project board.
#
# This exists because filing and board membership fail for different reasons and
# a caller has to be able to tell them apart. `gh issue create --project` folds
# them into one call and answers with one exit code: it resolves the board title
# before the create mutation but adds the item after it, so a board that
# resolves and then refuses leaves the issue filed, its URL never printed, and
# the command exiting non-zero. An agent reading that as "nothing happened"
# files it again, and the repository ends up with a duplicate plus an orphan
# whose number nobody knows — #232's own failure mode, produced by the fix for
# it. Hence the split below, which is the shape `github-board.sh` already uses
# for the same reason.
#
# So the issue is filed first and its URL printed before anything else can fail.
# Everything after that line is board resolution, and none of it may be reported
# as a filing failure.
#
# Board membership is not decoration here. `opening-a-change` Step 5 makes a
# pull request's membership a step that can be observed as unfinished, and an
# issue had no equivalent at any point in its life; on 2026-09-06 that asymmetry
# had left 23 of 65 open issues off the board (#232). So a board that was named
# and could not be confirmed exits non-zero — the step is unfinished and
# something has to be able to see that — while a board that demonstrably does
# not exist is an ordinary outcome for a repository that has none, reported and
# exited 0. The two are told apart by the lookup and never by matching gh's
# error text, so that a missing `project` scope cannot read as a repository that
# never had a board.
#
# The board defaults to the repository's own name rather than to a literal in
# the config, because the config is package data installed into any repository
# that picks this backend. A literal would name *this* project in *their* file:
# every repository under the same owner would file its issues onto this board,
# since the lookup is owner-scoped and would match. A repository whose board is
# titled something else passes that title as the third argument, the way
# `start`/`stop` pass a column name.
#
# Called as argv tokens from `.agents/trackers/github.json` — never through a
# shell — so a title carrying `$(...)` or quotes reaches `gh` inert.
#
# Requires a `gh` token carrying the `project` scope, which `gh auth login` does
# not grant by default: `gh auth refresh -s project`. Without it the lookup
# fails rather than answering "no board", which is why that case exits non-zero:
# every issue filed would otherwise land off the board quietly, which is the
# thing being fixed.
set -uo pipefail

title=${1:-}
body=${2:-}
board=${3:-}

if [[ -z "$title" ]]; then
  echo "usage: github-issue-create.sh <title> <body> [board]" >&2
  exit 2
fi

url=$(gh issue create --title "$title" --body "$body") || exit 1
echo "$url"

if ! nwo=$(gh repo view --json owner,name --jq '.owner.login + " " + .name'); then
  echo "✗ could not read this repository — $url is on no board" >&2
  exit 1
fi
read -r owner name <<<"$nwo"
board=${board:-$name}

# `--limit 100` because gh's default is 30, and a listing that stops short of
# the board is indistinguishable here from a repository that has none: the issue
# would be filed off the board under a message saying that was deliberate, which
# is #232 with reassuring output. 100 is the same ceiling `github-board.sh`
# argues for, and for the same reason — an owner past it is a shape nobody here
# has, and cursoring for it costs more than the case is worth.
#
# The board title reaches jq through the environment rather than the filter
# text: `gh --jq` takes no `--arg`, and splicing a config value into a jq program
# is the same class of mistake this file avoids with argv.
#
# `first(...)` rather than a list: two projects sharing a title is a shape nobody
# here has, and picking one silently beats adding to both by accident — the same
# call `github-board.sh` makes when an issue is on two boards.
if ! number=$(WFCTL_BOARD="$board" gh project list --owner "$owner" --limit 100 \
      --format json \
      --jq 'first(.projects[] | select(.title == env.WFCTL_BOARD) | .number)'); then
  echo "✗ could not read $owner's projects — $url is on no board" >&2
  exit 1
fi

# Numeric rather than non-empty: a lookup that succeeds and prints nothing —
# `first(...)` over no match, or a `--format json` shape that moved — must fall
# to the no-board branch rather than reach `item-add` as a project number.
if [[ ! "$number" =~ ^[0-9]+$ ]]; then
  echo "ℹ no project titled '$board' — $url is on no board"
  exit 0
fi

if ! gh project item-add "$number" --owner "$owner" --url "$url" >/dev/null; then
  echo "✗ could not add $url to '$board'" >&2
  exit 1
fi

echo "✓ $url → $board"
