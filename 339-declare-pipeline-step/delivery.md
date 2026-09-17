# Delivery Plan: Declare pipeline step (339)

**Feature**: `339-declare-pipeline-step` | **Date**: 2026-09-17
**Source**: `specs/339-declare-pipeline-step/tasks.md` (61 tasks)
**Parent issue**: #339

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 | T001–T037 | `wfctl/_pipeline.py` (modified), `wfctl/_declared.py` (created), `wfctl/_evidence.py` (renamed from `_predicates.py`, modified), `wfctl/cli.py` (modified), `tests/conftest.py` (modified), `tests/test_declared.py` (created), `tests/test_cli_status.py` (created), `tests/test_evidence.py` (renamed from `test_predicates.py`, modified), `tests/test_pipeline_state_names.py` (modified), `tests/test_pipeline_commands.py` (modified), `tests/test_pipeline_payload_snapshot.py` (modified), `tests/pipeline_payload_snapshot.json` (modified), and nine import-only touches the rename reaches — `_stall.py`, five test modules, `speckit.analyze.md`, `writing-a-scan-file/SKILL.md` | L (12 files of substance, 9 one-line) | T002a and T002b land first, so the rename is reviewable apart from the mechanism; T013, T029 and T037 gates green; `quickstart.md` § *Declare a pass and walk a branch through it* and § *Read wfctl's own passes* walked by hand |
| PR 2 | T038–T056 | `wfctl/_paths.py` (modified), `wfctl/cli.py` (modified), `wfctl/_pipeline.py` (modified), `AGENTS.md` (modified), `wfctl/agents/skills/*` (modified), `tests/test_step_none.py` (created), `tests/test_arch_records.py` (modified), `tests/test_paths.py` (modified), `tests/test_cli_status.py` (modified), `tests/test_pipeline_state_names.py` (modified), `tests/test_pipeline_payload_snapshot.py` (modified) | L (11 files) | PR 1 merged; T050 and T056 gates green; `install-skills` + `doctor` under `uv run`; both remaining quickstart walks done |

