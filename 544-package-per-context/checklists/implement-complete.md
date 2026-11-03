Implementation complete: 2026-11-02

## Tasks at completion

~~~~markdown
# Tasks: Check imports against the Context Map

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/` in this feature folder
**Prerequisites**: `plan.md` and `spec.md`. The level-2 record is `docs/architecture/contexts-are-packages.md`, already amended and committed on this branch. `design.md` records no level-3 decision.

**Tests**: Every rule the script enforces has a fixture test written before the
rule. The tests live in `tests/test_import_check.py` unless a task names
another file. Each one is a sentence naming the case it pins, per `AGENTS.md`.

**Organization**: One phase per user story in spec order. FR-015's approval
check has no user story of its own, so it gets its own phase after the stories,
followed by the phase that wires both modes into `wfctl verify` and CI.

No module under `wfctl/` moves in any task here. The moves come later under
#671.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel, since it changes a different file and depends on no incomplete task
- **[Story]**: the user story the task belongs to (US1 to US5)

---

## Phase 1: Setup

**Purpose**: The empty script and the test file that loads it, so every later
task has somewhere to land.

- [X] T001 Create `.github/scripts/check_imports.py` as a standard-library script with a `main()` that exits 0, a module docstring saying what it checks, and the constants `WIRING = ("cli.py", "_entry.py")`, `PACKAGE_DATA = ("agents", "specify", "contracts")`, `TRUSTED = (".github/scripts/check_imports.py", ".github/workflows/review.yml")`, and `IMPORTS_APPROVED_PREFIX = "imports approved "` (plan items 4.3.3, 4.3.5, 6.3.5, 7); verify with `uv run python .github/scripts/check_imports.py` exiting 0 and `uv run mypy` covering it
- [X] T002 Create `tests/test_import_check.py` with a `load_check()` loader copied from `tests/test_release_note_check.py`, and a fixture helper that builds a fake `wfctl/` tree and a fixture domain page under `tmp_path`, with real subpackages so the moved-package rules can be tested before any context moves (plan item 13); verify with `uv run pytest -q tests/test_import_check.py`

---

## Phase 2: Foundational

**Purpose**: The domain page carries what the check reads, and the script can
read the page, the baseline, the module placement, and the import graph. Every
story needs all four.

**⚠️ CRITICAL**: No user story work starts until this phase is complete.

### The domain page

- [X] T003 [P] Add a `### Shared packages` table, `| Package | Pattern | Holds |`, under the Bounded Contexts table in `docs/architecture/domain/wfctl.md`. It names `core` as a Shared Kernel holding the repo, branch, and trunk lookups, and `tracker` as an Anticorruption Layer translating between wfctl and the trackers (plan item 1); verify with T008's real-page test
- [X] T004 [P] Change the vocabulary row for Record in `docs/architecture/domain/wfctl.md` from "public module" to "a context's package outside `arch` exports no bare `Record`, `record`, `records`, or `load_record`", and note both changes for #544 on the page's `Amended` line (plan items 2 and 3); verify by reading the rendered row against FR-012

### Tests first

- [X] T005 [P] Write fixture tests for `read_domain(page)`: it returns the seven contexts with their packages, `core` and `tracker` as shared, and the six arrows between two contexts as pairs of context names (data-model §Domain); verify the tests fail against T001's empty script
- [X] T006 [P] Write fixture tests for `read_baseline(path)`: blank and `#` lines are ignored, `<file> <package>` is a placement, `<file> -> <file>` is a violation, a malformed line fails with its line number, a placement naming an unknown package fails, and a module placed twice fails (`contracts/baseline.md`, data-model §Baseline rules 1 - 2); verify the tests fail first
- [X] T007 [P] Write fixture tests for `module_contexts(root, domain, baseline)` covering plan item 4.3's seven cases: a file under a listed package, a placed flat file, `cli.py` and `_entry.py` as wiring, `wfctl/__init__.py` skipped while it imports no wfctl module, package data skipped, an unplaced flat file failing, and a `.py` file under an unlisted directory such as `wfctl/util/` failing as unplaced (FR-007, FR-008); verify the tests fail first
- [X] T008 [P] Write fixture tests for `import_graph(root)`: a function-local import, `from wfctl import _x`, a relative import, a module bound by an import and read as an attribute, and dotted names. Pin that `from wfctl.evidence import _status` targets `wfctl.evidence._status`, not `wfctl.evidence`, when `_status` is a module (plan item 4.4, spec Edge Cases). Add one test that reads the real `docs/architecture/domain/wfctl.md` with `read_domain` and finds seven contexts, two shared packages, and six arrows; verify the tests fail first
- [X] T009 [P] Write tests that the script takes the tree from the current directory and never from its own path, by running it with `cwd` set to a fixture tree in another directory, and that a symlinked domain page, baseline, or `.py` file fails, names the path, and never prints the target's content (plan items 4.9 and 4.10); verify the tests fail first

