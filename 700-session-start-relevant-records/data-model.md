# Data model: Session start loads the records for the branch's contexts

## Selection

`_contexts.Selection`, a `NamedTuple` returned by `_contexts.select` and
`_evidence.records_for_branch`.

| Field | Type | Meaning |
| --- | --- | --- |
| `records` | `tuple[_arch.Record, ...]` | the accepted records to print, in the order given |
| `left_out` | `int` | accepted records not in `records` |
| `contexts` | `tuple[str, ...]` | the branch's contexts when they were used to select, else `()` |
| `unlisted` | `bool` | the repo has a name list and the branch lists no contexts |
| `unknown` | `str \| None` | the first listed name not on the name list |

Derived: `narrowed` is `left_out > 0`.

## `select(names, listed, accepted)`

Inputs: `names` from `_contexts.names(arch)`, `listed` from
`_contexts.listed(spec_dir)` or `None` when there is no spec folder, and
`accepted`, the in-force records.

| Condition, checked in order | Result |
| --- | --- |
| `names is None` | every record, nothing else set |
| `listed` is `None` or empty | every record, `unlisted=True` |
| a listed name not in `names` | every record, `unknown=<first such name>` |
| otherwise | records with no `governs`, or a `governs` sharing a name with `listed`; `contexts=listed`; `left_out` the rest |

Invariant: `len(records) + left_out == len(accepted)`.

## Session payload

| Key | Type | Meaning |
| --- | --- | --- |
| `accepted_records` | `int` | unchanged: every accepted record |
| `applying_records` | `int \| null` | `len(records)` when narrowed, else `null` |
