# Implementation Plan: SVG drawings

**Branch**: `740-svg-drawings` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this folder

## Summary

A record's drawing can be a hand-drawn SVG file in `drawings/` under the arch root, linked from the record as a markdown image, and wfctl checks it the same way it checks a mermaid fence. A new module, `wfctl/arch/_drawing.py`, turns whatever sits under a `## Boundary` or `### <kind>` heading into one frozen `Drawing` summary. The summary holds the labels, whether a failing step is shown, how to draw one in this format, the labels past the edge, and any problem reading it. The mermaid regular expressions move into that module unchanged. Every check in `_records.py` that reads a drawing reads the summary, so no check parses either format (`740-one-drawing-reader`).

A drawing with a problem, such as a missing file or invalid XML, gets one line naming the problem in place of the missing-drawing line, both at acceptance and as a doctor warning. `contracts/cli.md` lists the output for each case.

`drawings/` joins `non_record_subtrees`, so the design gate and the record listing never count an SVG as a record. The drawing style goes in one new reference file under `design-levels`, linked from the four skills that teach drawing (`740-drawing-style-one-file`). The skills and templates teach SVG as the default, and `record-drawing-can-be-svg.md` drops its mermaid copy.

Accepting a record is the user's sign-off on its drawing. `wfctl arch accept` writes each SVG's fingerprint on the `accepted` Log line, and doctor warns when an accepted record's SVG no longer matches. The user looks at the drawing and runs `wfctl arch accept` on the record again, which appends a `redrawn` line with the new fingerprint (research R-011, R-012). The worktree guard refuses the real accept from an agent, and the command refuses to write without a terminal, the same two checks `wfctl review sign-off` has. `--dry-run` stays open to agents (R-013).

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer` and `rich`, unchanged. SVG parsing uses `xml.etree.ElementTree` from the standard library, so the change adds no dependency. An SVG carrying a DOCTYPE is refused before parsing, so entity handling doesn't depend on the machine's expat version (research R-001).
**Storage**: Files only. SVGs live in `<arch-root>/drawings/`, committed beside the records.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `python3 .github/scripts/check_imports.py`, then `uv run wfctl install-skills` and `uv run wfctl doctor`. A one-off comparison in the scratchpad shows no record's result changed (research R-010).
**Target Platform**: macOS and Linux, wherever wfctl runs.
**Project Type**: CLI with bundled skills as package data.
**Performance Goals**: No measurable change. There is one reader per format and no cache, so one `validate` call parses a record's SVG a few times, once per check that reads it. An SVG is a few KB.
**Constraints**: No new runtime dependency. Every record that passes or fails acceptance today gets the same result (FR-011). The `no drawing` fix and the `_DRAWING_FIX` entries are the only reworded text. The `_DRAWING_FIX` entries print only under `wfctl arch accept`. The `no drawing` line is part of `accept_problems`, so its new wording also shows in the design gate's reason, and doctor doesn't print it. Minimal-complexity bias: two frozen dataclasses and three plain functions, not a class hierarchy.
**Scale/Scope**: 47 records carry a mermaid drawing today, one carries an SVG, and 38 print `no drawing`. Two contexts change, `architecture-records` and `design-method`.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. The gates below come from the accepted records `wfctl arch context` prints for this branch, and from `AGENTS.md`. Complexity Tracking records the substitution.

- [x] Validation plan exists: `pytest`, `ruff`, `mypy`, and the import check, plus the tests and the one-off comparison named in `quickstart.md`. A change under `wfctl/agents/` is also exercised after `uv run wfctl install-skills`, as `AGENTS.md` requires.
- [x] Complexity is justified: the new types are the `Drawing` summary, which `740-one-drawing-reader` argues against the direct baseline, and `Problem`, which has the same two fields as `Refusal`. No dependency is added.
- [x] Ownership is stated: wfctl computes the summary from the record and the SVG file. The author marks the failing step with a class, since wfctl would have to guess it from a color (`record-drawing-can-be-svg`). The user judges whether a drawing reads well.
- [x] `contexts-are-packages`: the new module is `wfctl/arch/_drawing.py`, with a leading underscore, imported only by `_records.py` inside the same package and by `tests/test_arch_labels.py`. `arch/__init__.py` exports nothing new. The `drawings/` constant goes in `wfctl/_paths.py` beside `VIEWS_DIR`.
- [x] `a-rule-is-expressed-as-a-check`: each rule the change adds is a refusal or a doctor warning, and the one rule that stays prose, the drawing style, is delivered by the skills at the moment an agent draws.
- [x] `the-author-declares-the-diagram-kind`: the change reads a kind's drawing in a second format, and still never infers the kind.
- [x] `knowledge-placement`: the style is guidance for the worker, so it lives in a skill reference file, not in `docs/architecture/`.
- [x] `change-carries-release-note`: `changes/740.addition.md`.

Post-design re-check: still passing. `_drawing.py` imports `wfctl._md`, which `_records.py` already imports. `_records.py` gains an import of `wfctl._paths`, which it doesn't have today. That import is allowed without a baseline line because `_paths` is a core module (`check_imports.baseline` lists `_paths.py core`), and any context may import core (PR-009).

## Project Structure

### Documentation (this feature)

```text
wfctl-specs/740-svg-drawings/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # The lines this change adds, and the one it rewords
├── scans/clarify.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
wfctl/
├── _paths.py                         # DRAWINGS_DIR, added to non_record_subtrees, with a #761 pointer;
│                                     # record_change, decided_on_this_branch, records_on_this_branch(skip=)
├── _record_gate.py                   # touched skips a record arch.redraw_only accepts
├── _evidence.py                      # branch_records and _level_records pass skip; _architecture_answered
│                                     # asks decided_on_this_branch
├── _review_gate.py                   # ACCEPT_REFUSAL; refuses `wfctl arch accept` without a --dry-run word, per command
├── cli.py                            # arch accept: terminal check, redrawn path on an accepted record;
│                                     # record: lines pass skip; _observe asks decided_on_this_branch
└── arch/
    ├── __init__.py                   # exports redraw_only
    ├── _drawing.py                   # new: Drawing, Problem, read_fence, fence_labels, read_svg, fingerprint, the mermaid regexes
    └── _records.py                   # _drawing/_drawings return Drawing; checks read the summary; problem lines;
                                      # accept writes fingerprints; _append_log; REDRAWN_LINE; redraw_only;
                                      # redraw; doctor's accepted-record warnings

