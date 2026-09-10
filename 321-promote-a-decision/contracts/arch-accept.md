# Contract — `wfctl arch accept`

```
wfctl arch accept [SLUG] --agreed "<where the human agreed>"
```

| | |
| --- | --- |
| `SLUG` | optional. The record to accept, named by slug. Omitted, the command lists what could be accepted and exits 1. |
| `--agreed` | required when `SLUG` is given. Where the human agreed. Free text. |

`--agreed` is not declared required by the option parser, because the no-slug
listing must not be blocked by a missing citation. It is enforced after the slug
is resolved, so the two refusals arrive in the order the reader can act on them.

## Exit codes

| Code | When |
| --- | --- |
| 0 | the record was accepted |
| 1 | every refusal, including the bare listing — nothing was written |

## Outputs

**Accepted.** The line it wrote is quoted, because that line is the artifact.

```
✓ a-human-accepts-a-decision is accepted — agreed on #321
  Logged: 2026-09-09  accepted    — agreed on #321
```

**No slug.** Exit 1: a caller that meant to accept and gave no argument accepted
nothing.

```
✗ Name the record to accept.

  Proposed, and promotable:
    a-branch-is-claimed-not-inherited
    a-human-accepts-a-decision
    …

  wfctl arch accept <slug> --agreed "<where the human agreed>"
```

**No slug, and nothing is promotable.**

```
✗ Name the record to accept.
  Every record is already accepted or ended — nothing is promotable.
```

Exit 1, like every other no-slug call. FR-007 requires the request to report as
unsuccessful, and it does not distinguish why nothing was accepted: a caller that
asked to accept and accepted nothing must not read 0. An earlier draft of this
contract exited 0 here on the grounds that nothing was asked for that could not
be given — that is green over a no-op, which is the reading this repository
refuses everywhere else.

**Unknown slug.**

```
✗ No record 'promised-evidence' — did you mean one of these?
    promised-evidence-blocks-on-silence
```

With no near match, the promotable list is printed instead, as above.

**Missing citation.**

```
✗ --agreed is required: say where the human agreed to this.
```

**Placeholder citation.**

```
✗ "<where>" is a placeholder, not a citation — say where the decision was agreed.
```

Matched as `<…>` with nothing but non-`>` inside, which is the rule
`arch none --reason` already applies and the shape documentation and help text
write.

**Already accepted.**

```
✗ a-rule-is-expressed-as-a-check is already accepted (2026-09-06). Nothing to do.
```

The date is read from the record's last `accepted` `Log` line. Inventing one from
elsewhere would be a claim the file does not make, so a record carrying none
answers the question rather than dropping it:

```
✗ layer-model is already accepted (no acceptance logged). Nothing to do.
```

Checked: all ten records accepted by hand before this command existed carry the
line, so this branch fires for nothing today. It is still required — `_set_status`
requires a `## Log` section, not an `accepted` entry inside it, so a status edited
without one reaches here. User Story 2 scenario 1 requires the message to say
*when*, and a silently shortened sentence would leave a reader unsure whether the
date was missing or the record was accepted today.

**Ended.**

```
✗ mirror-supersedes-the-wrapper is superseded, not proposed. A decision that is
  binding again is a new record, not a reopened one.
```

**Unreadable status.**

```
✗ tracker-owns-the-issue-key-shape has no readable status. Fix its frontmatter
  first — accepting it would overwrite whatever it says.
```

**No `## Log` section, or no `status:` key.** Raised by `_arch` and rendered here;
nothing is written in either case.

```
✗ docs/architecture/<slug>.md: no '## Log' section to append to
```

## Guarantees

- Every refusal leaves the file byte-identical.
- Success changes exactly two lines: the `status:` value, and one appended `Log`
  entry. A record with CRLF endings keeps them; a record with no final newline
  gains one before the entry rather than having the entry welded on.
- The write is atomic — the file is its old contents or its new ones.
- The status key changed is the one a reader sees, when frontmatter repeats it.

## What this command does not do

- It does not verify the citation. Nothing can (NFR-001).
- It does not accept more than one record per invocation. The backlog is promoted
  one agreement at a time, which is what an agreement is.
- It does not write to the session event log or any state directory.
- It does not reach `rejected` or `retired`.
