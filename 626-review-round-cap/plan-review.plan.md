# Implementation Plan: wfctl stops a review group after three rounds

**Branch**: `626-review-round-cap` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `626-review-round-cap/spec.md`

## Summary

`wfctl review start <group>` counts the runs a group has started on the branch,
and it refuses to start one past the cap unless the user's sign-off covers
every commit left to review. The cap is `review.rounds` in `wfctl.json`, and the default is 3. wfctl
reads the cap from the trunk's copy, so the agent can't raise its own cap on the
branch. A cap of 0 means no review run starts, and every change needs the user's
sign-off.

Each group now runs once per round. `opening-a-change` no longer tells the
security group to run again over its own fixes, so a group's run count is the
branch's round count. That lets wfctl count rounds from the run records it
already writes, and nothing new is stored.

The code change is small:

1. `_review_config` parses `review.rounds`.
2. `_review` finds the trunk from the default branch, reads the cap from the
   trunk's copy, counts runs, and adds the cap to `start`.
3. The `review start` command prints the warnings, the round in the header,
   and the two new outcomes.

Reviews also stop trusting the branch's own `trunk` setting. wfctl reads the
trunk from `wfctl.json` on the default branch, the one `origin/HEAD` names, and
a branch that names a different trunk gets a warning, not a refusal. Without
this, an agent could point `trunk` at a branch it pushed and raise its own cap.
It also closes a gap that predates the cap, where a changed trunk could hide a
branch's commits from the PR check (R11). The worktree guard's code doesn't
change, since it reads the trunk through `trunk_refs`. The rest of the change
is text in two skills and `AGENTS.md`.

Design records read before this plan (via `reading-design-records`):

```
Design records: none — design.md records no level-3 decision
```

The accepted level-2 records `review-round-count` and `review-round-cap` are
the boundary this plan implements. Both were accepted on 2026-10-25, after
clarify.

`design.md` was written before clarify, and three of its lines are out of date.
It says `review.rounds` must be 1 or more, it gives the warning as "isn't a
number of 1 or more", and its outcome 3 line names the head. `spec.md` and
`contracts/cli.md` override all three: the value is 0 or more, and both lines
are the ones in `contracts/cli.md`. Where
`design.md` and this plan disagree, follow this plan.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer` and `rich` for the CLI, and no new
dependency. `_review_config` and `_review` import neither, since the guard
imports them. `git` runs as a subprocess through `_review._git`.
**Storage**: No new stored state. The cap is read from git, and the count is
read from the run folders under `<state dir>/reviews/<group>/runs/`. See
`data-model.md`.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy`, `uv run wfctl check config`, and the end-to-end check in
`quickstart.md` after `uv run wfctl install-skills --agent claude`.
**Target Platform**: the `wfctl` CLI on macOS and Linux
**Project Type**: CLI
**Performance Goals**: The trunk read adds up to five local git calls to each
`trunk_refs` call, and two more when the branch declares a different trunk.
The cap read adds two more and one directory listing. `review start` makes
three trunk reads (its warning, the cap, and the commit range), so it adds up
to 23 git calls. It runs a few times per branch, so no target is set. `review
start` passes no timeout to its git calls today, and the new calls follow it.
The guard makes one trunk read per group, so it adds up to 21 calls with three
groups, each a few milliseconds under the guard's 5-second timeout (R9).
**Constraints**: The guard path must not import `typer` or `rich`
(`tests/test_guard_entry.py`). Skill source is edited under `wfctl/agents/`,
never under `.agents/` or `.claude/` (`layer-model`). Tests pin `NO_COLOR`.
And a minimal-complexity bias.
**Scale/Scope**: Two modules change (`_review_config.py` and `_review.py`), plus
one command in `cli.py`, two skills, `AGENTS.md`, and a release note.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records `wfctl arch context` prints. Complexity
Tracking records the substitution.

- [x] Validation plan exists: the three commands in `AGENTS.md`'s definition of
      done, `wfctl check config`, the tests listed under Project Structure, and
      the end-to-end check in `quickstart.md`.
- [x] Complexity is justified: no new module, no new stored file, and no new
      hook. The trunk read reuses `trunk_refs` and `_git`, and the count reuses
      the folder rule `latest_run` already applies.
- [x] Ownership is stated:
      1. wfctl counts the rounds a group has run and decides whether another
         may start. The agent shouldn't count, since it's the party looping,
         and a restarted conversation loses its count
         (`review-round-count`).
      2. The trunk holds the cap, and wfctl reads it from there. The branch has
         no say, since the agent writes the branch (`review-round-cap`). That
         includes which branch is the trunk: wfctl reads `trunk` from the
         default branch, so the agent can't point the cap at a branch it
         wrote (R11). Where the clone has no `origin/HEAD`, or doesn't fetch
         every branch, the branch's own setting still decides. That's a known
         limit in the cap record's Consequences.
      3. The user owns the way past the cap, which is the existing sign-off. The
         guard already refuses the sign-off command from an agent.
      4. git owns which commits exist and what the trunk holds. The cap and the
         count are derived from git and the run folders on every call.
