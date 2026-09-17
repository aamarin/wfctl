# Implementation Plan: Declare pipeline step

**Branch**: `339-declare-pipeline-step` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/339-declare-pipeline-step/spec.md`

## Summary

A pipeline step gains an ordered list of passes, exactly one level deep. A pass
has the shape a step has — a name, a command or a statement that a person
performs it, a continuation, and a predicate — and reports the same four state
names. Two lists fill it: wfctl's own, hardcoded in the step table, and a
repository's, read from `wfctl.json` under a new `steps` key. Nothing on a pass
records which list it came from.

`brainstorm` is the first consumer of its own mechanism. Its two artifacts — an
architecture record, and `design.md` — become two passes, which is what turns
"the step is unfinished and here is one sentence about why" into two rows with a
state each and a command that produces the outstanding one.

A person declares a pass inapplicable with `wfctl step none <step>.<name>`, which
writes one file per pass into the change under review. The claim is not read
back: a reviewer disagreeing with it is its only check. The default position view
hides a settled-away pass; `--all` brings it back with the reason; the
machine-readable view always carries everything.

A new `wfctl check config` reports every declaration wfctl cannot honour and
exits non-zero. Nothing is dropped silently — that is the whole of why the check
exists, and it is what Question 5 settled.

Two modules are added (`_declared`, and a `check` command group). No dependency
is added. `doctor` is not touched.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: typer, rich. Nothing is added.
**Storage**: `wfctl.json` in the repository, read-only. Claims are files under the arch root, in the change under review. No state-dir shape changes; no new event type.
**Testing**: `uv run --frozen --extra dev pytest -q`, `ruff check wfctl/ tests/`, `mypy wfctl/`, then `uv run wfctl install-skills --prune --yes --agent claude` and `uv run wfctl doctor`. The five by-hand exercises in `quickstart.md`.
**Target Platform**: macOS and Linux developer machines, anywhere the CLI runs
**Project Type**: CLI, with the skills it ships as package data
**Performance Goals**: no new read per `status` for a repository that declares nothing — `wfctl.json` is already read for `verify`. A repository that declares passes pays one predicate call per pass, only under a step that was reached.
**Constraints**: `pipeline-state-is-one-payload` holds — one inference, every view a rendering. A repository declaring nothing sees byte-identical output. No aliases, no migration: the `steps` key is new, and its absence is every repository's current state.
**Scale/Scope**: 2 new modules, ~6 modules touched, 3 new CLI surfaces, 1 payload key, ~18 new tests, 1 snapshot rewritten

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

There is no `.specify/memory/constitution.md` in this repo. The gates below come
from `AGENTS.md` and the accepted records `wfctl arch context` prints. The
substitution is noted under Complexity Tracking.

- [x] **Validation plan exists**: the three `uv run` commands, `install-skills`
      then `doctor`, the five by-hand exercises in `quickstart.md`, and the
      eighteen tests it names. Four of those exercises are cases the suite can
      pass while the behaviour is wrong, which is why the spec lists them
      separately.
- [x] **Complexity is justified**: one level of nesting, and the record's own
      *Considered* section carries why a general tree was rejected — every view
      learns recursion and every consumer learns depth, to express a nesting
      nobody has asked for. The direct baseline (an extra evidence path on the
      parent's predicate) is rejected in the record for the reason that is this
      feature's point: the pass stays invisible, which is the defect rather than
      a cost of fixing it.
- [x] **Ownership is stated**: wfctl owns *which passes a step requires and what
      state each is in*, as data on the payload. The parent step's predicate
      cannot own it — a predicate returns one state and one reason, so every pass
      collapses into a string, and a string has no state to route from, count, or
      declare away. The repository owns *which passes exist beyond wfctl's own*,
      because only it knows its process. A person owns *whether a pass applies to
      this change*, because no artifact can answer that — the second level-2
      record, `an-absent-artifact-is-claimed-not-inferred`.
- [x] **`pipeline-state-is-one-payload`**: `sub_steps` is a field on the payload,
      never a sentence a view parses back out of the parent's annotation. The
      console's `--all` filter runs at the moment of printing; the JSON is
      unfiltered. The record is extended, not superseded — its three claims are
      about one inference and views that compute nothing, and all three survive a
      payload whose steps carry passes. What goes is the flatness, which that
      record described rather than claimed.
- [x] **`a-rule-is-expressed-as-a-check`**: every rule this feature states about
      a declaration is visible in an artifact the work already produces —
      `wfctl.json` — so every one of them is a `check config` finding rather than
      prose. That is the rule applied to itself, and it is what Question 5
      settled for the nesting cap.
- [x] **`a-step-carries-sub-steps-one-level-deep`** (proposed): this plan is its
      implementation. The predicate-not-path decision is honoured — `evidence` is
      sugar that builds the file-exists predicate, and wfctl's own passes carry
      callables that read what no path can.
- [x] **`an-absent-artifact-is-claimed-not-inferred`** (proposed): "ran and
      produced nothing" and "does not apply" are one state (FR-017), and the
      claim is committed to the change under review rather than inferred.
- [x] **`knowledge-placement`**: a fact about one file goes in that file — the
      `steps` schema is documented beside its reader in `_declared`; the
      constraint on who owns pass state is in the arch record; nothing new goes
      into `AGENTS.md` except the `check config` verb.
- [x] **`vendor-upstream-skills`**: none of the files touched are spec-kit
      derived. `speckit-orchestrate` needs no change, and the wrapper commands
      under `wfctl/agents/commands/` are wfctl's own.
- [x] **`session-state-is-re-derived`**: claims are read off disk on every
      inference. Nothing is cached, and no claim is written to the state dir.
- [x] **`wfctl-runs-the-verification`**: unchanged. `check config` is not a
      definition of done and does not touch `verify.json`.
- [x] **`the-underscore-is-the-module-contract`**: `_declared` is private, and
      `_pipeline` imports it rather than parsing JSON itself.

Re-checked after Phase 1: unchanged. The one thing Phase 1 moved is where a
manual pass's `next_command` lands, and it moved *toward* the payload rather than
into a view.

## Project Structure

### Documentation (this feature)

```text
specs/339-declare-pipeline-step/
├── plan.md              # This file
├── research.md          # Phase 0 — eleven decisions, including design.md's two open questions
├── data-model.md        # Phase 1 — SubStep, DeclaredPass, ClaimedAbsence, the payload
├── quickstart.md        # Phase 1 — what to run, and the tests to add
├── contracts/
│   ├── cli.md           # check config, step none, status --all
│   ├── status-payload.md# the sub_steps key
│   └── wfctl-json.md    # the steps schema
├── design.md            # brainstorm output, already on specs-trunk
└── spec.md              # clarified, five questions banked
```

### Source (repository root)

```text
wfctl/
├── _declared.py         # NEW — parse and validate wfctl.json's `steps`; pure over parsed JSON
├── _pipeline.py         # Step gains sub_steps; _infer_steps walks them; the payload carries them
├── _predicates.py       # brainstorm splits into two pass predicates; file-exists builder for `evidence`
├── _paths.py            # non_record_subtrees gains step-claims/
├── cli.py               # `check config`, `step none`, `status --all`, indented rendering
└── agents/
    └── skills/          # position-reading prose where it names the eight rows