### Implementation

- [X] T010 Implement `read_domain(page)` in `.github/scripts/check_imports.py`: parse the Bounded Contexts table with each Package cell's backticks stripped, the Shared packages table, and the `### Context Map` mermaid block, map each node label to a context name, skip a node whose label ends in `(outside)` and every edge touching it, and fail when a package name appears twice across the two tables (plan item 4.1). The strict line-by-line failures come in US4; verify with T005 and T008's real-page test
- [X] T011 Implement `read_baseline(path)` in `.github/scripts/check_imports.py`, returning `Placement(module, package, line)` and `Violation(src, dst, line)` (plan item 4.2); verify with T006
- [X] T012 Implement `module_contexts(root, domain, baseline)` in `.github/scripts/check_imports.py` with the seven cases in plan item 4.3, using `WIRING` and `PACKAGE_DATA` from T001; verify with T007
- [X] T013 Implement `import_graph(root)` in `.github/scripts/check_imports.py`, returning one `Import(src, dst, line)` per import of a wfctl module, with the walk `tests/test_architecture_view.py` uses (plan item 4.4, research R1); verify with T008
- [X] T014 Make every read in `.github/scripts/check_imports.py` take its root from `Path.cwd()`, and refuse any path that is a symlink or resolves outside the root, naming the path without reading it (plan items 4.9 and 4.10); verify with T009
- [X] T015 Validate Phase 2 with `uv run pytest -q tests/test_import_check.py`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The script can read everything it checks. No rule runs yet.

---

## Phase 3: User Story 1 - An import the map doesn't allow fails the change (Priority: P1) 🎯 MVP

**Goal**: An import between two contexts that the map draws no arrow for fails,
with the boundary drawn and the action to take.

**Independent Test**: Add an import from an Evidence and derivation module into
a Session continuity module, run the check, and confirm it fails with both
context names and the drawn boundary. Remove the import and confirm it passes.

**Verification**:

- Automated: `tests/test_import_check.py`, one test per acceptance scenario 1 - 3
- Manual: quickstart.md's first exercise, adding `from wfctl._session import record_blocked` to `wfctl/_verify.py` and reverting it
- Evidence: the `no-arrow` block in `contracts/failure-output.md`, printed for that import

### Tests for User Story 1 ⚠️

- [X] T016 [P] [US1] Write fixture tests for US1's three scenarios: an Evidence module importing a Session module fails as `no-arrow`, a Session module importing from the `wfctl.evidence` package passes, and two modules in one context pass (FR-001, FR-003); verify the tests fail first
- [X] T017 [P] [US1] Write a test that the `no-arrow` failure prints the file and line, both context names, the drawn boundary, and the action, in the shape `contracts/failure-output.md` gives (FR-011); verify the test fails first

### Implementation for User Story 1

- [X] T018 [US1] Implement `violations(graph, contexts, domain)` in `.github/scripts/check_imports.py` with rules 2 and 5 of plan item 4.5: same context allowed, and no arrow from the target's context to the importer's refused. Keep the six rules as one ordered list so US2 adds the rest in place; verify with T016
- [X] T019 [US1] Implement `render(failure)` for `no-arrow`, the success line `✓ imports follow the Context Map (N modules, M baseline lines)`, the trailing count, and exit 1 on any failure in `.github/scripts/check_imports.py` (plan item 4.8); verify with T017
- [X] T020 [US1] Validate US1 with `uv run pytest -q tests/test_import_check.py` and quickstart.md's first exercise on the real tree — merge gate

