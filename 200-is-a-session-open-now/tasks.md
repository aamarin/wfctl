# Tasks: is a session open now?

**Input**: Design documents from `specs/200-is-a-session-open-now/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and
`uv run mypy wfctl/` are this repository's whole bar and every phase ends on
them. `uv run` is not optional — the dev deps are pinned on purpose and a bare
`pytest` reports failures a green tree does not have.

**Organization**: grouped by user story. Phase 3 alone closes #200 and is the
MVP; phases 4 and 5 protect what phase 3 would otherwise break.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel — different files, no dependency on incomplete work
- **[Story]**: US1, US2, US3 from spec.md
- Every implementation task names a verification path or is paired with one

## Path Conventions

Single project. `wfctl/` and `tests/` at the repository root; shipped skills
under `wfctl/agents/skills/`.

---

## Phase 1: Setup

**Purpose**: establish the baseline this change is measured against.

- [X] T001 Confirm the bar is green before touching anything: run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` and record the test count in the branch's working notes
- [X] T002 Capture the released behaviour this feature must not change: run `uv run wfctl status --json` on a branch with a recorded session and save the payload to compare against in T028

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the identity has to be readable, storable and reportable before any
story can use it. Every task here blocks all three stories.

- [X] T003 Add `last_session_id(agent_dir)` to `wfctl/_session.py`, returning the `session_id` of the last `start` line or `None`, skipping malformed lines the way `session_started` does; verify with `tests/test_agent_session.py::test_last_session_id_reads_the_most_recent_start`
- [X] T004 Add `session_open_for(agent_dir, session_id)` to `wfctl/_session.py`, returning the holder relation as one of `"self"`, `"other"`, `"none"`, `"unknown"` per contracts/cli.md; verify with `tests/test_agent_session.py::test_session_open_for_returns_unknown_when_no_id_presented`
- [X] T005 Treat an empty or whitespace-only identity as absent in `wfctl/_session.py`, so `${WFCTL_SESSION_ID:+…}` collapsing unset and empty does not diverge downstream; verify with `tests/test_agent_session.py::test_empty_session_id_is_absent_not_an_identity`
- [X] T006 Add `--session-id` to `start_cmd` in `wfctl/cli.py` with a `WFCTL_SESSION_ID` environment fallback, resolved once and passed down rather than re-read per call site; verify with `tests/test_cli_start.py::test_session_id_falls_back_to_the_environment`
- [X] T007 Add `session_open` and `session_holder` to `PipelineReport` in `wfctl/_pipeline.py` and fill them in `build_report`, leaving `session_started` untouched; verify with `tests/test_pipeline.py::test_report_carries_both_session_answers`
- [X] T008 Thread the caller's identity into `build_report`'s signature in `wfctl/_pipeline.py`, defaulting to `None` so every existing caller keeps compiling and keeps its current behaviour; verify with `uv run mypy wfctl/` and `tests/test_pipeline.py::test_build_report_without_an_id_reports_unknown`
- [X] T009 Emit `session_open` and `session_holder` in the `status --json` payload in `wfctl/cli.py`; verify with `tests/test_cli_status.py::test_json_payload_carries_the_new_fields`
- [X] T009a Assert the state dir gains no new file once an identity is recorded — FR-010 forbids a separate file and no task asserts it, so a `session.json` added later would pass every other test here; verify with `tests/test_agent_session.py::test_the_identity_adds_no_file_to_the_state_dir`

