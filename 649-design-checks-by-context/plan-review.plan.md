# Implementation Plan: The design checks match records to the contexts a branch changes

**Branch**: `649-design-checks-by-context` | **Date**: 2026-10-26 | **Spec**: `spec.md` in this feature folder
**Input**: Feature specification from `spec.md`, the design in `design.md`, and the level-3 record `docs/architecture/design/649-contexts-module.md`

## Summary

Brainstorm's two design checks pass on any record today, whatever part of wfctl it covers. After this change, a repo whose domain page lists its context names gets a stricter check. Every context a branch lists in `design.md` needs a record that governs it, or a "no" for that context with a reason. A repo with no name list keeps today's check.

One new module, `wfctl/_contexts.py`, reads the name list from the domain page and the branch's `Contexts` line from `design.md`, and matches them against records and per-context "no" answers. The architecture check and #648's software design check both call it. `_arch.py` gets a `governs` field on `Record` and a `validate` finding for an unknown name. #635's `_design_exceptions` module gets a `context` argument, so a per-context "no" lands in `exceptions/<context>/`. `wfctl arch none` and `wfctl step none` get a `--context` option.

Implementation waits on #648 and #635 merging, since this change edits code both of them add. Phase A below touches neither and can start first.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, no new ones
**Storage**: Files. The domain page under `<arch-root>/domain/`, `design.md` and the `exceptions/` folder in the spec folder, and record frontmatter under the arch root.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, then `uv run wfctl verify` and `uv run wfctl doctor`
**Target Platform**: macOS and Linux, wherever wfctl runs
**Project Type**: CLI
**Performance Goals**: No measurable change to `wfctl status`. The new reads are one small file per accepted domain page, one `design.md`, and the records this branch already lists.
**Constraints**: No new runtime dependency. The domain page header is scanned with `_arch._key_value`, the rule `_frontmatter` already uses, rather than a markdown parser. Minimal-complexity bias.
**Scale/Scope**: One repo has a name list today (this one, once Phase A lands), with six contexts and six outside parties.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. The gates below come from `AGENTS.md` and the accepted records, and Complexity Tracking records the substitution.

- [x] Validation plan exists: the Validation Strategy in `spec.md`, plus the test files named under Project Structure.
- [x] Complexity is justified: one new module, justified in `649-contexts-module.md` against the direct baseline of adding the code to `_evidence.py` and `_arch.py`. The `Level` constants below are the one addition beyond that record, and research decision R2 justifies them.
- [x] Ownership is stated: see "Who computes what" below.
- [x] `session-state-is-re-derived`: every value is read from files at check time, and nothing is cached between runs.
- [x] `a-rule-is-expressed-as-a-check`: an unknown name on a `Contexts` line or in a `governs` field is a pause or a doctor finding, not prose.
- [x] `vendor-upstream-skills`: no spec-kit-derived skill is edited. The skill changes go to wfctl's own skills and templates.
- [x] `domain-page-names-contexts` (accepted): wfctl reads the names from the domain page and ships none of its own.
- [x] `wfctl-runs-the-verification`: the definition of done is `wfctl verify`, not a self-report.

### Who computes what

| Value | Computed by | Why not the other side |
| --- | --- | --- |
| The name list | The user writes it on the domain page, and wfctl reads it | wfctl runs in repos whose contexts it has never seen, and an agent would be making up the names its own work is checked against |
| A branch's contexts | The agent writes the `Contexts` line | Today's modules overlap contexts, so wfctl can't tell a changed file's context. #544 changes this |
| Whether every listed context has an answer | wfctl, at check time | An agent answering it would be grading its own work |
| Which contexts a record governs, and the reason for a "no" | The agent | Only the author of the record knows what it decides |

## Implementation

### Phase A: names, `governs`, and doctor (needs neither #635 nor #648)

