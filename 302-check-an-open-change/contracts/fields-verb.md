# Contract: the `fields` verb

A tracker declares `fields` in `.agents/trackers/<name>.json`, under `verbs` for
issues and under `changes` for changes. Both are optional; a backend that cannot
report fields declares neither and the check says so and exits zero.

## Placeholders

```
verbs.fields     {id}   — and {me}, allowed in every verb
changes.fields   {id}   — and {me}
```

Added to `ALLOWED` and `ALLOWED_CHANGES` in `wfctl/_tracker.py`. Both tables
already reject an undeclared verb, so nothing else changes to make a config
carrying `fields` valid and one carrying `check` invalid.

## What it must print

One JSON object on stdout, whose values are scalars or arrays of scalars. Keys
are the backend's own field names — wfctl neither supplies nor validates them.

```json
{"labels":["enhancement","P1"],"assignees":["aamarin"],
 "milestone":null,"projectItems":[]}
```

Exit zero. A non-zero exit is a failed read: its stderr is reported and the run
exits non-zero (FR-017).

## What wfctl does with a payload that breaks the contract

| Payload | Behaviour |
| --- | --- |
| not valid JSON | finding naming the tracker config; exit non-zero |
| valid JSON, not an object | same |
| a value that is an object, or an array containing one | finding naming the tracker config and the offending key; exit non-zero |
| an empty object | no keys to compare; the run reports nothing to check |

The point of reporting rather than raising: the payload comes from a hand-edited
config, and a traceback out of a comparison names the wrong thing. The reader
needs to be sent to the file they can fix.

## Why the tracker flattens rather than wfctl

`gh` returns a label as `{"id":…,"name":"enhancement","color":…}`. Unwrapping
inside wfctl means knowing that `name` identifies a label, `login` an assignee
and `title` a board item, which is one tracker's vocabulary in wfctl's own source
— the thing FR-004 forbids and
`docs/architecture/the-repo-names-the-fields-a-change-must-carry.md` records.

## GitHub's declaration

```json
"changes": {
  "list":   ["gh","pr","list","--state","open","--author","{me}"],
  "view":   ["gh","pr","view","{id}"],
  "fields": ["gh","pr","view","{id}","--json",
             "labels,assignees,milestone,projectItems,reviewRequests",
             "--jq","{labels:[.labels[].name],assignees:[.assignees[].login],milestone:(.milestone.title//null),projectItems:[.projectItems[].title],reviewRequests:[.reviewRequests[].login]}"]
}
```

and the matching `verbs.fields` over `gh issue view`, which emits the same key
names so the two payloads compare key by key.

## Reading it

`_tracker.read_fields(repo_root, section, id) -> tuple[dict | None, str | None]`,
the same shape as `read_issue_labels`:

| Returns | Means |
| --- | --- |
| `(payload, None)` | the verb ran and its output parsed |
| `(None, None)` | nobody was asked — no tracker, or the verb is not declared |
| `(None, detail)` | the answer did not arrive — non-zero exit, timeout, or unparseable output |

Bounded at 15 seconds per call (FR-016), matching `read_issue_labels`. The two
middle and bottom rows must not be collapsed: the first is the ordinary state of
a repository that declined a capability, the second decides the run.
