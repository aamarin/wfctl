# Session start loads only the branch's own context

Contexts: session-continuity, agent-host, trackers

## Problem Statement

How might `/start-session` give an agent what it needs for this branch's issue, without loading the whole repository's open work every session?

A `/start-session` in this repository costs 19.2k tokens above a 43.8k baseline, measured on `main` at 13216e8 on 2026-11-01. The skill's own instructions are 8.4k of that, and most of the rest is repository-wide context: the open issue list, the open PR list, every accepted record's slug, and `doctor` notices about other issues. In a worktree, the session works on one issue, so most of that context goes unused.

## Recommended Direction

wfctl builds the session-start report, and the skill runs it and reports what it printed. That moves the rule about what to load out of skill prose, where an agent can skip or add a step without anyone seeing, and into code.

The `/start-session` skill runs four commands, in three steps:

1. `wfctl start && wfctl doctor --session`. `start` still refuses or allows the session and claims the branch. `doctor --session` prints the same findings as plain `doctor`, but leaves out the notices about issues claimed by two spec folders unless they name this branch's issue.
2. `wfctl arch context`, since the accepted records bind the session's work.
3. `wfctl status --session`, whatever `doctor` exited with. It prints the pipeline position, the whole handoff, the count of commits the branch is ahead of the trunk, the branch's commits and uncommitted changes, and, on a branch that names an issue, that issue with its description, its parent epic, and the branch's open PR with its check state and unanswered review comments. A request the last handoff left unanswered is still printed in full.

On `main`, where the branch names no issue, each tracker line reads `not-applicable`, and no repository-wide list loads until the conversation asks for one.

The skill keeps the step 8 table that decides between starting work and asking what to work on, with one change. On an issue branch whose handoff names no first action, the agent works out where to start from the commit count, the pipeline position, and the issue, and asks only when they disagree (`session-start-reads-branch-progress.md`). The skill also keeps #679's paragraph about the spec question on an issue branch with no spec folder. The `doctor` repair guidance moves to a reference file beside the skill, which the agent opens only when `doctor` prints something other than a ✓.

## Architecture decisions

- docs/architecture/session-start-reads-branch-progress.md — wfctl builds the session-start report with no repository-wide list, and an issue session with no first action in its handoff starts from the branch's progress. Supersedes `session-report-built-in-code.md`.
- docs/architecture/tracker-reads-report-failure.md — the tracker backend gets optional `parent` and `branch` read verbs, and every tracker line with no answer prints a reason code. Supersedes `backend-tracker-reads-parent-and-change.md`.

## Software design decisions

- docs/architecture/design/432-session-report-is-a-status-flag.md — the report is `wfctl status --session`, not part of `wfctl start` and not a subcommand
- docs/architecture/design/432-doctor-session-scopes-claim-notices.md — `doctor --session` leaves out claim notices for other issues

## Key Assumptions to Validate

- [ ] The new `/start-session` costs materially less than 19.2k tokens above the baseline, in an issue worktree and on `main`. Measure it with the headless `claude -p` run from the handoff, before and after.
- [ ] The step 8 decision lands on the same row as before, from the smaller report, except on an issue branch whose handoff names no first action, where the agent now starts from the branch's progress. Run `/start-session` on an issue branch and on `main`, and compare the row each one names.
- [ ] GitHub's sub-issues API gives an issue's parent in one call. A tracker without an equivalent prints `Parent: unsupported` (`tracker-reads-report-failure.md`).
- [ ] No second view of `status` is coming soon. If one comes, a `status` command group becomes worth its cost.

## MVP Scope

In scope:

1. `wfctl status --session`, with `--json`.
2. The tracker backend's `parent` and `branch` verbs for GitHub. A backend that lacks either verb, or fails on it, prints a reason code on that line.
3. `wfctl doctor --session`.
4. `start-session/SKILL.md` rewritten to run the four commands and keep the step 8 table, with the repair guidance moved to a reference file.
5. The alignment check compares the branch's commits against the branch's own issue, not every open issue.
6. The release note, `changes/432.change.md`.

Out of scope:

1. Changing anything else `/start-session` decides. Apart from the issue-branch change above, the step 8 table, the doctor repair policy, and the freshness rules stay the same.
2. A size limit test on `start-session/SKILL.md`. The spec's 2026-11-02 clarification moved it to #693, which checks every skill's growth instead.

## Not Doing (and Why)

- Putting the report in `wfctl start` — the report has to be re-readable mid-session without claiming the branch again.
- A `wfctl status session` subcommand — there is no second view, and an end-of-session view would exist only for symmetry.
- A ranked repository-wide issue list on `main` (#296) — sessions there are usually exploratory, so a list loaded before anyone asks often goes unused. #296's ranking applies to the on-demand list instead.
- Letting a repo add its own session-start steps — that is #689, and it builds on the command this change adds.
- Quieting `install-skills` output during worktree creation — that is #691. It is a worktree creation cost, not a session start cost.
- Shrinking the per-turn skill reminders — the largest one was the user's own response-shape hook, which was cut to a short digest on 2026-11-02 outside this change.

## Open Questions

None. The size limit test was settled in the spec's 2026-11-02 clarification, which moved it to #693.
