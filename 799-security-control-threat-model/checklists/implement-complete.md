Implementation complete: 2026-11-18

## Tasks at completion

~~~~markdown
# Tasks: Security control threat model

**Input**: Design documents from `specs/799-security-control-threat-model/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/threat-model-section.md, quickstart.md
**Design records**: `docs/architecture/design/799-threat-model-in-the-record.md` (present). Level 2: `security-change-needs-threat-model.md`, `accept-check-threat-model.md`.

The plan review's MAJOR and MINOR findings (PR-001 to PR-007 in `plan-review.md`)
are folded into the tasks they bear on, and each task names the finding.

Trigger wording, everywhere: "adds, removes, loosens, or tightens a security
control" (clarify Q1). design.md's draft text says "narrows", and these tasks
replace it (PR-004).

## Phase 1: Setup

- [x] T001 Create the folder `wfctl/agents/skills/architecture-decisions/references/`. Verify: `ls` shows it.

## Phase 2: Foundational

- [x] T002 Write `wfctl/agents/skills/architecture-decisions/references/threat-model.md`: what a security control is, with wfctl's four kinds as examples; when the section is required (the trigger wording above); the `## Threat model` section with its four `###` parts, `Defends against`, `Must keep catching`, `Accepts`, and optional `Must let through`, in that order; what each holds; that each list item is a short description, a colon, and the form in backticks as the item's last code span; that each "Must keep catching" form gets a test that fails if the control lets it through; and that a removal writes "Accepts" and leaves "Must keep catching" empty. Verify: T011's heading test reads this file.
- [x] T003 Add a paragraph to `wfctl/agents/skills/architecture-decisions/SKILL.md`, under "Writing one", saying a record for a security control change carries a `## Threat model` section and pointing at `references/threat-model.md`. Verify: `grep -n "references/threat-model.md" wfctl/agents/skills/architecture-decisions/SKILL.md`.

## Phase 3: User Story 1 - The author writes a threat model before code (P1)

**Goal**: a control change reaches the threat-model reference at level 2, before code.
**Independent Test**: walk a pretend control change through the installed `design-passes` and `design-levels` (quickstart steps 1-5).

### Verification

- `uv run wfctl install-skills`, then the quickstart walkthrough steps 1-5.
- `uv run pytest -q tests/test_threat_model_skills.py`.

### Implementation

- [x] T004 [US1] In `wfctl/agents/skills/design-passes/SKILL.md` step 1, after Nygard's five categories under the design-decision question, add a paragraph: a change that adds, removes, loosens, or tightens a security control answers this question yes, however small; what a security control is in one sentence; why (a loosened control can let through an action that can't be undone, such as an accepted record or a merged PR, and a tightened one can refuse ordinary work, as #769 did before #792); and that a change leaving what the control refuses and lets through unchanged, such as a rename, doesn't count. Verify: quickstart step 3.
- [x] T005 [US1] In `wfctl/agents/skills/design-levels/SKILL.md` level 2, after "The answer is written as a record, not as a section", add a paragraph: when the change adds, removes, loosens, or tightens a security control, the record carries a `## Threat model` section, written before any code, following `.agents/skills/architecture-decisions/references/threat-model.md`; and the method is `architecture-design` with safety under the stated adversary as the driver. Add a Verification checklist item for it. Verify: quickstart step 4.

## Phase 4: User Story 2 - The security reviewer judges against the record (P1)

**Goal**: the reviewer finds the threat model itself, judges against the trunk's accepted version, and names the record.
**Independent Test**: read the installed `reviewing-security` and `fanning-out-code-review` as a reviewer and a coordinator on the pretend change (quickstart steps 6-7).

### Verification

- Quickstart steps 6-7.
- `uv run pytest -q tests/test_threat_model_skills.py`.
- SC-003: this branch's own security group reports each carry a `Judged against:` line (PR-005).

### Implementation

- [x] T006 [US2] Add a section "Judge against the threat model" to `wfctl/agents/skills/reviewing-security/SKILL.md`, before "Write one report". It says:
  1. Find the threat models: run `wfctl arch-root`, then `git grep -l '^## Threat model' <head> -- <arch-root>`, and keep the records whose `governs` field and Decision name a control the run's commits change.
  2. Judge against the trunk's version when the record is accepted there. The trunk is the `trunk` key in `git show origin/HEAD:wfctl.json` when that sets one, and `origin/HEAD` otherwise, the same trunk reviews already measure against. Read the record with `git show <trunk>:<path>`; it's accepted there when its frontmatter `status` is `accepted`. A branch that also changes the record's status doesn't change this, since the trunk's copy is the one the user accepted (PR-008). If the branch changed an accepted record's lists, judge against the trunk's lists, and report any form moved out of "Must keep catching" or into "Accepts" as a finding, since only the user moves the bar (PR-001, FR-013). A record proposed on the branch is judged as written, and the report says it's proposed.
  3. The four cases: a "Must keep catching" form let through is a finding; a "Must let through" form refused is a finding; an "Accepts" form isn't a finding and goes under the judged-against line as a note; a form in none of the lists is a finding if an agent the "Defends against" part describes could reach it and a note otherwise, and either way the reviewer asks for it to be added to a list (FR-006, PR-003).
  4. A change that adds, removes, loosens, or tightens a control with no threat model is a finding titled "Security control changed with no threat model" (FR-007).
  5. Name each record judged against with a `Judged against: <path> (<status>)` line under the `## security-and-hardening` heading. Add that line to the report example.
  6. Name the four headings, `Defends against`, `Must keep catching`, `Accepts`, and `Must let through`, and link `../architecture-decisions/references/threat-model.md`.
  Verify: quickstart step 6 and T011.
