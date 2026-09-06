#!/usr/bin/env bash
# Set an issue's `Status` column on a GitHub Projects v2 board.
#
# This exists because a board write cannot be one argv, and a tracker verb is
# one argv. `gh project item-edit` addresses an item by its node id and has no
# by-issue-number form, so the write is two calls: one query that resolves the
# item, project and field ids together with the issue's state and the column it
# is in now, and one mutation that sets the value.
#
# Called as argv tokens from `.agents/trackers/github.json` — never through a
# shell — so the issue key arrives as `$1` rather than inside a command string.
# The numeric check below is not what makes that true; it is what keeps a
# hand-typed `wfctl issue start '$(...)'` from reaching `gh` as an issue number
# and coming back as a confusing API error.
#
# Requires a `gh` token carrying the `project` scope, which `gh auth login` does
# not grant by default: `gh auth refresh -s project`. Without it every call here
# fails with GitHub's scope error, which the hooks swallow — so a board that
# never moves is the symptom to check this against first.
#
# Exit 0 when there was nothing to set: an issue on no board, a board with no
# such column, or a guard below that declined. Non-zero is reserved for a call
# that should have worked and didn't.
set -uo pipefail

issue=${1:-}
status=${2:-}

# `--only-if-open-in <column>` is the teardown direction, and it carries both
# conditions because they answer one question: is this item still where `start`
# left it? An issue whose work merged is closed, and moving it out of `Done`
# would undo the one transition the board gets right on its own; an issue whose
# change is in review has moved on to another column, and dragging it back to a
# backlog reads as work that never began. The pair is checked from the query
# already being made, so neither costs a call.
guard_column=""
if [[ "${3:-}" == "--only-if-open-in" ]]; then
  guard_column=${4:-}
fi

if [[ -z "$issue" || -z "$status" ]]; then
  echo "usage: github-board.sh <issue> <status> [--only-if-open-in <column>]" >&2
  exit 2
fi

if [[ ! "$issue" =~ ^[0-9]+$ ]]; then
  echo "✗ '$issue' is not an issue number" >&2
  exit 2
fi

nwo=$(gh repo view --json owner,name --jq '.owner.login + " " + .name') || exit 1
read -r owner name <<<"$nwo"

# The status name reaches jq through the environment rather than the filter
# text: `gh --jq` takes no `--arg`, and splicing a config value into a jq
# program is the same class of mistake this file avoids with argv.
#
# `first:100` is the connection's own ceiling — 101 is refused with
# EXCESSIVE_PAGINATION — and it is asked for in one page rather than cursored.
# An issue on 101 boards would have its 101st silently missed; cursoring for
# that costs `pageInfo`, an `$endCursor` variable and a `--paginate` loop in a
# file whose whole point is that a board write stays two calls.
#
# `options != null` rather than `field != null`: a `Status` field that is not a
# single select still matches the inline fragment's parent and comes back as
# `{}`, which is not null, and iterating its absent options aborts jq — turning
# an unusual board into the non-zero exit this file promises not to produce.
ids=$(WFCTL_BOARD_STATUS="$status" gh api graphql \
  -f owner="$owner" -f repo="$name" -F num="$issue" \
  -f query='query($owner:String!,$repo:String!,$num:Int!){
    repository(owner:$owner,name:$repo){
      issue(number:$num){
        state
        projectItems(first:100){
          nodes{
            id
            fieldValueByName(name:"Status"){
              ... on ProjectV2ItemFieldSingleSelectValue{ name }
            }
            project{
              id
              field(name:"Status"){
                ... on ProjectV2SingleSelectField{ id options{ id name } }
              }
            }
          }
        }
      }
    }
  }' \
  --jq '.data.repository.issue as $issue
        | $issue.projectItems.nodes[]
        | . as $node
        | select($node.project.field.options != null)
        | $node.project.field.options[]
        | select(.name == env.WFCTL_BOARD_STATUS)
        | [$issue.state, ($node.fieldValueByName.name // ""),
           $node.id, $node.project.id, $node.project.field.id, .id]
        | join("\u001f")'
) || exit 1

if [[ -z "$ids" ]]; then
  echo "ℹ #$issue is on no board carrying a '$status' status — nothing set"
  exit 0
fi

# Unit separator, not a tab. An item on the board with no `Status` set yet — the
# state 21 items on this project were in before it was reconciled by hand, and
# the exact population this script exists to move — makes the second field
# empty. Bash treats tab as IFS *whitespace* and folds a run of it into one
# separator, so `read` would drop that empty field and shift every id one place
# left: the mutation then gets an option id where a project id belongs and
# GitHub answers `Could not resolve to a node with the global id`. A
# non-whitespace IFS character separates exactly once and preserves the gap.
#
# First match wins, and `read` takes the first line on its own. An issue on two
# boards is a shape nobody here has, and picking one silently beats writing to
# both by accident.
IFS=$'\x1f' read -r state current item project field option <<<"$ids"

if [[ -n "$guard_column" ]]; then
  [[ "$state" == "OPEN" ]] || exit 0
  [[ "$current" == "$guard_column" ]] || exit 0
fi

gh api graphql -f project="$project" -f item="$item" -f field="$field" -f option="$option" \
  -f query='mutation($project:ID!,$item:ID!,$field:ID!,$option:String!){
    updateProjectV2ItemFieldValue(input:{
      projectId:$project, itemId:$item, fieldId:$field,
      value:{ singleSelectOptionId:$option }
    }){ projectV2Item{ id } }
  }' >/dev/null || exit 1

echo "✓ #$issue → $status"
