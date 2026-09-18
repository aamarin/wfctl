# CLI contract: declared passes

## Added

### `wfctl check config`

Validates the repository's own `wfctl.json` — every declaration wfctl cannot
honour, in one run (FR-022). It reads configuration and the installed command
directories; it never reads the state dir and never writes.

| Situation | Output | Exit |
| --- | --- | --- |
| No `wfctl.json` | `✓ no configuration to check` | 0 |
| `steps` absent | `✓ wfctl.json: no passes declared` | 0 |
| Every declaration honourable | `✓ wfctl.json: <n> passes under <m> steps` | 0 |
| Any finding | `✗ wfctl.json:` then one `  - <finding>` per problem | 1 |
| Malformed JSON | `✗ wfctl.json: not valid JSON (<detail>)` | 1 |

Findings, one line each. `<step>.<name>` throughout, because that is the form
the name is written in wherever it is typed (FR-002b):

| Finding | Text |
| --- | --- |
| Unknown step key | `'<key>' is not a pipeline step — one of: brainstorm, specify, clarify, plan, tasks, analyze, decompose, implement` |
| Missing name | `<key>[<i>] has no 'name'` |
| Duplicate name | `<step>.<name> is declared twice under one step` |
| Both `command` and `manual` | `<step>.<name> declares a command and 'manual' — one or the other` |
| Neither | `<step>.<name> declares no command and is not marked manual — say which` |
| Command not installed | `<step>.<name> names <command>, which is not installed in this repository` |
| Missing evidence | `<step>.<name> has no 'evidence'` |
| Sibling not found | `<step>.<name> names sibling '<sibling>', which is not declared under <step>` |
| Unsatisfiable order | `<step>: the stated order cannot be satisfied — <a>, <b>, <c>` |
| Nested pass | `<step>.<name> declares passes of its own; passes nest one level below a step` |
| Bad `on_finish` | `<step>.<name> has on_finish '<v>' — one of: automatic, review_required` |

A pass marked `manual` is never reported for a missing command (FR-022a). A name
reused under a *different* step is never reported (FR-002a).

### `wfctl step none <step>.<name> --reason "<text>"`

Declares that one pass does not apply to the change under review (FR-012). It
generalises `wfctl arch none`, and refuses on the same two grounds.

| Situation | Output | Exit |
| --- | --- | --- |
| Written, and part of the change | `✓ Recorded: <step>.<name> does not apply — "<reason>"` | 0 |
| `--reason` empty | `✗ --reason cannot be empty: say why this pass does not apply.` | 1 |
| `--reason` is `<placeholder>` | `✗ "<why>" is a placeholder, not a reason — say why this pass does not apply.` | 1 |
| No such pass | `✗ <step>.<name> is not a declared pass. Under <step>: <names>` | 1 |
| Bare name, one match | resolves; output as the first row | 0 |
| Bare name, several matches | `✗ '<name>' is declared under <step-a> and <step-b> — qualify it` | 1 |
| Bare name, no match | `✗ '<name>' is not a declared pass` | 1 |
| Written outside the change | `⚠ Wrote <path>, but it is not part of the change under review …` | 1 |

Writes `<arch-root>/step-claims/<branch>/<step>.<name>.md`. Nothing is written on
any refusal (FR-013). A bare name never resolves against the current step
(FR-002c).

## Changed

### `wfctl status`

Passes render indented under their step, in the order they run. A settled-away
pass is hidden (FR-018):

```
brainstorm   ▶  ← current
  architecture ●
  design-doc   ▶  /speckit.brainstorm
specify      ○
```

A pass's glyph is drawn from the same four-state map a step's is (`_STATE_GLYPH`)
— the row holding the pipeline reads `▶`, not a fifth symbol invented for
passes. `design-doc` above is `▶` for the same reason `brainstorm` itself is:
it is the one thing outstanding.

A pass that is holding the pipeline is always shown, claimed or not — the row
stays visible until it is settled, so a step never reports itself unfinished with
the reason off screen.

A repository that declares nothing sees exactly what it sees today (US1
acceptance 4): no indented rows, no blank line, no header.

### `wfctl status --all`

Shows every pass including the settled-away ones, each carrying the reason its
claim was written with (FR-019):

```
brainstorm   ●
  architecture ●
  design-doc   ●
  ui-design    –  claimed: backend-only change, nothing to design
```

### `wfctl status --json`

See `status-payload.md`. `--all` does not change it: the payload always carries
the full tree (FR-020), so the flag selects a console rendering and nothing else.

### `wfctl next` / `wfctl resume`

`next-step.md` may now name a pass's command. Where the outstanding pass is
`manual`, the file names the pass and says a person performs it (FR-007):

```
Next step: <step>.<name>
auto: false
why: a person performs this pass
Run this command to continue.
```

## Unchanged

`wfctl doctor` reports nothing about declared passes (R5). `wfctl arch none`
keeps its own verb, its own path and its own text — `step none` is a second
command, not a rename.