**Checkpoint**: An import against the map fails with the boundary drawn.

---

## Phase 4: User Story 2 - Other contexts import a context's package, never its modules (Priority: P1)

**Goal**: An import of a module inside another context's package fails even
when the map allows the dependency. The shared packages may be imported from
anywhere and import no context, and wiring may import any context's package.

**Independent Test**: In a context the map allows, import a module inside
another context's package and confirm the check fails. Import the same name from
the package instead and confirm it passes.

**Verification**:

- Automated: `tests/test_import_check.py`, one test per acceptance scenario 1 - 3, plus the shared-package edge cases
- Evidence: the `internal-module` and `shared-imports-context` blocks in `contracts/failure-output.md`

### Tests for User Story 2 ⚠️

- [X] T021 [P] [US2] Write fixture tests for US2's three scenarios: a Session module importing `wfctl.evidence._status` fails as `internal-module` and names `wfctl.evidence`; any module importing `core` or `tracker` passes; `cli.py` importing a context's package passes and importing a module inside one fails (FR-004, FR-005, FR-006); verify the tests fail first
- [X] T022 [P] [US2] Write fixture tests for the edge cases: a shared package importing a context fails as `shared-imports-context`, `_entry.py` follows the same rule as `cli.py`, an unmoved target is exempt from the internal-module rule, and an indirect dependency through an allowed package is not a violation; verify the tests fail first
- [X] T023 [P] [US2] Write tests that `internal-module` and `shared-imports-context` print in the shapes `contracts/failure-output.md` gives; verify the tests fail first

### Implementation for User Story 2

- [X] T024 [US2] Add rules 1, 3, 4, and 6 of plan item 4.5 to `violations()` in `.github/scripts/check_imports.py`, in that order relative to US1's rules, so the first rule that matches decides; verify with T021 and T022
- [X] T025 [US2] Add `render()` output for `internal-module` and `shared-imports-context` in `.github/scripts/check_imports.py`; verify with T023
- [X] T026 [US2] Validate US2 with `uv run pytest -q tests/test_import_check.py` — merge gate

**Checkpoint**: All six import rules run on fixtures.

---

## Phase 5: User Story 3 - Today's violations are listed, and the list only shrinks (Priority: P2)

**Goal**: The check passes on today's code with the shipped baseline, fails on
any new violation or unplaced module, and fails on any baseline line that
matches nothing.

**Independent Test**: Run the check on the current code and confirm it passes.
Delete one import that the baseline lists and confirm the check fails until
that baseline line is removed.

**Verification**:

- Automated: `tests/test_import_check.py`, one test per acceptance scenario 1 - 5, and the real-tree test (SC-001)
- Manual: quickstart.md's second exercise, removing the `_spec_copy` import from `wfctl/_spec_store.py` and reverting it
- Evidence: `uv run python .github/scripts/check_imports.py` printing the success line on the real tree

### Tests for User Story 3 ⚠️

- [X] T027 [P] [US3] Write fixture tests for scenarios 2 - 4: a violation line whose import is gone fails as `stale-violation` and says to delete the line, a placement line for a module that moved into its package or was deleted fails as `stale-placement`, and a new flat module with no line fails as `unplaced-module` (FR-008, FR-009); verify the tests fail first
- [X] T028 [P] [US3] Write tests that the three baseline failures print in the shapes `contracts/failure-output.md` gives; verify the tests fail first
- [X] T029 [P] [US3] Write real-tree tests: the check passes on this repository with `.github/scripts/check_imports.baseline` (scenario 1, SC-001), the baseline places 39 flat modules and lists 8 violations, and `_pipeline.py -> _session.py` is one of them (scenario 5, FR-014, SC-005); verify the tests fail first

### Implementation for User Story 3