**Rationale**: Multiple PRs. The feature is 61 tasks over 17 files — XL by the
sizing table, which cannot ship as one PR. Two, not three: `plan.md` phases the
work into the mechanism + US1, then US2, then US3, but US2 is 8 tasks over 5
files and **4 of those 5 are files the mechanism PR already edits**
(`_pipeline.py`, `_evidence.py`, `test_evidence.py`,
`test_pipeline_state_names.py`). A PR of its own would be a stack carrying
conflicts against its own base and saving no review size. The split that earns
its keep is the one between *the mechanism and its consumers* and *the exit* —
different files, different verb, and a design question still open against the
second (#409).

**PR 1 closes**: `Closes #410`
**PR 2 closes**: `Closes #411`

The parent, #339, is closed by hand once both are merged and its acceptance
criteria are satisfied. Neither PR closes it — one PR closes exactly one issue.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #410 (Issue A) | T001–T037 | `[339] A step carries passes — the mechanism, a repository's pass, and wfctl's own` | L | PR 1 |
| #411 (Issue B) | T038–T056 | `[339] A pass that does not apply — wfctl step none, and the exit it gives the gate` | L | PR 2 |

**Grouping pattern**: Sub-feature split, under #339 as parent.
**Rationale**: Two sub-features with separate acceptance criteria and separate
runtime paths — a pass existing and being routed to, versus a pass being declared
away — each one PR's worth of work and neither reviewable as part of the other.

### Getting this spec into a sub-issue worktree

`wfctl feature-paths` in the sub-issue worktree prints `FEATURE_DIR`. This repo
records a `spec_root` outside the working tree
(`/Users/andremarin/Development/wfctl-specs`), so this spec dir is already at a
stable absolute path every worktree can read and there is nothing to copy.

`resolve_spec_dir` scans that root for a `delivery.md` whose Issue Grouping Map
names the branch's issue key, and `speckit-orchestrate` takes that row's `Tasks`
column as the sub-issue's range. The scan reads the first cell of each row in the
first table under the heading, which is why `#410` and `#411` lead their cells.

---

## Sequencing: PR 2 cannot start before PR 1 merges

Not a tidiness preference. Four of PR 2's five implementation tasks read what
PR 1 produces:

| PR 2 task | Needs, from PR 1 |
| --- | --- |
| T045, T046 | `_declared.load`'s pass list (T005, T007) — nothing to resolve `<step>.<name>` against until it exists |
| T047 | `sub_steps` on `_PipelineStep`, and the walk in `_infer_steps` (T009) |
| T048 | the indented rendering that `--all` filters (T023) |
| T042 | `tests/test_cli_status.py`, which T014 creates |

They also collide on files: `wfctl/cli.py` carries T023–T026 in PR 1 and
T045/T046/T048 in PR 2; `wfctl/_pipeline.py` carries T003–T012a and T034 in PR 1
and T047 in PR 2.

**The one independent slice** is T044 and T041 — `step-claims/` added to
`_paths.non_record_subtrees`, two tasks over two files PR 1 never touches. Too
small to be its own PR under the one-issue-per-PR rule, so it runs as wave 0 of
PR 2 and can be written before PR 1 merges if someone wants a head start.

**The parallelism that is available is inside each PR**, not between them. The
wave tables below are where it lives: PR 1's wave 3 fans to five agents, PR 2's
wave 1 to five.

---

## Parallelization Waves — PR 1 (#410)

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | Both edit `tests/conftest.py`. T002 extends what T001 wrote |
| 1 | Sequential | T003 | The type boundary three lanes share. `SubStep` must exist before `_declared.load` can name it in a signature |
| 2 | Parallel, coordinated | (T004 → T009 → T010 → T011 → T012 → T012a) ‖ (T005 → T007 → T008) ‖ T006 | Three files, three lanes. Within a lane strictly sequential — same file. The lanes share `SubStep` and `_declared.load`'s signature: draft together, type-check together |
| 3 | Sequential | T013 | Fan-in gate. `pytest -q && ruff check && mypy` |
| 4 | Parallel | (T015 ‖ T016 ‖ T019 ‖ T020) ‖ (T017 ‖ T017a) ‖ (T018 ‖ T022) ‖ (T021 ‖ T022a) ‖ T014 | Five lanes by file: `test_declared.py`, `test_predicates.py`, `test_pipeline_state_names.py`, `test_pipeline_commands.py`, `test_cli_status.py`. Tasks inside a lane share a file, so one agent owns each lane |
| 5 | Parallel | (T023 → T024 → T025 → T026) ‖ T027 | `cli.py` is one lane, strictly ordered. The snapshot rewrite depends only on T011's payload shape, already landed |
| 6 | Sequential | T028 → T029 | The by-hand walk, then the gate. T028 cannot be automated — a test that constructs the payload directly has not tested that a repository can reach it |
| 7 | Parallel | T030 ‖ T031 ‖ T032 | Three test files, no shared state |
| 8 | Sequential | T033 → T034 → T035 | `_predicates.py` then `_pipeline.py`: T034 orders the two passes T033 creates, and T035 checks the one existing assertion that pins `current == "brainstorm"` |
| 9 | Sequential | T036 → T037 | The second by-hand walk, then the merge gate |

**Single-agent order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 →
T009 → T010 → T011 → T012 → T012a → T013 → T014 → … → T029 → T030 → … → T037.

---

## Parallelization Waves — PR 2 (#411)

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T044 → T041 | `_paths.non_record_subtrees` and its test. Independent of PR 1 — the only part of this PR that can be written before PR 1 merges |
| 1 | Parallel | (T038 → T038a → T039) ‖ T040 ‖ T042 ‖ T043 ‖ T043a | Five lanes by file: `test_step_none.py`, `test_arch_records.py`, `test_cli_status.py`, `test_pipeline_payload_snapshot.py`, `test_pipeline_state_names.py`. T040 is the one where a wrong answer looks like success — a claim must not satisfy the boundary check |
| 2 | Parallel | (T045 → T046 → T048) ‖ T047 | `cli.py` in order, `_pipeline.py` beside it. **#409 has to be settled before T045 and T047 are written** — the two artifacts specify opposite behaviour for a claim that cannot reach a reviewer |
| 3 | Sequential | T049 → T050 | Both quickstart walks, then the merge gate |
| 4 | Parallel | (T051 → T052) ‖ T053 | Both AGENTS.md tasks are one lane despite the `[P]`; the skills prose is separate |
| 5 | Sequential | T054 → T055 → T056 | `install-skills --prune --yes --agent claude` then `doctor`, both under `uv run`; the full quickstart; the final gate |

**Single-agent order**: T044 → T041 → T038 → T038a → T039 → T040 → T042 → T043 →
T043a → T045 → T046 → T047 → T048 → T049 → T050 → T051 → T052 → T053 → T054 →
T055 → T056.

---

## Agent Fanning Instructions

Both PRs are L, so fanning is worth it at waves 4 (PR 1) and 1 (PR 2) — the test
waves, where every lane is a different file and no lane reads another's output.

**PR 1, wave 4 — five agents.** Each owns one test file end to end. Give each the
same preamble and one lane:

```
Repo: the wfctl worktree for #410. Read specs/339-declare-pipeline-step/spec.md
(Requirements), data-model.md (§ Validation rules, § States) and
contracts/cli.md before writing anything. House style: the test name is a
sentence and the docstring says why the test exists, naming the failure it
catches — a docstring that restates the assertion is not carrying its weight.
Pin NO_COLOR on anything that touches console output; conftest.py explains the
presence-only semantics.

Your lane: <tasks>. Do not edit any file outside <file>.
Verify with: uv run --frozen --extra dev pytest -q <file>
```

Lanes: `tests/test_declared.py` (T015, T016, T019, T020) · `tests/test_predicates.py`
(T017, T017a) · `tests/test_pipeline_state_names.py` (T018, T022) ·
`tests/test_pipeline_commands.py` (T021, T022a) · `tests/test_cli_status.py` (T014).

**Fan-in gate after PR 1 wave 4**: `uv run --frozen --extra dev pytest -q` — every
test in the wave is expected to fail here, because wave 5 is what implements
against them. What the gate checks is that they fail for the stated reason rather
than on import.

**PR 2, wave 1 — five agents.** Same preamble, lanes `tests/test_step_none.py`
(T038, T038a, T039) · `tests/test_arch_records.py` (T040) · `tests/test_cli_status.py`
(T042) · `tests/test_pipeline_payload_snapshot.py` (T043) ·
`tests/test_pipeline_state_names.py` (T043a).

**Do not fan waves 2, 5 or 8 of PR 1, or wave 2 of PR 2.** Every one of them has
a lane that is a single file edited in a fixed order, and a second agent in that
lane is two agents rewriting each other's work.
