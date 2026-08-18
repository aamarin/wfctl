# Review: working diff (#31, step-command drift check)

**Target**: `git diff HEAD` — `wfctl/_pipeline.py`, `wfctl/cli.py`,
`tests/test_pipeline_commands.py`
**Date**: 2026-08-17
**Reviewed against**: spec.md FR-001…FR-010, issue #31 and its two comments

## Findings

```
BLOCKER  tests/test_pipeline_commands.py:L138 — the test claiming to stop `cli`
         re-inlining the /end-session literal asserted only that the constants
         contain it, never that `cli` uses the constants. Re-inlining passed
         every test → drive `wfctl next` to a finished pipeline and compare its
         real output against STORY_COMPLETE_FILE / STORY_COMPLETE_CONSOLE
WARNING  wfctl/_pipeline.py:L28 — completion messages built from
         `_LOOSE_COMMANDS[0]`; adding or reordering the tuple silently rewrites
         user-facing text → name the constant `_END_SESSION` and build from it
NIT      wfctl/_pipeline.py:L1 — module docstring said "step inference and
         display"; it now also owns the command inventory → docstring updated
NIT      wfctl/_pipeline.py:L27 — `END_SESSION` public but referenced only
         inside the module → `_END_SESSION`; public surface stays the two
         message constants `cli` imports
NIT      tests/test_pipeline_commands.py:L72 — `cmd.lstrip("/")` strips a
         character class, not a prefix → `cmd.removeprefix("/")`
NIT      tests/test_pipeline_commands.py:L68 — report header read "step commands
         with no shipped file" but can now hold non-step entries → "commands
         wfctl names with no shipped file"
```

All six fixed. `pytest` 403 passed, `mypy` clean, `ruff` clean.

### The blocker, in detail

The test was written to close the gap #31's first comment identified, and its
docstring claimed two halves: that `/end-session` is in the checked inventory,
**and** that `cli` still emits it rather than inlining its own copy.

It only did the first. `assert "/end-session" in STORY_COMPLETE_FILE` tests the
constant, not the caller. Nothing bound `cli.py` to that constant, so a future
edit re-inlining `"Story complete. Open PR or run /end-session.\n"` would have
left all nine tests green — which is precisely the invisible drift this feature
exists to catch, reintroduced by the fix for it.

Verified rather than reasoned: `cli.py` was temporarily edited to emit
`/end-sess`, the suite was run, and the new test failed with

```
assert 'Story complete — open PR or run `/end-session`.' in
       'Story complete — open PR or run `/end-sess`.\n'
```

then reverted. The test now drives the real `next` command through the
`storyctl_dir` fixture to a genuinely complete pipeline and compares stdout and
`next-step.md` against the constants.

## Passes with nothing to report

- **Security** — no user input, no secrets, no network, no subprocess. The only
  I/O is a glob of a directory inside the installed package.
- **Performance** — `next_step_content` went from two dict lookups to one.
  `_named_commands()` rebuilds a 9-entry dict per call, ~5 calls per suite run.
  Immaterial.
- **Architecture** — the merged `_STEPS` table removes a class of state rather
  than guarding it, and `_STEP_NAMES = list(_STEPS)` derives order from the one
  definition. `cli` importing presentation constants from `_pipeline` follows the
  direction dependencies already flow.
- **Over-engineering** — production code is net shorter than before
  (`_pipeline.py` replaced three tables with one). `_LOOSE_COMMANDS` is a
  one-element tuple, which reads speculative but is not: the check iterates it,
  so the next non-step command wfctl names is covered by adding one line, with no
  test change. #31's comment anticipates exactly that.

## Coverage against the spec

FR-001…FR-010 all have an asserting test. FR-007 (never report commands nothing
names) was structural-only at analyze time and is now pinned by
`test_commands_no_step_names_are_not_reported`.

net: `Lean already.` — production code shrank; the additions are tests.
Verdict: **Approve** (blocker fixed and verified in-session).
