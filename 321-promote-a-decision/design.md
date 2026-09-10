# Nothing promotes a decision to accepted — #321

## The idea in one line

A human accepts an architecture record; `wfctl arch accept <slug> --agreed
"<where>"` is how wfctl writes that down, and wfctl never infers the transition
from a merge, a green step, or shipped code.

## The problem, in the surface it shows on

`wfctl arch context` is what `/start-session` runs to load the contract an agent
works under. Today it ends:

```
14 records not shown (14 proposed) — docs/architecture/
```

Two of those fourteen describe rules the code already enforces. There is no
command that would move any of them, and `_arch.supersede` — the module's only
status mutation — has never been reachable from the CLI either.

## Level 1 — behaviour

Every reachable state of the new command, as the string it renders, judged in
that state.

**Nothing named.** The listing that makes the backlog nameable; it exists here
and nowhere else, so no other command's output grows.

```
✗ Name the record to accept.

  Proposed, and promotable:
    a-branch-is-claimed-not-inherited
    a-human-accepts-a-decision
    …
    wfctl-classes-the-action-not-the-command

  wfctl arch accept <slug> --agreed "<where the human agreed>"
```
True: nothing was promoted, so the exit code is 1. A caller that meant to promote
and forgot the argument must not read this as success.

**A slug that is not a record.**

```
✗ No record 'promised-evidence' — did you mean one of these?
    promised-evidence-blocks-on-silence
```
True. The near-miss is the common case: slugs are long and hand-typed.

**No citation.**

```
✗ --agreed is required: say where the human agreed to this.
```
True. This is the field the whole rule rests on; a promotion without it is the
un-auditable transition the record exists to prevent.

**A placeholder citation.**

```
✗ "<where>" is a placeholder, not a citation — say where the decision was agreed.
```
True, and it is the failure `arch none --reason` already documents: a reader who
pastes the example back gets a committed record whose evidence is `<where>`.

**Already accepted.**

```
✗ a-rule-is-expressed-as-a-check is already accepted (2026-09-06). Nothing to do.
```
True, and it renders instead of a second `Log` line. A second `accepted` entry
would claim a second agreement that never happened.

**Superseded, rejected or retired.**

```
✗ mirror-supersedes-the-wrapper is superseded, not proposed. A decision that is
  binding again is a new record, not a reopened one.
```
True. Only `proposed` promotes; the other three keep the states this change was
told not to touch.

**No readable status.**

```
✗ tracker-owns-the-issue-key-shape has no readable status. Fix its frontmatter
  first — accepting it would overwrite whatever it says.
```
True, and distinct from the row above: the reader's next action is editing the
file, not writing a new record.

**Success.**

```
✓ a-human-accepts-a-decision is accepted — agreed on #321
  Logged: 2026-09-09  accepted    — agreed on #321
```
True. It names the line it wrote, because that line is the whole artifact.

### What level 1 generated for level 3

- The near-miss row means the slug set has to be loaded before the argument is
  rejected — so the command reads every record whatever it was asked, and the
  listing and the suggestion come off one read.
- Three distinct refusals for "not proposed" mean the current status has to reach
  the message, not just a boolean. `Record.status` already carries it.
- The success line quotes the `Log` line, so the caller composes it before
  writing rather than letting the module compose it privately.

## Level 2 — architecture

`docs/architecture/a-human-accepts-a-decision.md`

A human owns *"is this decision binding?"*; wfctl owns *"where was that said, and
when?"*. wfctl cannot compute the first because every signal it has — a merge, a
green step, a shipped command — is evidence the decision was **implemented**, and
a record promoted on its own implementation can never disagree with the
implementation.

## Level 3 — design

Claims this design rests on, split by whether they were checked.

| checked | assumed |
|---|---|
| `supersede()` has no caller outside tests — `grep` | no third transition arrives soon; `rejected` and `retired` have no consumer |
| `_frontmatter_end` and `_key_value` say they exist so parser and `supersede` cannot disagree | the 12-character `Log` column is convention, not accident |
| every `Log` line pads its status to 12 characters | |
| `_predicates.Source` names `accepted-record`, `_PROMISED` contains it, nothing produces it | |
| `required-sections-are-wfctls` merged `proposed` and was accepted three commits later | |
| `wfctl-runs-the-verification`'s promotion commit says it made "the contract match code" | |

Both assumptions are recorded with what would falsify them in the design record
below.

## Software design decisions

- docs/architecture/design/321-one-status-mutation.md — `supersede` and `accept`
  are two callers of one `_set_status`, because a copied mutation body is where
  the file format's four hazards get lost.

## Out of scope

- Promoting the fourteen. This change states the rule; applying it to the backlog
  is a separate review, and a diff that flips fourteen statuses buries the one
  decision a reviewer is meant to argue with.
- `rejected` and `retired`. No consumer, no demand.
- #299's gate. This makes `accepted-record` producible; it does not read it.
