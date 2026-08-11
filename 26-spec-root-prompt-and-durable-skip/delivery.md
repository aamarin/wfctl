# Delivery Plan: spec-root prompt and durable-spec skip

**Feature**: `26-spec-root-prompt-and-durable-skip`
**Date**: 2026-08-11
**Source**: tasks.md (48 tasks), plan.md, spec.md (23 FR + 8 SC), analysis-report.md (0 critical)

## Decision: one PR, closing two issues

**PR count**: 1 · **Issues closed**: 2 (#26, #27) · **New issues created**: 0

This departs from the delivery skill's rule that one PR closes exactly one issue.
The departure is deliberate, was decided before this branch was created, and is
recorded here rather than left for a reviewer to discover.

### Why

Per the comment on #26 and `aamarin/wf-skills#23`, the one-PR-one-issue rule was
tooling friction rather than principle. What governs is **split on logical
boundaries and genuine coupling, not on issue count**. #26 makes `spec_root`
reachable; #27 is what teardown should do once a repo has taken it. They are the
setup and the consequence of one setting.

### The boundary signals, honestly

| Signal | Verdict | Reasoning |
|---|---|---|
| File conflict risk | **bundle** | US1, US2 and US3 all edit `wfctl/cli.py`. Concurrent PRs would conflict on it. |
| Reviewability | **bundle** | Teardown correctness cannot be assessed from the predicate alone — it needs the exit status, the hook, and the atomicity fix together. |
| Mergeable increment | *split candidate* | Phase 2 alone merges clean; so does Phase 3; so does Phase 4. |
| Story independence | *split candidate* | US1 and US2 share no runtime path. |

Two of four favour splitting. They were weighed and overridden: shipping #27's
skip behaviour to a population with no way to opt into a durable layout is the
half-change `plan.md` argues against, and `cli.py` is a genuine shared boundary
rather than an incidental one.

### Correction to the record

The comment on #26 describes `Closes #26, Closes #27` as "the documented Pattern 4
shape." It is not. Pattern 4 is hierarchical — a parent epic with one child issue
per PR, the parent closed only on the final PR. This plan matches none of the four
documented patterns; it is a deliberate departure, which is why it is justified
here at length instead of cited.

### No parent epic

An epic earns its keep when children ship separately. These do not: one repo,
adjacent code in `_archive.py` and `cli.py`, nothing to coordinate across
releases.

## Issue Grouping Map

| Issue | Title | Tasks | Files | PR |
|---|---|---|---|---|
| #27 | archive-story should skip specs that are already durable | T003–T026, T038–T043 | `_archive.py`, `cli.py`, `.workmux.yaml`, `test_archive_specs.py`, `test_remaining_commands.py` | PR 1 |
| #26 | install-skills should ask where specs live on first setup | T027–T037 | `cli.py`, `test_install_skills.py` | PR 1 |
| — | shared setup and polish | T001, T002, T044–T048 | `README.md` | PR 1 |

PR 1 description carries `Closes #26` and `Closes #27`.

The rename (T003–T007) is filed under #27 rather than its own issue: it exists to
make #27's blocking hook safe to arm, and has no standalone user value.

## Parallelization Waves

| Wave | Tasks | Parallel? | Gate |
|---|---|---|---|
| **0** | T001, T002 | [P] — read-only | baseline captured, three commands green |
| **1** | T003, T004, T005 [P] → T006 → T007 | tests parallel, impl sequential | rename + alias landed, behaviour unchanged |
| **2** | T008–T017 [P] ‖ T027–T032 [P] ‖ T038–T040 [P] | [P] — three distinct test files | all new tests written and **confirmed failing** |
| **3** | T018 → T019 → T020 → T021 → T022 | sequential, causal | US1 implementation |
| **3′** | T033 → T034 → T035 → T036 | sequential | US2 implementation — coordinate with 3 |
| **3″** | T041, T042 | sequential | US3 implementation — coordinate with 3 |
| **4** | T023, T024 [P], T025 [P] | docstrings parallel | T026, T037, T043 merge gates |
| **5** | T044 [P], T045 [P], T046, T047, T048 | docs parallel | full suite green vs. Wave 0 baseline |

### Wave 3 is a coordination point, not a parallel one

Waves 3, 3′ and 3″ all modify `wfctl/cli.py`. They are logically independent but
share a file, which the skill's table classifies as **coordinate**: draft
together, type-check together, do not fan to concurrent agents editing the same
file. If run by one agent, take them in order 3 → 3′ → 3″.

### Causal ordering inside Wave 3

Not stylistic — each step makes the next expressible:

1. **T018 before T019** — "at-risk artifacts existed and failed" cannot be
   expressed until the plan distinguishes at-risk from not.
2. **T019 before T020** — the promote-on-success rewrite decides what a non-zero
   exit leaves on disk, so the exit rule must be settled first.
3. **T020 before T022** — the hook turns a status into a refused removal, which is
   what makes retries common enough for residue to matter. Arming it first means
   the first real failures manufacture exactly the junk directories T017 exists to
   prevent.
4. **T024, T025 last** — they describe what shipped.

### Wave 1 must precede Wave 3

Phase 2's alias is foundational by risk, not by priority. A repo whose
`.workmux.yaml` still names `archive-story` would hit an unknown command, exit
non-zero, and — since a failing `pre_remove` aborts removal (research.md R-001) —
find its worktrees **unremovable**. Arming the blocking hook before the alias
exists converts a silent-loss bug into an outage.

## Verification Gates

| Gate | Command | Blocks |
|---|---|---|
| Wave 0 | `uv run pytest -q && uv run ruff check . && uv run mypy` | everything |
| Wave 1 (T007) | same | Wave 3 |
| Wave 2 | every new test confirmed **failing** | Wave 3 |
| US1 (T026) | `uv run pytest -q tests/test_archive_specs.py` + lint + types | Wave 5 |
| US2 (T037) | `uv run pytest -q tests/test_install_skills.py` + lint + types | Wave 5 |
| US3 (T043) | full suite + lint + types | Wave 5 |
| Final (T048) | full suite, test count compared against Wave 0 | merge |
| Manual (T046) | `quickstart.md` end to end, including 5a, 5b, `--force`, old-hook | merge |

Wave 2's gate is the easily-skipped one. Several tests assert **absence** — no
archive directory, no recorded key, no junk directory — and pass vacuously against
the wrong setup. Confirm each fails before implementing.

## Out of Scope

- **#36** — sweep the transitional checks. Explicitly blocked on this shipping;
  this branch adds the fifth. Do not pull into any wave.
- **#37** — untracked/uncommitted rescue. Separate concern, and its exposure
  narrowed once testing showed the removal tool already guards work version
  control can see.

## Post-Merge

1. Verify #26 and #27 both closed by the PR merge.
2. `wfctl doctor` on this repo — it has `spec_root` set and is its own test case
   for the durable-skip path (T047).
3. #36 becomes unblocked; its table gains the fifth entry this branch adds.
