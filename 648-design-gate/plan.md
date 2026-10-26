# Implementation Plan: Brainstorm holds until the software design question is answered

**Branch**: `648-design-gate` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this feature folder

## Summary

Brainstorm gains a third built-in pass, `software-design`, between
`architecture` and `design-doc`. It holds the pipeline until the branch either
touches `<arch-root>/design/` or claims the pass with `wfctl step none
brainstorm.software-design --reason "…"`. The reader is a copy of the
architecture pass's question, pointed at `design/`, and it builds its own
remedy. `wfctl status` widens its pass column to fit the longest name. Three
skills are reworded so the level-3 question asks for a structural choice and
names the claim as the "no" answer.

When git can't answer, both brainstorm checks now hold instead of letting the
branch through. A new `wfctl.json` setting, `design_record_checks`, turns both
checks off for a repo where git can never answer. This amends
`promised-evidence-blocks-on-silence.md` (research R10).

Design records read: 1 listed in `design.md`.

- `docs/architecture/design/software-design-none-is-a-claim.md`

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer`, `rich`; nothing added
**Storage**: none added. The pass reads git and the existing claim files.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy`, `uv run wfctl verify`, `uv run wfctl doctor`,
`uv run wfctl check config`, and `quickstart.md`. `verify` runs the release
note check FR-011 relies on, and `doctor` is the step `AGENTS.md` asks for
after a skill change.
**Target Platform**: macOS and Linux shells, same as today
**Project Type**: CLI
**Performance Goals**: one extra `git status` and at most one extra `git diff`
per `wfctl status` while brainstorm is current. The architecture pass already
makes the same two calls.
**Constraints**: payload version stays `1.3`; no new command; minimal-complexity
bias
**Scale/Scope**: every repository that runs brainstorm, including pfms

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records `wfctl arch context` prints. Complexity
Tracking records the substitution.

- [x] Validation plan exists: the three commands in `AGENTS.md`'s definition of
      done, `wfctl verify`, `wfctl doctor`, `wfctl check config`, the tests
      under Project Structure, and the end-to-end check in `quickstart.md`.
- [x] Complexity is justified: no new module, command, file kind, or stored
      value. One function moves between modules to avoid an import cycle
      (research R4).
- [x] Ownership is stated:
      1. wfctl computes whether the pass is answered, from git and the claim
         file, on every read. The agent shouldn't report it, since it's the
         party the pass checks.
      2. The person on the branch, or the agent under auto-approve, decides
         whether the change makes a structural choice. wfctl can't compute
         that.
      3. The human reviewer judges the answer in the PR, where the record or
         the claim is a committed file.
- [x] `session-state-is-re-derived`: the pass is read from git and the claim
      folder on every call, and nothing is stored.
- [x] `pipeline-state-is-one-payload`: the reason and the remedy are in the
      payload, and `status`, `next`, and `resume` render them from there.
- [x] `a-rule-is-expressed-as-a-check`: a skipped level 3 leaves no record and
      no claim, which is visible, so the rule is a check rather than prose in
      `design-levels`. The same holds for SC-004: a skill that drops the claim
      command shows in its text, so a test checks all three skills (test 13).
- [x] `layer-model` and `vendor-upstream-skills`: `design-levels`,
      `speckit-brainstorm`, and `software-design-decisions` are wfctl-owned,
      so they're edited in place under `wfctl/agents/skills/`.
- [x] `knowledge-placement`: the pass is described in the skills that ask the
      question. `AGENTS.md` doesn't list brainstorm's passes, so it needs no
      edit.
- [x] `change-carries-release-note`: `changes/648.change.md` (research R8).

Re-checked after Phase 1: `data-model.md` and `contracts/cli.md` add no stored
value, no payload field, and no dependency. Every gate passes.

## Code changes

### `wfctl/_paths.py`

1. Move `arch_location(root, repo_root)` here from `_pipeline.py`, unchanged,
   with its docstring (research R4). The new reader only calls it for an arch
   root inside the tree, so it always gets the repo-relative form.
