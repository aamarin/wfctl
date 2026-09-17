# #408 — drafted revisions, for review

Nothing below has been applied. Each block is replacement text for a named
paragraph, so a yes is "apply block N" and a no costs you nothing.

All three records are `proposed`. Revising a proposed record is not accepting
it — `status:` stays `proposed` in every draft here, and the `Log` gains a
`revised` line rather than an `accepted` one.

---

## 1. `an-absent-artifact-is-claimed-not-inferred` — four edits

Verdict: **revise the record.** The spec's design is newer and reasoned; the
record was written before `step-claims/` existed and never caught up.

### 1a. Decision — the storage sentence

Today:

> The file goes where `wfctl arch none` already writes — the declarations
> directory under the arch root — and carries the same guards: an empty reason
> is refused, a `<why>` placeholder is refused, and a write that landed
> somewhere no reviewer will see it warns and exits non-zero.

Replace with:

> The file goes under a directory of its own —
> `<arch-root>/step-claims/<branch>/<step>.<name>.md`, one file per pass — and
> carries the same guards `arch none` already applies: an empty reason is
> refused, a `<why>` placeholder is refused, and a write that landed somewhere
> no reviewer will see it warns and exits non-zero. One file per pass because a
> branch makes as many claims as it has passes, and a single shared file would
> mean the second claim destroys the first. `step-claims/` joins
> `_paths.non_record_subtrees`, so no reader of the arch root counts a claim as
> a record.

Sources: `data-model.md:92`, `research.md` R6, `contracts/cli.md:55`, FR-015,
FR-016.

### 1b. Decision — the last line

Today:

> `wfctl arch none` becomes the level-2 instance of this verb rather than a
> mechanism of its own.

Replace with:

> `wfctl arch none` keeps its own verb, its own path and its own text. The two
> are siblings rather than one generalised: `arch none` overwrites a whole file
> holding a single boundary claim, and a branch with several claimed-away passes
> would lose all but the last through it. Overloading it with an optional pass
> argument would also blur refusals and a path that are specific to the boundary
> question.

Source: `plan.md` § Complexity Tracking, row 3 — which already states this
departure and its reason. This edit brings the record into line with a decision
the plan made deliberately.

### 1c. Consequences — first paragraph

Today:

> `wfctl step none <name>` is a new verb, and it generalises `wfctl arch none`
> rather than sitting beside it. The declarations file gains a line per declared
> sub-step instead of holding a single claim.

Replace with:

> `wfctl step none <name>` is a second claim-writing verb beside `wfctl arch
> none`, not a generalisation of it. Each claim is its own file under
> `step-claims/`, so two claims on one branch never contend for one path, and a
> repeated claim on the same pass replaces exactly itself.

### 1d. Consequences — the state count

Today:

> A sub-step has three reachable states and no ambiguity in any of them: `done`
> when the artifact exists, `pending` when it does not, `skipped` when someone
> declared it. Unlike the top-level pipeline, `skipped` on a sub-step has exactly
> one producer, so the glyph means one thing.

Replace with:

> A pass has four reachable states, the same four a step has (FR-005): `done`
> when its predicate is satisfied, `in_progress` when the parent step is current
> and this pass is the outstanding one, `pending` when the parent has not been
> reached or an earlier pass under it is outstanding, and `skipped` when a claim
> exists for it on this branch or the parent step is itself `skipped`.
>
> `skipped` therefore has two producers, not one, and `claimed` is what tells
> them apart: non-null when a person declared the pass away, null when the state
> was inherited from a parent the pipeline walked past. A parent reaches
> `skipped` only by being walked past — `brainstorm` with a `spec.md` and no
> `design.md`, `clarify` with a `plan.md` already written, `implement` over a
> sentinel with no open task, `decompose` with no `delivery.md` — so an inherited
> `skipped` means no claim was ever owed, and the glyph needs none.
>
> What the claim buys is that a pass skipped *under a parent that ran* always
> carries a sentence. That is the property the single-producer wording was
> reaching for, and it survives intact once the field rather than the state name
> is what carries the distinction.

**This corrects the record twice, and the second was not in #408.** The scan
caught the three-versus-four count. It did not catch that `data-model.md:138`
gives `skipped` a second producer — the parent being skipped — which contradicts
the record's "exactly one producer" in the same sentence.

A fifth state name was considered and rejected: the payload already answers the
question with `claimed`, and the record's own *Considered* section rejects a
state-per-cause on that ground — *"nothing branches on the difference, and the
reason sentence already carries it for the only reader who cares."*

### 1e. `data-model.md` — the rule nobody has written down

The mechanism is documented twice and the inference is documented nowhere:

| Fact | Where |
| --- | --- |
| `claimed` holds the person's reason, or null | `data-model.md`, payload section |
| `skipped` comes from a claim **or** from the parent | `data-model.md:138` |
| **`claimed == null` is how you tell those apart** | **nowhere** |
| A parent is skipped in four places, all meaning *walked past* | four inline comments in `_predicates.py`, collected nowhere |