**Checkpoint**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` all green. The payload carries the new answers and nothing reads them yet.

---

## Phase 3: User Story 1 — A second conversation is told the truth (P1) 🎯 MVP

**Goal**: a conversation that did not open the branch's session is refused by
every gate, in wording that names the conversation rather than the branch.

**Independent Test**: on a branch with a recorded session, present an identity
that was never recorded and invoke a gated step. The gate refuses and names the
remedy. Ship only this phase and #200 is closed.

- [X] T010 [US1] Add the second refusal string to `wfctl/cli.py` beside `_NO_SESSION`, naming the conversation rather than the branch, per contracts/cli.md; verify with T011
- [X] T011 [P] [US1] Assert the two refusal strings are distinct and that neither is a substring of the other in `tests/test_cli_status.py::test_the_two_refusals_are_distinct`, asserting distinctness rather than either one's wording so a copy edit does not fail the suite
- [X] T012 [US1] Gate `resume_cmd` in `wfctl/cli.py` on the holder relation, refusing with exit 1 when it is `"other"` and proceeding when it is `"self"` or `"unknown"`; verify with `tests/test_cli_resume.py::test_resume_refuses_a_conversation_that_does_not_hold_the_branch`
- [X] T013 [US1] Gate `end_cmd` in `wfctl/cli.py` the same way, refusing rather than taking over, because ending writes a handoff nothing recovers; verify with `tests/test_cli_end.py::test_end_refuses_rather_than_taking_over`
- [X] T014 [US1] Render the held-by-another state in `wfctl status`'s console output in `wfctl/cli.py`, so a reader can tell a fresh branch from a held one without opening a file (SC-005); verify with `tests/test_cli_status.py::test_console_names_the_holder_relation`
- [X] T015 [US1] Change `speckit-orchestrate` step 0 in `wfctl/agents/skills/speckit-orchestrate/SKILL.md` to read `session_open` instead of `session_started`, and to render the second refusal when `session_holder` is `"other"`; verify by running `uv run wfctl install-skills` and exercising the gate by hand per quickstart.md
- [X] T016 [US1] Present the host's identity from `wfctl/agents/skills/start-session/SKILL.md` in the `${WFCTL_SESSION_ID:+--session-id "$WFCTL_SESSION_ID"}` shape, naming no host-specific variable (FR-013, `no-hardcoded-agent`); verify with `tests/test_skills_ship.py::test_start_session_names_no_host_variable`
- [X] T017 [P] [US1] Assert wfctl's own source never reads a host-specific session variable, in `tests/test_architecture.py::test_no_host_session_variable_is_named_in_source` — the check `a-rule-is-expressed-as-a-check` requires for a rule visible in an artifact the work already produces
- [X] T017a [P] [US1] Assert no shipped skill derives the session-open answer from the event log itself — grep `wfctl/agents/` for `events.jsonl` and allow only `start-session`'s stop-kind read, which asks a different question (FR-011); verify with `tests/test_skills_ship.py::test_no_skill_reads_the_event_log_for_session_state`

**Verification**: `uv run pytest -q` green; `uv run wfctl install-skills` then the two-conversation sequence in quickstart.md § *See it fixed*, confirming the refusal, its wording, and exit 1.

**Checkpoint**: #200's defect is closed. A displaced conversation is refused and cannot yet recover — phase 4 is what makes that state exitable.

---

## Phase 4: User Story 2 — A displaced conversation recovers with one command (P2)

**Goal**: `/start-session` takes the branch over, and the takeover is visible.

**Independent Test**: from the refused state, run the session-opening command
once and confirm the same gated step now passes. No file deleted, no flag passed,
nothing edited by hand.

- [X] T018 [US2] Append a `start` event carrying the new identity in `start_cmd`'s already-initialized path in `wfctl/cli.py` when the presented identity differs from the holder; verify with `tests/test_agent_session.py::test_start_with_a_new_id_appends_a_start_event`
- [X] T019 [US2] Keep `start` idempotent in the log when the presented identity equals the holder, preserving the two existing tests that pin `events.jsonl` byte-identical after a repeat `start`; verify with `tests/test_agent_session.py::test_start_is_idempotent`
- [X] T020 [US2] Leave the holder untouched when no identity is presented, so an unwired caller never displaces a wired one; verify with `tests/test_agent_session.py::test_a_caller_with_no_id_never_takes_over`
- [X] T021 [US2] Print the takeover on `start`'s console output in `wfctl/cli.py` per contracts/cli.md (FR-014, SC-007); verify with `tests/test_cli_start.py::test_takeover_is_announced`
- [X] T022 [US2] Accept the first identified session on a branch whose holder is absent as a takeover rather than a refusal (FR-012); verify with `tests/test_agent_session.py::test_a_branch_recorded_before_identities_accepts_the_first_one`
- [X] T023 [P] [US2] Assert a takeover leaves the earlier `start` line intact, so the history of who held the branch survives; verify with `tests/test_agent_session.py::test_takeover_appends_and_never_rewrites`
- [X] T023a [US2] Assert no sequence of interrupted sessions needs manual cleanup (SC-004, which no other task covers) — open, abandon without `end`, take over, abandon again, take over again, and confirm every gate still answers with no file deleted or edited by hand; verify with `tests/test_agent_session.py::test_abandoned_sessions_need_no_cleanup`

**Verification**: `uv run pytest -q` green; the full quickstart.md § *See it fixed* sequence including the takeover and the reversal, confirming A is refused after B takes over.

**Checkpoint**: the refusal in phase 3 has an exit, and the branch's history of holders is readable.

---

## Phase 5: User Story 3 — A repo nobody wired up is untouched (P3)

**Goal**: a caller presenting no identity sees the released behaviour, everywhere.

**Independent Test**: with no identity presented, exercise every gate this
feature touches and diff the outcomes against the payload captured in T002.

- [X] T024 [US3] Mirror `session_started` into `session_open` when the holder relation is `"unknown"`, in `wfctl/_pipeline.py`; verify with `tests/test_pipeline.py::test_unwired_caller_sees_the_released_answer`
- [X] T025 [US3] Enumerate the gate surface this feature touches in `tests/test_no_regression_unwired.py`'s module docstring — `status`, `resume`, `end`, `start`, and the orchestrate gate — because SC-002 measures against a surface nobody had written down (the row `/speckit.clarify` deferred here)
- [X] T026 [US3] Assert every enumerated gate behaves identically with no identity presented, parametrised over the four branch states in `tests/test_no_regression_unwired.py`; verify with `uv run pytest -q tests/test_no_regression_unwired.py`
- [X] T027 [P] [US3] Assert `session_started` answers identically to the released version across the same four states (SC-006), in `tests/test_pipeline.py::test_session_started_is_unchanged`
- [X] T028 [US3] Diff a live `uv run wfctl status --json` against the payload captured in T002 with `WFCTL_SESSION_ID` unset, confirming only additive keys appear; verify by hand per quickstart.md § *See that an unwired repository is untouched*

**Verification**: `uv run pytest -q` green; the quickstart's unwired sequence, ending on the `grep` that confirms the holder was not displaced.

**Checkpoint**: all three stories delivered. An unwired repository is provably untouched.

---

## Phase 6: Polish & Cross-Cutting

- [X] T029 [P] Document `--session-id` and `WFCTL_SESSION_ID` in `README.md` beside the existing `WFCTL_AGENT` guidance, since the mapping belongs in a shell profile and a reader needs to find that out somewhere; verify by reading the rendered section
- [X] T030 Ask the reader where they agreed to `docs/architecture/design/200-session-id-rides-on-the-start-event.md`, then run `uv run wfctl arch accept 200-session-id-rides-on-the-start-event --agreed "<where>"`. Phases 3–5 going green is the record being *implemented*, which `arch accept`'s own help names as the one evidence it will not promote on — "a record promoted on its own implementation can never disagree with the implementation" — and `--agreed` has no value a run can supply for itself; verify with `uv run wfctl arch context` listing the slug
- [X] T031 Revisit the nesting-marker paragraph in `docs/architecture/session-identity-comes-from-the-caller.md` — the measurement found the flag set with no parent, so the rule built on it has no signal to key on; amend or remove it, or record in the branch's notes why it stands; verify with `uv run wfctl arch check docs/architecture/session-identity-comes-from-the-caller.md`
- [X] T032 Run `uv run wfctl doctor` and confirm no finding stands; then `uv run wfctl install-skills` and exercise `/start-session` and the orchestrate gate by hand, because the suite checks that skills ship and cross-reference, not that they read well
- [x] T033 Run the review panel over the whole change before opening anything — `fanning-out-code-review` — and carry every finding not applied into the change description's Additional Context; verify by the panel's own reconciliation step

---

## Dependencies

```
Phase 1  Setup
   └─► Phase 2  Foundational  (T003–T009)
          ├─► Phase 3  US1  (T010–T017)   ← MVP, closes #200
          │      └─► Phase 4  US2  (T018–T023)
          └─► Phase 5  US3  (T024–T028)
                 └─► Phase 6  Polish  (T029–T033)
