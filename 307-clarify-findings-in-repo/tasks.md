# Tasks: Scan files for clarify and analyze

**Input**: `plan.md`, `spec.md`, and the two records committed on this branch.
**Branch**: `307-clarify-findings-in-repo`

Two of the three phases are already on the branch — the design pass committed its
records, and the clarify step committed the first scan file by hand under the
design it was implementing. Those are ticked below rather than omitted, because a
task list that hides completed work reads as a smaller change than it is.

## Phase 1 — Design records (US1, US2)

- [x] T001 Write the level-2 record at
      `docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md`, naming
      the repository as owner of "was this change scanned" and the spec store as
      owner of "what did it say". Commit it.
- [x] T002 Write the level-3 record at
      `docs/architecture/design/307-the-coverage-map-is-the-evidence.md`, deciding
      that the coverage table is the file's body, with the rendered example and the
      two graphs. Commit it.
- [x] T003 Confirm both records are reachable: `wfctl arch check` exits 0 for each.

## Phase 2 — Dogfood the format (US1, US2)

- [x] T004 Write `docs/architecture/scans/307-clarify.md` following the design:
      verdict, coverage table over all ten taxonomy categories, findings with the
      alternative each answer was decided against, and a Deferred section. Commit it.
- [x] T005 Confirm `wfctl arch check docs/architecture/scans/307-clarify.md` exits 0.
- [x] T006 Write `docs/architecture/scans/307-analyze.md` at the analyze step,
      covering the six detection passes and requirement-to-task coverage. Commit it,
      then `wfctl arch check` it.

## Phase 3 — Ship the instruction (US1, US2, US3)

- [x] T007 Add the scan-file instruction to
      `wfctl/agents/commands/speckit.clarify.md`. Wrapper only —
      `wfctl/agents/skills/speckit-clarify/SKILL.md` is not touched (FR-008).
      The instruction must carry, each named because analysis found T007 standing in
      for eight requirements with nothing to check it against (C1):
      - the destination `<arch-root>/scans/<issue>-clarify.md`, with the root read
        from `wfctl arch-root` and never written in (FR-007, FR-014)
      - the four-value status set `Clear` / `Resolved` / `Deferred` / `Outstanding`
        (FR-004)
      - the verdict as one of `satisfied` / `unsatisfied` / `inconclusive`, with what
        each means for this step (FR-003)
      - a pointer to `FEATURE_DIR`'s artifact, never a copy of it (FR-006)
      - the empty-run rule: a full coverage table and a findings section that says
        the scan looked (FR-005)
      - replace the file whole on a re-run, never append (FR-011)
      - commit, then `wfctl arch check` the committed path (FR-013)
      - the word "scan file", not receipt or record (FR-015)
- [x] T008 Add the same instruction to
      `wfctl/agents/commands/speckit.analyze.md`, with the same eight points over
      its own categories: the six detection passes plus requirement-to-task
      coverage, and `inconclusive` defined as an artifact it could not read.
- [x] T009 Add the AGENTS.md paragraph: where a scan file goes, that the arch root
      is asked rather than assumed, and that the instruction lives in the wrapper
      because the skill is derived. Guidance for the worker, per
      `knowledge-placement`; the constraint itself stays in the record.

## Phase 3b — Act on analysis (C1, B1, D1)

- [x] T009a Fix FR-004's status vocabulary — analysis found it naming no set while
      the skill carries two (B1).
- [x] T009b Expand T007/T008 into one line per requirement they carry (C1).
- [x] T009c Point spec.md's Assumptions at the level-3 record instead of restating
      it; two of the three copies were gitignored, so the drift would be invisible
      (D1).

## Phase 4 — Tests (FR-012)

- [x] T010 `tests/test_scan_files.py`: both wrappers ship in the bundle and each
      carries the scan-file instruction. Names the failure it catches — a change
      under `wfctl/agents/` that the suite cannot otherwise see.
- [x] T011 Same file: a `.md` under `<arch-root>/scans/` does not appear in
      `wfctl arch context`, pinning `NO_COLOR`. Catches a future move of `scans/`
      to the arch root's top level, which would file scan files among the decisions
      in force.
- [x] T012 Same file: `wfctl arch check` accepts a path under `scans/` — the
      claim the whole design rests on, asserted rather than assumed.

## Phase 5 — Verify and open (definition of done)

- [x] T013 `uv run pytest -q` green.
- [x] T014 `uv run ruff check wfctl/ tests/` and `uv run mypy wfctl/` green.
- [x] T015 `uv run wfctl install-skills`, then exercise the changed command. The
      live re-scan of this branch's own spec found the replace-whole rule would
      have deleted the first session's three answers — the defect the suite could
      not see, fixed as FR-011 and the session shape. A run over a spec with
      *nothing* to report was not reached live: every scan of this spec surfaced
      something. That path is held by
      `test_each_review_wrapper_requires_the_empty_run_to_write_a_file` and by the
      rendered example in each wrapper, and is stated here rather than claimed.
- [x] T016 `uv run wfctl doctor` green after the reinstall.
- [x] T017 Run the review panel (`fanning-out-code-review`) and carry its
      disposition table into the PR body.
- [x] T018 Open the change from `.github/PULL_REQUEST_TEMPLATE.md` with
      `--body-file`, saying which of #286's open questions this destination answers.
      `Closes #307`.

## Dependencies

- T006 waits on the analyze step running, which waits on T001–T005 only for the
  format it copies.
- T007–T009 are independent of each other and can land in one commit.
- T010–T012 depend on T007 and T008 existing to assert against.
- T015 depends on T007–T009 being installed, and is the only step that exercises
  what was shipped rather than what was written.