2. Add `DESIGN_RECORD_CHECKS_KEY = "design_record_checks"` beside `TRUNK_KEY`,
   and `design_record_checks(repo_root) -> tuple[bool, list[str]]`, shaped like
   `declared_trunk`. It returns whether the checks are on, and the problems
   with the setting. A missing key or a missing `wfctl.json` means on. `"on"`
   and `"off"` are the only valid values, and anything else is a problem and
   reads as on, so a typo never turns a check off.
3. Add `design_record_checks_problems(repo_root)` for `check config`. It
   returns the value problems, plus one more when the arch root is outside the
   tree and the setting isn't `"off"`.

### `wfctl/_pipeline.py`

1. Import `arch_location` from `_paths`, so `_pipeline.arch_location` keeps
   working for `cli` and the tests.
2. Add `SubStep("software-design", "/speckit.brainstorm", _AUTOMATIC,
   _evidence.brainstorm_software_design)` between `architecture` and
   `design-doc`. Extend the comment above the passes to say why it sits there
   (research R1).

### `wfctl/_evidence.py`

1. Add `SOFTWARE_DESIGN_REASON = "no software design record for this change"`
   beside `DESIGN_BLOCK_REASON`, with a comment in the same style.
2. Add `SOFTWARE_DESIGN_HELP`, the four-line remedy in `contracts/cli.md`, with
   a `{location}` slot.
3. Add `GIT_UNANSWERED_REASON = "git can't tell whether this branch changed
   the architecture folder"` and `GIT_UNANSWERED_HELP`, the remedy in
   `contracts/cli.md` naming `trunk` and `design_record_checks`. Both checks
   use the same pair.
4. Add `CHECKS_OFF_REASON = "turned off by design_record_checks in
   wfctl.json"`.
5. Add `brainstorm_software_design(ev)` after `brainstorm_architecture`
   (research R2):
   1. `spec.md` exists: return `Assessment("done")`.
   2. `design_record_checks` is off: return `Assessment("skipped",
      display=CHECKS_OFF_REASON)`. The text goes in `display`, not `reason`,
      the same way `DRAWINGS_UNCHECKED` does. `collect_warnings` turns the
      `reason` of every finished pass into a warning, so a `reason` here would
      print a warning on every `status`, `next`, and `resume` in a repo that
      turned the checks off on purpose.
   3. Ask `touched_on_this_branch(ev.repo_root, arch / DESIGN_DIR)`, and map
      `None`, `True`, and `False` to `inconclusive`, `satisfied`, and
      `unsatisfied`.
   4. If `blocks(verdict, "repo-declared")` is false, return
      `Assessment("done")`.
   5. Otherwise pick the reason from the verdict. `inconclusive` returns
      `Assessment("in_progress", GIT_UNANSWERED_REASON,
      remedy=GIT_UNANSWERED_HELP)`, and `unsatisfied` returns
      `Assessment("in_progress", SOFTWARE_DESIGN_REASON,
      remedy=SOFTWARE_DESIGN_HELP.format(location=arch_location(arch / DESIGN_DIR, ev.repo_root)))`.
   The reader checks the verdict only after `blocks` has decided to hold. If
   it handled `inconclusive` first, the reader would be deciding for itself
   what git's silence means, which the amended record forbids. The docstring
   says why it mirrors `_architecture_answered`, why it builds its own remedy,
   and why its source is `repo-declared` (research R10).
