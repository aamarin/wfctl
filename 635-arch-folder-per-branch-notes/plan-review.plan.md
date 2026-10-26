# Implementation Plan: Design exceptions move to the spec folder

**Branch**: `635-arch-folder-per-branch-notes` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this feature's spec folder

## Summary

`wfctl arch none` and `wfctl step none` stop writing into the architecture
folder. Both write into an `exceptions/` folder inside the branch's spec folder, and
the PR body carries the same answers to the reviewer under a new "Moves a
boundary?" section. Two checks keep the copies honest before the PR opens, and
an attended session pauses when a record is written on a branch that said "no
new boundary". The work has six parts:

1. **One module.** `wfctl/_design_exceptions.py` owns the exceptions folder's path and file
   format (`design-exceptions-module.md`). Both commands write through it, and the
   brainstorm gate, the pipeline, and the session summary read through it.
2. **The gate and its exclusions.** The gate counts a boundary exception in the
   spec folder, and `declarations/` joins the arch-root folders that answer
   nothing, so an old declaration no longer releases it.
3. **The PR section.** This repo lists "Moves a boundary?" under
   `change_sections` and adds the heading to its PR template. wfctl's code
   doesn't name it.
4. **The agreement check.** `check-body` reports any exception whose reason
   isn't in the PR body (research R12).
5. **The guard's record checks.** The worktree guard holds `gh pr create` and
   `gh pr merge` when a record contradicts the branch's own "no new boundary",
   or when a record the branch touches isn't accepted (research R13, R14).
   `architecture-decisions` tells an attended agent to stop when it writes a
   record on such a branch (research R15).
6. **Cleanup and text.** The 15 declarations are deleted, the 5 step claims
   move to their spec folders, and the skills, help text, and record that name
   the old location are updated.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, already in use. Nothing new.
**Storage**: Plain files in the spec folder, which `wfctl store specs` commits
to `specs-trunk` with the rest of the folder.
**Testing**: `uv run pytest -q`, with a new `tests/test_design_exceptions.py` and edits to
`tests/test_step_none.py`, `tests/test_pipeline_commands.py`,
`tests/test_warnings_after_gate.py`, `tests/test_paths.py`, docstrings in four
test files, and the `_contract.py`
fixture (research R8). Plus `uv run ruff check wfctl/ tests/`,
`uv run mypy`, and `uv run wfctl check config`.
**Target Platform**: macOS and Linux shells where wfctl runs.
**Project Type**: CLI, plus the skills tree it ships as package data.
**Performance Goals**: The gate reads one more file and makes no new git call.
An exception present skips the git call it makes today.
**Constraints**: wfctl names no PR heading (`_sections.py`). No edit to
Spec Kit-derived skills (`vendor-upstream-skills`). `opening-a-change` gains no
section list. Minimal-complexity bias.
**Scale/Scope**: One new module of about 60 lines, a second of about 80 lines
for the guard's record checks, edits in `cli.py`, `_pipeline.py`,
`_evidence.py`, `_paths.py`, `_review_gate.py`, and `_contract.py`, six skill
files, one related record, `AGENTS.md`, the PR template, and `wfctl.json`. 15
files deleted and 5 moved to spec folders.

## Design records

Design records: 2 listed in design.md

- `docs/architecture/design-exceptions-live-with-specs.md`
- `docs/architecture/design/design-exceptions-module.md`

Both are `proposed`. The plan follows both as written. The level-2 record is
the one `wfctl status` lists under "architecture accepted", and accepting it is
the user's call.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. The gates below come from
`AGENTS.md` and the in-force records, as recorded under Complexity Tracking.

- [x] Validation plan exists: the three `uv run` commands, the tests in
      research R8, `uv run wfctl check config`, `uv run wfctl install-skills
      --agent claude` with the installed text read back, and the hand checks
      in `quickstart.md`.
- [x] Complexity is justified: one module of plain functions, argued against
      changing four call sites in place by `design-exceptions-module.md`. One helper,
      `_paths.feature_dir`, moved out of `feature_paths_cmd` so the exception
      commands and `feature-paths` name the same folder (research R1).
- [x] Ownership is stated: the person or agent on the branch decides whether a
      boundary moved or a pass applies, and writes the reason. `_design_exceptions` owns
      where it's stored and its format. The pipeline computes each pass's
      state from the exceptions folder on every read. The repo owns whether the
      PR section is required, through `change_sections`.
- [x] `a-rule-is-expressed-as-a-check`: the boundary answer is visible in the
      spec folder and the PR body, so the gate and `check-body` check it. A
      record that contradicts it, or that nobody accepted, is visible in the
      branch's commits, so the guard checks those. The pause in R15 stays
      skill text, and the guard's acceptance check catches an agent that
      skips it.