1. **`wfctl/_contexts.py`**, new, with `names(arch)` and `listed(spec_dir)`.
   - `names(arch: Path) -> frozenset[str] | None` reads every `*.md` directly under `arch / DOMAIN_DIR`. For each page, it scans the lines before the first `## ` heading with `_arch._key_value`. A page counts only when its `State` value is `accepted`. The names are the comma-separated entries of its `Contexts` and `Outside parties` values, trimmed, with empty entries dropped. It returns `None` when no accepted page has a `Contexts` key.
   - `listed(spec_dir: Path) -> tuple[str, ...] | None` reads `spec_dir / "design.md"` the same way, before the first `## ` heading. It returns `None` when there's no file or no `Contexts` key, and the entries in order with duplicates removed otherwise. An empty value returns `()`.
   - Only the header is read, because a `design.md` quotes `Contexts: …` inside code blocks further down. This repo's own `design.md` does, in its Behavior section.
   - Both use one private helper, `_header(path) -> dict[str, str]`, so the two reads follow one rule.
2. **`wfctl/_arch.py`**:
   - `Record` gains `governs: tuple[str, ...] = ()`, defaulting so every existing constructor call still works.
   - `parse_record` reads `front.get("governs", "")` and splits it on commas, the same way `_contexts` splits a header value. The split lives in `_arch` as `split_names(value) -> tuple[str, ...]`, and `_contexts` imports it, since `_contexts` already imports `_arch` and the reverse import would create a cycle.
   - `validate(records, names: frozenset[str] | None = None)` adds one finding per unknown name when `names` is given: `Finding("error", slug, f"governs {name}, which isn't on the domain page's name list")`. Existing callers pass nothing and see no change.
3. **`wfctl/cli.py` `_check_arch_records`** passes `_contexts.names(root)` to `validate`.
4. **`docs/architecture/domain/wfctl.md`** gets the two header lines after `State: accepted`, with the names from `649-contexts-module.md`.
5. **Skill and template text** (see Project Structure for paths):
   - The `model-the-domain` template's `State` line offers `accepted`, and the template gets `Contexts:` and `Outside parties:` lines under it. The skill tells the agent to fill them from the Bounded Contexts table and the outside parties list, as kebab-case short names.
   - The `architecture-decisions` and `software-design-decisions` record templates get `governs: <names from the domain page's Contexts or Outside parties line>` in their frontmatter, and each skill says what the field is for.
   - `design-levels` tells the agent to decide which contexts the branch changes at level 2, before writing any record, since every record's `governs` field and every per-context "no" depends on that list. `speckit-brainstorm` tells it to write that list as the `Contexts` line under the title of `design.md`.
   - The "no" answer: everywhere a skill teaches `wfctl arch none --reason` or `wfctl step none brainstorm.software-design --reason`, it adds that a repo with a name list answers once per context with `--context <name>`, and the bare form is refused there (FR-016). That covers `design-levels` (the level-2 declaration block and level 3), `speckit-brainstorm` (the re-entry paragraph and its `allowed-tools` line), `architecture-design`, `software-design-decisions`, and `design-passes`. Task generation greps `wfctl/agents/` for `arch none` and `step none` and lists every hit, so none is missed.
6. **Name shape.** `names` keeps only entries matching `[a-z0-9]+(-[a-z0-9]+)*`, since each name becomes a folder under `exceptions/` in Phase B, and a name holding `/` or `..` would write outside it. `_check_arch_records` reports each dropped entry as a finding on the domain page, so a malformed name is visible rather than silently missing.
7. **Tests**, in `tests/test_contexts.py` and the files named below:
   - `names`: accepted page read, proposed page ignored, two pages combined, no list returns `None`, a malformed entry dropped.
   - `listed`: header line read, a `Contexts:` line inside a code block below the first `## ` ignored, missing line returns `None`, empty value returns `()`, duplicates removed.
   - `parse_record` reads `governs`, and `validate` reports an unknown name only when given a list (`test_arch_records.py`).
   - `wfctl doctor` reports an unknown `governs` name and a malformed domain-page entry, and stays clean in a repo with no list (`test_remaining_commands.py`).

### Phase B: per-context "no" answers (after #635 merges)

