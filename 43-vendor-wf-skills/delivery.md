# Delivery Plan: Vendor wf-skills (43)

**Feature**: `43-vendor-wf-skills` | **Date**: 2026-08-16
**Source**: `wfctl-specs/43-vendor-wf-skills/tasks.md` (51 tasks)
**Parent issue**: [#43](https://github.com/aamarin/wfctl/issues/43)

The spec root is outside the repo. Resolve it with `wfctl feature-paths` and read
`FEATURE_DIR`; never assume `specs/` in the working tree.

---

## File-touch matrix

| File | P1 | P2 | US1 | US2 | US3 | US4 | P7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `wfctl/agents/**`, `wfctl/specify/**` (create, ~80 files) | ● | | | | | | |
| `pyproject.toml` (modify) | ● | | | | | | ● |
| `wfctl/_bundle.py` (create) | | ● | | | | | |
| `tests/test_bundle.py` (create) | | ● | | | | | |
| `tests/conftest.py` (modify) | | ● | | | | | |
| `wfctl/cli.py` (modify) | | | ● | ● | ● | | |
| `tests/test_install_skills.py` (modify) | | | ● | ● | ● | | |
| `tests/test_install_config.py` (modify) | | | ● | | | | |
| `tests/test_tracker.py` (modify) | | | ● | | | | |
| `.github/workflows/ci.yml` (modify) | | | | | | ● | |
| `README.md` (modify) | | | | | | | ● |
| `wfctl/_manifest.py` (modify) | | | | | | | ● |

**11 hand-edited files → L.** The skill's rule for L is to flag rather than
auto-split; the scope was put to the user and a two-way split agreed.

One correction to a claim carried in `tasks.md`: the vendored tree is not
"thousands of files". This repo's installed `.agents/` + `.specify/` is **64
files**, and a fresh clone adds `trackers/github.json` and `configs/workmux/*`
on top — the installed tree already carries per-skill `assets/` and
`references/`. Call it under 100; the exact count lands when T001 runs and is not
worth a clone to pin now. Still the largest diff in the feature by a wide margin,
but reviewable by reading a file listing.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
| --- | --- | --- | --- | --- |
| PR 1 | T001–T012, T040, T041, T044 | `wfctl/agents/**`, `wfctl/specify/**` (create), `pyproject.toml`, `wfctl/_bundle.py` (create), `tests/test_bundle.py` (create), `tests/conftest.py`, `.github/workflows/ci.yml` | M (+ bulk data) | T006 and T012 checkpoints pass; the `wheel` job is green; the SC-008 removal experiment fails the job as expected |
| PR 2 | T013–T039, T042, T043, T045–T051 | `wfctl/cli.py`, `tests/test_install_skills.py`, `tests/test_install_config.py`, `tests/test_tracker.py`, `.github/workflows/ci.yml`, `README.md`, `wfctl/_manifest.py`, `pyproject.toml` | L | PR 1 merged; T050 passes — `pytest`, `ruff check .`, `mypy`, all three CI jobs green, quickstart.md walked end to end |

**Rationale**: Multiple PRs. Three of the four boundary signals favour a split at
the Phase 2 / Phase 3 line, and none favours splitting anywhere inside PR 2.

| Signal | Reading |
| --- | --- |
| **1. File conflict** | PR 1 and PR 2 share only `ci.yml` and `pyproject.toml`, and only sequentially. Inside PR 2, US1/US2/US3 all edit `wfctl/cli.py` and `tests/test_install_skills.py` — splitting them means concurrent edits to the same two files. |
| **2. Reviewability** | Strongly favours the split. PR 1 is verified by reading `pyproject.toml` and one CI job; PR 2 is ~300 lines of real logic. Bundling them buries the second in the first. |
| **3. Mergeable increment** | PR 1 changes no behaviour at all — the tool works identically before and after. PR 2 is mergeable as a unit; US1 alone would leave `doctor` on its legacy warning branch, which is safe but not a state to sit in. |
| **4. Story independence** | US1 → US2 → US3 is a hard chain: each consumes the manifest shape the previous one writes. US4 is genuinely independent, which is why its wheel job moves into PR 1. |

**Why the wheel job moves forward into PR 1 — and only half of it does.**
`tasks.md` places T040/T041 in Phase 6, but they are the only check that can
detect a broken `package-data` declaration or a lost exec bit, the two failure
modes the source-tree suite is structurally blind to. Landing them with the
bundle means the bundle is never unverified.

The job splits by what each half can assert without `cli.py`:

| Half | Assertion | PR |
| --- | --- | --- |
| **T040, T041** — packaging | build the wheel, install it into a clean env, assert `wfctl/agents/**` and `wfctl/specify/**` are in `site-packages` and the `.sh` files are mode `755` there | PR 1 |
| **T051** — end-to-end | run `install-skills` in a scratch repo, diff the installed tree against the bundle, assert the exec bit survived `shutil.copy2` (FR-018, SC-002) | PR 2 |

T051 cannot run in PR 1: `cli.py` is untouched there, so `install-skills` still
clones, and the job would diff *upstream `main`* against the vendored copy —
network-dependent in a job about the offline bundle, and green only while
upstream happens to match the tree T001 copied. T042/T043 stay in PR 2 for the
same class of reason: they clean up CI state that only becomes stale once
`--repo` is gone.

**PR 1 closes**: `Closes #45`
**PR 2 closes**: `Closes #46, Closes #43`

Two `Closes` on one PR reads against SKILL.md's red flag list, so to save the
next reader the check: this is the sanctioned exception in
`references/issue-grouping-patterns.md` Pattern 4 — the parent epic close is
allowed on the final PR only, and only once the parent's acceptance criteria are
satisfied. The one-issue-per-PR rule still holds; #43 is an epic, not PR 2's
issue.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
| --- | --- | --- | --- | --- |
| [#45](https://github.com/aamarin/wfctl/issues/45) (Issue A) | T001–T012, T040, T041, T044 | `[43] Vendor the wf-skills tree into the wfctl package` | M (~3–4h) | PR 1 |
| [#46](https://github.com/aamarin/wfctl/issues/46) (Issue B) | T013–T039, T042, T043, T045–T051 | `[43] Source installs from the bundle; retire the clone` | L (~6–8h) | PR 2 |

**Grouping pattern**: Hierarchical — parent epic #43 stays open until both PRs
merge.
**Rationale**: Two PRs, so two issues; the parent already exists and carries the
scope decisions, so it becomes the epic rather than being duplicated.

### Getting this spec into a sub-issue worktree

Nothing to move. `wfctl feature-paths` reports
`FEATURE_DIR=/Users/andremarin/Development/wfctl-specs/43-vendor-wf-skills`,
outside the working tree, so every sub-issue worktree resolves the same absolute
path. `speckit-orchestrate` step 0 globs that spec root for `*/delivery.md`,
matches the branch's issue key against the table above, and takes that row's
`Tasks` column as the sub-issue's range.

---

## Parallelization Waves

### PR 1 — #45

| Wave | Mode | Tasks | Gate / Notes |
| --- | --- | --- | --- |
| 0 | Sequential | T001 → T002 | Copy from a **fresh clone**, not this repo's `.agents/` (it has no `trackers/` or `configs/`). Gate: `git ls-files -s wfctl/specify/scripts/bash` shows `100755`. |
| 1 | Sequential | T003 → T004 | Gate: the wheel carries the files with the exec bit. **A zero-file result means T003's globs are wrong — hard stop, everything downstream builds on nothing.** |
| 2 | Parallel | T005 ‖ (T040 → T041) | Both read the Wave 1 wheel. T041 edits the job T040 creates, so that pair is internally sequential. Both assert against `site-packages`, never against an `install-skills` run — see T051. |
| 3 | Sequential | T006 | Phase 1 checkpoint. |
| 4 | Sequential | T007 | `wfctl/_bundle.py` must exist before its tests. |
| 5 | Parallel* | T008 ‖ T009 ‖ T010 | *Logically independent, but all three land in `tests/test_bundle.py`. One agent writes all three functions — not a fanning candidate (see below). |
| 6 | Sequential | T011 | Autouse `bundle` fixture in `tests/conftest.py`. |
| 7 | Sequential | T012 → T044 | Phase 2 checkpoint, then CI green + the SC-008 removal experiment once. |

### PR 2 — #46

| Wave | Mode | Tasks | Gate / Notes |
| --- | --- | --- | --- |
| 0 | Parallel | T013 ‖ T014 ‖ T015 | Three different test files, no shared state. The one genuine fanning wave in the feature. |
| 1 | Sequential | T016 → T017 | Both touch `tests/test_install_skills.py`; T017 deletes a test T016 would otherwise have edited. |
| 2 | Sequential | T018 → T019 | Same file. |
| 3 | Sequential | T020 → T021 → T022 → T023 → T024 → T025 | All in `wfctl/cli.py`. Strictly ordered: targets, then the clone deletion, then everything that depends on the variables it removes. |
| 4 | Sequential | T026 | US1 checkpoint. `doctor` is degraded-but-safe here — it finds no `commit` and takes its existing warning branch (`cli.py:1874-1879`). Do not stop at this wave. |
| 5 | Parallel* | T027 ‖ T028 ‖ T029 ‖ T030 | Four doctor states, independent assertions, same file. Write them before touching `cli.py` — they are easy to write in a way that passes against the old code. |
| 6 | Parallel | T031 ‖ T032 | T032 is read-only confirmation of existing behaviour. |
| 7 | Sequential | T033 | US2 checkpoint. |
| 8 | Parallel* | T034 ‖ T035 ‖ T036 | Three migration tests, same file. |
| 9 | Parallel | T037 ‖ T038 | T038 is read-only confirmation. |
| 10 | Sequential | T039 | US3 checkpoint. |
| 11 | Parallel | (T042 → T043 → T051) ‖ (T045 → T047) ‖ T046 | Three files: `ci.yml`, `README.md`, `_manifest.py`. Each group is internally sequential because it shares a file. T051 is the end-to-end half of the wheel job PR 1 deferred; it is unblocked from Wave 4 onward and only sits here to keep `ci.yml` edits in one group. |
| 12 | Sequential | T048 → T049 → T050 | Quickstart end to end, version bump, final gate. |

**Single-agent order** (recommended — see the fanning note):
T001 → T002 → T003 → T004 → T005 → T040 → T041 → T006 → T007 → T008 → T009 →
T010 → T011 → T012 → T044 ‖ then PR 2: T013 → T014 → … → T050 in numeric order,
with T040–T044 already done.

---

## Agent Fanning Instructions

**Recommended: a single agent per PR.**

The wave tables above are the dependency truth, but only **PR 2 Wave 0**
(T013 ‖ T014 ‖ T015) clears the fanning bar — three distinct files, no shared
state. Every other parallel wave in this feature is parallel *logically* while
concentrating in one file: `tests/test_bundle.py` for T008–T010,
`tests/test_install_skills.py` for T027–T030 and T034–T036. Fanning agents onto
one file trades a few minutes of wall clock for merge conflicts in a file that is
being rewritten anyway.

**Wave 0 fanning (3 agents), if used.** One prompt, substituted per agent:

```
You are implementing task {TASK} for feature 43-vendor-wf-skills.
Spec dir: run `wfctl feature-paths`, read FEATURE_DIR.

Task: Modify {FILE}

Convert `{BUILDER}` (line {LINE}) from a git-repo builder to a plain directory
builder: drop `git init` / `git config` / `git add` / `git commit`, and drop the
now-unused `subprocess` import if nothing else in the file uses it. Rename the
tree it builds from the dotted `.agents/…` layout to the undotted `agents/…`
layout that matches the new package paths.

Constraints:
- Do not touch the call sites — that is T016.
- Do NOT run pytest, ruff or mypy: two sibling agents are editing other test
  files and the tree is transiently inconsistent.

Signal "{TASK} complete" when the file is saved.
```

| Agent | TASK | FILE | BUILDER | LINE |
| --- | --- | --- | --- | --- |
| A | T013 | `tests/test_install_skills.py` | `_make_wf_skills_repo` | 22 (its `subprocess` import is line 4) |
| B | T014 | `tests/test_install_config.py` | `_make_wf_skills_repo_with_config` | 18 |
| C | T015 | `tests/test_tracker.py` | `_make_wf_skills_repo_with_tracker` | 260 |

**Fan-in gate after Wave 0:** `uv run pytest -q` — expected to **fail** at this
point, because the call sites still pass `--repo`/`--ref`. The gate is that the
failures are only those call-site errors, not import or syntax errors. T016 is
what makes it green.

---

## Verification checklist

- [x] `delivery.md` written to the spec dir resolved by `wfctl feature-paths`
- [x] PR count justified with the 4-signal rationale
- [x] Issue count equals PR count — 2 and 2
- [x] Every task assigned to exactly one wave (51 tasks: 15 in PR 1, 36 in PR 2)
- [x] GitHub issues created and numbered — #45, #46
- [x] Each issue's `Closes` line references exactly one PR
- [x] Sub-feature issues linked to parent epic #43, which carries the progress list
