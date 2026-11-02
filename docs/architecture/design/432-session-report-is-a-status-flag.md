---
status: proposed
governs: session-continuity
---

# The session report is a flag on `wfctl status`

## Context

Under `session-report-built-in-code.md`, one wfctl command builds the
session-start report. This record picks that command.

Two commands already run at session start, and they do different jobs. `wfctl
start` changes state: it refuses a session the branch doesn't allow, claims the
branch for the calling conversation, and can take the branch over from another
conversation. `wfctl status` changes nothing and can run any number of times.
The report only reads state, so it belongs with `status`.

The accepted record also rejected adding the issue lines to plain `wfctl
status`. The reason was speed. `status` runs on every pipeline step and in the
supervisory screen, so a tracker call there would add network time to every
command that reads status, not only to session start.

## Verified

- `start_cmd` (`wfctl/cli.py:363`) refuses through
  `_refuse_unless_the_issue_allows_a_session`, then appends a `start` event or
  takes the branch over, and prints one line. It already computes the pipeline
  position with `build_report` at `cli.py:426`, to name the step in that line.
- `status_cmd` (`wfctl/cli.py:615`) takes `--json` and `--all`, builds the
  report with `build_report`, and writes nothing.
- `build_report` (`wfctl/_pipeline.py:1126`) has eight callers in `cli.py`, so
  the pipeline payload is computed the same way wherever it is read.
- 24 files under `wfctl/agents/` mention `wfctl status`.

## Assumed

- No second view of `status` is coming soon. If one comes, a `status` command
  group becomes worth its cost, and this flag becomes one of its views.

## Direct baseline

Put the report in `wfctl start`. After it claims the branch, `start` reads the
handoff, the commits, and the tracker, and prints the finished report. The
`/start-session` skill runs one command.

## Decision

`wfctl status --session` prints the session-start report. It builds the same
pipeline payload as plain `status`, then adds the handoff and the branch's
commits and uncommitted changes. On a branch that names an issue, it also adds
that issue, its parent epic, and the branch's open PR. `--session --json` prints
the same report as JSON.

Plain `wfctl status` is unchanged and makes no tracker call. `wfctl start` still
refuses or allows the session, claims the branch, and prints one line.

`/start-session` runs `wfctl start && wfctl doctor --session`. When `start`
succeeds, the skill then runs `wfctl status --session` whatever `doctor`
exited with. `doctor` exits 1 on drift the skill still has to repair, and that
drift shouldn't keep the report from printing.

## Diagram

```
            baseline                               decision

          ┌───────────────┐                      ┌───────────────┐
          │ build_report  │                      │ build_report  │
          │ (payload)     │                      │ (payload)     │
          └───────────────┘                      └───────────────┘
            ▲ calls    ▲ calls                     ▲ calls   ▲ calls
            │          │                           │         │
          ┌─┴──────────┴──┐  ┌──────────┐      ┌───┴───┐ ┌───┴──────────┐
          │ start         │  │ status   │      │ start │ │ status       │
          │ claim + report│  │          │      │ claim │ │ --session    │
          └───────────────┘  └──────────┘      └───────┘ │ (new)        │
            │ calls  │ writes                    │writes └──────────────┘
            ▼        ▼                             ▼         │ calls
          ┌───────┐ ┌────────┐                 ┌────────┐  ┌─▼──────┐
          │tracker│ │events  │                 │events  │  │tracker │
          └───────┘ └────────┘                 └────────┘  └────────┘
```

Neither graph adds a divider, and both have four arrows. The decision is built
to absorb a change to what the report shows. In the baseline, that change goes
into `start`, which has three arrows: it calls `build_report`, calls the
tracker, and writes the event log. In the decision, it goes into `status
--session`, which has two arrows and writes nothing. As a result, a change to
the report can't break the claim. To re-read the
report mid-session, you run `status --session`. In the baseline, you would
run `start` again, which can take the branch over.

## Considered

- **The direct baseline, the report inside `wfctl start`.** It saves one
  command per session, and `start` already computes the pipeline position. We
  didn't choose it because the report can't be re-read without claiming the
  branch again. A command that both writes state and calls the network is also
  harder to reason about when one of them fails.
- **A new top-level verb, such as `wfctl session`.** It reads as clearly as the
  flag. We didn't choose it because the report starts from the pipeline payload
  that `status` already builds. A second command printing the same payload goes
  against `pipeline-state-is-one-payload.md`.
- **A `status` subcommand, `wfctl status session`.** It gives later views a
  shared home. We didn't choose it because there is no second view. We
  considered an end-of-session view, but it would have existed only for
  symmetry. A subcommand also lets options go on either side of it, as in
  `status --json session` and `status session --json`.

## Consequences

wfctl calls the tracker only when a caller passes `--session`, so pipeline steps
and the supervisory screen don't pay for those calls. If the tracker is slow or
down, `status --session` is slow or missing a line, but `start` never fails
because of it.

`/start-session` runs four wfctl commands: `start`, `doctor --session`, `arch
context`, and `status --session`. Today it runs six: `start`, `doctor`, `arch
context`, `status --json`, `issue list`, and `change list`. `arch context` stays
because the accepted records bind the session's work, and the report lists only
their count.

## Verification

- A test that plain `wfctl status` makes no tracker call, with a backend that
  fails if called.
- A test that `status --session` on an issue branch prints the issue, parent,
  and PR lines, and on `main` prints none of them.
- A test that `status --session` writes nothing to the event log.
- The token measurement in #432's handoff, run before and after.

## Log

- 2026-11-02  proposed  — #432 level 3: which command prints the session-start
  report
