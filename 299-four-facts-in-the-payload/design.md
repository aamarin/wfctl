# The payload says which fact is missing

**Issue:** #299 — child of epic #100, scope item 4, and its last open child.
**Mode:** `auto_approve: true`. Every gate below was answered into this document
and into the records it lists; approval moves to the PR.

## The idea in one line

A branch is blocked on four independent questions with four different owners, and
today all four are read off one step state — so a reader cannot tell which one is
unanswered.

## The problem, concretely

Two branches. Both have every task ticked and a green definition of done. One has
an architecture record still `proposed`; the other's was accepted. `wfctl status`
prints the same eight lines for both, and `--json` carries the same payload.

```
implement    ●  12/12 done
next: Story complete — open PR or run `/end-session`.
```

`design_block` is why: it counts a record under the arch root *whatever its
status*, and says so in its own docstring — a `proposed` record proves the
question was put, which is the thing that gate is for. Nothing else reads a
record's status at all. Nothing reads the integration grant as a fact about the
branch either.

`_predicates.py` already names the two missing rungs in its own commentary — "6 a
decision has authority; 7 integration was approved" — and the per-predicate list
below it shows no step reaching either.

## Level 1 — behavior

Four facts render as their own block between the step table and `next:`. One line
per fact: a glyph, the fact's name, one detail phrase.

**The reachable states, each read in that state and judged.**

Everything settled:

```
artifacts written       ●  8 of 8 steps
definition of done      ●  passed at 47e3e9c
architecture accepted   ●  readiness-is-not-a-step-state
integration authorized  ●  granted by --allow-notify
```

True. Nothing outstanding, and the reader can say so without opening anything.

The situation #299 was filed over — tests pass, record still proposed:

```
artifacts written       ●  8 of 8 steps
definition of done      ●  passed at 47e3e9c
architecture accepted   ○  proposed — readiness-is-not-a-step-state
integration authorized  ○  nobody has allowed it for this work
```

True, and it is the pair of lines that does not exist today.

A branch that touched no architecture:

```
architecture accepted   –  no record on this branch
```

True. `○` here would read as "architecture is not yet binding", which sends a
reader to accept a record that was never written. There is no architecture
pending, so the question does not arise.

