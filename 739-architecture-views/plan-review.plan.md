# Implementation Plan: architecture views

**Branch**: `739-architecture-views` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this folder, for #739 and #738.

## Summary

Every repository that uses wfctl gets the same required views: a system context view, a container view, and one component view for each context on the domain page. wfctl ships a template for each, and `wfctl arch context` prints the paths of the views that exist and a line for each one that's missing, filtered by the contexts the branch lists. Each view lists the code it covers, and a view whose covered code has commits newer than the view is marked stale. A missing or stale view never blocks anything. Each arrow in a container or component view names the code that creates it, so the user can check it.

On the same branch, a record's `diagram` field takes a list of kinds, with one `### <kind>` drawing for each under `## Boundary`. Acceptance refuses a list that repeats a kind, a declared kind with no drawing, and a drawing for a kind the record didn't declare. The record template opens with the decision, then the drawings. The domain model template trades most of its wide tables for short lists.

Design records: none, since `design.md` records no level-3 decision.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, already in use. Nothing new.
**Storage**: Markdown files in the repository. wfctl stores nothing new.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py`
**Target Platform**: The `wfctl` CLI on macOS and Linux
**Project Type**: CLI, with skills and templates shipped as package data
**Performance Goals**: `wfctl arch context` stays close to today's speed. The views add one `stat` per required view, and two `git` calls per present view to check whether it's stale (R-010). wfctl's own repository has nine required views, so that's at most 18 `git` calls.
**Constraints**: No new runtime dependency, so the `diagram` list is read by the existing line scan rather than a YAML parser. No new import arrow between contexts. Minimal-complexity bias.
**Scale/Scope**: Seven contexts in wfctl's own repository, so nine required views. Fewer than 100 records on disk.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`, so the gates below come from `AGENTS.md` and the accepted records. The substitution is noted under Complexity Tracking.

- [x] Validation plan exists: the four commands above, plus the tests in Validation Strategy below and the manual checks in `quickstart.md`.
- [x] Complexity is justified: one new module and one new property. Each one replaces a guess that would otherwise sit in the CLI (R-001, R-004).
- [x] Ownership is stated: wfctl computes which views are required and which are missing, because the list is wfctl's (`required-views-are-wfctls.md`). The agent draws each view, and the user judges it. The record's author declares the kinds, and wfctl checks each has a drawing (`the-author-declares-the-diagram-kind.md`).
- [x] `contexts-are-packages`: the new module sits inside `wfctl/arch/` with a leading underscore, and other code reaches it through the package. It reads the domain page, which this context already reads, so no new arrow is needed.
- [x] `a-rule-is-expressed-as-a-check`: the list of required views is checked against the shipped templates by a test (FR-004). A stale view is visible in git history, so it's a check here (R-010). The stability layout rule and the arrow labels are prose in the templates for now. A broken one is visible in the view, so each one is a check, and #743 builds it, covering the wrong-way arrow drawn in the normal color too.
- [x] `change-carries-release-note`: `changes/738.addition.md` and `changes/739.change.md`.
- [x] `knowledge-placement`: the view templates are guidance for the worker, so they ship in a skill. The decisions are in `docs/architecture/`.
- [x] `vendor-upstream-skills`: no spec-kit-derived skill is edited. The changes land in `architecture-design`, `architecture-decisions`, `model-the-domain`, and `start-session`, which are wfctl's own.

Post-design re-check: all gates still pass. Phase 1 added no module beyond R-001 and no import arrow.

## Project Structure

### Documentation (this feature)

```text
739-architecture-views/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md             # written by /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── _paths.py                          # VIEWS_DIR, added to non_record_subtrees (FR-008)
├── cli.py                             # arch context prints the Views block (FR-005, FR-006)
├── arch/
│   ├── __init__.py                    # lazy re-exports for the new names
│   ├── _contexts.py                   # contexts(arch): the Contexts line only (R-002)
│   ├── _views.py                      # new: required views, present, missing, and stale (R-001, R-003, R-010)
│   └── _records.py                    # Record.kinds, _drawings, new blockers and findings (FR-009 to FR-015)
└── agents/skills/
    ├── architecture-design/
    │   ├── SKILL.md                   # names the view templates in Inputs
    │   └── views/                     # new
    │       ├── system-context.md      # FR-003, FR-003c
    │       ├── container.md           # FR-003, FR-003a, FR-003b, FR-003c
    │       └── component.md           # FR-003, FR-003a, FR-003b, FR-003c
    ├── architecture-decisions/
    │   ├── SKILL.md                   # declaring and drawing more than one kind, and the section order (FR-017, FR-017a)
    │   └── record-template.md         # same, reordered to open with the decision (FR-017, FR-017a)
    ├── model-the-domain/
    │   └── domain-model-template.md   # short lists instead of wide tables (FR-016)
    └── start-session/
        └── SKILL.md                   # step 2 says what the Views block means (User Story 2)

docs/
├── reference.md                       # the diagram field's list form only (FR-019)
└── architecture/
    ├── required-views-are-wfctls.md   # reordered (FR-017a), stale views and the review's limit added
    ├── the-author-declares-the-diagram-kind.md  # reordered (FR-017a)
    └── views/
        ├── system-context.md          # new: wfctl's own (FR-018)
        └── container.md               # new: wfctl's own (FR-018)

changes/
├── 738.addition.md
└── 739.change.md

tests/
├── test_arch_views.py                 # new: required views, filter, stale views, Views block, template match (FR-001 to FR-006a)
├── test_arch_diagram_kinds.py         # new: list parsing, per-kind drawings, refusals, doctor warnings (FR-009 to FR-015)
└── test_paths.py                      # extended: views/ is not a record (FR-008), written first
```