1. **`wfctl/_design_exceptions.py`**: `write`, `boundary`, and `passes` take a keyword-only `context: str | None = None`. With a context, the folder is `exceptions/<context>/`, so `exceptions/<context>/boundary.md` and `exceptions/<context>/<step>.<pass>.md`. The title line names the context: `# No new boundary for <context>` and `# <step>.<pass> does not apply to <context>`. Without one, behavior is #635's unchanged, and `passes` keeps its one-level glob, so it never reads a per-context file as a whole-pass claim.
2. **`wfctl arch none --context <name>`** and **`wfctl step none <step>.<pass> --context <name>`**. Both run #635's reason checks first, then:
   - Refuse when `_contexts.names(arch)` is `None`: `✗ --context needs a name list on the domain page, and <arch-root>/domain/ has none.`
   - Refuse a name not on the list, printing the list.
   - `step none` accepts `--context` only for `brainstorm.software-design`, the one pass the contexts check reads, and refuses it on any other pass.
   - With a name list and no `--context`, `arch none`, `step none brainstorm.architecture`, and `step none brainstorm.software-design` refuse and name the option, since a branch-wide "no" doesn't answer a listed context (FR-011).
   - On success, each prints `✓ Recorded: <context> needs no new boundary — "<reason>"` (or `… brainstorm.software-design does not apply to <context> …`), then #635's "Put the reason in the PR body." line.
3. **`wfctl/_contexts.py`** gains `unanswered` and `pause`:
   - `unanswered(listed, records, spec_dir, *, pass_name=None) -> str | None` returns the first listed context that no record in `records` governs and that has no "no". With `pass_name=None`, it asks `_design_exceptions.boundary(spec_dir, context=c)`. Otherwise it asks `_design_exceptions.passes(spec_dir, context=c).get(pass_name)`.
   - `pause(names, spec_dir, records, level) -> tuple[str, str] | None` returns the reason and remedy, or `None` when every context is answered. It checks in this order: no `Contexts` line or an empty one (FR-007), then a name not on the list (FR-008), then `unanswered` (FR-005). `level` is one of two constants, `ARCHITECTURE` and `SOFTWARE_DESIGN`, each carrying the record noun, the pass name, and the command for the "no" answer. Research decision R2 explains why.
   - `answers(listed, records, spec_dir, level) -> list[str]` returns one line per context that was answered with a "no", as `<context>: no — <reason>`, for the done display.