6. Change the architecture check the same way:
   1. `_architecture_answered` returns `None` when `design_record_checks` is
      off, after the `spec.md` escape and before asking git.
   2. It passes `"repo-declared"` to `blocks` instead of `"ambient"`, and
      returns `None` when `blocks` is false. Only when `blocks` holds does it
      pick the reason: `GIT_UNANSWERED_REASON` for an `inconclusive` verdict
      and `DESIGN_BLOCK_REASON` for `unsatisfied`. This is the same order as
      item 5, for the same reason.
   3. `brainstorm_architecture` attaches `GIT_UNANSWERED_HELP` as the remedy
      when the reason is `GIT_UNANSWERED_REASON`. When the setting is off, it
      returns `Assessment("skipped", display=CHECKS_OFF_REASON)`, with the
      text in `display` as item 5.2 explains.
   4. The comment at `_architecture_answered`'s `blocks` call, and the
      `blocks` docstring's "ambient evidence proceeds" paragraph, both say
      why these two checks are the exception.
   5. `brainstorm` itself reads `_architecture_answered` to tell `pending`
      from `in_progress`. A held branch where git can't answer reads
      `in_progress`, the same as any other held branch.
7. Update the docstrings and comments that count brainstorm's passes as two:
   1. `brainstorm`'s docstring, which says "its two passes".
   2. `brainstorm_architecture`'s docstring, "One of `brainstorm`'s two
      built-in passes".
   3. `brainstorm_design_doc`'s docstring, "`brainstorm`'s other built-in
      pass".
   4. The `Step` docstring in `_pipeline.py`, which says brainstorm "splits the
      two artifacts it already produces". The new pass reads git rather than an
      artifact brainstorm writes, so the sentence has to say what earns it a
      row.
   5. `tests/test_declared.py:21`, "`brainstorm`'s two built-in passes".

### `wfctl/cli.py`, `check_config_cmd`

1. Call `_paths.design_record_checks_problems(repo_root)` before the early
   return for a missing `wfctl.json` (`cli.py:6637-6639`). A repo that keeps
   its arch root outside the tree declares it in the manifest or in
   `WFCTL_ARCH_DIR`, so it may have no `wfctl.json` at all. If the finding ran
   after that return, it would never print in the repo it's written for.
2. With no `wfctl.json`, print any problems it returns under the same
   `✗ wfctl.json:` heading and exit 1, since the fix is a key in that file.
   With none, print `no configuration to check` as today.
3. With a `wfctl.json`, add those problems to `problems`, beside
   `declared_trunk_problems`.

### `wfctl/cli.py`, `status_cmd`

1. Before the step loop, compute `pass_width = 2 + longest + 2` from every pass
   name in the payload, hidden ones included (research R7).
2. Use `.ljust(pass_width)` for `sub_name` in place of `.ljust(16)`, and
   rewrite the comment above it to say why the width is computed.

Because the built-in `plan-walkthrough` is 16 characters, the width is 20 in
every repository. Every pass row moves four columns right, including in a
repository that declares nothing, so `tests/test_cli_status.py:56` changes with
it.

## What the skill and doc rewrites say

### `design-levels`, the four-levels table (line 39)

The Form cell for level 3 becomes "Which module owns the logic, which pattern
fits, named alternatives + why. A file layout or schema alone doesn't answer
it." The Question cell stays.

### `design-levels`, level 3 gate (lines 233 - 239)

The last sentence, "A structural choice with no credible alternative earns no
record, and saying so is the answer", is followed by the claim, in the same
form level 2 gives `arch none`:

> State that with a claim, not a sentence in the transcript:
>
> ```bash
> wfctl step none brainstorm.software-design --reason "<why no structural choice>"
> ```
>
> Brainstorm holds on its `software-design` pass until the branch either touches
> `<arch-root>/design/` or carries this claim. A placeholder reason is refused.

### `design-levels`, where each answer is written (line 88)

An unattended run follows this table to find where each gate's answer goes.
The level-3 row becomes "`design.md`, plus a record under `<arch-root>/design/`
when credible alternatives were weighed, or a `brainstorm.software-design`
claim when the branch writes none". That matches the level-2 row, which already
names "the declared absence of one".

### `design-levels`, Where the levels land (line 410) and Verification (line 487)

1. The level-3 bullet says that both cases that earn no record answer with the
   claim. A choice with no credible alternative earns no record. Neither does a
   branch whose only structural choice drew a boundary, since that was level
   2's record. In both cases, the branch writes nothing under `design/`, so it
   claims the pass with `wfctl step none brainstorm.software-design --reason
   "<why>"`, and the reason says which case it is.