Add to `data-model.md`, under the state table:

> A pass reaches `skipped` two ways, and `claimed` is what separates them. A
> non-null `claimed` is a person's sentence, written by `wfctl step none` into
> the change under review. A null `claimed` on a `skipped` pass means the state
> was inherited: the parent step was walked past, so the pass was never reached
> and no claim was owed. No consumer needs a second state name for this — the
> field already answers it, and `--all` renders the sentence where there is one.

---

## 2. `a-step-carries-sub-steps-one-level-deep` — one edit

Verdict: **revise the record.** `spec.md`'s clarification Q2 decided this
deliberately and gave a reason; the record predates it.

### 2a. Consequences — the `doctor` paragraph

Today:

> `doctor` gains a finding for a declared sub-step whose command is not
> installed, and it is new logic rather than a wiring-up. The command inventory
> `_pipeline` keeps is consumed by the test suite, not by `doctor` — and a test
> in wfctl's own suite cannot reach this case anyway, because the command it
> would check ships from the consuming repository. What `doctor` already has is
> the installed command directories it walks for drift, which is where the
> answer is.

Replace with:

> `doctor` is not touched. A declared pass whose command is not installed is a
> finding about configuration the repository wrote for itself, and the drift
> report's remit is state wfctl installed — so the finding lands in `wfctl check
> config` instead, alongside every other rule this feature states about a
> declaration. That is `a-rule-is-expressed-as-a-check` applied to this feature's
> own rules, and it is what `spec.md`'s clarification Q2 settled.
>
> A test in wfctl's own suite still cannot reach the case, because the command
> it would check ships from the consuming repository. `check config` is run
> against a repository rather than shipped as an assertion about one, which is
> why the finding belongs there rather than in a suite.

Sources: `spec.md` clarification Q2, `plan.md` ("`doctor` is not touched"),
`contracts/cli.md` § Unchanged.

Note: commit `d6a9f21` already corrected the command-inventory claim in this
paragraph and left the destination. This finishes that edit.

---

## 3. `brainstorm-is-one-step-with-addressable-levels` — one edit, plus a plan line

**My recommendation changed after reading both sides.** I said "keep the record,
change the plan." Having read the record's argument, it is aimed at a table
shape that #339 replaces, so the record is what should move — narrowly, and with
its ownership claim kept and made explicit.

The record rejects a second axis because *"a table whose value type is
`(command, auto)` has no way to express a gate whose exit condition is a written
artifact, so representing the levels there would mean inventing four commands to
carry four flags."* #339 changes that value type: a pass carries a **predicate**,
which is exactly the thing that expresses an artifact condition. The two
alternatives the record rejected — four peer table entries, and a per-level flag
on every entry — are neither of them what T004 and T034 do.

What does still bite is ownership, and it survives intact: the plan makes
addressable only the two passes that leave an artifact. `architecture-design`
writes nothing itself and gets no pass, so `design-levels` keeps ownership of
which *gates* run, while the step table carries only which *artifacts* are owed.
That distinction is currently in neither document.

### 3a. Decision — second paragraph

Today:

> `_STEPS` keeps answering exactly one question — which command advances this
> step — and gains no second axis. A per-level authority switch reads the level
> vocabulary, not the step table.

Replace with:

> `_STEPS` gains no per-level flag. What that rejects is a second axis on the
> entry itself: a table whose value type is `(command, auto)` cannot express a
> gate whose exit condition is a written artifact, and four flags carrying four
> levels is the split `_pipeline.py:16` records the failure of — an entry could
> carry level policy for a step that has no levels, and nothing would say so.
>
> A step entry carrying an ordered list of passes, each with a predicate of its
> own, is not that shape. The predicate is what expresses the artifact
> condition, and a step with no passes carries an empty list rather than
> inapplicable policy. So the table's value type may grow a pass list; what it
> may not grow is a flag per level.
>
> The ownership line is unchanged and narrower than it reads. `design-levels`
> owns which gates run inside `brainstorm` and what returning to one means. The
> step table carries only those passes that leave an artifact a reader can point
> at — `architecture-design` hands its result to `architecture-decisions` and
> writes nothing itself, so it gets no pass. Two of four levels are addressable
> in the table; all four remain `design-levels`'.

Add to `Log`:

> - 2026-09-17  revised     — #408: the "no second axis" sentence was reasoning
>   about a `(command, auto)` value type that #339 replaces with a
>   predicate-carrying pass list. The ownership claim is unchanged, and the
>   artifact-versus-gate split it implies is now written down.

### 3b. `plan.md` § Constitution Check — a gate that is missing

The record is the one most directly about `brainstorm`'s internals and this
feature is the one changing them, so it belongs in that checklist whichever way
3a goes. Insert after the `a-step-carries-sub-steps-one-level-deep` row:

> - [x] **`brainstorm-is-one-step-with-addressable-levels`** (proposed):
>       `brainstorm` stays one entry in `_STEPS` with one command and one `auto`
>       flag. The two passes it gains carry predicates rather than per-level
>       authority flags — the shapes that record rejects are four peer table
>       entries and a flag per level, and T004/T034 are neither. `design-levels`
>       keeps ownership of which gates run inside the step; the table carries
>       only the two passes that leave an artifact, which is why
>       `architecture-design` gets no row.

If you reject 3a instead, this row becomes the departure note — same position,
stating that the plan departs and why, on the record's own terms.

---

## 4. Two vocabularies — recommendation, and the collision

**Settled the other way, 2026-09-17.** `SubStep` is kept and
`wfctl-counts-the-passes` keeps the word. The two vocabularies stand, and
`a-step-carries-sub-steps-one-level-deep`'s Consequences now says so, which is
what stops a later reader filing the divergence as drift. What follows is the
rejected recommendation, kept for its counts and for the collision it names.

Verdict as drafted: **"pass" wins, and `wfctl-counts-the-passes` gives up the
word.**

Counts, so the cost is on the table rather than asserted:

| Spelling | Where it lives | Occurrences in the spec dir |
| --- | --- | --- |
| `sub-step` / `sub_step` / `SubStep` | records, data-model, code to be written | 63 |
| "pass" | spec, plan, tasks, contracts, every user-facing string | dominant everywhere else |

Renaming toward "pass" means `SubStep` → `Pass`, `sub_steps` → `passes`, and
both record titles. None of that code exists yet — #410 writes it — so the
rename is free today and costs forty call sites after #410 lands.

**The collision is real and #408 named it.** `wfctl-counts-the-passes`
(proposed) already uses "pass" for one iteration of the orchestrate loop. Three
senses of one word in one arch root is worse than two vocabularies.

My call: that record should say **iteration**, not pass. It is proposed, nothing
consumes its vocabulary yet, and "iteration" is the more natural word for a loop
that re-enters the same step — the record's own Context sentence reads *"Nothing
counts the passes"* about a loop, where "iterations" loses nothing. Retitle to
`wfctl-counts-the-iterations`.

That is a change to a record outside #339's scope, so it is the one item here I
would file rather than apply in this branch — unless you say otherwise.

---

## 5. Naming, settled in conversation — applies to code #410 has not written

Full reasoning and the rejected candidates are in `339-naming.md` beside this
file. Summary of what the implementation should carry:

| Today | Becomes | Why |
| --- | --- | --- |
| `Predicate` (type alias, `_predicates.py:86`) | `EvidenceReader` | A predicate promises a bool; this returns a four-valued `State` plus two render strings |
| `Step.predicate` (field) | `reads` | `_pipeline.py`'s own docstring already says *"What each step reads is `_predicates`"* |
| `Reading` | `Assessment` | An interpreted judgment derived from evidence, not a neutral measurement |
| `continuation` | `on_finish` | Names the moment it governs — continue or pause when this finishes |
| `SubStep`, `sub_steps` | unchanged | Kept, which also leaves "pass" free for `wfctl-counts-the-passes` |
| `State` | unchanged | Bare on purpose: the same type grades a step and a sub-step, so any prefix is false at one level |

Rejected with reasons worth keeping: `Outcome` (`pending` and `in_progress` are
not outcomes), `Grade` (the four states are nominal, not an ordered score),
`Standing` (best finalist; silent about evidence having been interpreted),
`EvidenceResult` / `EvidenceOutput` (named for the input), `StepState` /
`PipelineState` / `PipelineGrade` (collide with `_PipelineStep`, with an accepted
record's phrase, and with `PipelineReport` respectively).

Blast radius: 139 occurrences of `predicate` across `wfctl/` and `tests/`, 26 of
`continuation`. Free today; forty-odd call sites more after #410 lands.

## 6. Open, and not settled: `Assessment.annotation`

One word means two things a hop apart — an override on `Assessment`, a resolved
string on `_PipelineStep`. A rename toward presentation (`display_note`) was
inspected and rejected: the field ships in `status --json` and is written into
session state, so it is not view-only.

Candidates for the override only: `override`, `instead_of_reason`, or leave it.
`_PipelineStep.annotation` stays regardless — it is the payload's public key.

## What I would do on a yes

1. Apply 1a–1d, 2a, 3a to the three records in `docs/architecture/`, `status:`
   untouched, one `revised` Log line each. One commit.
2. Apply 3b to `plan.md` in the spec root. Separate commit on `specs-trunk`.
3. File the `wfctl-counts-the-passes` rename as its own issue, and apply the
   sub-step → pass rename across the three records and the spec artifacts only
   once you have answered it.
4. Comment on #408 with what was applied and what was left, then it is yours to
   close.

Open question I could not settle for you: **1d's second half** — whether
`skipped` keeps its single-producer property. Everything else here has a newer
artifact that clearly wins.
