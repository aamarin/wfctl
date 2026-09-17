# Research: declare pipeline step

Phase 0 for `plan.md`. Everything the spec left to planning, plus the two
questions `design.md` handed forward under *Open questions for planning*. Each
entry is a decision, why it holds, and what it beat.

The two level-2 records this feature was designed under —
`a-step-carries-sub-steps-one-level-deep` and
`an-absent-artifact-is-claimed-not-inferred` — are the input, not a subject.
Nothing below reopens either; where a decision follows from one, it says so.

## R1 — A declaration lives in `wfctl.json` under `steps`, keyed by step name

**Decision.** The repository's passes are read from `wfctl.json`:

```json
{
  "verify": [ ... ],
  "steps": {
    "brainstorm": [
      { "name": "ui-design",
        "command": "/pfms-ui-design-workflow",
        "evidence": "ui-contract.md" }
    ]
  }
}
```

**Rationale.** `wfctl.json` is already the file a repository writes policy into
that must survive `install-skills` — `verify` and `change_check` are both there,
and `AGENTS.md` states the reason: `.agents/` is gitignored and rewritten, so a
policy written there works for one session and then vanishes with no error. A
pass declaration has exactly that lifetime requirement. Keying by step name is
FR-002 and is the record's decision, so no `after: specify` anchor exists to
break when the built-in table is reordered.

**Alternatives considered.** A file of its own (`.wfctl/steps.json`) — a second
config file for a repository to learn, and the `install-skills` hazard reappears
the moment someone puts it under a dotted directory. A tracker-style config
under `.agents/` — ruled out by the same gitignore argument that put
`change_check` in `wfctl.json`.

## R2 — `name` is an explicit, required field

**Decision.** Every declared pass carries `name`. It is not derived from
`command`.

**Rationale.** `docs/references/README.md` records the declaration as carrying
`command` and `evidence` and no name, and records the problem with that in the
same breath: `wfctl status` has to print something and `wfctl step none` has to
take something. Deriving the name from the command fails on the case FR-022a
exists for — a pass a person performs declares no command, so there is nothing
to derive from. A derived name is also not stable: renaming a skill renames the
pass, which silently invalidates every claim written against the old name.

Uniqueness is per-step (FR-002a) and the addressed form is `<step>.<name>`
(FR-002b), both settled in clarification. The references note's strongest
argument against — that a bare name resolving against the *current* step is
unsafe because the current step is inferred rather than set — is what FR-002c
answers: a bare name resolves only when globally unambiguous, never against the
current step.

