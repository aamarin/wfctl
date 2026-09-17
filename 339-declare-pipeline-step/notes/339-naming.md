# #339 naming — what is settled, what is open, and where the names came from

Working document. Nothing here is applied to code.

## What this is about, for a reader without the codebase

wfctl tracks where a feature sits in a fixed eight-stage pipeline — brainstorm,
specify, clarify, plan, tasks, analyze, decompose, implement — and tells the
agent what to run next. Each stage is a **step**. wfctl decides a step's state by
reading artifacts on disk: if `spec.md` exists, `specify` is done.

**Issue #339** is that the pipeline is one level shallower than the work it
tracks. A project that runs a design pass of its own — pfms runs a UI design
workflow between brainstorming and specifying — can only write that pass's
position in prose. Nothing reads the sentence, so a feature that walked past the
UI design looks identical to one that ran it. The same gap exists inside wfctl:
`brainstorm` is really four design gates, two of which write durable records, and
all four collapse into one row.

So #339 gives a step an ordered list of **sub-steps**, one level deep, each with
a state of its own. A project declares its own in `wfctl.json`; wfctl's built-in
ones are hardcoded and carry no mark distinguishing them.

**Why the names are being reworked now.** None of this code is written yet — #410
writes it. A rename costs nothing today and forty call sites after that PR lands.
Two names in the *existing* code are the problem, and #339 is about to propagate
both one level down into the new shape:

- `predicate` promises a boolean by convention. It returns a four-valued state
  plus two strings meant for rendering. Every reader has to unlearn the word once.
- `continuation` does not say what it governs. It holds whether the agent may
  proceed to the next step without pausing for a human.

A third name, `Reading`, is the return type of that callable, and it is the one
still open: a *reading* is a neutral measurement, and this value ranks the step
on a four-name scale.

**What a good name has to survive here.** Two constraints keep recurring below,
and both come from decisions already made:

1. The same callable type grades a **step** and a **sub-step**, so a name
   containing either word is false half the time.
2. `wfctl`'s architecture records are in force and own vocabulary — the whole
   status payload is already called *pipeline state*, `Verdict` already means
   *could the evidence be read at all*, and `Finding` already belongs to
   configuration checks. A name that borrows one of those makes an existing
   decision look applicable to a question it does not answer.

## The shapes being named

```python
# wfctl/_predicates.py
State = Literal["done", "in_progress", "pending", "skipped"]

@dataclass(frozen=True)
class Evidence:                       # the artifact reads the walk already did
    spec_dir: Path; repo_root: Path
    spec_text: str; has_markers: bool; plan_text: str
    tasks_text: str; tasks_open: bool; tasks_done: int; tasks_total: int
    ...

class Reading(NamedTuple):            # ← the open one
    state: State
    reason: str | None = None         # the routing read
    annotation: str | None = None     # what a view renders

Predicate = Callable[["Evidence"], Reading]

# wfctl/_pipeline.py
class Step(NamedTuple):
    command: str
    continuation: Continuation        # "automatic" | "review_required"
    predicate: Predicate

# #339 adds, one level down:
class SubStep(NamedTuple):
    name: str
    command: str | None               # None → a person performs it
    continuation: Continuation
    predicate: Predicate
```

## Settled

| Today | Becomes | Why |
| --- | --- | --- |
| `Reading` | `Assessment` | An interpreted judgment derived from evidence, not a neutral measurement. See below |
| `continuation` | `on_finish` | Names the moment — when this finishes, continue or pause. `continuation` left the reader to infer what it governed |
| `predicate` (field) | `reads` | The module docstring already says *"What each step reads is `_predicates`"* — the code finally matching its own prose |
| `Predicate` (type) | `EvidenceReader` | A predicate promises a bool; this returns a four-valued `State` plus two render strings. A *reader* may be named for what it consumes |
| `SubStep` | `SubStep` | Kept. Also frees "pass" for `wfctl-counts-the-passes`, which uses it for orchestrate-loop rounds |
| `State` | `State` | Bare on purpose — see *The prefix problem* |

## Settled: `Reading` → `Assessment`

```python
assessment = step.reads(ev)
# EvidenceReader -> Assessment
```

The objection to `Reading`: a reading is a *measurement*, neutral. This one is an
interpretation of evidence, and the word says the looking rather than the
judging.

`Assessment` was withdrawn earlier in this document on the ground that it "names
no scale". That objection does not hold: `state: State` already names the scale,
and repeating it in the container name is the gratuitous context the same naming
guidance forbids. Reopened and taken.

The two rejections below are sharper than anything in the candidate tables that
follow, and they are what closed the question:

| Rejected | Because |
| --- | --- |
| `Outcome` | `pending` and `in_progress` are not outcomes. They are positions in a lifecycle, and a name promising a result is disinformation for two of the four values |
| `Grade` | The four states are nominal lifecycle categories, not an ordered score. `Grade` falsely implies ranking |

`Standing` was the best finalist and loses narrowly: it answers *where does this
step stand?* but is silent about the fact that evidence was interpreted to reach
the answer. `Assessment` carries both, and reads without translation at the call
site.

The candidate tables below are kept as the record of what was considered.

### The prefix problem

Every compound tried so far fails on one of four grounds. This is why the
surviving candidates are bare words.