- [X] T030 [US3] Implement `stale(baseline, graph, contexts)` in `.github/scripts/check_imports.py`, returning every placement line whose module no longer exists or sits in a package, and every violation line that matches no failing import (plan item 4.7); verify with T027
- [X] T031 [US3] Make `violations()` drop a failing import that a violation line lists, and add `render()` output for `unplaced-module`, `stale-placement`, and `stale-violation` in `.github/scripts/check_imports.py`; verify with T027 and T028
- [X] T032 [US3] Write `.github/scripts/check_imports.baseline` with one placement line for each of the 39 modules in research R7's placement table and one violation line for each of the 8 module pairs in its violation table, sorted with placements first (plan item 5, `contracts/baseline.md`). The user checks the placement lines against R7 before merging, so copy R7 exactly and make no judgment of your own; verify with T029
- [X] T033 [US3] Validate US3 with `uv run pytest -q tests/test_import_check.py`, `uv run python .github/scripts/check_imports.py`, and quickstart.md's second exercise — merge gate

**Checkpoint**: The check passes on the real code and fails on any regression.

---

## Phase 6: User Story 4 - The maintainer changes the map, and the check follows (Priority: P2)

**Goal**: The rules come from the domain page alone, and a page the check
can't read fails instead of reading as an empty map.

**Independent Test**: Add an arrow to a copy of the domain page and confirm an
import the check refused before now passes.

**Verification**:

- Automated: `tests/test_import_check.py`, one test per acceptance scenario 1 - 3
- Evidence: the `unreadable-domain` block in `contracts/failure-output.md`

### Tests for User Story 4 ⚠️

- [X] T034 [P] [US4] Write a fixture test that adding an arrow to the page makes a refused import pass with no change to the script (scenario 1, SC-004). The approval half of scenario 1 is tested in Phase 8. US1's rules already make this pass, so verify by deleting the arrow from the fixture and seeing the test fail
- [X] T035 [P] [US4] Write fixture tests that an arrow to or from an `(outside)` node is ignored (scenario 2), and that a missing contexts table, missing Shared packages table, missing `### Context Map` block, a label that matches no context, and a block line such as `EV ==> SC` each fail as `unreadable-domain` with the line number and never pass as an empty map (scenario 3, FR-010); verify the tests fail first
- [X] T036 [P] [US4] Write a test that `unreadable-domain` prints in the shape `contracts/failure-output.md` gives; verify the test fails first

### Implementation for User Story 4

- [X] T037 [US4] Make `read_domain()` in `.github/scripts/check_imports.py` accept only the three line forms in plan item 4.1, the `flowchart` header, a node `ID["Label"]`, and an edge `A -->|"text"| B` or `A --> B`, skip blank lines, and fail on any other line with its number. Also fail, naming the section, when a table or the block is missing; verify with T035 and with T008's real-page test, since the real block has a blank line between its nodes and edges
- [X] T038 [US4] Add `render()` output for `unreadable-domain` in `.github/scripts/check_imports.py`; verify with T036
- [X] T039 [US4] Validate US4 with `uv run pytest -q tests/test_import_check.py` — merge gate

**Checkpoint**: The map on the page is the only copy the check uses.

---

## Phase 7: User Story 5 - A bare "record" is kept for decision records (Priority: P3)

**Goal**: A context's package outside `arch` can't export a bare `Record`,
`record`, `records`, or `load_record`.

**Independent Test**: Export `load_record` from a fixture package other than
`arch` and confirm the check fails. Rename it `load_verdict` and confirm it
passes.

**Verification**:

- Automated: `tests/test_import_check.py`, one test per acceptance scenario 1 - 4, all on fixtures, since no package exists on this branch
- Evidence: the `reserved-name` block in `contracts/failure-output.md`

### Tests for User Story 5 ⚠️

- [X] T040 [P] [US5] Write fixture tests for the four scenarios: `Record` in a non-`arch` package's `__all__` fails, `CompletionRecord` passes, an unexported `record` in an underscore module passes, and `Record` in `arch`'s `__all__` passes (FR-012). Include the `reserved-name` output shape; verify the tests fail first

### Implementation for User Story 5