- [x] `session-state-is-re-derived`: The count and the cap are read on every
      call and never stored. `run.json` gains no field.
- [x] `review-covers-unreviewed-commits`: Each run still covers every commit
      since the group's last review. Dropping security's extra run changes only
      when security reviews its own fixes, which is its next run, and no commit
      goes unreviewed.
- [x] `a-rule-is-expressed-as-a-check`: The cap was a skill instruction, and
      #622's plan recorded that as a deviation for this issue to close. The run
      records make a violation visible, so the cap is now a check in `review
      start`. This closes the deviation.
- [x] `wfctl-runs-the-verification`: The refusal comes from wfctl's count of the
      run folders, not from the agent's word.
- [x] `knowledge-placement`: `review.rounds` gets a paragraph in `AGENTS.md`
      "Declaring reviewers", since it's guidance for whoever configures a
      repository. The per-round instruction stays in `opening-a-change`.
- [x] `layer-model` and `vendor-upstream-skills`: `opening-a-change` and
      `fanning-out-code-review` are wfctl-owned skills, so they're edited in
      place under `wfctl/agents/skills/`.
- [x] `change-carries-release-note`: `changes/626.addition.md` for the new
      key, and `changes/626.change.md` for the round order and the trunk read
      (R10).

Re-checked after Phase 1: `data-model.md` and `contracts/cli.md` add no stored
value, no hook row, and no dependency. Every gate passes.

## Code changes

### `wfctl/_review_config.py`

1. Add `DEFAULT_ROUNDS = 3`, and add `rounds` to `_REVIEW_KEYS`.
2. Add `parse_rounds(review)`. It returns `(None, None)` when the key is absent,
   `(n, None)` for a valid value, and `(None, problem)` otherwise. A valid value
   is an `int` of 0 or more and not a `bool`. The problem string is
   `review.rounds must be a whole number of 0 or more`.
3. `load` appends `parse_rounds`'s problem to `problems`, so `check config`,
   `review start`, and the guard all report an invalid value on the branch
   (R1, R9).
4. Add `load_rounds(repo_root)`. It returns the working tree's valid value or
   None, and the command uses it only for the mismatch warning.

### `wfctl/_review.py`

1. Extract `_run_numbers(agent_dir, group)` from `latest_run`. `latest_run`
   and the new `runs_started` both call it (R3).
2. Add `_read_config_at(repo_root, ref, timeout)`. It reads `wfctl.json` on a
   ref with `ls-tree` and then `show`, parses it with `json.loads`, and returns
   the object, or None with a reason when there's no file or it isn't a JSON
   object (R2).
3. Add `TrunkRounds` and `trunk_rounds(repo_root, timeout, *, branch)`. It reads
   `wfctl.json` from `trunk_refs(...)[0]` through `_read_config_at`, and it
   returns the cap, the short ref name, and a warning line or None (R2). It
   takes the `review` value itself. When the top level or `review` isn't an
   object, it uses the default with a warning. Otherwise it hands `review` to
   `_review_config.parse_rounds`.
4. Add `ReviewTrunk` and `review_trunk(repo_root, timeout)`. It finds the trunk
   from `wfctl.json` on the default branch, following the five steps and the
   case table in R11, and returns the trunk's name, where it came from, and a
   warning line or None. Step 1 runs `git symbolic-ref --quiet --short` with
   `answers=(0, 1)`, so a missing `origin/HEAD` exits 1 and a git failure
   still raises. With no `origin/HEAD`, or a clone that doesn't fetch every
   branch, it falls back to `_paths.trunk_branch`. A working-tree `trunk` that
   names a branch the clone doesn't have, or isn't a branch name, still
   raises `NoTrunk`, as today, so `review start` and the guard's `_judge`
   agree.
5. `trunk_refs` calls `review_trunk` in place of `_paths.trunk_branch`. Its
   signature doesn't change, and it keeps today's same-name check and
   `NoTrunk`, in that order. On the default-branch path, both messages name
   `wfctl.json on origin/<default>` rather than the working tree's file.
   `_refuse_a_single_branch_clone` runs only on the fallback path, where it
   runs today. The readers that move to the default branch's trunk are the
   ones that go through `trunk_refs`: the cap read, `review start`'s commit
   range, `review sign-off`, and the PR check's `unreviewed`. `_judge`'s own
   same-name check and `main`-checkout rule keep reading
   `_paths.trunk_branch` (R9). Rewrite the `trunk_refs` docstring to say the
   trunk comes from `review_trunk`, and that a declared trunk decides only on
   the fallback path.