tests/
├── test_pipeline*.py    # pass states, ordering, roll-up, cascade
├── test_declared.py     # NEW — validation findings, one per rule
├── test_cli_status.py   # indentation, --all, the no-passes-declared regression
├── test_step_none.py    # NEW — claims, refusals, FR-016
└── pipeline_payload_snapshot.json   # rewritten wholesale
```

**Structure Decision**: the existing single-package layout. This feature adds one
private module beside the ones it talks to, and one command group inside `cli.py`
where every other command lives. No package, no sub-package, no registry.

## Phased delivery

Priority order is the spec's, and each phase is independently observable.

| Phase | Delivers | Observable by |
| --- | --- | --- |
| 1 | `SubStep` on `Step`, `_declared`, payload + `status` rendering, `check config` | US1 — declare a pass, see the row, get the command |
| 2 | `brainstorm`'s two built-in passes, the predicate read order fixed | US2 — wfctl's own passes report separately |
| 3 | `wfctl step none`, `step-claims/`, `--all`, `non_record_subtrees` | US3 — a pass claimed away, and the gate that still holds |

Phase 1 ships a mechanism with one consumer; phase 2 is the evidence it was the
right one. Phase 3 is what stops phases 1 and 2 installing a gate with no exit.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and `wfctl arch context` | This repo has no `.specify/memory/constitution.md`; the template requires the substitution be recorded | Shipping the two project-independent gates alone would drop `pipeline-state-is-one-payload` and `a-rule-is-expressed-as-a-check`, which are the two records this change is most able to break |
| A new module, `_declared` | One reader for two consumers — inference and the check must not disagree about what a file declares | Parsing in `cli.py` or in `_verify` makes two parsers of one file, which is FR-022's own failure mode |
| A second claim-writing verb beside `wfctl arch none` | A branch makes one boundary claim and as many pass claims as it has passes; `arch none`'s whole-file overwrite would lose all but the last (FR-015) | Generalising `arch none` to take an optional pass argument overloads a command whose refusals and path are specific to the boundary question |

## Known rough edge

`speckit-orchestrate` renders `Next: run \`{next_command}\` when ready.` A manual
pass reaches that line with a qualified pass name rather than a command, so it
reads *run `brainstorm.design-review`* for something nobody runs. The `reason`
line directly beneath it says a person performs the pass, and `auto: false` is
what keeps the loop from emitting it — so this is wording, not routing. Left as
found rather than fixed here: changing that sentence is a change to a
spec-kit-derived skill's wrapper, which `vendor-upstream-skills` wants as its own
diff.

## Design records

Design records: none — `design.md` records no level-3 decision. Its
`## Software design decisions` section says so in prose and explains why: every
structural choice that weighed a credible alternative here was a choice about who
owns a piece of truth or about the contract between a repository and wfctl, so
each landed in a level-2 record instead. The two named in its `## Architecture
decisions` section are level-2 and bind as level-2:

  docs/architecture/a-step-carries-sub-steps-one-level-deep.md
  docs/architecture/an-absent-artifact-is-claimed-not-inferred.md

Both are `proposed`. Accepting them is the human's call, never the agent's.