- [X] T041 [US5] Implement `exported_record_names(root, contexts)` in `.github/scripts/check_imports.py`, reading each moved package's `__init__.py` `__all__` with `ast`, and add `render()` output for `reserved-name` (plan item 4.6); verify with T040
- [X] T042 [US5] Validate US5 with `uv run pytest -q tests/test_import_check.py` and confirm the real tree still passes — merge gate

**Checkpoint**: The rule check is complete. Every FR from FR-001 to FR-012 has a test.

---

## Phase 8: Additions wait for a person (FR-015)

**Purpose**: A baseline line, map arrow, shared package, context-to-package
pair, or change to a `TRUSTED` file that a branch adds fails until a person
approves it with `wfctl arch approve-imports`. The record's approval paragraph
and plan item 6.3.5 state the limit. CI enforces the comparison, and the local
refusals stop a shortcut, not an agent set on getting around them.

**Independent Test**: On a fixture git repository with a script on its `main`,
add a placement line on a branch and confirm `--approvals` fails and lists it.
Add the note line with the right digest and confirm it passes. Add one more
line and confirm it fails again.

**Verification**:

- Automated: `tests/test_import_check.py` on fixture git repositories with their own notes, never this repository's history; `tests/test_review_notes.py`; `tests/test_review_gate.py`
- Manual: quickstart.md's third exercise, which needs the script on `main` and so runs on the first branch after this one merges. Note that in the PR body rather than claiming it ran
- Evidence: the `unapproved-addition` block in `contracts/failure-output.md`

### Tests first

- [X] T043 [P] Write fixture-repository tests for `--approvals --base <ref>` in `tests/test_import_check.py`: the merge base is the first line of output; each of the five kinds of addition is listed, including a renamed context adding each of its arrows, a swapped Package cell adding a pair, a trusted file absent at the merge base listed as `changed`, and one present there and gone at `HEAD` listed as `deleted`; a deleted baseline line or arrow is not an addition; the merge-base page parses with its allowances (no Package column, no Shared packages table); and a missing base ref, no merge base, or a page that fails to parse at the merge base exits 1 with git's or the parser's message (plan item 6, data-model §Approval); verify the tests fail first
- [X] T044 [P] Write fixture-repository tests in `tests/test_import_check.py` that the digest is the first 12 hex characters of SHA-256 over the sorted addition lines, that a note line `imports approved <digest>` on any commit in `<merge-base>..HEAD` under `refs/notes/wfctl-review` passes, that one more addition after the note fails, that `--json` prints the additions, digest, and `merge_base` without checking for a note, and that the failure prints the `unapproved-addition` block from `contracts/failure-output.md`; verify the tests fail first
- [X] T045 [P] Write a test in `tests/test_import_check.py` that pins the script's `IMPORTS_APPROVED_PREFIX` to `wfctl._review_notes.IMPORTS_APPROVED_PREFIX`, since the script can't import wfctl (plan item 7); verify the test fails first
- [X] T046 [P] Write tests in `tests/test_review_notes.py` for `run_approve_imports` on a fixture repository: it refuses without a terminal; it refuses when wfctl's own `__file__` sits inside one of the repository's worktrees, comparing resolved paths; it refuses on a detached `HEAD` and says to check out the PR's branch; it refuses when `origin/<current branch>` is missing and says to push, and when `HEAD` differs from it and says whether to push or pull; it exits 1 when `origin/HEAD` is unset or the fetch fails; it prints a `git diff` for a changed trusted file; it exits 1 when the trunk has no script and says the first baseline is approved by merging its PR by hand; and `approve_imports` itself refuses without a terminal (plan items 7 and 8); verify the tests fail first
- [X] T047 [P] Write tests in `tests/test_review_gate.py` that the worktree guard refuses `wfctl arch approve-imports` and `uv run wfctl arch approve-imports` from an agent with a refusal line, the same way it refuses the existing review sign-off command, and allows an unrelated `wfctl arch` command (plan item 9); verify the tests fail first

### Implementation