- [x] `review-covers-unreviewed-commits`: the guard's review check is
      unchanged. The record checks run after it, in the same pass, and add
      their own refusals.
- [x] `knowledge-placement`: a fact about one branch goes in that branch's spec
      folder, and the architecture folder keeps only constraints on the
      system.
- [x] `session-state-is-re-derived`: exceptions are read from disk on every
      inference, with no cache, as `_step_claims` did.
- [x] `change-carries-release-note`: `changes/635.change.md`, since a user
      running `arch none` sees the file land somewhere else.
- [x] `layer-model`: skill edits go to `wfctl/agents/`, never `.agents/`.
- [x] `vendor-upstream-skills`: none of the edited skills is Spec Kit-derived.

Post-design re-check: still passing. Research R6 keeps the session summary off
`_architecture_answered`, since that function's `spec.md` escape would read
every branch past specify as answered.

## Project Structure

### Documentation (this feature)

```text
635-arch-folder-per-branch-notes/
├── design.md            # brainstorm output
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _design_exceptions.py                        # new: folder, write, boundary, passes
├── _paths.py                         # feature_dir; DECLARATIONS_DIR in non_record_subtrees
├── cli.py                            # arch_none_cmd, step_none_cmd (and their --help docstrings), feature_paths_cmd, _observe, end_cmd
├── _pipeline.py                      # _step_claims removed; calls _design_exceptions.passes(spec_dir)
├── _evidence.py                      # _architecture_answered checks _design_exceptions.boundary first
├── _contract.py                      # nested fixture writes through _design_exceptions.write
├── _declared.py                      # comment naming STEP_CLAIMS_DIR, rewritten for exceptions/
├── _record_gate.py                   # new: the guard's two record checks (R13, R14)
├── _review_gate.py                   # _judge calls _record_gate.refusal after the review check
└── agents/skills/
    ├── architecture-decisions/SKILL.md  # the pause on a branch with a boundary exception (R15)
    ├── architecture-design/SKILL.md  # lines 69 - 71: the reviewer reads the PR body
    ├── design-levels/SKILL.md        # level 2: where arch none writes, what the gate reads
    ├── model-the-domain/SKILL.md     # "it writes one declaration"
    ├── writing-a-scan-file/SKILL.md  # drops <root>/declarations/ from the naming example
    └── opening-a-change/SKILL.md     # Step 4: copy design exceptions into the body; Step 5: resolve a check-body mismatch (R12)

tests/
├── test_design_exceptions.py         # new; epic sub-issue sharing
├── test_record_gate.py               # new; story 5 scenarios 3 - 6
├── test_sections.py                  # story 5 scenarios 1 and 2, beside the other check-body source tests
├── test_step_none.py                 # spec-folder paths; visibility tests replaced; scenario 2.2
├── test_pipeline_commands.py         # arch none tests move to the spec folder; scenarios 1.2, 1.3
├── test_end_reports_observations.py  # Boundary line with an exception and no record
├── test_warnings_after_gate.py       # writes its exception through _design_exceptions
├── test_paths.py                     # STEP_CLAIMS_DIR import and test replaced with DECLARATIONS_DIR
├── test_pipeline_state_names.py      # docstring
├── test_declared.py                  # docstring
└── test_skill_cross_references.py    # docstring

docs/architecture/an-absent-artifact-is-claimed-not-inferred.md  # three passages (research R9 item 10)
docs/architecture/design-exceptions-live-with-specs.md           # Consequences: step claims move, not deleted (edited before tasks)
docs/architecture/declarations/       # deleted, 15 files
docs/architecture/step-claims/        # deleted; its 5 files move to their spec folders (research R10)
.github/pull_request_template.md      # "## Moves a boundary?" with its comment
wfctl.json                            # change_sections gains "Moves a boundary?"
AGENTS.md                             # arch root exclusions; step none paragraph
changes/635.change.md                 # release note
```

**Structure Decision**: The exceptions code is a new module, as
`design-exceptions-module.md` decided, rather than functions in `_paths.py` or code left
in each caller. `feature_dir` goes in `_paths.py`, since it resolves a path and
sits beside `resolve_spec_dir` and `spec_root`.

**Epic sub-issues**: An epic's sub-issues share the epic's spec folder, so they
share its exceptions too. A sub-issue that adds an architecture record keeps
sharing the folder, and the record answers the boundary question for it. The
guard doesn't treat that as a contradiction, since the exception isn't the
sub-issue's own, but it still holds the PR until the record is accepted. A
sub-issue that needs different pass exceptions or its own plan gets its own
spec folder, named after its branch. wfctl checks for that folder first, so the
sub-issue stops sharing and starts with no exceptions. For example, #701 and
#702 both use #700's boundary exception until #702 gets a `702-record-reader/`
folder of its own (research R11).

### `wfctl/_design_exceptions.py`

