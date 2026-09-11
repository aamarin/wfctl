# Analysis scan — #352

## Session 2026-09-11

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 11 · Critical: 0 · Acted on: 8 · Accepted: 3 (plus 6 from a review panel, below)
- Detail: `<spec-root>/352-session-stopped-not-finished/checklists/analysis-report.md`
- Mode: auto-approve. Step 8's remediation question was settled by the run rather
  than by a human. The eight edits below land in `tasks.md` only — no spec, plan
  or source file was touched — and every one of them is a task whose stated
  verification could not observe what the task changes. A reviewer can take any
  of them back on the pull request.

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Outstanding (1 LOW, accepted) |
| C · Underspecification | Resolved (2 fixed; 1 LOW stands) |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved (3 fixed; 1 LOW stands) |
| F · Inconsistency | Resolved (3 fixed) |
| G · Design-record contradiction | Deferred (no design.md) |
| Requirement-to-task coverage | 85% |

`D · Clear` over an absent constitution: this repo has no
`.specify/memory/constitution.md`, and `plan.md` substitutes the gates from
`AGENTS.md` and the ten accepted records `wfctl arch context` projects, recording
the substitution in Complexity Tracking as the template requires. The
substituted gates were read and no requirement, plan element or task conflicts
with one.

`G · Deferred` because `FEATURE_DIR` carries no `design.md` —
`reading-design-records`' fourth state, `unknown`. `/speckit.brainstorm` was
skipped on this branch, so it is not established that there were no level-3
decisions; nothing is known either way. The level-2 record this branch did write,
`stop-kind-is-a-field-not-an-event.md`, is not in pass G's scope and was read as
input to the other six passes instead.

### Findings

- **F · Inconsistency, HIGH** — T004 said to rewrite step 9's first row "leaving
  rows two and three as they stand", while `contracts/start-session-step-9.md`
  rewrites row two as well. Row two's present condition — "a summary, and an
  `end` event" — is true of a *continued* stop too, so left alone it matches the
  same branch row one now matches, and the routing rule is ambiguous on exactly
  the case the feature exists to fix.
  → Fixed: T004 now rewrites both rows and says why row two is not optional.
  Decided against leaving it to T006's prose reconciliation: T006 verifies by
  reading, and a second matching row is a defect a reader is as likely to
  rationalise as to catch.

- **E · Coverage gap, HIGH** — `_row()` in
  `tests/test_start_session_asks_conditionally.py` selects a row by its condition
  column's prefix and calls `pytest.fail` when none matches. T003 and T004 change
  the prefixes of rows one and two, so two existing tests go red, and no task
  owned updating them. T007's merge gate would have been the first thing to say
  so, with no assignee.
  → Fixed: T002 gained clause (b), re-anchoring both assertions.
  Decided against deleting them: they carry #244's two acceptance criteria, and
  the branch that protects an attended session is the one they pin.

- **C · Underspecification, HIGH** — T003 rewrites **step 4** and verified "with
  T002's assertions". Every helper in that module slices from step 9's heading
  downward (`text[text.index(_STEP_NINE_HEADING):]`), so step 4 sits above the
  slice and is unreachable. T003 would have shipped with no verification at all.
  → Fixed: T002 gained clause (c), a `_step_four()` slice asserting the stated
  `grep … | tail -1` command and its three-outcome table; T003's verify now names
  it specifically.
  Decided against verifying T003 by reading, as T006 does: the `tail -1` is the
  whole of FR-007, and a rule whose only check is a reader is the rule's absence
  under `a-rule-is-expressed-as-a-check`.

- **E · Coverage gap, HIGH** — T020 asserts three existing readers reach today's
  verdict (SC-005) and verified with `tests/test_session_existence.py
  tests/test_agent_session.py`. Neither module references
  `_stall._passes_this_sitting` or `_stall.opens_a_new_sitting`; `tests/test_stall.py`
  is the only module that exercises sitting behaviour. Two of the three readers
  named were unverified by the command given.
  → Fixed: `tests/test_stall.py` added to T020's command, with a line saying why
  it is not optional.

- **C · Underspecification, MEDIUM** — T016 asserted "the most-recent-wins rule
  (FR-007)" in `tests/test_session_stopped_not_finished.py`, a CLI-level module.
  FR-007 is `tail -1` inside a skill markdown; there is no wfctl function to
  call, and Phase 5 declares no production change. As written the test could only
  observe the log's file order, which is FR-008's property and already T015's.
  → Fixed: T016 restated as what it can observe, with an explicit "this does not
  verify FR-007" and a pointer to what does.
  Decided against moving T016 into US1: it reads a history only US2's writer
  produces, and the phase ordering is the dependency graph's, not a filing error.

- **F · Inconsistency, MEDIUM** — the `- [ ] (fill in)` placeholder is written by
  `_render_session_summary` at `wfctl/_session.py:458`; T011 put the detector
  that recognises it in `cli.py`. The literal would live in two modules with
  nothing binding them, so a change to the template kills the FR-013 warning
  silently.
  → Fixed: T011 now requires the placeholder to come from a shared constant
  beside the template.
  Decided against a test asserting the two strings match: a constant makes the
  drift unrepresentable, and a test asserting two literals are equal is the
  weaker form of the same rule.

- **E · Coverage gap, MEDIUM** — "a continued stop never relaxes the quote gate"
  is the first invariant `contracts/start-session-step-9.md` lists, and its only
  verification was `quickstart.md` half 3 by hand. The row-level check that pins
  every other cell can reach it.
  → Fixed: T002 gained clause (d). The manual half stays — it is the only thing
  that exercises the rendered skill.