- [X] T048 Implement `--approvals --base <ref> [--json]` in `.github/scripts/check_imports.py` with plan item 6's five steps: merge base, `git show` reads of the page and baseline at both commits, one `git ls-tree <commit> -- <TRUSTED paths>` per side, the five kinds of addition, the digest, and the note lookup. Any failed git call exits 1 with git's message, and a shallow clone or missing ref is never a reason to skip; verify with T043 and T044
- [X] T049 Add `render()` output for `unapproved-addition` in `.github/scripts/check_imports.py`, with the `baseline`, `map`, and `trusted` labels and the instruction to run the installed `wfctl`; verify with T044
- [X] T050 Add `IMPORTS_APPROVED_PREFIX`, `approve_imports(repo_root, digest)`, and `run_approve_imports(repo_root)` to `wfctl/_review_notes.py`. `run_approve_imports` carries plan item 8's six steps, writes the trusted copy under `tempfile.mkdtemp()`, and runs it with `sys.executable -I`. `approve_imports` repeats the terminal check, appends the line to `HEAD`'s note, sends the ref to `origin` the way a sign-off does, and calls the existing `rerun`; verify with T045 and T046
- [X] T051 Add `wfctl arch approve-imports` to `wfctl/cli.py`. It checks stdin and stdout are a terminal, as the review sign-off command does, then calls `run_approve_imports` and holds no other logic (plan item 8); verify with T046 and `uv run wfctl arch --help` listing the command
- [X] T052 Add `_APPROVE_IMPORTS = re.compile(r"\barch\b.*\bapprove.?imports\b", re.S)` beside `_SIGN_OFF` in `wfctl/_review_gate.py`, with a matching refusal line (plan item 9); verify with T047
- [X] T053 Validate Phase 8 with `uv run pytest -q tests/test_import_check.py tests/test_review_notes.py tests/test_review_gate.py`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The approval check works on fixture repositories, and the
command is refused from an agent's shell.

---

## Phase 9: Where each mode runs (FR-013)

**Purpose**: `wfctl verify`, CI's `lint` job, and the suite run the branch's
copy of the rule check. CI's `review` job runs the default branch's copy of
both modes.

- [X] T054 Add `["uv", "run", "--frozen", "--extra", "dev", "python", ".github/scripts/check_imports.py"]` to `verify` in `wfctl.json` (plan item 10); verify with `uv run wfctl check config` and `uv run wfctl verify`
- [X] T055 [P] Add a step to the `lint` job in `.github/workflows/ci.yml` that runs `python3 .github/scripts/check_imports.py` with the branch's copy, needing no history or notes (plan item 11); verify with a new test in `tests/test_review_workflow.py` that the `lint` job runs the script, and on the PR's CI run
- [X] T056 [P] Add a step to the `review` job in `.github/workflows/review.yml`, after the notes fetch, with plan item 12's three parts: take the default branch from `github.event.repository.default_branch` through `env`, check `origin/$DEFAULT^{commit}` resolves in `pr`, write the default branch's script to `$RUNNER_TEMP` with `git -C pr show`, and run it with `python3 -I` in `pr`, first with no arguments, then with `--approvals --base "origin/$DEFAULT"`. The step runs nothing from `pr/`. Verify with `uv run pytest -q tests/test_review_workflow.py`, whose existing tests check that the job runs nothing from `pr/` and pastes no expression into a shell line, plus new tests that the step takes the default branch through `env`, writes the script under `$RUNNER_TEMP`, and runs it with `python3 -I`. The step doesn't run on this branch's own PR, since `main`'s `review.yml` lacks it, so these tests are the only check it gets before merge
- [ ] T057 Validate Phase 9 with `uv run wfctl check config` and `uv run wfctl verify`, and check the real-tree run finishes in under 5 seconds (SC-003) — merge gate

**Checkpoint**: Both modes run where FR-013 says.

---

## Phase 10: Polish and cross-cutting concerns

