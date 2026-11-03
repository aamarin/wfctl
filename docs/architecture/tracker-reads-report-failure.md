---
status: accepted
diagram: data-flow
governs: session-continuity, trackers
supersedes: backend-tracker-reads-parent-and-change
---

# Every tracker line in the session report gives a reason

## Context

In a worktree, the session-start report shows three things
(`session-report-built-in-code.md`):

1. The branch's issue.
2. The issue's parent epic.
3. The branch's open PR, with whether its checks pass and how many review
   comments are unanswered.

wfctl reads the issue today with `view`, but not the other two.

wfctl calls a PR, a merge request, or a patchset a change, since the tracker
config's `changes` section covers all three. No existing verb reads either
one:

- The issue verbs are `list`, `view`, `close`, `comment`, `create`, `label`,
  `labels`, `fields`, `state`, `start`, and `stop`. None of them returns a
  parent.
- The change verbs are `list`, `view`, and `fields`. Each one takes a change
  id, which a session on a branch with no recorded PR doesn't have.

Each tracker finds a parent and a PR its own way:

- GitHub: a sub-issues API returns an issue's parent, and a PR is found by
  its branch name.
- Jira: a story links to an epic through a field whose name differs between
  projects.
- Gerrit: a patchset belongs to a change, not to a branch.

Some trackers have no parent.

Previously, the report left a line out whenever its lookup gave no answer,
whether the tracker had nothing to report or the lookup failed
(`backend-tracker-reads-parent-and-change.md`). Currently, an agent that sees
no PR line can't tell whether the branch has no PR or the lookup failed or
timed out. If the branch has a PR with failing
checks or unanswered review comments, the agent starts work without knowing
about them. This gap was found in the #432 plan walkthrough.

## Direct baseline

Keep the earlier record's rule: a lookup that fails or times out leaves its
line out, with no notice. This requires no code changes, and the report stays
as short as possible. However, the agent can't tell a failed lookup from
a branch with no PR, or from a tracker that has no such lookup. That's why the
decision below gives every line a reason code.

## Decision

The tracker backend has two new read verbs, and a backend can leave out either
one:

1. `parent` takes an issue id. It prints the parent's id and title, or nothing
   when the issue has no parent.
2. `branch`, in the `changes` section, takes a branch name. It prints the
   branch's open change with its check state and its count of unanswered
   review comments, or nothing when the branch has no open change.

The report always prints all three tracker lines: the issue, the parent, and
the PR. When a lookup returns an answer, the line shows it. Otherwise, the line
shows one of these reason codes:

| Code | Meaning |
| --- | --- |
| `none` | The tracker answered, and there's nothing to show, such as no parent or no open PR. |
| `unsupported` | The tracker backend doesn't implement this lookup. |
| `no-tracker` | The repository has no tracker configured. |
| `bad-config` | The tracker config can't be read, or its entry for this lookup is malformed. |
| `failed` | The lookup exited with an error. |
| `timeout` | The lookup gave no answer within 15 seconds. |
| `not-applicable` | The branch names no issue, such as `main`, so no lookup runs. |

For example, `PR: none` means the branch has no open PR, and `PR: timeout`
means the agent doesn't know yet and should run `wfctl status --session`
again. The JSON report has the same code for each line.

## Owns truth

The backend finds an issue's parent and a branch's open change, in its
tracker's own terms.

wfctl can't compute either one. A parent is a sub-issue link on GitHub and a
project-specific field on Jira. A change is found by branch on GitHub and
by change id on Gerrit, so a Gerrit backend would most likely leave `branch`
out.

wfctl doesn't read any tracker's vocabulary. The `fields` verb returns
attributes under the backend's own key names, and wfctl never reads those
names, on purpose. wfctl draws the same line for whether an issue is open
(`backend-tracker-maps-issue-state.md`).

wfctl assigns the reason code, because the backend can't in two cases:

1. A backend that timed out or crashed can't report its own failure.
2. A backend that isn't configured, or has no such verb, never runs.

wfctl sees the config, the exit code, the output, and the timeout, so it is
the only side that can tell the seven cases apart. The backend's part stays the
same: print an answer, or print nothing and exit 0, which wfctl shows as
`none`.

## Boundary

```mermaid
flowchart LR
    subgraph wfctl["wfctl builds the report"]
        ASKP["asks for the parent of the branch's issue"]
        ASKC["asks for the branch's open change"]
        CONFIG["reads the tracker config"]
        LINE["tracker line: the answer"]
        CODE["tracker line: reason code"]
    end
    subgraph backend["tracker backend"]
        PARENT["parent: id and title, or nothing"]
        CHANGE["branch: open change, check state,<br>unanswered review comments, or nothing"]
    end
    ASKP --> CONFIG
    ASKC --> CONFIG
    CONFIG -- "no-tracker, bad-config, unsupported" --> CODE
    CONFIG --> PARENT
    CONFIG --> CHANGE
    PARENT -- "an answer" --> LINE
    CHANGE -- "an answer" --> LINE
    PARENT -- "nothing: none" --> CODE
    CHANGE -- "nothing: none" --> CODE
    PARENT -- "failed, timeout" --> CODE
    CHANGE -- "failed, timeout" --> CODE
    backend -- "which reason code a line gets" --x CODE
```

The `--x` edge is the decision. The backend reports what its tracker holds, and
wfctl assigns the reason code. wfctl sets `not-applicable` before any lookup
runs, so it isn't drawn.

## Considered

- **Leave a failed lookup out (the direct baseline).** We didn't choose this
  because the agent can't tell a failed lookup from a branch with no PR, and
  misses failing checks and unanswered review comments.
- **Print only `failed`, and leave the other cases out.** We didn't choose
  this because a missing line would still have two meanings. The agent couldn't
  tell "no PR" from "this tracker has no PR lookup", and the user decided that
  no line should be blank. With the decision above, an `unsupported` line
  repeats in every session in that repository, which #434 asks the report to
  avoid. We accept that cost, since the line is one short code that tells the
  user the tracker config needs updating.
- **Print the error text with the failure.** We didn't choose this because the
  error from `gh` or a script can be long or include the full command line.
  The reason code tells the agent what it needs, and rerunning
  `wfctl status --session` shows whether a `failed` or `timeout` persists.
- **Add no verb.** We didn't choose this because a session picking up a
  reviewed branch needs the PR line first.
- **Read the parent and the PR from `fields`.** We didn't choose this because
  `fields` returns the backend's own key names, and wfctl never reads those by
  name. If wfctl guessed at a key, it would treat every backend that names it
  differently as having no parent.
- **Have the skill run `gh` for these two reads.** We didn't choose this
  because it ties a skill every repository installs to one tracker. It also
  moves the rule about what to load back into the skill's instructions, which
  `session-report-built-in-code.md` moves into wfctl.

## Log

- 2026-11-02  proposed    — the #432 plan walkthrough found that a failed lookup reads as "no PR"; revised the same day so every line carries a reason code
- 2026-11-02  accepted    — Andre, #432 session 2026-11-02: 'Nothing should ever be blank, we should have distinct reasoncodes of why it doesn't apply, it failed, or etc.' Accepted after reviewing the seven-code record (5bcbe57).
