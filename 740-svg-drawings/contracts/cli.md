# CLI contract: SVG drawings

These are the lines this change adds to `wfctl arch accept`, `wfctl doctor`, and the worktree guard, and the fix text it rewords. Every other line that exists today keeps its wording when the drawing is a fence (FR-011).

## The reworded fix text

FR-011 allows two kinds of fix text to change. The `_DRAWING_FIX` entries print only under `wfctl arch accept`'s refusal lines, since `accept_problems` carries only a refusal's problem half. The `no drawing` line is an `accept_blockers` string, so `accept_problems` carries it whole, and its new wording shows in the design gate's reason too. `validate` carries neither, so doctor output doesn't change.

A one-kind record with nothing drawn gets the same blocker as today, with its fix naming an SVG first, since SVG is now the default:

```
no drawing: add an SVG image or a fenced block under '## Boundary'
```

Today it reads `no drawing: add a fenced block under '## Boundary'`. The line still fires for exactly the same records, so every record keeps its acceptance result (PR-001). `tests/pipeline_payload_snapshot.json` carries the old text twice and is updated with it.

Each `_DRAWING_FIX` entry names an SVG in `drawings/` first and the mermaid form second:

| Kind | Today | After |
| --- | --- | --- |
| `data-flow`, `component` | `a mermaid flowchart` | `an SVG in drawings/, or a mermaid flowchart` |
| `state` | `a mermaid stateDiagram-v2` | `an SVG in drawings/, or a mermaid stateDiagram-v2` |
| `sequence` | `a mermaid sequenceDiagram, including the step that fails (an alt block or a -x message)` | `an SVG in drawings/ with class="failing-step" on the step that fails, or a mermaid sequenceDiagram with an alt block or a -x message` |

Two exact-output tests in `tests/test_arch_diagram_kinds.py` pin the old `sequence` text, at lines 207-213 and 299-307. Both are updated to the new text, and their other lines stay the same (PR-015).

## A drawing with a problem

`data-model.md` lists each problem and its fix. A problem line replaces the missing-drawing line that the same record would otherwise get, at the same place in the reading order. The record never gets both (PR-002).

| Record | What `accept_problems` returns | What doctor warns, while proposed |
| --- | --- | --- |
| One kind, problem under `## Boundary` | `'## Log'` blocker if any, then `<problem>: <fix>` where `no drawing` would sit, then the kind blockers | `<problem>` |
| Several kinds, problem under `### <kind>` | `accept_blockers` as today, then `### <kind>: <problem>` where `declares a <kind> diagram but doesn't draw one` would sit | `### <kind>: <problem>` |

In the multi-kind case the `Refusal` is `Refusal("### <kind>: <problem>", <fix>)`, so `wfctl arch accept` prints the fix under it the way it prints every kind refusal.

A drawing with a problem doesn't count as drawn. The failing-step check and the label check skip it, so a broken SVG gets one line, not three.

### Doctor

`validate` already repeats `_drawing_refusals` for a proposed record, which covers the multi-kind case. For a one-kind record, `validate` adds a warning with the problem text when `_drawing(record).problem` is set. Before this change, a one-kind record could have no drawing problem, so this adds a path rather than changing one (PR-003).

An accepted record gets the same problem warning, and a warning for each SVG that changed since the user accepted it (FR-021). No accepted record links an SVG today, so no current finding changes.

## `wfctl arch accept` refusals

| Case | Line, for a one-kind record |
| --- | --- |
| The SVG doesn't exist | `drawing links drawings/x.svg, which doesn't exist: create it, or correct the link.` |
| The SVG is outside `drawings/` | `drawing links ../x.svg, which is outside drawings/: move it into the drawings/ folder beside the records, and update the link.` |
| A sequence SVG with no failing step | `a sequence drawing with no step that fails: add class="failing-step" to the element that fails` |
| No terminal, without `--dry-run` | `✗ wfctl arch accept needs a person at an interactive terminal` |

The rest of the problem cases follow the same pattern from `data-model.md`. A sequence fence with no failing step keeps today's line, since its `failure_fix` is today's text.

## `wfctl arch accept` on an accepted record

| The record | Result |
| --- | --- |
| Any acceptance check fails, such as a drawing problem or a sequence SVG with no `failing-step` | The same refusal a proposed record gets, and exit 1 |
| At least one SVG no longer matches its fingerprint, or has none on the Log | Appends a `redrawn` Log line with every SVG's current fingerprint, prints `✓ <slug>: drawing signed off` and the line, and exits 0 |
| Every SVG matches, or it has no SVG | Today's refusal for an accepted record, unchanged |

The rows are checked in that order. `--agreed` is required the same way as for a proposed record, and `--dry-run` says which row it would take and writes nothing.

A branch whose only change to an accepted record is a `redrawn` line in its `## Log` doesn't count as changing that record. The record gate, the design gate, the session's `Boundary` line, and the `record:` lines all pass it over (FR-026).

## `wfctl doctor` warnings

| Case | Records | Line |
| --- | --- | --- |
| A drawing with a problem | proposed, accepted | the problem text, as above |
| A label missing from the prose | proposed | `drawing label '<text>' appears nowhere else in the record` (unchanged) |
| A sequence SVG with no failing step | proposed | `declares a sequence diagram with no step that fails — add class="failing-step" to the element that fails` |
| A label past the edge | proposed | `drawing label '<text>' runs past the drawing's edge` |
| An SVG changed since acceptance | accepted | `drawing <link> changed since it was accepted — look at it, then run wfctl arch accept <slug> --agreed "<where>"` |

Superseded and retired records get none of these, since their drawings no longer bind anything.

## The worktree guard

| Command, in the agent's shell | Result |
| --- | --- |
| `wfctl arch accept <slug> --agreed "<where>"` | Refused: `✗ wfctl arch accept is for a person to run in their own terminal, not an agent. An agent can run it with --dry-run.` |
| `uv run wfctl arch accept <slug> --agreed "<where>"` | Refused, the same line |
| `wfctl arch accept --dry-run -- <slug>` | Allowed |
| `wfctl arch accept --dry-run -- a; wfctl arch accept b --agreed x` | Refused, since the second command has no `--dry-run` |
| `wfctl arch accept b --agreed "after a --dry-run"` | Refused, since `--dry-run` is inside a quoted word |

## Example

```
$ wfctl arch accept --dry-run -- example
✗ example can't be accepted:
  drawing links drawings/example-data-flow.svg, which doesn't exist: create it, or correct the link.
```