wfctl/agents/skills/
├── design-levels/
│   ├── SKILL.md                      # rewrites the mermaid sentence, links the style file
│   └── references/drawing-style.md   # new: the style, with a #761 pointer
├── architecture-decisions/
│   ├── SKILL.md                      # rewrites five passages, the immutability section included; links the style file
│   └── record-template.md            # SVG by default, mermaid still passes
├── software-design-decisions/
│   ├── SKILL.md                      # links the style file
│   └── design-record-template.md     # SVG by default, mermaid still passes
├── model-the-domain/
│   ├── SKILL.md                      # line 250: an SVG in the record, mermaid in the domain document
│   └── references/visual-language.md # rewrites the format sentence, links the style file
└── architecture-design/views/
    ├── system-context.md             # SVG by default
    ├── container.md                  # SVG by default
    └── component.md                  # SVG by default

docs/
├── reference.md                      # a drawing can be a linked SVG; the failing-step class
└── architecture/record-drawing-can-be-svg.md   # mermaid copy removed; Consequences already states the sign-off (commit 320b19c)

changes/740.addition.md

tests/
├── test_arch_drawing_svg.py          # new: the SVG reader, problem output, and doctor warnings
├── test_arch_drawing_fingerprint.py  # new: the Log line, CRLF, redrawn, doctor's changed-SVG warning
├── test_review_gate.py               # extended: arch accept refused, --dry-run allowed as a word, one command at a time
├── test_redraw_only.py               # new: the four conditions, each failing on its own, and the no-newline case
├── test_record_gate.py               # extended: a redraw-only record change passes; any other edit beside it doesn't
├── test_design_gate_drawing.py       # extended: an SVG in drawings/ is not a record; a redraw-only record
│                                     # doesn't answer the boundary question, with and without a name list
├── test_paths_redraw.py              # new: record_change and decided_on_this_branch on a real git repo,
│                                     # uncommitted and untracked records, no trunk
├── test_scan_files.py                # extended: a redraw-only branch's Boundary line, and its record: lines,
│                                     # beside the scan-file cases those two already exclude
├── test_drawing_style_links.py       # new: the four links to the style file resolve
├── test_arch_labels.py               # imports fence_labels from _drawing; assertions unchanged
├── test_arch_accept.py               # patches _at_terminal where it accepts for real; one test for the refusal
├── test_arch_accept_drawing.py       # patches _at_terminal in the tests that accept for real; assertions unchanged
├── test_arch_accept_dry_run.py       # patches _at_terminal in the pasted-bullet test; parity tests unchanged
├── test_arch_diagram_kinds.py        # the two sequence fix assertions take the new _DRAWING_FIX text
└── pipeline_payload_snapshot.json    # the reworded no-drawing line, twice
```

**Structure Decision**: A new private module inside the `arch` package holds both readers and the summary types, since `_records.py` is 1,276 lines and the readers have no other caller. The mermaid regexes move there with their docstrings. `_records.py` keeps the heading logic (`_section_bounds`, and which fence or link belongs to which `### <kind>`), because that's about the record's structure, not the drawing's format. It also keeps the message prefixes. The summary carries only `failure_fix`, the half of the failing-step message that depends on the format.