- [X] T058 [P] Add a short section to `AGENTS.md` saying what the check enforces, how to read a failure, which additions wait for `wfctl arch approve-imports`, that the person runs the installed `wfctl` and never `uv run wfctl` in a worktree, that they reinstall from `main` once this branch merges, and the two recovery routes when `main`'s copy blocks a branch (plan item 14). Load the `writing-style` skill first; verify by reading it against plan item 14
- [X] T059 [P] Create `changes/544.addition.md` with `uv run towncrier create 544.addition.md --content "…"`, saying every install gains `wfctl arch approve-imports` and a guard refusal for it, and that wfctl's own CI checks its imports against the Context Map (plan item 15, research R9); verify with `uv run wfctl verify`'s release note check
- [ ] T060 Run the definition of done from quickstart.md: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl verify`, `uv run wfctl check config`, and `uv run wfctl doctor` — merge gate
- [ ] T061 Before the PR opens, write in its body that the user approves this branch's baseline and both `TRUSTED` files by merging the PR by hand from their own terminal, after checking the 39 placement lines against research R7 and reading the diffs of `.github/scripts/check_imports.py` and `.github/workflows/review.yml`. The agent doesn't merge it (plan, Phase D closing paragraphs, FR-015); verify with `wfctl check-body`

---

## Dependencies and execution order

### Phase dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup, and blocks every story
- **US1 (Phase 3)**: depends on Foundational
- **US2 (Phase 4)**: depends on US1, since it adds rules to the ordered list in `violations()` and output to `render()`
- **US3 (Phase 5)**: depends on US1 and US2, since the real-tree test needs every import rule to produce the 8 violations the baseline lists
- **US4 (Phase 6)**: depends on Foundational only. It changes `read_domain()`, which no story after Phase 2 edits
- **US5 (Phase 7)**: depends on Foundational only
- **Approval (Phase 8)**: depends on US3 and US4, since it compares the baseline and the strict page reader at two commits
- **Wiring (Phase 9)**: depends on US3, since `wfctl verify` must pass on the real tree. T056 also depends on Phase 8
- **Polish (Phase 10)**: depends on everything before it

### Within each phase

- Tests are written first and fail before the implementation.
- Every task in `.github/scripts/check_imports.py` edits the same file, so implementation tasks there run in sequence even where their tests run in parallel.
- Each phase ends on its merge gate.

### Parallel opportunities

- T003 and T004 edit the domain page, and T005 to T009 write tests, so they can run alongside each other once T002 is done. T003 and T004 edit the same file, so one person does both.
- Within each story, the test tasks marked [P] run together.
- US4 and US5 can run in parallel with US2 and US3, since they touch different functions. They still share one script file, so merge them one at a time.
- T055 and T056 edit different workflow files, though both add tests to `tests/test_review_workflow.py`. T058 and T059 edit different files.

## Parallel example: Phase 2 tests

```text
Task: "Fixture tests for read_domain in tests/test_import_check.py"   (T005)
Task: "Fixture tests for read_baseline in tests/test_import_check.py" (T006)
Task: "Fixture tests for module_contexts in tests/test_import_check.py" (T007)
```

All three write to one test file, so they don't depend on each other but can't
be edited at the same time. One agent writes them in sequence, or each lands in
its own test class.

## Implementation strategy

### MVP first

1. Phases 1 and 2.
2. Phase 3, US1: an import against the map fails with the boundary drawn.
3. Stop and validate with quickstart.md's first exercise.

The MVP can't merge on its own. The real tree breaks the map in 8 places, so
`wfctl verify` would fail until US3's baseline lands.

### Incremental delivery

1. Setup, Foundational, US1, and US2 give every import rule on fixtures.
2. US3 makes the check pass on the real tree, and is the first point where it can join `wfctl verify`.
3. US4 and US5 finish the rule check.
4. Phase 8 adds the approval check and the command.
5. Phase 9 wires both modes in, and Phase 10 finishes the docs and the release note.

`/speckit.decompose` decides the PR boundaries. Nothing here assumes a phase is a PR.

## Notes

- The domain page drawings in `design.md` predate the amended record and name a "public module". `contracts/failure-output.md` governs the output.
- Writing a scan or PR text through a shell heredoc containing the review sign-off command's words trips the worktree guard's regex. Use the Edit tool.
- Commit after each task or logical group, and run each phase's merge gate before moving on.
~~~~
