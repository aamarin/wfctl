---
status: proposed
governs: session-continuity
---

# `doctor --session` leaves out claim notices for other issues

## Context

`wfctl doctor` prints a dim notice for every issue number that two spec folders
both claim. This repository has four such issue numbers. Every session start
prints all four notices, 17 lines, though none concern the current branch. #432 counts them as repository-wide context that session
start shouldn't load.

The notices are useful when the user runs `doctor` to check the whole
repository, so they should stay in that run.

## Verified

- `doctor_cmd` (`wfctl/cli.py:8728`) takes no options.
- `_report_double_claimed_keys` (`wfctl/cli.py:8250`) prints one notice per
  `claim_conflicts(repo_root)` entry, and each entry carries its issue key as
  `c.key`. It is called once, at `cli.py:8804`.
- The notices never reach the exit code (docstring at `cli.py:8265`).

## Assumed

- The claim notices are the only `doctor` output that is the same every session
  and unrelated to the branch. If another kind shows up, `--session` leaves it
  out too, filtered by whatever ties it to a branch. A notice with no such tie
  would falsify this, since there would be nothing to filter on.

## Direct baseline

The `/start-session` skill tells the agent to leave the claim notices out of its report unless
they name the branch's issue. `doctor` doesn't change.

## Decision

`wfctl doctor --session` prints a claim notice only when its key is the issue
the branch names. On a branch that names no issue, it prints none. Every other
line and the exit code match plain `doctor`. Plain `wfctl doctor` is unchanged.

The flag is named `--session` to match `wfctl status --session`, since both
flags limit the output to what session start needs.

## Diagram

```
          baseline                          decision

        ┌──────────────┐                  ┌──────────────┐
        │ claim_       │                  │ claim_       │
        │ conflicts    │                  │ conflicts    │
        └──────────────┘                  └──────────────┘
          ▲ calls                           ▲ calls
        ┌─┴────────────┐                  ┌─┴────────────────┐
        │ doctor       │                  │ doctor --session │
        │ prints all 4 │                  │ filters by key   │
        └──────────────┘                  │ (new)            │
          │ read by                         └──────────────────┘
        ┌─▼────────────┐                    │ read by
        │ agent: skill │                  ┌─▼────────────┐
        │ prose drops  │                  │ agent        │
        │ the lines    │                  └──────────────┘
        └──────────────┘
```

Neither graph adds a divider. In the baseline, the lines still reach the
agent's context, so the tokens are spent even though the skill asks the agent
to ignore them. The rule is also only skill prose, and no artifact can confirm
that the agent followed it (`a-rule-is-expressed-as-a-check.md`). In the
decision, wfctl filters with one comparison, and the agent never sees the lines.

## Considered

- **The direct baseline, a skill instruction.** We didn't choose it because the
  lines still reach the agent's context, and that is the cost #432 is cutting.
- **Filter the notices in plain `doctor` whenever the branch names an issue.**
  It needs no flag. We didn't choose it because the user running `doctor` in a
  worktree would lose the repository-wide view without asking to.
- **Move the claim notices into `status --session`.** We didn't choose it
  because they are a `doctor` finding about spec folders, and the session
  report reads the branch and the tracker.

## Consequences

`/start-session` passes `--session` to `doctor`. A claim notice for the
branch's own issue still prints, since that conflict affects which spec folder
the branch resolves to.

## Verification

- A test with two claimed keys where `doctor --session` on a branch naming one
  of them prints only that notice, and plain `doctor` prints both.
- A test that `doctor --session` on `main` prints no claim notice.

## Log

- 2026-11-02  proposed  — #432 level 3: keep doctor's repository-wide notices
  out of session start
