#!/usr/bin/env bash
# Set an issue's `Status` column on a GitHub Projects v2 board.
#
# This exists because a board write cannot be one argv, and a tracker verb is
# one argv. `gh project item-edit` addresses an item by its node id and has no
# by-issue-number form, so the write is two calls: one query that resolves the
# item, project, field and option ids together, one mutation that sets the
# value. The query does all four at once rather than the three `gh project`
# subcommands the same job takes from the outside.
#
# Called as argv tokens from `.agents/trackers/github.json` — never through a
# shell — so the issue key arrives as `$1` rather than interpolated into a
# command string. The numeric check below is what makes that true of this file
# too, since everything under it does interpolate.
#
# Exit 0 when there was nothing to set: an issue on no board, or a board with no
# such column, is the ordinary state of a repo that keeps a curated board, not a
# failure. Non-zero is reserved for a call that should have worked and didn't.
set -uo pipefail

issue=${1:-}
status=${2:-}
guard=${3:-}

if [[ -z "$issue" || -z "$status" ]]; then
  echo "usage: github-board.sh <issue-number> <status-name> [--if-open]" >&2
  exit 2
fi

if [[ ! "$issue" =~ ^[0-9]+$ ]]; then
  echo "✗ '$issue' is not an issue number" >&2
  exit 2
fi

# `--if-open` exists for the teardown direction. A worktree removed after its
# work merged leaves the issue closed, and moving a closed issue back to a
# backlog column would undo the one transition the board still gets right.
#
# ponytail: an open issue whose PR is already in review reads as not-started
# after this. Narrow the guard to "open and no linked PR" if that shows up; it
# costs another call to find out, and a stale `Todo` is cheaper than the column
# this replaces.
if [[ "$guard" == "--if-open" ]]; then
  state=$(gh issue view "$issue" --json state --jq .state 2>/dev/null) || exit 0
  [[ "$state" == "OPEN" ]] || exit 0
fi

nwo=$(gh repo view --json owner,name --jq '.owner.login + " " + .name') || exit 1
read -r owner name <<<"$nwo"

# The status name reaches jq through the environment rather than the filter
# text: `gh --jq` takes no `--arg`, and splicing a config value into a jq
# program is the same class of mistake this file avoids with argv.
ids=$(WFCTL_BOARD_STATUS="$status" gh api graphql \
  -f owner="$owner" -f repo="$name" -F num="$issue" \
  -f query='query($owner:String!,$repo:String!,$num:Int!){
    repository(owner:$owner,name:$repo){
      issue(number:$num){
        projectItems(first:10){
          nodes{
            id
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
  --jq '.data.repository.issue.projectItems.nodes[]
        | select(.project.field != null)
        | . as $node
        | .project.field.options[]
        | select(.name == env.WFCTL_BOARD_STATUS)
        | "\($node.id) \($node.project.id) \($node.project.field.id) \(.id)"'
) || exit 1

if [[ -z "$ids" ]]; then
  echo "ℹ #$issue is on no board carrying a '$status' status — nothing set"
  exit 0
fi

# First match wins. An issue on two boards is a shape nobody here has, and
# picking one silently beats writing to both by accident.
read -r item project field option <<<"$(head -n 1 <<<"$ids")"

gh api graphql -f project="$project" -f item="$item" -f field="$field" -f option="$option" \
  -f query='mutation($project:ID!,$item:ID!,$field:ID!,$option:String!){
    updateProjectV2ItemFieldValue(input:{
      projectId:$project, itemId:$item, fieldId:$field,
      value:{ singleSelectOptionId:$option }
    }){ projectV2Item{ id } }
  }' >/dev/null || exit 1

echo "✓ #$issue → $status"
