---
status: accepted
---

# wfctl runs the verification, not the agent

## Context

`README.md` sells "truth from artifacts — step read from real spec files, so
phases can't be faked or skipped". That holds for `specify`, `plan` and `tasks`,
where the artifact *is* the work. It does not hold for `implement`, which is
marked complete by the existence of a non-empty
`checklists/implement-complete.md` — a file `speckit-implement` instructs the
agent to write at the end of its own run. Ticking every box in `tasks.md` is a
second route to the same conclusion, and checkboxes are model-edited too.

Both routes end at the agent asserting it finished. Writing the file on a red
build reports `●`.

## Decision

wfctl runs a repo-declared verification command, records the verdict with the
tree it ran against, and reads completion from that record. The agent never
certifies its own completion.

Absence of a declared command degrades to today's behavior — wfctl is
language-agnostic and guessing a test command is worse than having none.

## Owns truth

wfctl owns "did the check pass, and against which tree?".

The agent cannot: a self-report is unfalsifiable. Nothing distinguishes an agent
that ran the suite and read it green from one that concluded it was finished,
because both produce the same sentence. The verdict has to be a side effect of
running the command, not a claim about having run it.

## Considered

- Agent writes `implement-complete.md` — today's behavior, and the failure being
  corrected. Forgeable by the party the check exists to constrain.
- Trust the agent, audit afterwards — the audit is another step nothing runs, so
  it degrades to trust within one release.
- `status` shells out to the test suite on every call — `status` runs constantly,
  including from `/start-session`. A pipeline read that takes a test run is a
  pipeline read nobody makes.

## Consequences

The verdict binds to a commit sha and a dirty flag, so a tree that moved after
the run reads stale rather than passing. That makes the check tamper-evident
rather than unforgeable, which is the honest ceiling for a local CLI.

## Log

- 2026-08-27  proposed    — seeded from #69; level 2 for this boundary is open
- 2026-08-29  accepted    — #96 shipped it; the code enforced a rule the contract still called open
