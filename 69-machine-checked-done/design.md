# Machine-checked done

**Issue:** #69 — Completion is self-certified: implement is done when the agent
says a file exists
**Branch:** `69-machine-checked-done`
**Status:** design approved; superseded in two places by `spec.md`

**Superseded.** `/speckit.clarify` and `/speckit.analyze` changed two shapes
recorded below. `spec.md` is authoritative for both.

| Here | Now |
| --- | --- |
| `"failed": null` — one failing command | a list; FR-013 runs every command, so a run can carry several failures |
| a failed status line naming only the exit code | it names the failing commands; SC-006 requires that from status alone |

The rest stands as written. This is the record of how the boundaries were drawn,
not a second specification.

## Problem statement

How might we let `wfctl status` report implementation complete only when
something other than the agent that did the work has said so — without wfctl
knowing any project's language, and without `status` growing expensive?

`README.md:15` claims *"step read from real spec files, so phases can't be faked
or skipped."* That holds for `specify`, `plan` and `tasks`, whose artifacts are
the work itself. It does not hold for `implement`, which has two self-asserted
routes to `●`:

- `_pipeline.py:162` — a non-empty `checklists/implement-complete.md`, written by
  `speckit-implement/SKILL.md:179`, the same skill that did the work.
- `_pipeline.py:166` — every checkbox in `tasks.md` ticked, and checkboxes are
  model-edited.

Neither reads a verdict. Writing the sentinel on a red build reports `●`.

## Behavior

### What the user sees

Symbol vocabulary is unchanged — `○ ▶ ● –`. What grows is the number of ways to
reach `▶`, and the reason is printed beside it.

```
implement    ▶  12/12 done  ← current
                unverified — run `wfctl verify`

implement    ▶  12/12 done  ← current
                failed — 2 of 3 at a1b2c3d
                  uv run ruff check wfctl/ tests/
                  uv run mypy wfctl/

implement    ▶  12/12 done  ← current
                stale — verified at a1b2c3d, HEAD is e4f5a6b

implement    ▶  12/12 done  ← current
                stale — verified at a1b2c3d, tree dirty

implement    ●  12/12 done
                verified at a1b2c3d
```

### Every reachable state

| `tasks.md` | `verify` configured | record | shows |
|---|---|---|---|
| absent | — | — | `○` |
| open boxes | no | — | `▶` |
| ticked / sentinel | no | — | `●` — today, unchanged |
| ticked | yes | none | `▶` unverified |
| ticked | yes | some argv exited ≠ 0 | `▶` failed |
| ticked | yes | pass, `sha` ≠ HEAD | `▶` stale |
| ticked | yes | pass, tree dirty | `▶` stale |
| ticked | yes | pass, config changed since | `▶` stale |
| ticked | yes | pass, all match | `●` |

Row 3 is the degrade path. A repo that never configures a command sees no
change whatsoever — verification is an AND on top of today's conditions, so the
sentinel keeps its existing job and nothing breaks.

### Level-1 decisions and their level-3 consequences

| Decision | Consequence at level 3 |
|---|---|
| Gate with `▶`, not a new symbol | no legend change; the reason must be carried in the existing `annotation` field |
| A stale record is not a pass | the record must store `sha` and `dirty`, and `status` must re-read live git every run |
| A pass under the old command is not a pass under the new one | the record must store the `command` it ran, not only the verdict |
| `wfctl next` must not send you back to a step with nothing left to do | `next_step_content` needs a case; step → command is currently a total map with no room for a reason |

## Boundaries and ownership

```
agent                          │  wfctl
───────────────────────────────┼──────────────────────────
config time                    │
  writes wfctl.json         ───┼─►  reads argv list
    (human, committed)         │
                               │
implement                      │
  edits code, ticks boxes      │
  runs `wfctl verify`       ───┼─►  runs each argv
                               │    records exit + sha + dirty + command
                               │
status                         │
  (nothing)                    │    reads record + live git
                               │    decides ● or ▶
                               │
  "it passed"  ────────────────┼──✗ never accepted from the left
```

Read a phase label, read left, follow the arrow, drop down. A blank left cell
means nothing crosses there. The bottom row is the reason the feature exists.

| Value | Computed by | Why not the other side |
|---|---|---|
| the verify command | human, at config time, committed | wfctl cannot know a project's language; guessing is worse than having none |
| the verdict (exit codes) | wfctl, running each argv | an agent-asserted verdict is the defect being fixed |
| code identity (`sha`, `dirty`) | wfctl via git, at write **and** read | an agent-supplied sha is exactly as forgeable as the verdict |
| the implement symbol | `_pipeline._infer_steps`, from record + live git | it is a function of the two values above, neither of which the agent owns |

### The bar this buys: tamper-evident, not unforgeable

An agent with shell access can write any file wfctl reads, so a locally
unforgeable record is not reachable. What changes is the cost of a false green:
today it is a step you skip, afterwards it is a record you must deliberately
fabricate, and the fabrication expires on the next commit or edit.

`README.md:15` is reworded as part of this change. "Can't be faked" is false
before and after; the honest claim only becomes available once a verdict exists
to point at.

## Design

### Config — `wfctl.json`, repo root, tracked

```json
{
  "verify": [
    ["uv", "run", "pytest", "-q"],
    ["uv", "run", "ruff", "check", "wfctl/", "tests/"],
    ["uv", "run", "mypy", "wfctl/"]
  ]
}
```

A **list** of argvs, not one. `AGENTS.md` states this repo's own definition of
done as three commands plus `wfctl doctor`; a single-argv schema would mean wfctl
could not verify wfctl without inventing a wrapper script it does not have. Every
argv must exit 0.

Argv tokens, never a shell string — `_tracker.py`'s substitution already
establishes this shape, so a token containing `$(...)` is inert.