6. Extract `_covered_by_sign_off(repo_root, agent_dir, timeout)` from
   `unreviewed`. It returns the signed-off commit, or None, and a function that
   answers, for any commit, whether the sign-off covers it. `unreviewed` uses
   it unchanged (R4).
7. Add `RoundCapReached(ReviewError)`, with the three message forms in R6.
8. `start` gains `cap: int`. After the empty-range return, it counts the runs
   started. At or past the cap, it checks whether the sign-off covers every
   commit in the group's range, which is the check `unreviewed` makes. If it
   does, `start` returns a `Started` whose `sign_off` is the signed-off commit.
   Otherwise it raises `RoundCapReached`. Under the cap, it writes the run as
   today (R4). The check isn't whether the sign-off covers the head, because a
   clean merge of the trunk after a sign-off makes a head that `commit_range`
   leaves out. The guard would allow that PR, so `review start` has to as
   well.
9. `Started` gains `rounds: int` and `sign_off: str | None`. `rounds` is the
   number of runs the group had started before this call, on every outcome.
   `sign_off` is set only on outcome 3. Every existing construction passes
   them.

### `wfctl/cli.py`, `review_start_cmd`

1. After the groups load, call `review_trunk` and print its warning. Then call
   `trunk_rounds` and print its warning, and compare the result with
   `load_rounds` and print the mismatch warning. A `ReviewError` from either
   call prints `✗` and the message on one line, and exits 1 (R5). Both get
   `timeout=None`, the same as `_review.start` gets today.
2. Pass `cap=` to `_review.start`.
3. Catch `RoundCapReached` before `ReviewError`. Print `✗ <message>` and the
   sign-off line, then exit 1.
4. Check `started.sign_off` before the existing `started.run is None` check,
   since outcome 3 also returns a `Started` with no run. When it's set, print
   the outcome 3 line from `contracts/cli.md`, using `started.rounds`, the cap,
   and the signed-off commit, and return.
5. Add ` · round {started.rounds + 1} of {cap}` to the header.
6. Update the docstring to say the command refuses a run past `review.rounds`.

## What the skill and doc rewrites say

### `opening-a-change` Step 1 (lines 73 - 89)

The paragraph that starts **wfctl refuses the PR until every group has reviewed
the newest commit** keeps its first two sentences. The rest says each group runs
once per round, in order. A fix the code group commits is reviewed by security in
its next run, along with security's own fixes. Security doesn't run again before
code starts.

The paragraph that starts **Stop after three complete rounds** becomes:
**wfctl stops a group after the repository's round cap.** `wfctl review start`
counts each group's runs on the branch and refuses one past `review.rounds`,
which is 3 by default. When it refuses, the agent stops, shows the user the
commits the guard lists, and asks them to run `wfctl review sign-off` in their
own terminal or to say how they want to proceed. The agent shouldn't start
another round or sign off itself. The sentence about #626 goes.

### `opening-a-change`, the guard-refusal bullet (line 375)

"After three complete rounds, ask the person for a sign-off, as Step 1 says"
becomes "If `review start` refuses a group at the round cap, ask the user for a
sign-off, as Step 1 says."

### `fanning-out-code-review` Step 1 (line 82 and the paragraph after it)

The example header becomes
`security run 003 · round 3 of 3 · 2 commits since a1b2c3d · head 9f8e7d6`.
After the up-to-date sentence, two sentences are added:

1. When a sign-off covers every commit left at the cap, `review start` says nothing is
   left to review and exits 0. Go on to the next group.
2. When it refuses at the cap, stop and follow `opening-a-change` Step 1, which
   asks the user for a sign-off.

### `AGENTS.md` "Declaring reviewers"

A new paragraph after the one on reviewer IDs:

> `review.rounds` caps how many times each group runs on one branch, and the
> default is 3. `wfctl review start` refuses a run past the cap until the user
> signs off. A cap of 0 means no review runs, so every change needs a sign-off.
> wfctl reads the value from the trunk's `wfctl.json`, not the branch's, since
> the agent can edit the branch. Raising the cap is a change merged to the
> trunk, and `review start` warns when a branch sets a different value.
>
> For the same reason, reviews read `trunk` from `wfctl.json` on the default
> branch, the one `origin/HEAD` names, and not from the branch. If your trunk
> isn't your default branch, such as `develop`, declare it in the default
> branch's `wfctl.json`. Until you do, reviews measure against the default
> branch, and `review start` warns on every branch that declares something
> else.

## Project Structure

### Documentation (this feature)