### Skill prose that changes

The templates ask for SVG, so every sentence in the skills that states mermaid as the rule, or says acceptance needs a fence, changes with them. If it didn't, an agent would read "a record is drawn in mermaid" in the skill and "draw an SVG" in the template (PR-005). Each passage below is rewritten, and the style itself is linked rather than restated.

| Passage | Says today | Says after |
| --- | --- | --- |
| `design-levels/SKILL.md:371-374` | a level-2 sketch is redrawn as mermaid when it lands in a record | ASCII while the gate is answered; a record's drawing is an SVG in `drawings/`, drawn to `references/drawing-style.md`, and a mermaid block still passes |
| `architecture-decisions/SKILL.md:92-105` | Boundary is drawn in mermaid unless ASCII is better; `_drawing` reads any non-empty fence | Boundary links an SVG by default, per the style file; a mermaid or ASCII fence still passes; wfctl reads the SVG's labels and checks them |
| `architecture-decisions/SKILL.md:119-124` | the failing row is an `alt`, `opt`, `break` or `critical` block, or a `-x` message | in an SVG, the failing step carries `class="failing-step"`; in mermaid, today's four blocks or a `-x` message |
| `architecture-decisions/SKILL.md:139-140` | a data-flow and a component sketch are both mermaid flowcharts | the two can look alike in either format, so the headings are what tell them apart |
| `architecture-decisions/SKILL.md:284-289` | a fenced block and a `diagram:` are what acceptance requires; mermaid is the default | an SVG image or a fenced block, and a `diagram:`, are what acceptance requires; SVG is the default |
| `model-the-domain/references/visual-language.md:3-7` | in a record or a domain document it is mermaid | in a record it is an SVG, drawn to the style file; in a domain document it stays mermaid until #761 gives domain documents a place for their drawings |
| `architecture-decisions/SKILL.md:230-237` | once accepted, only the status changes and one Log line is appended | the same, plus a `redrawn` Log line when the user signs off a layout fix to the SVG; a change to what the drawing shows supersedes the record |
| `model-the-domain/SKILL.md:250` | sketches are ASCII while answering and mermaid in the document and the record | ASCII while answering, an SVG in the record, and mermaid in the domain document, linking `references/visual-language.md` for what each shows |