| Prefix | Example | Fails because |
| --- | --- | --- |
| `Evidence*` | `EvidenceResult`, `EvidenceOutput` | Names the input. The evidence is inert; the reader produces the value |
| `Reading*` | `ReadingOutcome`, `ReadingResult` | Stutters at the call site — `reading = step.reads(ev) -> ReadingOutcome` — and demotes `Reading` to the act |
| `*State` | `StepState`, `ReadingState`, `InferredState` | Shadows the sibling `State`, and `x.state: State` names the container after its field |
| `Pipeline*` | `PipelineGrade`, `PipelineOutcome`, `PipelineResult` | `PipelineReport` already exists for the whole payload; the prefix has to be told apart by its second word in an import list |
| `Step*` / `SubStep*` | `StepOutcome`, `SubStepReader` | The same type serves both levels, so a level in the name is false half the time |

Also ruled out on meaning rather than shape:

- `*Result` — promises success-or-failure. No reader has an error arm; every
  call succeeds and only the grade varies. And "did the read succeed" is the
  question `Verdict` already owns.
- `Assessment` — graded, but names no scale. Withdrawn.

### Taken in `wfctl/` (occurrence counts, verified)

| Word | Uses | Owns |
| --- | --- | --- |
| `Verdict` | 25 | whether evidence could be read at all |
| `Report` | 40 | `build_report`, `PipelineReport` — the whole payload |
| `Finding` | 12 | `check config` findings |
| `Inference` | 31 | the walk that produces the payload (`pipeline-state-is-one-payload`) |
| `Signal` | 44 | prose |
| `Mark` | 37 | prose, and `has_markers` |
| `Standing` | 24 | prose only — no identifier |
| `Bearing` | 14 | prose |
| `Call` / `Answer` / `Note` / `Tell` | 79 / 322 / 43 / 71 | ordinary English, everywhere |

### Candidates, grouped by the metaphor they commit to

**Grading — the name says the value ranks the row.**

| Name | Uses | Reads as |
| --- | --- | --- |
| `Grade` | 0 | how this row scored. Short, unclaimed, commits to the scale |
| `Score` | 0 | same, but implies a number and this is nominal |
| `Determination` | 0 | what was determined. Accurate, formal, long |

**Neutral — the name says "this is what came of it" and lets `State` carry the scale.**

| Name | Uses | Reads as |
| --- | --- | --- |
| `Outcome` | 0 | what the row came to. The plainest honest option |
| `Conclusion` | 0 | what the reader concluded. Slightly grand for three fields |
| `Reading` | current | the incumbent |

**Position — the name says where the row stands rather than how it scored.**

| Name | Uses | Reads as |
| --- | --- | --- |
| `Stance` | 0 | wrong register — a stance is chosen, this is observed |
| `Posture` | 3 (prose) | same objection |
| `Standing` | 24 (prose, no identifier) | *how the step stands.* Unclaimed as a symbol, and `step.reads(ev) -> Standing` reads cleanly at both levels |

**Judicial — `Verdict` is taken, but its neighbours are not.**

| Name | Uses | Reads as |
| --- | --- | --- |
| `Ruling` | 2 (prose) | overstates — nobody decided, a file was stat'd |
| `Opinion` | 5 (prose) | implies it could differ between readers. It cannot |

**Diagnostic.**

| Name | Uses | Reads as |
| --- | --- | --- |
| `Diagnosis` | 1 (prose) | reads evidence, returns a diagnosis. Accurate; medical register sits oddly beside `Evidence` |
| `Observation` | 7 (prose) | same neutrality problem as `Reading`, with a longer word |

### The three I would actually put up

```python
outcome  = step.reads(ev)    # Outcome   — neutral; State carries the scale
grade    = step.reads(ev)    # Grade     — commits to the ranking
standing = step.reads(ev)    # Standing  — says where the row stands
```

`Standing` is the one not yet considered in conversation and the one I would
argue for second: it is true at both levels, unclaimed as an identifier, and it
answers the question the pipeline actually asks — *where does this step stand?* —
rather than describing the act that answered it.

Its cost: 24 prose uses of "standing" in `wfctl/`, none of them identifiers, so
a grep for the symbol is noisy even though the namespace is free.

## The one field still open: `Assessment.annotation`

`annotation` names two different things one hop apart.

```
Assessment.annotation       an OVERRIDE; None means "the reason is what renders"
  └─► renders()             reason if annotation is None else annotation
        └─► _PipelineStep.annotation      the RESOLVED string
              ├─► payload["annotation"]    _pipeline.py:583  → wfctl status --json
              ├─► cli.py:603               console
              └─► cli.py:848               observed.step, written to session state
```

A rename toward presentation — `display_note`, `view_annotation` — was considered
and rejected on inspection: the field is not view-only. It ships in the
machine-readable payload and is written into durable session state, and
`pipeline-state-is-one-payload` is why — the string is computed during inference
precisely so that no view derives it.

What would pay is renaming the *override*, where the collision actually is:

| Candidate | Reads as |
| --- | --- |
| `Assessment.override` | this replaces what would otherwise render |
| `Assessment.instead_of_reason` | explicit, long |
| leave as `annotation` | accepts one word meaning two things a hop apart |

`_PipelineStep.annotation` stays either way — it is the payload's public key.

## Where this lands

Blocks 5 and 6 of `408-drafts.md`. Nothing here changes `State`, `Evidence`, or
the `_predicates.py` module name — the module keeps its name while the type
inside it does not, which is the next thing that may read wrong.
