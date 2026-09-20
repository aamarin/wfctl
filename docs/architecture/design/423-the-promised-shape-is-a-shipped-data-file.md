---
status: proposed
---

# The shape `wfctl status --json` promises is a data file shipped in the wheel, not a Python constant read only by a test

## Context

`wfctl-owns-whether-a-worktree-wants-a-human` settles who derives `attention`.
It does not say how the payload's shape is written down, and #423 asks for a
version key whose whole value depends on something being comparable against it:
a number nobody checks drifts to whatever the last author remembered to type.

The pressure is that the payload is built as a dict literal inside
`status_cmd`. Adding, renaming or removing a key is a one-line diff in a
function whose reviewer is reading it for something else. Nothing in the
repository states what the command promises, so nothing can disagree with a
change to it.

`pipeline-state-is-one-payload` constrains where the payload is computed and is
not restated here.

## Verified

- `wfctl/cli.py:504` builds the payload as `console.print_json(data={…})` — a
  dict literal inline in `status_cmd`, with no named structure between it and
  the terminal.
- `rich.console.Console.print_json` ends `self.print(json_renderable,
  soft_wrap=True)`, so rich never wraps the payload; the only corruption it
  introduces is styling.
- `tests/conftest.py:27` sets `NO_COLOR=1` and line 36 pops `FORCE_COLOR`,
  explaining that *"Claude Code exports FORCE_COLOR=3, so on that machine 30
  tests failed on a clean tree."*
- `tests/test_cli_status.py:83` reads the payload as
  `json.loads(runner.invoke(app, ["status", "--json"]).output)` — through
  `CliRunner`'s non-tty buffer, which is why no test has ever seen the styling.
- Two copies of a payload contract already exist, at
  `wfctl-specs/339-declare-pipeline-step/contracts/status-payload.md` and
  `wfctl-specs/384-strip-allow-notify/contracts/status-payload.md` — both in a
  gitignored tree resolving outside the working directory.

## Assumed

- That recording each key's type alongside its name earns its cost. Falsified if
  the types turn out to restate what mypy already proves about the builder, in
  which case names alone carry the check.
- That a consumer would read a shipped contract file. Falsified if #424 lands
  without opening it, which would leave the file worth having for the reviewer
  alone — still a reason to keep it, but a weaker one than this record claims.
- That the regeneration path will not be run reflexively. Withdrawn by #423's
  clarify scan, which made running it the intended path: a version typed by hand
  to turn a red test green is a reflex too, and a cheaper one to perform without
  thinking. What the assumption was protecting — the author deciding whether a
  break should be published — is carried instead by the hold that writes the
  paths and leaves the version, and by the commit body saying which of the two
  reasons applied. Neither is a check, and the reviewer reading the version move
  in the diff is what stands behind them.

## Direct baseline

A module-level constant beside the payload: `CONTRACT_VERSION = "1.0"` and a
`frozenset` of dotted key paths. One test builds a report, walks the emitted
payload, and compares the two sets in both directions.

This satisfies every mechanical requirement in #423. The check fires on a
rename, on a removal and on an unrecorded addition, and the diff of the
`frozenset` is as readable as any other list of strings.

## Decision

The promised shape is `wfctl/contracts/status-payload.json`, shipped as package
data: the version, and a sorted map of dotted key path to type name. One test
walks the live payload and compares both directions, failing with the offending
paths named and the bump the change owes.

## Diagram

```
             baseline                          decision

stable    ┌────────────────────┐            ┌────────────────────┐
          │ build_report       │            │ build_report       │
          │ the one payload    │            │ the one payload    │
          └────────────────────┘            └────────────────────┘
═══ pipeline-state-is-one-payload ═══════════════════════════════════════
               │ renders                         │ renders
volatile  ┌────▼─────────┐                  ┌────▼─────────┐
          │ status --json│                  │ status --json│
          └──────────────┘                  └──────────────┘
                 ▲                                 ▲
                 │ compares                        │ compares
          ┌──────┴────────┐                 ┌──────┴────────────┐
          │ KEY_PATHS     │                 │ status-payload    │
          │ a constant in │                 │ .json, in the     │
          │ _pipeline.py  │                 │ wheel             │
          └───────────────┘                 └───────────────────┘
                 ▲                                 ▲
                 │ imports wfctl                   │ reads a file
          ┌──────┴────────┐                 ┌──────┴────────────┐
          │ the test      │                 │ the test          │
          └───────────────┘                 │ a consumer        │
                                            └───────────────────┘
```

The graphs differ by one edge: who can read the promise. A constant is reachable
only by importing wfctl, so the promise is legible to the test and to a reviewer
who opens that module. A shipped file is legible to a consumer pinning a version
and to a reviewer reading the pull request's file list — and the two copies of
`contracts/status-payload.md` verified above are what the unreadable case already
looks like in this repository: documented three times, reviewed zero.

## Considered

- The constant beside the payload, described under *Direct baseline* — sound,
  and it loses on reach rather than on fault. It checks exactly what the file
  checks; what it cannot do is answer a consumer asking what shape it will get,
  which is the question #423 was filed to make answerable.
- A prose contract under `contracts/`, as #339 and #384 each wrote — rejected
  because both of those live in the gitignored spec tree and neither is current.
  A third copy would be the same artifact a third time, and
  `a-rule-is-expressed-as-a-check` puts a documented contract nobody verifies on
  the wrong side of its own test.
- Record only a hash of the shape and let the version guard it — rejected
  because the failure would say the shape changed without saying how, and the
  reviewer seeing *what* changed is the payoff this record rests on.
- Derive the shape from the report's type annotations and check nothing by hand
  — rejected as not credible in this codebase: the payload is a dict literal, not
  a typed structure, so there is nothing to introspect without first building the
  structure this record would then be about.

## Consequences

The file is package data, so `MANIFEST`/`pyproject` inclusion is part of the
change and a missing entry ships a wheel whose contract file is absent.

A change to the payload now touches two files. That is the cost and also the
mechanism: the second file is what a reviewer sees.

A regeneration command makes the update path one step, and makes a thoughtless
bump one step as well. The commit body is where the argument has to be, which is
a convention rather than a check.

What this file checks is the set of key paths and the type at each one, and that
is the whole of it. A contract change carried in a value passes untouched: a
fourth kind reaching a consumer written for three, a `detail` that keeps its type
and changes what it reports, a reordering of the rank. The keys are identical, so
the check is silent and the version does not move — and a consumer pinning that
version is given no signal that anything changed. Stated here because the check
passing is the evidence a reader will take for the contract holding, and the two
are not the same claim.
`wfctl-owns-whether-a-worktree-wants-a-human` carries why that class is named
rather than closed.

## Verification

A test that renames a key in the payload builder and asserts the suite fails
naming that key; a second that adds a key and asserts the failure asks for the
minor digit rather than the major. Both are the check itself under test, which is
what a golden file needs and a constant would need equally.

## Log

- 2026-09-20  proposed  — #423's level-3 gate; written before `design.md` so the document can cite it by path
- 2026-09-20  revised   — `Consequences` now states what the check does not cover, so a green check is not read as the contract holding; the third `Assumed` is withdrawn, regeneration having become the intended path in #423's clarify scan. Still proposed, so the body was revised rather than superseded