Absent file, absent key, or empty list → today's behavior.

### Record — `$(wfctl state-dir)/verify.json`

```json
{
  "command": [["uv", "run", "pytest", "-q"]],
  "exit": 0,
  "failed": [],
  "sha": "a1b2c3d",
  "dirty": false,
  "at": "2026-08-22T14:02:11Z"
}
```

Per-branch, per-machine, never committed — it sits beside `current.json` and
`events.jsonl`, which are already this shape. A fresh clone reads *unverified*,
which is true: that checkout has verified nothing.

`failed` names the argv that broke, so `▶ failed` can say which one.

### Surfaces touched

- `_pipeline._infer_steps` — one branch on the implement arm. It already takes
  `repo_root`, documented at `_pipeline.py:69` as unused and kept only for
  signature stability; this gives the parameter a job.
- `next_step_content` — a verification-blocked implement routes to
  `wfctl verify`, not `/speckit.implement`.
- new `wfctl verify` — runs each argv in order, writes the record, exits with
  the first non-zero code.
- `doctor` — a malformed `wfctl.json` reported as drift; it already exits
  non-zero on findings (#54).
- `install-skills` — must **not** add `wfctl.json` to `.gitignore`.
- `README.md:15` — reworded.

### Claims: checked and assumed

**Checked — opened the code**

- `_pipeline.py:162` and `:166` — both `●` routes exist as described
- `speckit-implement/SKILL.md:179` — writes the sentinel
- `status` already runs two git subprocesses (`rev-parse --show-toplevel`,
  `branch --show-current`), so `+2` more is the same order of cost
- `_tracker.py` builds argv tokens, never a shell string
- implement is `auto: False` in `_STEPS`, so `speckit-orchestrate` stops rather
  than looping on a gated `▶`
- `_pipeline.py:69` documents `repo_root` as unused
- blast radius: 10 references across `test_pipeline_commands.py` and
  `test_storyctl.py`
- `.gitignore` covers `.agents/`, `.claude/`, `.specify/`,
  `.wf-skills-manifest.json`, `specs/` — corroborated by `AGENTS.md`'s layer
  model table, which lists every one as installed output, committed: no

**Assumed — and wrong, found at this gate**

1. *`.agents/verify.json` is a proven shape, reusing the tracker pattern.* It is
   gitignored, by wfctl's own installer. A fresh clone and CI would both read
   "no command configured" and degrade silently — the feature would be invisible
   exactly where an independent verdict is worth most. **This invalidated the
   level-2 boundary and was revised upward**, not worked around: the command
   moved to a new committed file, the first wfctl has.
2. *One argv is enough.* `AGENTS.md`'s definition of done is three commands.
   Schema changed to a list.

**Still assumed, carried into the spec**

- No existing `wfctl verify` name collision — checked against the command list,
  but not against shell aliases or a future speckit verb.
- `wfctl.json` is the right name. `.wfctl.json` would sit with `.workmux.yaml`
  as a dotfile; `wfctl.json` is chosen to be visible, since a repo's definition
  of done is not incidental config.

## Decisions ledger

| # | Level | Decision |
|---|---|---|
| 1 | behavior | configured check not green → implement `▶`, gated |
| 2 | behavior | record binds `sha` + `dirty`; any drift → stale |
| 3 | architecture | wfctl runs the check — tamper-evident, not unforgeable |
| 4 | architecture | record in the state dir, per-branch, per-machine |
| 5 | architecture | command in `wfctl.json`, repo root, **tracked** |
| 6 | design | `verify` is a list of argvs; all must exit 0 |
| 7 | design | record stores the command, so a config change staleness it |

## MVP scope

**In:** `wfctl.json` read, `wfctl verify`, the record, the `_infer_steps` branch,
the `next_step_content` case, the `install-skills` ignore fix, the `README:15`
reword.

**Out of the MVP, in the issue's spirit:** `doctor` reporting a malformed
`wfctl.json`. It is a one-line addition once the loader exists, and it does not
gate the feature working.

## Not doing

- **A `verify-check` command.** `tracker-check` exists because a tracker config
  is exercised only on a verb that may not run for days. `wfctl verify` runs the
  config immediately and fails loudly on a bad one. A third validation command
  earns nothing.
- **Auto-detecting the test command** from a Makefile, `package.json`, or
  `justfile`. The issue rules it out and is right: a wrong guess reports a green
  build for a suite that never ran, which is the defect with extra steps.
- **CI as the trust anchor.** Genuinely unforgeable, and it costs a network
  round-trip inside `status`, requires a PR to exist, and assumes a
  GitHub-shaped repo. Rejected against the "status stays cheap" constraint.
- **Putting the command in `.workmux.yaml`.** Already committed and already read
  by `doctor`, but it is workmux's file and workmux is optional; wfctl would
  gain a dependency on a tool it does not require.
- **Removing the sentinel or the checkbox route.** Both must keep working
  unchanged for repos with no `verify` configured. Verification is an AND on
  top, not a replacement.
- **A per-step verify command.** One definition of done per repo. Per-step
  verification is a different feature with no evidence anyone wants it.

## Open questions

- `wfctl.json` or `.wfctl.json`? Cheap now, a migration later.
- Should `dirty` ignore untracked files? A scratch file invalidating a green
  record is defensible but will chafe. Decide at spec time, with a stated
  default.
- Does `wfctl verify` run the argvs in order and stop at the first failure, or
  run all and report every failure? Stopping is cheaper; running all is more
  useful on a first run.
- `install-skills` must not ignore `wfctl.json` — does it need a positive test
  asserting the file stays tracked, given `_ensure_gitignored` is called with a
  list that is easy to extend by accident?
