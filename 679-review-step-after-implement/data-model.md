# Data model: Review step after implement

This change adds no stored state. It reads two kinds of files that already exist, adds one exception file, and adds fields to in-memory types and the status payload.

## Files read, unchanged

The review state lives in the branch's state folder, `$(wfctl state-dir)/reviews/`. Only `wfctl review check` and `wfctl review sign-off` write these files.

| File | Holds | Read by |
| --- | --- | --- |
| `reviews/<group>/last-reviewed.json` | `{sha, run, at}`, the last commit a complete run covered | `coverage_from_state`, through `pending_at_head` |
| `reviews/sign-off.json` | the commit a person signed off | same |

## New file

`<spec-folder>/exceptions/spec.md` holds the branch's "no spec" answer. `wfctl spec none` writes it through `_design_exceptions.write`.

```markdown
# `spec` does not apply

No behavior change: … No significant design decision: … No ownership change: …
```

The title comes from `_design_exceptions._title`, unchanged. The file is in effect only while none of `design.md`, `spec.md`, `plan.md`, or `tasks.md` exists in the same folder. Otherwise the pipeline ignores it and warns.

## In-memory types

`HeadCoverage` in `_review`, returned by `pending_at_head`:

| Field | Type | Meaning |
| --- | --- | --- |
| `pending` | `dict[str, tuple[str, ...]]` | each group's unreviewed commits, oldest first, with fully reviewed groups left out |
| `since` | `dict[str, str \| None]` | the newest of the group's last reviewed commit and the signed-off commit that's still on the branch, filled only when the caller passes `for_status=True`. `None` when neither is on the branch, when neither descends from the other, or when a git read fails |
| `capped` | `tuple[str, ...]` | the pending groups whose started rounds have reached the round cap, filled only when the caller passes `for_status=True` |
| `trunk_ref` | `str \| None` | the trunk ref the coverage was measured against, which the guard passes on to its record check. `None` when the trunk couldn't be resolved |
| `error` | `str \| None` | why coverage can't be computed, such as an unreadable config, a missing trunk, or a branch with no commits |
| `remedy` | `str \| None` | the fix for a config problem, set where it's caught. `None` for an error whose message names its own fix |

`Evidence` in `_evidence` gets three fields, all defaulted:

| Field | Type | Set when |
| --- | --- | --- |
| `review` | `HeadCoverage \| None` | `implement` reads done. Otherwise `None` |
| `no_spec` | `str \| None` | `exceptions/spec.md` has a reason and no spec artifact exists |
| `stale_no_spec` | `str \| None` | `exceptions/spec.md` has a reason and an artifact exists. Holds the artifact's name |

`Step` in `_pipeline` gets `spec_step: bool = False`, which is `True` on brainstorm, specify, clarify, plan, tasks, analyze, and decompose.

`PipelineReport` gets `no_spec: NoSpec | None`, with `NoSpec(reason: str, path: str)`.

## Review step states

| Condition | State | Reason | Annotation | Remedy |
| --- | --- | --- | --- | --- |
| `implement` isn't done | `pending` | none | none | none |
| `error` is set | `in_progress` | the error | the error | `remedy`, set only for a config problem |
| `capped` isn't empty | `in_progress` | each capped group and its cap | the reason | ask the user to sign off |
| a group has unreviewed commits | `in_progress` | none | each group's state | none |
| no group has unreviewed commits | `done` | none | none | none |

A group's state is `not reviewed yet (N commits)`, or `N commits unreviewed since <short sha>`. The short sha is the newest reviewed commit still on the branch, so after a run followed by a later sign-off it names the signed-off commit. A group whose `since` is `None` reads the first form.

A new commit after a complete review first makes `implement` stale through the verification record, so review reads `pending` again until `wfctl verify` passes. It then reads `in_progress` with one commit per group.

## Status payload, version 1.4

- `steps` has a ninth entry, `review`, after `implement`.
- On a no-spec branch, the seven spec steps read `"state": "skipped"` and `"annotation": "no spec"`, and every pass under them reads `skipped`.
- A new top-level key, always present:

```json
"no_spec": {
  "reason": "No behavior change: … No significant design decision: … No ownership change: …",
  "path": "/…/679-example/exceptions/spec.md"
}
```

It's `null` when no "no" is in effect, including when one is on disk but a spec artifact outranks it.