```python
BOUNDARY = "boundary"

def folder(spec_dir: Path) -> Path: ...
def write(spec_dir: Path, name: str, reason: str) -> Path: ...
def boundary(spec_dir: Path) -> str | None: ...
def passes(spec_dir: Path) -> dict[str, str]: ...
```

`data-model.md` gives each function's behavior and the file format.

### The callers

1. `arch_none_cmd` keeps both reason checks, then calls
   `_design_exceptions.write(feature_dir(branch, repo_root), BOUNDARY, reason)` and prints
   the two success lines from `contracts/cli.md`. The `touched_on_this_branch`
   check and its warning go (research R5).
2. `step_none_cmd` keeps its reason checks and pass resolution, then calls
   `_design_exceptions.write(feature_dir(...), qualified_name, reason)`. The unlink and
   `_refuse_unseen` block goes. `_refuse_unseen` stays for `step sign-off`.
3. `_architecture_answered` returns `None` after its `spec.md` escape when
   `_design_exceptions.boundary(spec_dir)` is set, before the git call (research R3).
4. `_pipeline.py:393` passes `_design_exceptions.passes(spec_dir)` when `spec_dir` is set
   and `{}` otherwise (research R7).
5. `_observe(repo_root, report, spec_dir)` reads "answered" when a boundary
   exception exists, and otherwise maps the git answer as it does today
   (research R6, FR-014).
6. `check_body_cmd` composes a fourth source, `_exception_findings(body)`,
   beside `_section_findings`. It resolves the spec folder with
   `resolve_spec_dir`, reads `_design_exceptions.boundary` and
   `_design_exceptions.passes`, and returns one finding per reason missing from
   the body after both are whitespace-collapsed. It skips the boundary
   exception when the folder isn't named after the branch and
   `_evidence._branch_records` returns a record, since that record answers the
   boundary question for the sub-issue. Outside a wfctl repo, or with no spec
   folder, it returns nothing (research R12).