**Alternatives considered.** Name derived from the command's last path segment —
fails for a manual pass and is unstable under rename. Always-qualified with no
bare form (Terraform's rule) — tighter than the problem's size, and against this
CLI's own precedent, where `wfctl arch none` takes a bare form because the scope
admits only one.

## R3 — `evidence` resolves against the feature directory

**Decision.** A relative `evidence` path is resolved against `FEATURE_DIR` — the
same directory `spec.md`, `plan.md` and `design.md` are read from. An absolute
path is used as given.

**Rationale.** Evidence answers "has this pass run *on this branch*". A path
resolved against the repository root names one file for every feature, so the
first branch to write it leaves the pass reporting finished on every branch
after — a false `done` that no later run corrects. The feature directory is the
one base under which a per-branch answer is the natural reading, and it is where
every existing predicate already looks (`_predicates.Evidence` holds
`spec_dir`).

That `FEATURE_DIR` is typically gitignored does not weigh against it: `spec.md`
is too, and evidence exists for wfctl's reading rather than for a reviewer. What
a reviewer must see is the *claimed absence*, and that is written somewhere else
entirely (R6).

**Alternatives considered.** Repo-root-relative, which is how the record's own
example (`design/ui-contract.md`) reads — rejected on the false-`done` argument
above. Both, selected by a prefix — two bases to explain and a syntax to invent,
for a case nobody has yet asked for; a repository that needs a committed
artifact names it absolutely today and asks for the shorthand when the second
one arrives.

## R4 — The check is `wfctl check config`

**Decision.** FR-022's check ships as a new command group: `wfctl check config`.
`tracker-check` is left where it is.

**Rationale.** Clarification settled the *shape* — a check over the repository's
own configuration, exiting non-zero, with `tracker-check` as the precedent — and
left the spelling to planning. #402 records the verb vocabulary this repo is
moving toward: `check <thing>`, with `check tracker`, `check body` and `check
config` named, and `doctor` staying as it is. Naming this one into the new
grouping from the first commit means the rename #402 eventually performs is one
verb shorter rather than one verb longer.

Renaming `tracker-check` here would be a drive-by on a surface this feature does
not otherwise touch, and it is #402's to do.

**Alternatives considered.** `wfctl config-check`, matching `tracker-check`'s
existing hyphenated shape — consistent today and wrong tomorrow, since #402's
direction is the grouped form. Folding the findings into `doctor` — refused in
clarification: `doctor`'s remit is state wfctl installed that has since drifted,
and a repository's own configuration is neither.

## R5 — `doctor` reports nothing about declared passes

**Decision.** `doctor` is unchanged by this feature. This closes `design.md`'s
first open question.

**Rationale.** The question was "what `doctor` reports for a declared sub-step
whose command is not installed, and whether that is a finding or a warning".
Clarification answered it one level up: that report belongs to the configuration
check, not the drift report. So the answer is neither finding nor warning —
`doctor` does not look.

What `doctor` still owns is the thing `check config` borrows: the installed
command directories. `_AGENT_TARGETS` in `cli.py` names them —
`.agents/commands`, `.claude/commands`, `.bob/commands` — and a declared command
`/x` is installed when `<layer>/commands/x.md` exists under any installed layer.
`design.md` corrected itself on this during the design pass and the correction
stands: the inventory `_pipeline` keeps is read by the test suite and cannot
reach a command shipping from the consuming repository, so this is new logic
reading `doctor`'s directories rather than a wiring-up of `doctor`'s data.

## R6 — A claimed absence is one file per pass, under `step-claims/`

**Decision.** `wfctl step none <step>.<name> --reason "…"` writes
`<arch-root>/step-claims/<branch>/<step>.<name>.md`, and
`_paths.non_record_subtrees` gains `step-claims/`.

**Rationale.** FR-015 requires that a second claim on one branch not destroy the
first, while a second claim on *the same pass* replaces it. One file per pass
gets both for free from the filesystem — `write_atomic` to a path derived from
the pass's own qualified name is a replace, and two different passes are two
different paths. `arch none`'s single `declarations/<branch>.md` is a whole-file
overwrite precisely because a branch makes one boundary claim; a branch makes as
many pass claims as it has passes, so the same shape would lose all but the last
(FR-015, SC-005).

The qualified form in the path is FR-002b, which requires `<step>.<name>`
wherever the name is written into a path.

`non_record_subtrees` is the FR-016 half. `wfctl arch context` already excludes
non-record corners for free — `load_records` globs one level — but
`records_on_this_branch` and `_observe` ask git about the whole arch root and are
handed the exclusions by name. A claim left out of that list would count as a
record on the branch, which is exactly "a pass's claimed absence answering the
boundary question" that FR-016 forbids and SC-006 tests. `AGENTS.md` names this
list as the place a fourth reader finds out, and this is the fourth reader.

**Alternatives considered.** One file per branch with a section per pass —
correct, and it makes "replace one pass's claim" a parse-and-rewrite of a
hand-edited file rather than a write. Writing claims into the feature directory,
as #339 originally proposed — `design.md` verified during the design pass that
`specs/` is gitignored, so the claim would reach no reviewer, which is the whole
of what a claim is for.

## R7 — A parent step's state is its own reading, downgraded by its passes

**Decision.** Inference evaluates the step's own predicate first, then its
passes. Where the step's own reading is `done` and any pass is `in_progress` or
`pending`, the step reports `in_progress`. Where the step's own reading is
`pending` or `skipped`, its passes are not evaluated and report `pending` and
`skipped` respectively.

**Rationale.** FR-006 requires a step to report unfinished while any pass is
outstanding, and says nothing about a step whose own evidence is missing. The
asymmetry is the cascade `_infer_steps` already runs: a step nothing has reached
yet has passes nothing has reached either, and calling their predicates would
spend reads to print a column of `pending` that the parent already says. A
`skipped` step is the same argument — `design-levels` allows a change to pass
brainstorm by, and its passes were passed by with it.

This keeps `brainstorm`'s existing predicate doing the job only it can do. Its
`pending` branch (nothing here yet) and its `skipped` branch (the pipeline moved
on without one) are facts about the step, not about either pass; what its `done`
/ `in_progress` branch computes is precisely what the two passes now compute
between them, and that branch becomes the roll-up.

**Alternatives considered.** Deriving the parent's state entirely from its
passes — `brainstorm` would lose the `skipped` reading, and a step with no passes
would have no state at all. Evaluating passes under a `pending` parent so the
payload is always complete — pays predicate reads on every step of every run for
a column whose value is already determined.

## R8 — Reading and validating the declaration is its own module

**Decision.** A new `wfctl/_declared.py` parses `wfctl.json`'s `steps` key and
returns `(passes, problems)`, the shape `_verify.load_config` already uses.
`_pipeline` consumes the passes; `wfctl check config` renders the problems.

**Rationale.** One reader, two consumers, and they must not disagree — a pass
that inference silently drops while the check calls the file clean is FR-022's
own failure. `_verify` is the wrong home (its docstring scopes it to the
definition of done, and it spawns subprocesses); `_pipeline` is the wrong home
for the reason its docstring gives, that it is pure inference over files and
splitting the payload's shape from the inference filling it is the one boundary
`pipeline-state-is-one-payload` rules out — a JSON parser and a validator inside
it would be a third job, not that boundary, but it is still the module every
predicate test imports.

A separate module also keeps validation testable without a repository: the
problems are a pure function of parsed JSON, which is the shape `_settings` and
`_workmux` already argue for.

**Alternatives considered.** Extending `_verify.load_config` to return a third
value — every existing caller rewritten to ignore it, and the module's own
docstring made false. Parsing inline in `cli.py` — the check and inference would
then be two parsers of one file, which is the disagreement above.

## R9 — Ordering overrides name a sibling; the default needs no configuration

**Decision.** Passes run in written order, the tool's before the repository's
(FR-003). A declared pass may carry `"before": "<name>"` or `"after": "<name>"`
naming a sibling under the same step. A name that does not exist, and a set of
constraints with no satisfying order, are both findings from `check config`
(FR-003a) rather than an arbitrary resolution.

**Rationale.** This is Andre's call recorded in clarification, against the
recommendation of tool-first-only: interleaving is configurable customization
and the default costs no configuration. The sibling is named bare rather than
qualified because both passes are under one step, where FR-002a guarantees the
name is unique.

Refusing an unsatisfiable set rather than resolving it is the same argument as
FR-004's: a repository that wrote a cycle and got *some* order has been given an
answer nobody can predict from the file they wrote.

**Alternatives considered.** A numeric `order` field — invites gaps and
renumbering, and two passes claiming one number needs the same refusal anyway.
Resolving a cycle by falling back to written order — quiet, and the fallback is
indistinguishable from the constraint having been honoured.

## R10 — A pass with no command declares `"manual": true`

**Decision.** A declared pass carries either `command` or `"manual": true`, and
exactly one of them. `check config` reports a pass carrying both, or neither.

**Rationale.** FR-022a requires a pass a person performs to be expressible, and
FR-007 requires the position view to name the pass and say a person performs it.
A `command` of `null` would express the same thing, and it expresses it by
absence — the reading a JSON author is most likely to produce by accident, by
deleting a line. An affirmative key makes the by-hand case a statement someone
wrote rather than a field someone forgot, which is the distinction FR-022 exists
to keep.

**Alternatives considered.** `"command": null` — above. Omitting `command`
entirely — same argument, one step weaker: a missing key and a key someone meant
to fill are the same file.

## R11 — `python-pattern-selection` is not touched here

**Decision.** Out of scope. This closes `design.md`'s second open question.

**Rationale.** The question was whether that skill should always write its
departure to a file when a repository tracks it as a pass. It is a change to what
that skill writes, and `design.md` says so in the same sentence. A pass earns a
row only if it leaves an artifact somebody can point at — the spec's own
assumption — so a repository that wants that pass tracked is asking for a change
to the skill, and the mechanism this feature ships is what makes the ask
expressible. Folding it in would put a skill edit inside a payload change and
give the feature a second reason to fail review.

**Alternatives considered.** Shipping it as one of wfctl's own passes under
`implement` — it is level 4, its output today is a judgment recorded in prose,
and the record is explicit that a practice writing nothing itself stays what it
is: how you do a pass, not a pass.
