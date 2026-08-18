# Data Model: step-command drift check

**Date**: 2026-08-17
**Phase**: 1

Two entities, both already present in the system. This feature merges three
representations of the first into one and adds a check comparing it to the second.

## Step definition table

One entry per pipeline step. Replaces `_STEP_NAMES`, `_STEP_COMMAND` and
`_STEP_AUTO`, which are three parallel structures keyed by the same eight strings.

| Field | Type | Meaning |
| --- | --- | --- |
| step name | `str` (key) | Identifier used throughout inference and display |
| command | `str` | Slash command that advances the step |
| auto | `bool` | Whether orchestration may proceed unattended past it |

**Shape**: `dict[str, tuple[str, bool]]`.

**Ordering**: insertion order *is* pipeline order. The step-name list derives from
the keys rather than being maintained beside them, which is what makes a step
missing from one table and present in another unrepresentable.

**Values** — unchanged from today, and the restructure is a regression if any
differs:

| Step | Command | Auto |
| --- | --- | --- |
| brainstorm | `/speckit.brainstorm` | false |
| specify | `/speckit.specify` | true |
| clarify | `/speckit.clarify` | false |
| plan | `/speckit.plan` | true |
| tasks | `/speckit.tasks` | true |
| analyze | `/speckit.analyze` | false |
| decompose | `/speckit.decompose` | false |
| implement | `/speckit.implement` | false |

**Validation rules**:

- A step cannot be defined without both values — enforced by the literal's shape,
  not by a check.
- Lookup of an undefined step yields `("", False)`. This is load-bearing, not a
  defensive default: `cli.py:170` reads an empty command as "pipeline finished"
  and prints "story complete". Raising here would turn a completed pipeline into
  an error.

**State transitions**: none. The table is a constant.

## Shipped command set

The command files vendored into the package, one file per command.

| Field | Type | Meaning |
| --- | --- | --- |
| name | `str` | File stem, e.g. `speckit.plan` from `speckit.plan.md` |

**Location**: `wfctl/agents/commands/*.md`, reached as
`Path(wfctl.__file__).parent / "agents" / "commands"` — deliberately not through
`_bundle.BUNDLE_ROOT`, which the suite's autouse fixture repoints (`research.md`
R2).

**Cardinality**: 23 files at time of writing, of which 8 are named by the step
table. The remaining 15 — `speckit.checklist`, `speckit.brief`,
`speckit.orchestrate`, `code-review`, `start-session` and others — are commands
that no pipeline step advances to. They are not drift and are never reported.

**Relationship to the step table**: every step's command must appear here. The
converse does not hold and is not checked.