2. The level-3 checklist item gains "or the change carries a
   `brainstorm.software-design` claim with a reason".

### `speckit-brainstorm`

1. The re-entry paragraph ("If `design.md` already exists…") says the step can
   also be held on its `software-design` pass. The answer is a record under
   `<arch-root>/design/`, written with `software-design-decisions`, or
   `wfctl step none brainstorm.software-design --reason "<why>"`. As with the
   boundary question, `design.md` is not what was missing.
2. The "Where a level was answered with no record" sentence says the level-3
   case is answered by the claim as well as by the one line in `design.md`.
3. Under the auto-approve table, a sentence says the agent runs the claim
   itself, with a reason, and commits it. The PR review is the human sign-off,
   the same as for `arch none`, and no separate sign-off is added (FR-009a).

### `speckit-brainstorm` and `commands/speckit.brainstorm.md`, `allowed-tools`

Without a grant, an unattended run reaches the claim and gets a refusal or a
prompt nobody answers, so brainstorm stays held until a person steps in. Both
frontmatters gain the same entry:

```
Bash(wfctl step none brainstorm.software-design *)
```

We chose the narrow form because brainstorm's agent only ever needs to claim
this one pass. A `Bash(wfctl step none*)` grant, mirroring `arch none*`, would
let the same unattended agent claim away any pass, including
`plan.plan-review` and passes a repository declares. The skill text puts the
pass name straight after `step none`, so the command the agent runs matches the
grant.

`test_brainstorm_allows_the_commands_its_records_need` gains two assertions
for both surfaces: the narrow grant is present, and `Bash(wfctl step none*)` is
absent. Its existing check that the two grants are equal covers drift between
them.

### `software-design-decisions`, "Not for"

"An implementation that only ever had one shape is not a decision, and saying so
is an answer rather than a missing record" gains: "Say it with
`wfctl step none brainstorm.software-design --reason "<why>"`, which is what
releases brainstorm."

### `README.md`, the `wfctl status` example (lines 45 - 47)

Add the `software-design` row between `architecture` and `design-doc`, and
widen the pass rows to the new column. The new row shows `●`. The example's
`design-doc` row is `▶`, and the cascade only allows that once
`software-design` is done.

### `docs/reference.md`

A new section after "Declaring your trunk (`trunk`)", titled "Turning off the
design record checks (`design_record_checks`)". It says that both brainstorm
checks hold a branch when git can't answer, that `trunk` fixes a repo with no
base branch, and that `"off"` is for a repo whose architecture folder sits
outside the project. It shows `{ "design_record_checks": "off" }`.

### `changes/648.change.md`

"Brainstorm now holds a branch until the software design question is answered,
with a record under `docs/architecture/design/` or `wfctl step none
brainstorm.software-design`. Both brainstorm checks now hold a branch when git
can't tell whether it added a record. Name your base branch with `trunk`, or set
`design_record_checks` to `"off"` in `wfctl.json` if your architecture folder
is outside the project."

## Project Structure

### Documentation (this feature)

```text
648-design-gate/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _paths.py           # arch_location moves here; design_record_checks reader
├── _pipeline.py        # the third brainstorm pass, Step docstring
├── _evidence.py        # brainstorm_software_design, both checks hold when git can't answer
├── cli.py              # pass column width, check config finding
└── agents/
    ├── commands/speckit.brainstorm.md   # allowed-tools grant
    └── skills/
        ├── design-levels/SKILL.md
        ├── speckit-brainstorm/SKILL.md  # rewording and allowed-tools grant
        └── software-design-decisions/SKILL.md

tests/
├── test_software_design_pass.py           # new
├── test_declared.py                       # pass list assertions, docstring
├── test_cli_status.py                     # pass rows at the new width
├── test_skill_cross_references.py         # grant and claim-command checks
├── test_pipeline_payload_snapshot.py      # `recorded` gains a design/ record
├── pipeline_payload_snapshot.json         # regenerated, research R9
└── (fixtures found by the suite, research R9)

README.md
docs/reference.md
docs/architecture/promised-evidence-blocks-on-silence.md   # amended
changes/648.change.md
```

