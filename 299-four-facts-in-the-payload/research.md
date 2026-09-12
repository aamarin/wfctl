# Phase 0 research — #299

Every question below was resolved against this repository's code. Nothing is
carried from memory, and each answer names what was read.

## Which source answers each fact, and does a reader already exist?

| Fact | Source | Existing reader |
| --- | --- | --- |
| artifacts written | the spec dir | `_predicates.build_evidence` — already reads `spec.md`, `plan.md`, `tasks.md` unconditionally before the walk |
| definition of done verified | `wfctl.json` + the verification record | `_predicates.verification_block(repo_root)`, public since #236 |
| architecture accepted | the `status` field of records this branch touched | `_paths.records_on_this_branch` + `_arch.load_records` |
| integration authorized | the recorded human grant | `_session.resolved_notify(agent_dir, branch)` |

All four readers exist. This feature adds no source and no parser.

## Is a record's status read anywhere in inference today?

No. `load_records` and `in_force` appear only in `cli.py` (`arch context`, `arch
accept`, `arch check`). `_predicates.design_block` counts a record under the arch
root *whatever its status* and says so in its own docstring: "a `proposed` record
still means the question was put." That is why the two situations #299 names
produce identical payloads.

## Can a touched record under `design/` be told from a top-level one?

Not by slug — `records_on_this_branch` returns `Path(p).stem`, so
`design/299-facts-render-as-a-block.md` and a top-level record of the same name
would be indistinguishable. It does not have to be: `_arch.load_records` globs
**one level**, which is what already keeps `design/`, `declarations/` and
`views/` out of `wfctl arch context`. Intersecting the touched slugs with the
loaded record slugs therefore drops every subtree, including `scans/`, with no
second exclusion to maintain.

That is the answer to FR-009 and it is preferable to widening
`records_on_this_branch`'s single `exclude` parameter into a list, which would
add a signature every future caller has to get right in a direction that fails
open.

## What does "accepted" have to mean for a branch that supersedes a record?

Not literally `accepted`. A branch that supersedes a record leaves that record at
`superseded`, which a human moved it to; requiring `accepted` would report such a
branch as blocked forever.

The fact is unmet when a touched record is **`proposed` or carries no recognised
status**, and met otherwise. `_arch.STATUSES` is the closed set, and
`parse_record` already resolves anything outside it — absent, misspelled — to
`""`, never to `accepted`. So "waiting on a human" is exactly `proposed`, and
"unreadable" is exactly `""`.

## Does the pinned payload snapshot have to be regenerated?

No, and that is worth asserting rather than discovering.
`tests/test_pipeline_payload_snapshot.py` imports `_infer_steps` alone and pins
each step's `state`, `annotation`, `reason` and `remedy`. The facts live on
`PipelineReport`, not on the step dicts. A diff against that snapshot would mean
a step verdict moved, which this feature does not do — so the file staying byte-
identical is evidence, not an omission.

## Where does the notify grant's trunk correction live today?

In `cli.status_cmd`, after `build_report` returns: it calls `on_trunk`, rewrites
`notify_source` to `trunk` or `unknown-trunk`, and recomputes `notify`. That is a
view computing a fact, which `pipeline-state-is-one-payload` forbids; it survived
because nothing else needed the corrected answer.

Fact 4 needs it. Moving the correction into `build_report` gives one answer in
one place and leaves `status_cmd` rendering it. The comment currently at that
call site argues for asking *there rather than reading the grant back from the
log*, which this preserves — the grant is still read from the log once, by
`build_report`, and the trunk question is still answered with local git calls.

`build_report` has five call sites in `cli.py` (`status`, `next`, `resume`, and
two others) and is called directly by four test modules. Each gains the two local
git calls `status` already made. No call site loses a field.

## Does `verification_block` distinguish "no definition of done" from "passed"?

Yes, and only by returning `None` for both. `load_config` returns `(commands,
errs)`; with no errors and no commands the function returns `None` before
touching git — the FR-002 degrade path, which "must cost nothing". A malformed
config returns a reason and is therefore unmet, not absent.

So fact 2 asks `load_config` directly for the `n/a` case and calls
`verification_block` for the rest. The two readings cannot disagree, because the
degrade path is the first branch of the function being called.

## What does a fact say when the evidence cannot be read?

Unmet, with the detail naming the unavailable evidence — reached through the
existing rule and not a new one. `blocks("inconclusive", "human")` is `True`
because `human` is in `_PROMISED`, and `promised-evidence-blocks-on-silence`
gives the reason. The one case that reaches this is `on_trunk` returning `None`:
git cannot say whether this is the trunk.