4. **`_evidence._architecture_answered`** currently checks `spec.md`, then the boundary exception (#635), then `design_record_checks` (#648), then git. After the change it checks in the order below. The "off" check moves ahead of the boundary exception, because the per-context branch has to run before that exception and must not run when the checks are off. Both checks return answered, so the move doesn't change any result:
   1. `spec.md` exists: answered (#635 and today).
   2. `design_record_checks` is `"off"`: answered (#648).
   3. A name list exists and `design.md` exists: the per-context branch below, and nothing after it runs. This sits ahead of #635's whole-branch boundary exit and #648's git verdict, so neither a bare `boundary.md` nor a record about another context reaches its "answered" exit (FR-005a).
   4. Otherwise: #635's boundary exit and #648's git verdict, unchanged. A branch with a record and no `design.md` yet still reads as started here, so `brainstorm`'s pending-or-started reading is unchanged. Brainstorm can't finish without `design.md` anyway, since `design-doc` waits on it.

   The per-context branch calls `_contexts.pause(...)` with this branch's level-2 records and `ARCHITECTURE`. The records are `records_on_this_branch(repo_root, arch, exclude=[*non_record_subtrees(arch), arch / DESIGN_DIR])`, each read with `parse_record`, skipping a slug whose file the branch deleted. When `pause` returns a gap and `touched_on_this_branch` is inconclusive, it returns #648's git-unanswered reason instead, since an empty record list then says nothing about the branch. The return type widens from `str | None` to carry the remedy, and `brainstorm_architecture` passes the remedy into its `Assessment`.

   Gathering the records, calling `pause`, and the git-unanswered fallback live in one function, `_evidence.context_gap(repo_root, arch, spec_dir, level)`. It returns `None` when every listed context is answered, and otherwise the reason, the remedy, and whether git couldn't list the branch's records. The reader calls it here, and the session summary's Boundary line calls it too (item 7), so the two can't disagree.
5. **`brainstorm_architecture`**: when the per-context check passes and at least one context was answered with a "no", the done `Assessment` carries `display` with the `answers` lines joined by `; ` on one line, so a long list doesn't print as extra rows. It shows in plain `wfctl status` as well as `--all`, as any done display does. When `_judge_drawings` also has a display, such as `DRAWINGS_UNCHECKED`, the drawing text comes first and the answers follow after `; ` (FR-010a).
6. **`_pipeline`'s claim lookup**: when a name list exists, the claims dict built from `_design_exceptions.passes(spec_dir)` drops `brainstorm.architecture` and `brainstorm.software-design` before `_pass_states` reads it. A whole-pass claim already on disk, written before the domain page had a list, then no longer marks either pass skipped, and the reader runs (FR-011, SC-001).
7. **#635's other readers of the exceptions folder**, checked again once #635 merges:
   - `check-body`'s reason check reads every per-context reason too, through a new `_design_exceptions.reasons(spec_dir) -> list[tuple[str, str]]` that returns each label and reason across the branch-wide and per-context files.
   - The session summary's Boundary line is the first thing a restarted session reads. #635 has `_observe` read "answered" from the branch-wide boundary exception, and otherwise from git. Neither sees a per-context "no", so a branch that answered every context with a "no" would read "unanswered" while `wfctl status` shows the architecture pass done. With a name list and a `design.md`, `_observe` instead calls `_evidence.context_gap(..., ARCHITECTURE)`. No gap reads "answered", a gap reads "unanswered", and a gap git couldn't check reads "unknown", the three values `_BOUNDARY` maps today. Like #635's version, it skips the `spec.md` exit, because the line records whether the question was answered, not whether brainstorm is still paused (research R7).
   - The worktree guard's contradiction check (#635 R13) refuses `gh pr create` and `gh pr merge` when the branch's own spec folder holds a boundary exception and the branch touches a level-2 record. With a name list, item 2 refuses a branch-wide exception, so the check as #635 writes it can never fire. The guard therefore also reads each per-context exception. It refuses when the branch's own spec folder holds `exceptions/<context>/boundary.md` and a level-2 record the branch touches lists that context in its `governs` field. It reads `governs` from the record at the commit the command acts on, through git, the same way R13 reads the records. The refusal names the record and the context, and prints the command that deletes that context's exception. A "no" for one context and a record that governs a different one isn't a contradiction (research R8).
8. **Tests**:
   - `test_design_exceptions.py`: `write`, `boundary`, and `passes` with a context, `passes` without one ignoring subfolders, and `reasons`.
   - `test_pipeline_commands.py` and `test_step_none.py`: each `--context` success line, and each refusal in `contracts/cli.md`.
   - `test_design_gate_drawing.py`: every row of User Stories 1 to 4, including User Story 2 scenario 3 with `boundary.md` written directly through `_design_exceptions.write`, since the CLI now refuses it; User Story 2 scenario 4 with a governing record committed on trunk; and FR-013 with `spec.md` present.
   - `test_pipeline_state_names.py`: a whole-pass claim on disk doesn't skip either pass when a name list exists, and still does without one.
   - `test_end_reports_observations.py`: with a name list, the Boundary line reads "answered" for a branch that answered every listed context with a "no" and touched no record, and "unanswered" for a branch whose only record governs a different context. Without a name list, the line reads as #635 leaves it.
   - `test_record_gate.py`, since `_record_gate.refusal` is the guard's record check and `test_worktree_guard.py` tests the guard on writes into other worktrees: with a name list, `gh pr create` is refused for a branch with `exceptions/session-continuity/boundary.md` and a touched record that governs `session-continuity`, and allowed when the record governs only `install-and-drift`.

### Phase C: the software design check (after #648 merges)

1. **`_evidence.brainstorm_software_design`** gets the same order as Phase B step 4, with level-3 records from `records_on_this_branch(repo_root, arch / DESIGN_DIR)`, read from `arch / DESIGN_DIR / f"{slug}.md"`, and `SOFTWARE_DESIGN`. The per-context branch sits ahead of #648's `blocks`-false exit, which otherwise returns done once any level-3 record is touched.
2. The same done `display` as Phase B step 5.
3. A per-context "no" never hides the row, since `passes(spec_dir)` without a context doesn't read subfolders, and Phase B step 6 drops a whole-pass claim.
4. **Tests** in `test_software_design_pass.py`: every row of User Story 6, including scenario 3, where a level-2 record that governs the context doesn't answer the software design check.
5. **#635's level-3 record**, `design/design-exceptions-module.md`, gets a Log line and a short paragraph saying the folder now holds one subfolder per context, pointing at `649-contexts-module.md`. If that record is accepted by then, the edit is a new record that supersedes it instead.

### Phase D: PR body, release note, and verification

1. **`.github/pull_request_template.md`**: #635's "Moves a boundary?" section gets a `Contexts:` line in its placeholder.
2. **`opening-a-change`**: copy the `Contexts` line from `design.md` into whichever section of the PR template carries a `Contexts:` line, and list each per-context "no" with its reason under it. The skill names the line, not the section, since it never lists a template's sections.
3. **Skill text checks**: FR-015 to FR-018 have no automated test. After `uv run wfctl install-skills --agent claude`, the implementer reads each installed file named in Phase A item 5 and Phase D item 2, and `grep -rn "arch none\|step none" .agents/ .claude/` shows no instruction left that teaches the bare form without the `--context` note.
4. **`changes/649.change.md`** in the `change` category.
5. `uv run wfctl install-skills --agent claude`, then the scratch-branch check in `quickstart.md`.

## Project Structure

### Documentation (this feature)

```text
<spec-root>/649-design-checks-by-context/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── _contexts.py                 # new: names, listed, unanswered, pause, answers, ARCHITECTURE, SOFTWARE_DESIGN
├── _arch.py                     # Record.governs, split_names, validate(records, names)
├── _design_exceptions.py        # from #635: context argument on write, boundary, passes
├── _evidence.py                 # _architecture_answered, brainstorm_architecture, brainstorm_software_design (#648)
├── cli.py                       # arch none / step none --context, _check_arch_records, _observe
├── (worktree guard, from #635)  # per-context contradiction check
└── agents/skills/
    ├── model-the-domain/domain-model-template.md   # State accepted, Contexts, Outside parties
    ├── model-the-domain/SKILL.md
    ├── architecture-decisions/record-template.md  # governs
    ├── architecture-decisions/SKILL.md
    ├── software-design-decisions/design-record-template.md  # governs
    ├── software-design-decisions/SKILL.md
    ├── design-levels/SKILL.md                     # Contexts line, --context
    ├── speckit-brainstorm/SKILL.md                # Contexts line, --context
    └── opening-a-change/SKILL.md                  # Contexts line in the PR body

docs/architecture/domain/wfctl.md                  # the two header lines
.github/pull_request_template.md                   # Contexts line under Moves a boundary?
changes/649.change.md

tests/
├── test_contexts.py             # new: names, listed, unanswered, pause
├── test_arch_records.py         # governs parsing, validate finding
├── test_remaining_commands.py   # doctor finding
├── test_design_exceptions.py    # from #635: context argument
├── test_step_none.py            # --context
├── test_pipeline_commands.py    # arch none --context
├── test_design_gate_drawing.py  # architecture check by context
├── test_software_design_pass.py # from #648: software design check by context
├── test_end_reports_observations.py  # Boundary line by context
└── test_worktree_guard.py       # per-context contradiction
```

**Structure Decision**: Single project. The new module sits beside `_design_exceptions.py` and `_arch.py`, which it imports. Tests reuse `conftest.py`'s `storyctl_dir`, `write_record`, and `git_repo`, and the `_arch_root` helper from `test_step_none.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution; gates taken from `AGENTS.md` and the accepted records | The template asks for gates with a source | Borrowed gates from another project would be false |
| `pause`, `answers`, and the two `Level` constants added to the record's three functions | The spec added a missing-line pause, an unknown-name pause, a remedy per context, and the done display after the record was written | Formatting those in each check would put the same three-branch rule in both, which is what the record's decision exists to avoid |
