---
status: proposed
---

# A reviewer blocked from writing returns its report, and wfctl saves it as relayed

## Context

The accepted record on review coverage names three ways a panel wrongly reports
a review as done. One of them is a reviewer blocked from writing its report,
which looks the same as one that never ran. The host's permission layer can
refuse a reviewer's write, and the reviewer then has its findings and nowhere to
put them.

wfctl counts a report only when it finds a file that names the run's newest
commit and includes a verdict. So when a reviewer is blocked, either it leaves
no file and the run is incomplete, or someone else writes the file for it. The
accepted record leaves the process for the second case to this level.

## Verified

- `fanning-out-code-review/SKILL.md` Step 3 counts a reviewer as reported only
  when `$REVIEWS/$id.md` has a verdict line, and lists the reviewer as missing
  otherwise. It has no case for a reviewer that put its report in its reply.
- The same skill's check for reports from reviewers nobody dispatched reads
  filenames under `reviews/` and nothing else. A file the coordinator writes
  under a reviewer's id passes as that reviewer's report.

## Assumed

- A blocked reviewer can still reply to the coordinator. If a host drops the
  reply along with the write, this assumption fails, and the reviewer reads as
  missing. That is the safe direction.
- A blocked reviewer states why it was blocked. A reviewer that invents a reason
  passes the coordinator's check, but the roster still shows the reason to
  Andre.

## Direct baseline

The simplest approach has the coordinator write the file. When a reviewer
replies with its report instead of writing it, the coordinator saves the reply
to `reviews/<id>.md` with its own file tool. The file looks the same as one the
reviewer wrote, and wfctl counts it the same way.

## Decision

The coordinator saves the reply to a file and passes that file to wfctl, and
wfctl saves it. A wfctl command takes the reviewer's id and reads the report
from the file it is given, never from stdin or the command's own text. The
worktree guard matches command text, and a security report quotes the
commands the guard refuses, so a report pasted into the command would be
refused while the branch is unreviewed. It saves the report
under that id with a header that marks it as relayed and includes the block
reason the reviewer gave. wfctl refuses a relayed report that gives no reason.

The roster shows the relay on the reviewer's line, such as
`s2 claude ✓ relayed: write denied`. The panel skill tells the coordinator to
check that reason against what it saw. If the reviewer wasn't really blocked,
the coordinator reports a gap to Andre, because a reviewer that could write and
didn't is a hole in the process.

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

The line marks the existing decision that wfctl records a verification and the
agent never certifies its own work. In the baseline, the coordinator writes
straight into the report file under another reviewer's id, and nothing marks it.
In the decision, the coordinator calls a wfctl command, and wfctl writes the
file and marks it. The decision adds one command on wfctl's side and turns the
coordinator's write into a call.

## Considered

- Have the coordinator write the file, as the direct baseline describes. We
  didn't choose this because a report the coordinator wrote looks the same as
  one the reviewer wrote. Andre can't tell a relay from a forgery on the roster.
- Treat a blocked reviewer as missing and run it again. We didn't choose this
  because the block usually comes from a permission rule, which refuses the
  same write the second time. The run would never complete.
- Give every reviewer a place to write that the host never blocks. We didn't
  choose this because each host decides what its subagents can write, and wfctl
  can't change that from outside.

## Consequences

- A blocked reviewer's findings count, and the roster shows they were relayed
  and why.
- The coordinator still decides what to pass to wfctl. If the coordinator edits
  a reply before relaying it, this check doesn't catch it. The accepted record
  already states the same limit for a report the agent writes itself.
- wfctl refuses a relay with no block reason, so every relayed report includes a
  reason Andre can read on the roster.

## Verification

- A test relays a report with a block reason and checks that the roster line
  reads `✓ relayed:` with that reason, and that the run completes.
- A test relays a report with no block reason and checks that wfctl refuses it
  and the run stays incomplete.
- A test relays a report that names an older commit and checks that it doesn't
  count, the same as a written report.

## Log

- 2026-10-21  proposed  — #622 level 3. Andre agreed to the relay and added the
  rule that a reviewer that wasn't really blocked is a gap to report.
- 2026-10-23  proposed  — #622 plan review. The report now arrives from a
  file rather than stdin, so it never travels in the text the guard matches.
  Andre approved folding in the second review's findings.