```text
626-review-round-cap/
├── plan.md              # This file
├── research.md          # Phase 0: decisions this plan settled
├── data-model.md        # Phase 1: derived values and the four outcomes
├── quickstart.md        # Phase 1: the end-to-end check
├── contracts/
│   └── cli.md           # every line review start prints
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
wfctl/
├── _review_config.py    # DEFAULT_ROUNDS, rounds in _REVIEW_KEYS,
│                        #   parse_rounds, load_rounds
├── _review.py           # _run_numbers, runs_started, _read_config_at,
│                        #   TrunkRounds, trunk_rounds, ReviewTrunk,
│                        #   review_trunk, trunk_refs calls review_trunk,
│                        #   _covered_by_sign_off, RoundCapReached,
│                        #   start(cap=...), Started fields
├── cli.py               # review_start_cmd: warnings, header, outcomes 3 and 4
└── agents/skills/
    ├── opening-a-change/SKILL.md          # Step 1 and the refusal bullet
    └── fanning-out-code-review/SKILL.md   # header example and two sentences

AGENTS.md                # "Declaring reviewers": review.rounds, and trunk
                         #   read from the default branch
changes/626.addition.md  # release note: review.rounds and the refusal
changes/626.change.md    # release note: one run per group per round, and
                         #   trunk read from the default branch, including
                         #   that a trunk other than the default branch is
                         #   declared there
docs/architecture/design/642-commit-range-takes-judged-branch.md
docs/architecture/design/642-origin-head-trusted-on-full-fetch.md
                         # a Log line in each: #626 moved trunk resolution
                         #   for reviews into review_trunk

tests/
├── test_review_config.py  # parse_rounds: absent, 0, 3, -1, 1.5, "3", true;
│                          #   load reports the problem; load_rounds
├── test_review.py         # runs_started skips a folder with no run.json;
│                          #   start's order (up to date at the cap);
│                          #   outcomes 3 and 4; a sign-off on an older commit;
│                          #   a clean trunk merge after the sign-off gives
│                          #   outcome 3; a count above a lowered cap; a cap
│                          #   of 0; trunk_rounds for no file, no key, valid,
│                          #   invalid, bad JSON, a review that isn't an
│                          #   object, and a stale origin/main; review_trunk
│                          #   for every row of R11's case table, including
│                          #   a branch that names another trunk (the range
│                          #   and cap still come from the default branch's
│                          #   trunk), develop declared on the default branch,
│                          #   develop declared only on the branch, no
│                          #   origin/HEAD (falls back to the branch's
│                          #   setting), origin/HEAD naming a missing ref,
│                          #   a default-branch trunk the clone lacks, and
│                          #   symbolic-ref telling no origin/HEAD apart from
│                          #   a git failure;
│                          #   test_range_with_no_trunk_branch_names_the_trunk_key
│                          #   keeps passing unchanged, since a branch trunk
│                          #   the clone lacks still raises NoTrunk
├── test_review_cli.py     # every line in contracts/cli.md, with exit codes;
│                          #   test_start_with_no_trunk_branch_names_the_trunk_key
│                          #   keeps passing unchanged, for the same reason;
│                          #   the header test updated for the round;
│                          #   review sign-off succeeds on a branch that
│                          #   names another trunk;
│                          #   test_start_refuses_a_trunk_that_is_the_branch_under_review
│                          #   drops origin/HEAD, the layout where the
│                          #   branch's key still decides, and a new test
│                          #   pins the warning and the review against main
│                          #   when origin/HEAD is set
├── test_review_gate.py    # an invalid branch rounds fails the guard the way
│                          #   any other invalid review setting does; a branch
│                          #   that names another trunk still has its own
│                          #   commits counted as unreviewed; the main
│                          #   checkout still merges a reviewed branch with
│                          #   origin/HEAD set;
│                          #   test_no_trunk_branch_gives_the_error_refusal
│                          #   keeps passing unchanged
├── test_opening_a_change_panel.py  # rewrite
│                          #   test_the_panel_step_stops_after_three_rounds_to_ask_for_a_sign_off
│                          #   for FR-013: Step 1 names the round cap, runs
│                          #   each group once per round, and drops the #626
│                          #   sentence
└── test_review_fanout_skill.py  # FR-014: the example header carries the round,
                                 #   and the two new sentences for outcomes 3
                                 #   and 4
```

**Structure Decision**: No new module. The cap's parser goes in
`_review_config`, since it's the one reader of the `review` key. The trunk read
and the count go in `_review`, beside `trunk_refs` and `latest_run`, which they
reuse.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution, so the gates come from `AGENTS.md` and the accepted records | The repository records its constraints as architecture records | Borrowing another project's constitution would make the gates false |
