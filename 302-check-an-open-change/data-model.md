# Data model: check an open change

Nothing here is persisted. Every value is built per invocation and discarded,
per `session-state-is-re-derived`.

## Field payload

What one `fields` verb returns, for one change or one issue.

A flat mapping of key to value. Keys are the backend's own names; wfctl never
enumerates them. Values are one of:

| Value shape | Set when | Unset when |
| --- | --- | --- |
| string | non-empty | `null` or `""` |
| number, boolean | present | `null` |
| array of scalars | non-empty | `[]` |

Anything else — an object, or an array containing one — is a payload the
contract forbids, and is reported as a configuration problem naming the tracker
config (FR-012). It is never compared and never silently skipped.

Absent from the payload is distinct from present-but-unset. A key the verb never
emitted cannot be inherited, and a required key that is never emitted is its own
finding (FR-006).

## Expectation

Why a key is worth reporting. Exactly two sources, and a key with neither is
never mentioned:

```
key is expected
 ├─ required  ──► named in wfctl.json's change_check
 └─ inherited ──► set on the branch's issue payload
```

A key can be both. `required` is reported, because it is the source the reader
can act on directly — the repository said so, in a file they can open.

## Comparison

Per key, once the two payloads are in hand:

| Issue value | Change value | Required | Result |
| --- | --- | --- | --- |
| any | set, covers the issue's | either | satisfied |
| set | unset | either | finding — inherited |
| set (list) | set (list), missing some | either | finding — inherited, names what is missing |
| unset | unset | yes | finding — required |
| unset | unset | no | not reported |
| unset | set | no | not reported |
| — (key absent from change payload) | — | yes | finding — required key the tracker never reports |

The third row is why lists compare as a set difference rather than an emptiness
test: `opening-a-change` Step 6 says a label the change earns in its own right is
*added* to the issue's set, never swapped in for it, so extra values on the
change are never a finding.

## Finding

One key, plus what the reader needs to act:

- the key, as the backend names it
- which source expected it — `required` or `inherited`
- for `inherited`, the issue's value, so the reader knows what to copy
- for a required key the tracker never reports, what the tracker does report
  instead, so a spelling mismatch is visible rather than silent

## Report

What the command prints, in three markers with three distinct meanings:

| Marker | Meaning | Exit contribution |
| --- | --- | --- |
| `⚠` | a verdict, and it is a finding | non-zero |
| `✓` | a verdict, and the key is satisfied | zero |
| `ℹ` | no verdict — nothing was expected, or the tracker declined | zero |

`ℹ` is per-run, not per-key. A key that is unset everywhere and expected by
nobody prints nothing at all; the run-level `ℹ` appears only when there was
nothing to check, when a tracker declined, or when no tracker is configured.

A read that was attempted and failed is not `ℹ`. It reports the failure with what
the tracker said, prints whatever the other read still made checkable, and exits
non-zero (FR-016).