A repo that declares no definition of done (FR-002's degrade path):

```
definition of done      –  no definition of done declared
```

True. `●` would claim a verification that never ran.

No spec dir resolved for the branch:

```
artifacts written       ○  no spec dir for this branch
definition of done      ●  passed at 47e3e9c
```

True, and worth naming: three of the four facts are answerable with no spec dir,
which today's payload cannot say at all.

On the trunk:

```
integration authorized  –  this is the trunk
```

True. There is no branch to integrate.

Git cannot say whether this is the trunk:

```
integration authorized  ○  cannot tell whether this is the trunk
```

True. A human grant is promised evidence, and
`promised-evidence-blocks-on-silence` already says promised evidence blocks when
it is unavailable. The value reads unmet; the detail says why. `blocks` is not
touched to reach this — the rule already answers it.

**The level-3 consequences these level-1 decisions generate.** Both are
requirements the rendering forced, not choices made later:

- Rendering `–` rather than `○` for a branch with no record means the derivation
  needs *this branch's* record set, not the repository's projection — so
  `records_on_this_branch` and the arch root are resolved during inference.
- Rendering the facts as a per-feature block rather than per-step columns means
  they live on `PipelineReport` and not on the step dicts — which is why
  `tests/pipeline_payload_snapshot.json`, which pins `_infer_steps`, is untouched
  by this change.

## Level 2 — architecture

Answered as a record, not as a section here:

- `docs/architecture/readiness-is-not-a-step-state.md` — a step state says
  whether the pipeline may advance; readiness is four facts, each read from its
  own owner.

The boundary it draws, in the terms `design-levels` asks for:

```
the owner                              │  wfctl
───────────────────────────────────────┼──────────────────────────────
the spec dir                           │
  step artifacts on disk            ───┼─►  reads existence + sections
                                       │
wfctl.json + the verify record         │
  the repo declares its DoD         ───┼─►  verification_block()
  wfctl verify records a verdict       │
                                       │
the record's `status` field   (#321)   │
  a human runs `wfctl arch accept`  ───┼─►  reads status of this branch's
                                       │    records
                                       │
a human's grant               (#280)   │
  --allow-notify, or the label      ───┼─►  reads the event log
                                       │
  "the step state already says so" ────┼──✗ never derived from another fact
```

The bottom row is the decision. Every other row is a read.

## Level 3 — design

**The structural choice that weighed alternatives**, answered as a record:

- `docs/architecture/design/299-facts-render-as-a-block.md` — the four facts
  render as their own console block, not as annotation text and `--json`.

**The other structural choice, and why it earns no record.** Where the
derivations live: `_predicates.py`, beside `verification_block` and
`design_block`, which are already public and already read three of the four
sources. `_predicates.py`'s own module docstring names #299 as one of the four
issues it was split out to serve — "what a step accepts as evidence moves
whenever someone decides a rung was too weak". The alternative, a new `_facts.py`,
is credible but the codebase has already made this argument; a choice the repo
argued for before this branch existed is not a decision this branch made.

The payload shape lives on `PipelineReport` in `_pipeline.py`, the glyphs in
`cli.py`. That is the same three-way split `Reading` / `_PipelineStep` /
`_STATE_GLYPH` already uses.

**Checked against the code this session**

| Claim | What was read |
|---|---|
| No predicate reads a record's `status` | `load_records` and `in_force` appear only in `cli.py` |
| `design_block` accepts a record whatever its status | its docstring, `_predicates.py:490` |
| `verification_block` returns `None` when the repo declares no commands | `_predicates.py:432`, the FR-002 degrade path |
| The grant is read back from the event log, resolved once by `wfctl start` | `_session.resolved_notify`, `_last_resolved` |
| The payload snapshot pins `_infer_steps`, not `PipelineReport` | `tests/test_pipeline_payload_snapshot.py` imports `_infer_steps` alone |
| `records_on_this_branch` returns branch-scoped slugs, uncommitted included | `_paths.py:364` |
| `_STATE_GLYPH` is the only place a pipeline state is drawn | `cli.py:65`, and its own comment |

**Assumed, and what would falsify each**

| Claim | Falsified by |
|---|---|
| Four extra console lines do not make `status` too long to scan | a reader piping `status` through `head`, or asking for a flag that hides the block |
| The longest fact line fits 80 columns | a repo whose record slugs wrap; the detail truncates, the slug does not |
| Resolving the arch root and asking git per `status` is cheap enough | a measurable slowdown; `status` already shells out to git for `on_trunk` |

## Scope

In:

1. Four facts on `PipelineReport`, each derived from its own owner.
2. A `facts` list in `wfctl status --json`.
3. The console block, rendered in every state including all-met.
4. Tests that build the two situations #299 names and assert the console output
   differs.

Out, and why:

- **`blocks(verdict, source)`** — unchanged. That rule is about evidence being
  unavailable; this is about which question the evidence was about. #299's
  out-of-scope section is explicit and conflating them re-opens #287.
- **Who accepts a record, who authorizes integration** — #321 and #280 own those
  and both shipped. This consumes their answers.
- **Flipping `clarify` and `analyze` to automatic** — #325, queued behind this,
  and a separate judgment with a separate owner.
- **`next-step.md`** — #299 scope item 2 names `status`. The facts are for a
  reader; the file is for routing, which the step state still drives.
- **A fifth step state** — scope item 3, and the record's `Considered` says why.

## Definition of done

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

Then the thing the suite cannot see: build both situations #299 names — tests
passing with a `proposed` record, and the same after `wfctl arch accept` — and
confirm `wfctl status` tells them apart in the console, not only in `--json`.

## Software design decisions

- `docs/architecture/design/299-facts-render-as-a-block.md` — the four facts
  render as their own console block, because the reader who could not tell the
  two situations apart is the one who never opens `--json`.