- [x] T007 [US2] In `wfctl/agents/skills/fanning-out-code-review/SKILL.md` Step 2, after the six dispatch bullets, add a paragraph: the brief for a security reviewer states no security bar and names no threat-model record, since the reviewer finds the record itself and judges against what the user accepted; a coordinator that writes a bar can set it stricter or looser than the record, which is what looped #792. Verify: quickstart step 7.

## Phase 5: User Story 3 - The guard's threat model is a record (P2)

**Goal**: a test keeps `accept-check-threat-model.md` and the guard in agreement.
**Independent Test**: the new test passes, and fails when one listed form is changed to one the guard lets through.

### Verification

- `uv run pytest -q tests/test_accept_check_threat_model.py`.
- Mutation: change "Must keep catching" item 1 in a scratch copy read by the test's helper, or temporarily in the record, and confirm a failure; restore from a scratchpad backup.

### Implementation

- [x] T008 [US3] Write `tests/test_accept_check_threat_model.py`. It reads `docs/architecture/accept-check-threat-model.md` from `Path(__file__).resolve().parent.parent`, splits it at `### ` headings, and takes the last backtick span of each numbered item under `Must keep catching` and `Must let through` (some items name `--dry-run` or `arch` in their description first, so it's the last span, not the first; PR-007). For each "Must keep catching" form it asserts both that `_review_gate.read` returns `ACCEPT_REFUSAL` and that `wfctl.guard._hook.worktree_guard` on a JSON payload `{"tool_input": {"command": form}, "cwd": <repo root>}` returns non-zero, so the hook's substring prefilter is covered too (PR-002). For each "Must let through" form it asserts `ACCEPT_REFUSAL` isn't among `read`'s refusals, and that the hook doesn't refuse it with the accept refusal text (PR-002). It asserts each list is non-empty. Test names are sentences, and docstrings say why the test exists. Verify: `uv run pytest -q tests/test_accept_check_threat_model.py`.
- [x] T009 [US3] Check how `worktree_guard` reports a refusal (return code and stderr) in `wfctl/guard/_hook.py` before writing T008's hook assertion, and use the same `guard` fixture shape `tests/test_review_gate.py` uses if it fits. Verify: the T008 test fails when one "Must keep catching" form is replaced with `wfctl arch context`.

## Phase 6: Cross-cutting tests and polish

- [x] T010 [P] Write `tests/test_threat_model_skills.py` reading the bundle through `files("wfctl") / "agents" / "skills"` (tests don't ship with the bundle; PR-006). It asserts the reference's `##` heading `Threat model` and its four `###` headings are each named in `reviewing-security/SKILL.md`, that `design-levels/SKILL.md` and `reviewing-security/SKILL.md` both link `architecture-decisions/references/threat-model.md`, and that `design-passes/SKILL.md` carries the trigger wording "adds, removes, loosens, or tightens". Verify: `uv run pytest -q tests/test_threat_model_skills.py`.
- [x] T011 Mutation check for T010: in a scratchpad backup of `reviewing-security/SKILL.md`, rename one heading in the real file, confirm the test fails, then restore from the backup (SC-004). Verify: the test fails, then passes after the restore.
- [x] T012 Write `changes/799.change.md` with `uv run towncrier create 799.change.md --content "…"`, category `change`: a change to a security control now writes a threat model before code, and security reviewers judge against it. Verify: `uv run wfctl verify` release-note check.
- [x] T013 Run `uv run wfctl install-skills` and the whole quickstart walkthrough, then `uv run wfctl doctor` (PR-005). Verify: doctor exits 0.
- [x] T014 Run `uv run wfctl arch accept --dry-run -- <slug>` for `security-change-needs-threat-model` and `accept-check-threat-model` (PR-005). Verify: each prints "would be accepted".
- [x] T015 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, then `uv run wfctl verify`. Verify: all green.

- [x] T017 Added at the user's request during implement: a "How to write it" section in `references/threat-model.md` built on Shostack's four questions, with OWASP's review checklist and sndcr's rule that a form's test exists now; and two opt-in domain guides, `threat-model-agent-commands.md` (Saltzer and Schroeder's principles) and `threat-model-services.md` (OWASP and the STRIDE table in `security-and-hardening`). Vendoring Anthropic's whole-system `threat-model` skill was split out to #818. Verify: `uv run pytest -q` green with the guides installed.

- [x] T016 FR-011: `docs/architecture/accept-check-threat-model.md` carries R-013's decision, its accepted gap, and both lists. Done in brainstorm, commit a1fa811. Verify: `uv run wfctl arch accept --dry-run -- accept-check-threat-model` (T014).

## Dependencies

- T001 → T002 → T003, T005, T006, T010.
- T004 and T007 depend on nothing but can wait for T002 so the wording matches.
- T009 → T008.
- T010 → T011.
- T012-T015 last.

## Parallel opportunities

- T004, T005, T006, T007 edit different files and can run together once T002 is done.
- T008 and T010 are different test files.

## Implementation strategy

US1 and US2 together are the MVP: without both, a threat model is either never written or never read. US3 is the first record the step produces and makes its lists a check.
~~~~
