---
status: proposed
---

# A reviewer blocked from writing returns its report, and wfctl saves it as relayed

## Context

The accepted record on review coverage names three ways a panel wrongly reports
a review as done. One of them is a reviewer blocked from writing its report,
which looks the same as one that never ran. The host's permission layer can
refuse a reviewer's write, and the reviewer then has its findings and nowhere
to put them.

wfctl counts a report only when it finds a file that names the run's newest
commit and carries a verdict. So a blocked reviewer either leaves no file, and
the run is incomplete, or someone else writes the file for it. Level 2 left the
process for that second case to this level.

## Verified

- `fanning-out-code-review/SKILL.md` Step 3 counts a reviewer as reported only
  when `$REVIEWS/$id.md` carries a verdict line, and lists the reviewer as
  missing otherwise. It has no case for a reviewer that reported in its reply.
- The same skill's undispatched-report check reads filenames under `reviews/`
  and nothing else, so a file the coordinator writes under a reviewer's id reads
  as that reviewer's report.

## Assumed

- A reviewer that is blocked can still reply to the coordinator. A host that
  drops the reply along with the write would falsify this, and the reviewer then
  reads as missing, which is the safe direction.
- A reviewer states why it was blocked when it was. One that invents a block
  reason gets past the coordinator's check, and the roster still shows the
  reason to Andre.

## Direct baseline

The coordinator writes the file. When a reviewer replies with its report instead
of writing it, the coordinator saves the reply to `reviews/<id>.md` with its own
file tool. The file looks the same as one the reviewer wrote, and wfctl counts it
the same way.

## Decision

The coordinator hands the reply to wfctl, and wfctl saves it. A wfctl command
takes the reviewer's id and reads the report on stdin. It writes the report
under that id with a header marking it relayed, and the header carries the block
reason the reviewer stated. A relayed report with no stated reason is refused.

The roster shows the relay on the reviewer's line, such as
`s2 claude ✓ relayed: write denied`. The panel skill tells the coordinator to
check that reason against what it saw. If the reviewer wasn't really blocked,
the coordinator reports a gap to Andre, because a reviewer that can write and
doesn't is a hole in the process.

## Diagram

```
             baseline                                decision

          ┌──────────┐                            ┌──────────┐
          │ reviewer │                            │ reviewer │
          └────┬─────┘                            └────┬─────┘
               │ replies                               │ replies
          ┌────▼────────┐                         ┌────▼────────┐
          │ coordinator │                         │ coordinator │
          └────┬────────┘                         └────┬────────┘
               │ writes                                │ calls
═══ wfctl-runs-the-verification ═════════════════════════╪══════════════════
               │                                  ┌────▼─────────┐
               │                                  │ wfctl relay  │ (new)
               │                                  └────┬─────────┘
               │                                       │ writes, marked relayed
          ┌────▼────────┐                         ┌────▼────────┐
          │ report file │◄── reads ── check       │ report file │◄── reads ── check
          └─────────────┘                         └─────────────┘
```

The divider is the decision that wfctl records a verification and the agent
never certifies its own. In the baseline the coordinator's arrow crosses that
divider straight into the report file, so the coordinator writes a report under
another reviewer's id and nothing marks it. In the decision the coordinator's
arrow ends at a wfctl command, which writes the file and marks it. The graphs
differ by one command added on wfctl's side, and by the coordinator's write
becoming a call.

## Considered

- The coordinator writes the file, as the direct baseline describes. We didn't
  choose this because a report the coordinator wrote looks the same as one the
  reviewer wrote, and Andre can't tell a relay from a forgery on the roster.
- Treat a blocked reviewer as missing and run it again. We didn't choose this
  because the block usually comes from a permission rule that refuses the same
  write the second time, so the run never completes.
- Give every reviewer a write path the host never blocks. We didn't choose this
  because each host decides what its subagents may write, and wfctl can't change
  that from outside.

## Consequences

- A blocked reviewer's findings count, and the roster says they were relayed and
  why.
- The coordinator still chooses what to pass to wfctl. A coordinator that edits
  a reply before relaying it gets past this check, which is the same limit the
  accepted record states for a report the agent wrote itself.
- A relay with no block reason is refused, so every relayed report carries a
  reason Andre can read on the roster.

## Verification

- A test relays a report with a block reason and asserts that the roster line
  reads `✓ relayed:` with that reason, and that the run completes.
- A test relays a report with no block reason and asserts that wfctl refuses it
  and the run stays incomplete.
- A test relays a report that names an older commit and asserts that it doesn't
  count, the same as a written one.

## Log

- 2026-10-21  proposed  — #622 level 3. Andre agreed to the relay and added the
  rule that a reviewer that wasn't really blocked is a gap to report.