Domain documents keep mermaid because the spec puts SVGs for records, design records, and views in `drawings/`, and gives domain documents no folder. Moving them would need a decision this branch doesn't make (PR-016).

`quickstart.md` §5 greps these files after the change to confirm none still states the mermaid default for a record.

### An accepted record's drawing

An accepted record's SVG may change only in layout, such as moving a box or shortening a label, and the commit message says why. A change to what the drawing shows supersedes the record. `drawing-style.md` and the Consequences of `record-drawing-can-be-svg.md` both state this rule (walkthrough W1).

### What `drawings/` being excluded costs

Excluding `drawings/` from the record readers stops an SVG from counting as a changed record, and it also means a change to an accepted record's SVG doesn't reach the design gate. Before this change, a record's drawing lived in its body, where the frozen-body convention and the gate both covered it (PR-007).

The fingerprint closes that gap. Doctor warns when an accepted record's SVG is missing, moved out of `drawings/`, or can't be parsed, and when it no longer matches the fingerprint on its Log line (`contracts/cli.md`). Doctor can't tell a layout fix from a change in meaning, so the warning sends every edit to the user, who either signs off with `wfctl arch accept` or asks for a superseding record. `record-drawing-can-be-svg.md`'s Consequences states both.

### Who can accept

Accepting a record now carries the user's visual sign-off, so an agent mustn't be able to do it. The skills already say so, and this change adds the check, as `a-rule-is-expressed-as-a-check` requires. The guard refuses `wfctl arch accept` from an agent unless it carries `--dry-run`, and the command refuses to write without a terminal (R-013). This changes what an agent can run in every repo that installs wfctl, which is the same change `wfctl review sign-off` and `wfctl arch approve-imports` already made.

### A redraw on a branch

A `redrawn` Log line edits the accepted record's file, and every reader that asks what the branch decided counts an edited record. A branch that only fixes a drawing's layout says no boundary moved, so the record gate would refuse its PR and tell the author to delete that answer. Once deleted, the design gate would count the redraw as the boundary answer.

So every reader skips a record whose only change is added `redrawn` lines in its `## Log`, on an accepted record (R-014). The readers are the record gate, the per-context design gate through `branch_records`, the general boundary check, `_observe`'s `Boundary` line, and the `record:` lines (PR-020). Any other edit beside the `redrawn` lines still counts, committed or not, and a new or untracked record is never a redraw (PR-025, PR-026).

`wfctl.arch` recognizes the line, in the same module that writes it, so the format is spelled once (PR-027). `_paths` does the git side, beside `non_record_subtrees`, since AGENTS.md sends every new reader of the arch root there for the exclusions it has to make. `_paths` is core and can't import `wfctl.arch`, so each reader passes `arch.redraw_only` in.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Gates substituted from accepted records and `AGENTS.md` | The repo has no constitution file. | A gate with no source would be decorative, and the accepted records are what binds this branch. |
| A `Drawing` summary type | Four checks read two formats. | `740-one-drawing-reader` compares it with each check parsing both formats, which spreads format knowledge across four places. |
| A `Problem` type beside `Drawing` | A problem needs a fix line in both the one-kind blocker and the multi-kind `Refusal`. | A bare string has no fix to print, and reusing `Refusal` would make `_drawing.py` import from `_records.py`, which imports it. |
| A `redrawn` Log line | The doctor warning on a changed SVG needs a way to clear, and the user chose acceptance as the sign-off. | Superseding the record for every layout fix costs a new record for a moved box. An `approve-drawing` command was rejected as too verbose (R-012). |
| Reading font sizes from the SVG's `<style>` block | The style guide teaches classes, and the user chose to read both attributes and CSS (clarify Q4). | Attributes alone would miss every label sized by a class, which is how the existing SVG sizes its text. |