New tests in `tests/test_software_design_pass.py`, in a git repository with a
`main` trunk, using the setup `tests/test_design_gate_drawing.py` uses:

1. Held: `design.md` and an architecture declaration, nothing under `design/`.
   Brainstorm is current, the pass is `in_progress`, and the payload carries
   the reason and the remedy with the repo-relative location.
2. Released by an uncommitted file under `design/`.
3. Released by a committed file under `design/`.
4. A record under the arch root outside `design/` releases `architecture` and
   not `software-design`.
5. Released by `wfctl step none brainstorm.software-design`, with no
   `wfctl.json`. The row is hidden, and `--all` shows `claimed: <reason>`.
6. Not held when `spec.md` exists.
7. Held with no trunk, where git can't answer, with `GIT_UNANSWERED_REASON`
   and a remedy naming `trunk` and `design_record_checks` (FR-006).
8. Held when the arch root is outside the tree, with the same reason (FR-006).
8a. With `design_record_checks` set to `"off"`, both checks read `skipped`
    with `CHECKS_OFF_REASON`, in a repo with no trunk and in one with an arch
    root outside the tree (FR-006a). The payload's `warnings` list is empty in
    both, and `status` prints no warning line.
8b. A `design_record_checks` value other than `"on"` or `"off"` is a `check
    config` finding and leaves both checks on. An arch root outside the tree
    with the setting on is a finding too (FR-006b), both with a `wfctl.json`
    and in a repo with none, where `check config` exits 1 instead of printing
    `no configuration to check`.
8c. The architecture check holds with no trunk, where it used to let the
    branch through. The existing tests that asserted the old let-through
    change to assert the hold (research R10 lists them).
8d. With `_evidence.blocks` patched to return false, both checks read done
    when git can't answer. This proves each reader lets `blocks` decide what
    git's silence means. `test_every_inconclusive_verdict_goes_through_blocks`
    can't show that, since it only checks that `blocks` is called somewhere in
    the function, and a reader that returned early for `inconclusive` would
    still pass it.
9. Every pass glyph has at least two spaces before it, with `plan-walkthrough`
   and `software-design` both shown.
10. A declared `software-design` under brainstorm is a `check config` finding.
11. Still held when a design record was committed to `main` before the branch
    was cut. This is the case that separates "this branch answered" from "a
    record exists".
12. Under `auto_approve`, the held pass writes `auto: false` to `next-step.md`,
    so the run stops at brainstorm (US1 acceptance 3).

Changes to existing tests:

13. In `tests/test_skill_cross_references.py`, beside
    `test_the_no_boundary_exit_names_its_command`, a new test asserts that
    `design-levels`, `speckit-brainstorm`, and `software-design-decisions` each
    contain `wfctl step none brainstorm.software-design` (SC-004).
14. `test_brainstorm_allows_the_commands_its_records_need` asserts the narrow
    grant and the absence of the broad one, as above.
15. In `tests/test_pipeline_payload_snapshot.py`, the `recorded` repository
    gains a record under `design/`, so `design-with-record` still reads `done`
    and `test_the_matrix_reaches_both_design_states` keeps its meaning. A new
    row records a branch held on `software-design`.

**Structure Decision**: single project. Every change is in an existing module
except the new test file.

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution | This repository has none | Gates come from `AGENTS.md` and the accepted records, as in #626's plan |
| `arch_location` moves to `_paths` | `_evidence` needs it, and importing `_pipeline` from `_evidence` adds a cycle | An inline copy would be a second place the location format is written (research R4) |
| A new `wfctl.json` key, `design_record_checks` | A repo whose architecture folder is outside the project has no other way out of the hold, since `wfctl arch none` is found through git too | Reusing `trunk` with `"none"` would mix two different situations: no base branch, and an architecture folder git can't see (research R10) |