7. `_review_gate._judge` calls `_record_gate.refusal(session, branch, head,
   trunk)` once the review check finds nothing pending, and returns its
   refusal. `_judge` already calls `_paths.trunk_branch`, so it keeps that
   value before stripping `origin/` and passes it in, rather than having the
   new module make a second git call. The
   new module lists the level-2 records the branch touches with
   `git diff --name-only --diff-filter=d <trunk>...<head> -- <arch>`, and
   reads each one's status from `git show <head>:<path>`. `<trunk>` is the
   value `_paths.trunk_branch` returns, before `_judge` strips `origin/` from
   it, so the range is the same three-dot range `records_on_this_branch`
   reads. A three-dot diff starts at the merge base, so records the trunk
   gained after the branch point aren't listed, and an `origin/main` ahead of
   a stale local `main` doesn't move the base back.

   The list holds the same records `_evidence._branch_records` holds for the
   "architecture accepted" fact. A level-2 record is a `.md` file directly in
   the arch root, since `_arch.load_records` globs one level. So the guard
   keeps a path from the diff only when its parent is the arch root and it
   ends in `.md`. That leaves out level-3 records in `design/`, the view in
   `views/`, the scans, and every other subdirectory, and it needs no list of
   subdirectories, which would have to be read from the working tree rather
   than `head` (R13). `--diff-filter=d` leaves out a file the branch deleted,
   since `git show` fails on it and any error refuses. The 5 files under
   `step-claims/` this branch deletes are excluded twice, by the parent rule
   and by the filter. The guard can't call `_branch_records`, because it
   doesn't import `_evidence`, and `_paths.records_on_this_branch` reads `HEAD`
   and the working tree rather than `head` and returns an empty list when git
   fails. So the rule is written a second time here, and a test in step 8
   checks that both readers list the same records on the same branch.

   It refuses for
   the first of these that holds:
   1. The branch's own spec folder holds a boundary exception and the list
      isn't empty (R13). "Own" is `resolve_spec_dir(branch, root) ==
      spec_root(root) / branch`.
   2. A listed record's status is outside the ruled-on set (R14).

   It shares `_review_gate`'s `TIMEOUT` and its rule that any error refuses.
   It doesn't import `typer`, `rich`, or `_evidence`, since the guard runs
   before every Bash call and `_evidence` imports five other modules. So
   `_RULED_ON` moves from `_evidence.py` to `_arch.py` as `RULED_ON`, and both
   readers import it from there. The status is read with `_arch`'s frontmatter
   parser applied to the `git show` text. An arch root outside the working tree has no records in git, so both
   checks pass there, as the "architecture accepted" fact does.

### Order of work

1. `tests/test_design_exceptions.py`, failing, then `_design_exceptions.py`.
2. `_paths.feature_dir` with `feature_paths_cmd` moved onto it, and
   `DECLARATIONS_DIR` in `non_record_subtrees` and `STEP_CLAIMS_DIR` removed.
   The existing `feature-paths`
   tests cover the move.
3. The command tests in `test_step_none.py` and `test_pipeline_commands.py`
   rewritten for the spec folder and failing, then both commands.
4. Gate tests for an exception with no record, an exception with git unable to
   answer, and an old declaration with no exception, failing, then
   `_architecture_answered` and the pipeline's exception read.
   `test_design_gate_drawing.py` must stay green unchanged (SC-003). The
   scenario tests and the epic sub-issue tests in research R8 items 10 and 11
   go in here too.
5. A test for the Boundary line with an exception and no record, failing, then
   `_observe`.
6. `_contract.py`'s fixture and `test_warnings_after_gate.py`, then the full
   suite.
7. Tests for story 5 scenarios 1 and 2, failing, then `_exception_findings`.
   Beside them, a test for a sub-issue on the epic's folder: with a level-2
   record on the branch, `check-body` reports nothing for the epic's boundary
   exception, and without one it reports the missing reason.
8. Tests for story 5 scenarios 3 - 6, failing, then `RULED_ON` moved to
   `_arch.py`, `_record_gate.py`, and the call in `_review_gate._judge`. The
   existing guard tests must stay green unchanged, since a branch with no
   records passes both new checks. `test_record_gate.py` also covers three
   branches the existing guard tests don't:
   1. A branch that writes only a level-3 record under `design/` passes both
      checks, with and without a boundary exception.
   2. A branch that deletes a file under the arch root, at the top level and
      under a subdirectory, passes.
   3. A branch whose trunk gains a proposed record after the branch point
      passes, since the record isn't the branch's.
   4. On each fixture branch, the guard's list matches the slugs
      `_evidence._branch_records` returns.
9. Delete `declarations/`. Move the 5 step claims into `exceptions/` in their
   spec folders through `_design_exceptions.write`, then delete `step-claims/`.
   `grep -rn "step-claims\|STEP_CLAIMS" wfctl/ tests/` prints nothing. Store
   each of the 5 spec folders with `WFCTL_BRANCH=<branch> wfctl store specs`.
   Each run is a push, so ask the user before the first one (research R10).
   Then run the level-3 record's check,
   `grep -rn '"exceptions"\|boundary\.md' wfctl/cli.py wfctl/_pipeline.py wfctl/_evidence.py`,
   and confirm every hit is a call into `_design_exceptions`.
10. The PR template section, the `wfctl.json` key, and
   `uv run wfctl check config`.
11. The skill text, the two `--help` docstrings, the related record,
   `AGENTS.md`, the release note, `uv run wfctl install-skills --agent claude`,
   the checks in `quickstart.md`, and `uv run wfctl doctor`. The release note
   says to upgrade wfctl before writing an exception (research R4).
12. After the PR opens, post a comment on #382 saying its short track reads the
    boundary exception from the spec folder now, not a committed `arch none`
    file. Ask the user before posting it, since it's an outward action.

## Complexity Tracking

| Item | Why | Note |
| --- | --- | --- |
| No constitution | The repo has none | Gates taken from `AGENTS.md` and the in-force records listed above |
| `_paths.feature_dir` | The exception commands must name the same folder `feature-paths` creates | Moved out of `feature_paths_cmd`, not new logic (research R1) |
| `DECLARATIONS_DIR` kept after its folder is deleted | FR-007: an older wfctl can still write a declaration | One entry in `non_record_subtrees` (research R4) |
| `STEP_CLAIMS_DIR` removed with no fallback | Only wfctl 0.23.0 writes there, and the gap closes when the tool is upgraded | Accepted while wfctl has one user; the release note says to upgrade (research R4) |
| SC-004 covers code only | Skill text and the PR template comment name the exceptions folder too | Those texts are listed in research R9, so a later move updates them |
| FR-013 narrowed | `opening-a-change` must never carry a section list | The template comment names the section, and the skill names none (research R9) |
| `_record_gate.py` as a new module | `_review_gate.py` is about reviews, and its docstring says so | It reuses `_review_gate`'s parsing of which branch and commit a command acts on, and adds only the record checks (research R13, R14) |
| `RULED_ON` moved to `_arch.py` | The guard can't import `_evidence` without loading five more modules on every Bash call | One constant, two readers (plan caller 7) |
| Every branch that adds or edits a proposed record waits for a person before its PR opens | An unattended run could otherwise merge a boundary nobody approved, or change one already written | This PR waits on `design-exceptions-live-with-specs.md` and on #339's `an-absent-artifact-is-claimed-not-inferred.md`, which it edits, since #339 is closed. Its level-3 record doesn't hold it. An edit to a record held as proposed on purpose waits for that record's acceptance (research R14) |