```

**US1 before US2**: the takeover exists to give the refusal an exit, so the
refusal has to exist first. Building US2 alone produces a takeover nobody is
displaced by.

**US3 parallel to US1**: it reads the same foundational functions and touches
different files — its tests assert absence of change, which needs nothing US1
adds. Phase 6 waits for both.

## Parallel Execution

Within Phase 2: T003, T004 and T005 touch one file and are sequential; T006 and
T007 touch different files and run alongside each other once T004 lands.

Within Phase 3: T011 and T017 are `[P]` — new test files with no dependency on
the implementation tasks beside them.

Within Phase 4: T023 is `[P]` — a new assertion over behaviour T018 establishes.

Within Phase 5: T027 is `[P]` — a different file from T024–T026.

Phases 3 and 5 run in parallel in full once Phase 2 is green.

## Implementation Strategy

**MVP is Phase 3.** It closes the defect in #200 and is independently
demonstrable: present an unrecorded identity, be refused. It ships a rough edge —
a refused conversation has no way back — which is why phase 4 follows
immediately rather than being deferred.

**Phase 5 is not optional polish.** SC-002 is the constraint most easily lost
during implementation, and the one whose failure is invisible from inside the
feature: every unwired repository regressing at once looks, from the tests this
change adds, exactly like success.

**Phase 6 before any change is opened.** T030 and T031 are record work the
implementation earns rather than discovers, and T033 is the review panel, which
runs unattended and whose findings become commits before a description is written.