- **F · Inconsistency, LOW** — `tasks.md`'s own Format section requires "Exact
  file paths in every description", and T017, T019 and T020 named none. All three
  add assertions, and the module they belong in is inferable but never stated —
  which is the same class of defect as the four above, arriving as an omission
  rather than as a wrong pointer.
  → Fixed: all three now name `tests/test_session_stopped_not_finished.py`.
  Decided against a separate module per subject: US3 and Phase 6 are four
  assertions between them, and a module per assertion is the noise the task list
  already rejects one level up.

- **B · Ambiguity, LOW** — FR-014 says "*continued* is the canonical term …
  No other word names the same thing", with no carve-out, and the one
  user-facing line the feature adds reads `✓ Session stopped, not finished`.
  → Accepted: `contracts/wfctl-end.md` justifies the wording in place — it is the
  issue's own title, and it states what was *recorded* rather than a verdict on
  the work, which is the distinction #70 exists to hold. Editing `spec.md` to add
  the carve-out is outside this step, which is read-only on it. The exception
  belongs on the pull request, where a human can disagree with it.

- **E · Coverage gap, LOW** — FR-003 (survives a context reset), FR-010 (names no
  agent) and FR-014 (canonical term) carry no task.
  → Accepted: FR-003 falls out of storing the mark in `events.jsonl` rather than
  in memory, which is the storage decision itself; FR-010 and FR-014 are review
  properties the plan's Constitution Check already names. A grep for
  `recycle`/`unfinished`/`interrupted` would cover the last two cheaply, and is
  recorded here rather than added, because a lexical check on prose is the kind
  of rule that fires on a quotation of the rejected word.

- **C · Underspecification, LOW** — `pytest -k log` collects 32 tests across
  `test_tracker.py` and `test_worktree_guard.py`; `-k status` collects 57.
  → Accepted: both select the intended tests, and neither T017 nor T019 creates a
  module whose name would narrow them. Naming a module that does not exist yet
  would be the worse trade.

### Deferred

- **G · Design-record contradiction** — no `design.md` at `FEATURE_DIR`, so the
  list of level-3 records this feature was written against is `unknown` rather
  than `none`. The pass belongs to whichever step first has a list to read;
  `/speckit.brainstorm` was skipped here and no step downstream creates one.

### Later in the same session — a review panel over the finished change

Three reviewers, fresh context each, the whole `code-review` rubric each, over
`origin/main..HEAD`. Roster: r1 ✓ r2 ✓ r3 ✓, reports in
`<spec-root>/352-session-stopped-not-finished/reviews/`. Recorded here because
the passes above scanned `spec.md`, `plan.md` and `tasks.md` *before* the
branch-first routing rule existed, so nothing above covers the change as shipped.

Six findings applied, all verified against the code first:

- **Two reviewers, and one called it a blocker — the step prescribes a command
  the skill is not allowed to run.** `start-session`'s `allowed-tools` lists
  `Read` and specific `Bash(wfctl …)`/`Bash(git …)` prefixes; the new
  `grep … | tail -1` matches none. Every other fenced command in the file had an
  entry. Unattended that is a permission prompt — the stall the feature exists to
  remove — or an agent improvising with `Read`, which the step warns against four
  lines below. → Fixed: `Bash(grep*) Bash(tail*)`.
- **All three — a real routing state had no row.** Trunk, no stop at all, a
  quotable handoff: row one wanted an issue branch or a continued stop, row two
  wanted a *last stop*, row three wanted an unquotable handoff. Step 4's read
  names the outcome and step 9 consumed it nowhere, and the pre-#352 table
  resolved that same state the opposite way — so an agent filling the gap from
  precedent begins work against `main`'s accumulated handoff, which is SC-002.
  → Fixed: row two covers "no stop at all", in the skill, the contract and a
  test named for the state.
- **One reviewer, and the most valuable finding — the FR-013 warning was a
  guaranteed false positive on #352's own scenario.** `worktree-handoff` tells
  handoff authors "Do not add a TODO section", so every fresh worktree carries a
  complete handoff with no `## Next Session TODO`, and reading absent as unfilled
  warned on the file most likely to be right. Both clauses of the printed line
  were false. → Fixed: `end` judges only a file carrying the `**Step**:` reading
  it writes itself, which `end-session` already documents as the discriminator.
  FR-013 and `contracts/wfctl-end.md` were rewritten to match, and the warning
  reworded.
- **Two reviewers — an unguarded read could fail a stop that happened.**
  `summary_path.read_text()` runs after the `end` event is appended, and an
  invalid UTF-8 byte raises `UnicodeDecodeError`, a `ValueError` and not an
  `OSError`. → Fixed with the pair `_session.auto_approve` already catches, and a
  test that the stop survives.
- **Two reviewers — a duplicate test and two assertions that cannot fail.**
  `_row` selects a row by its condition column's prefix, and two new tests then
  asserted substrings of that same prefix; a third was byte-identical in body to
  an existing one. In the module whose own docstring is about assertions that
  stay green on a mutated artifact. → Fixed: the duplicate became the missing
  no-stop case, and the vacuous assertions now compare the two rows.
- **One reviewer — `--continued` was undocumented** in `using-wfctl`'s command
  table, which carries flags for every other command. → Fixed.

Accepted, not applied: a `str.partition` shrink in `names_no_first_action`
(the loop stops at the next heading, which `partition` would not); `# `-vs-`## `
heading near-misses (the template writes `## ` and nothing else is judged since
the fix above); README's `wfctl end` example (it demonstrates a session close,
not the flag set).
