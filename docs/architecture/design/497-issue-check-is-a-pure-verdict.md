---
status: proposed
---

# The worktree's issue check is a pure verdict over gathered facts, in its own module

## Context

`wfctl start` refuses a linked worktree whose branch names no open issue
(`session-start-worktree-requires-open-issue`), and it asks the tracker through
the `state` verb (`backend-tracker-maps-issue-state`). The check has ten
outcomes: two exemptions, four refusals, two ways to proceed, a warning, and a
proceed with the key checked only. Each has to hold on the first `start` and on
every one after it.

Three things make where the check lives a real choice.

1. Every input is IO: two `git rev-parse` calls, two manifest reads, the key
   pattern, and a subprocess to the tracker. A test of one outcome, written
   against the command, needs a linked worktree fixture and a fake tracker.
2. #493 plans a create command that checks the issue before `wm add`. It asks
   the same question at a different moment, and it has no session to open.
3. `start_cmd` is already 120 lines, most of it the takeover and sitting logic
   that `session-identity-comes-from-the-caller` governs.

## Verified

- `cli.py:316` resolves `branch` and discards the issue key; `cli.py:344`
  returns early on `report.session_started`, so a check placed after it runs
  once per branch.
- `cli.py:337` grants `--auto-approve` before that return, so the check has to
  come before the grant to leave a refused branch unwritten.
- `cli.py:896` and `cli.py:1027`: `resume` and `end` exit 1 on
  `not session_started`, so a refused `start` that appends nothing keeps a fresh
  branch refused by both.
- `_tracker.py:195` `configured_key_pattern` returns None when no tracker is
  recorded, which is the exemption for a repository with no tracker.
- `_tracker.py:307` `_read_verb` already returns the three states the check
  needs: `(None, None)` for a declined verb, `(None, detail)` for no answer, and
  stdout otherwise, with a 15 second timeout.
- `_paths.py:183` `main_checkout` returns None both for the main checkout and
  for a bare layout, so it cannot answer "is this a linked worktree". In this
  worktree `git rev-parse --git-dir` and `--git-common-dir` differ
  (`.git/worktrees/497-…` against `.git`); in the main checkout both print
  `.git`.
- `tests/conftest.py:153` points `WFCTL_REPO_ROOT` at `tmp_path`, while the
  suite itself runs inside a linked worktree. The git calls therefore have to
  run with `cwd=repo_root`, or every test reads as a linked worktree.

## Assumed

- The ten outcomes are the whole set. A new tracker answer or a new exemption
  would falsify it; either is one more row in `decide`, not a new structure.
- #493's create command calls the same verdict. If it lands with a different
  question, such as "does this title already have an issue", the module keeps
  one caller and the split has earned only its testability.

## Direct baseline

The check is inline in `start_cmd`, before the auto-approve grant. It calls
`git rev-parse`, reads both manifests, calls `_read_verb`, prints its line, and
raises `typer.Exit(1)` where it refuses. The tests drive `wfctl start` through
`CliRunner` with a git worktree fixture and a fake tracker script for each
outcome.

## Decision

A new module, `_issue_check`, holds two functions. `gather(repo_root, branch)`
does all the IO and returns a frozen record of facts: linked or not, installed
here, installed in the main checkout, the tracker configured or not, the key,
and the tracker's answer with its detail. `decide(facts)` is pure and returns a
verdict: proceed, warn with a line, or refuse with a line and a remedy.
`start_cmd` calls both, prints the verdict, and exits 1 on a refusal before
anything else in the command runs.

## Diagram

```
          baseline                          decision

stable                                     ┌──────────────┐
                                           │ decide(facts)│  pure
                                           └──────────────┘
                                                  ▲ reads facts
═══ process edge: git, manifests, tracker ════════╪═══════════════════
                                                  │
volatile  ┌───────────┐  calls  ┌────────┐  ┌─────┴─────┐ calls ┌────────┐
          │ start_cmd │───────► │ git,   │  │ gather()  │─────► │ git,   │
          │ decides   │         │ tracker│  └───────────┘       │ tracker│
          │ and prints│         └────────┘        ▲             └────────┘
          └───────────┘                     ┌─────┴─────┐
                                            │ start_cmd │ prints the verdict
                                            └───────────┘
```

The graphs differ in where the decision sits relative to the process edge. In
the baseline the ten outcomes live below it, inside the command, so each one is
tested through git and a subprocess. In the decision they live above it in
`decide`, which a test calls with a literal record of facts, and `gather` is
the one function that needs a fixture. The divider is the process edge the
repository already draws around `_workmux`, whose functions import nothing and
call no subprocess.

## Considered

- **Put the check in `_session`.** It is where the session's other rules live.
  It loses on fit: `_session` reads and writes the event log, and this check
  reads git and the tracker and never touches the log. It would also give
  #493's create command, which opens no session, a reason to import the session
  module.
- **Put the check in `_tracker`.** The tracker call is its most expensive input.
  It loses because `_tracker` runs a backend's commands and holds no opinion
  about worktrees, and "the main checkout is exempt" is not a tracker question.
  `_tracker` does gain `read_state`, beside `read_fields`, which is the part of
  this that belongs there.
- **The baseline.** Equally correct, and shorter by one module. It loses on the
  first pressure in Context: ten outcomes on two paths is twenty command-level
  tests with fixtures, where `decide` tests them as ten calls and the paths are
  covered by two.

## Consequences

`start` gains one function call and one early exit, and its existing logic is
unchanged. A new outcome is a branch in `decide` and a row in its tests. The
failure mode is a fact `gather` computes wrongly, which a pure `decide` cannot
catch; that is what the handful of `gather` tests against a real linked worktree
are for.

## Verification

1. `decide` has one test per outcome, with no git and no subprocess.
2. `gather` is tested against a real linked worktree and against the main
   checkout, which is where the `cwd=repo_root` requirement is pinned.
3. A command-level test runs `wfctl start` twice on a refused branch and sees
   the refusal both times, which is the re-entry path.

## Log

- 2026-09-27  proposed  — the check's ten outcomes needed a home that `start` and #493 can share