**Structure Decision**: Single project. Code lands in the `arch` package and the CLI wiring, and guidance lands in four of wfctl's own skills. The test file names are new because neither area has a test file that fits today, so a reviewer can read each area's tests on their own.

## Notes for tasks

1. **Write the failing test for `views/` first.** A branch that edits only a view must not read as deciding a record. Add the test to `test_paths.py`, beside the tests for `declarations/` and `step-claims/`, watch it fail, then add `VIEWS_DIR` to `non_record_subtrees`.
2. **Pin the existing records before changing acceptance (SC-004).** Copy every one-kind record on disk at the branch's base into `tests/fixtures/one-kind-records/`, and save each one's `accept_blockers` and `validate` result beside it. The test compares the fixture copies, never the live `docs/architecture/` folder, so a record added or accepted after this branch merges doesn't break it.
3. **The domain model template's Context Map keeps its mermaid drawing.** `check_imports.py` reads the mermaid on wfctl's domain page, and #745 brings that page in line with the template later. Every other table becomes a short list: Evidence, Scenarios, Ubiquitous Language, Subdomains, the Context Map's relationship table, the Invariants and Aggregate tables, Implementation feedback, and Open questions. A filled page then has one table, the Bounded Contexts table (SC-005). The Shared packages table is on wfctl's page, not in the template, so this change doesn't touch it.
4. **`--all` prints every component view.** It already prints every record whatever the branch lists, and the views follow it.
5. **The refusal text in `contracts/cli.md` is the contract.** Tests compare it exactly, with `NO_COLOR` set.
6. **Draw wfctl's two views last,** from the finished templates. They're the worked example the templates point to, and drawing them is the first test of SC-001. Give each a `covers` line and a label on every arrow.
7. **Stale-view tests build a real git repository** in `tmp_path`, with commits to a covered path before and after the view's commit. A mocked `git` would pass whatever `rev-list` range the code builds, so it can't catch an off-by-one in which commits count.
8. **The two proposed records are already in the new order,** committed during planning. Reorder the template to match them, and leave accepted records alone.
9. **Tell the agent what the Views block means.** `start-session/SKILL.md` step 2 says the last lines of `wfctl arch context` count the records left out. Add one sentence saying the Views block follows, that a missing, stale, or unchecked view is a reminder to draw or update it and never a refusal, and that the agent opens the views before changing a boundary.

## Validation Strategy

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py` pass.
- `test_paths.py`: `views/` is one of the folders that aren't records, so a branch touching only `views/` isn't reported as deciding a record. Written first, seen failing.
- `test_arch_views.py`:
  - The required views for a domain page with three contexts, with none, and with no domain page.
  - `Outside parties` names get no component view.
  - The branch filter, for each row of the table in `data-model.md`.
  - The `Views` block in `contracts/cli.md`, for a repository with some views present, with none, and with no architecture folder, and with `--all`.
  - The required-view names compared with the files under `architecture-design/views/` (FR-004).
  - `arch context` exits 0 with every view missing.
  - A view is stale after a commit to a covered path, and current again after a commit to the view. An uncommitted edit changes neither.
  - A view with no `covers` line, and one whose `covers` names a missing path, print as unchecked with their reasons.
  - A view with no commit yet prints as a plain path.
  - View paths with an architecture root outside the working tree print absolute, the same as the records footer, and each present view there prints as unchecked with `not in this repository's history`, not as current. A `git` failure doesn't change the exit code.
  - Each view template carries a `covers` line, and the container and component templates ask for arrow labels (FR-003b, FR-003c).
- `test_record_placement.py` or `test_arch_sections.py`: the record template's `##` headings appear in the FR-017a order.
- `test_arch_diagram_kinds.py`:
  - `Record.kinds` for a single kind, a list, `[]`, an empty value, and a missing field.
  - Acceptance passes for a one-kind record drawn directly under `## Boundary`, for the same record drawn under `### <kind>`, and for a two-kind record with both drawings.
  - Each refusal in `contracts/cli.md`, matched exactly.
  - The sequence failure-step rule applies to a sequence drawing inside a multi-kind record.
  - A `### data-flow` heading with no fence, followed by `### sequence` with one, is refused for the missing data-flow drawing. The same holds with `### Key` between them.
  - A fence above the first `###` heading in a two-kind record counts for neither kind, and `### Sequence` matches `sequence`.
  - A two-kind record with no fence at all prints one refusal per kind and no `no drawing` line.
  - A record with an old blocker and a new one prints the `cannot be accepted yet` block first, then the new refusal.
  - Doctor warnings on a proposed record, and none on an accepted one. An unknown kind is an error on every status (FR-015).
  - Every fixture copy of a one-kind record gives the acceptance result saved beside it (SC-004).
- `quickstart.md`, run by hand after `uv run wfctl install-skills`.
- `uv run wfctl doctor` and `uv run wfctl check config` report nothing new.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates taken from `AGENTS.md` and accepted records, not a constitution | The repository has no `.specify/memory/constitution.md` | Running with only the template's three gates would skip the import check and the release note, which CI enforces |
