---
status: proposed
supersedes: a-human-grants-outward-facing-authority
---

# wfctl records outward actions and never gates them; the host's permission layer is the only gate

## Context

#280 shipped a grant — `wfctl start --allow-notify`, or the `authority:notify`
label — and without one `wfctl issue comment`, `create` and `label` refuse. It
was built to answer #131: an unattended run should finish the outward actions it
planned without stopping. What it did instead was add a stop.

- On #371 an attended session was refused after the maintainer had said "file
  it". The grant overrode the one person it exists to defer to, and that person
  could not lift it from where they sat.
- Filing #384, the issue that removes the grant, needed the grant.
- With the grant on, the same `wfctl issue create` was still refused by Claude
  Code's auto-mode classifier. The host gates these commands on its own, so the
  grant was a second refusal stacked on a first, never the only one.

The name is a proxy that fails both ways. It is called *notify* and gates three
tracker verbs; `git push` notifies nobody here and no wfctl verb performs it; a
board move reaches the tracker and is ungated; this repository has no watchers.
The maintainer: *"it makes not sense that an 'outward actions authorized' flag is
tied to notifications of a repo."*

Two things were built on the grant. `wfctl notify` records an action the run took
or declined, and refuses without a grant. `wfctl blocked` (#364) records a
refusal wfctl never saw, and exists as a separate verb only because `notify`'s
grant check stood in front of every other spelling. Since #371 merged,
`_restart.py` folds a late `notify-action` into the session summary before
`/clear`, which makes a recorded push the only trace a restarted session leaves
of one.

## Direct baseline

Keep the grant and default it to granted. No verb changes, no payload change, no
skill edits; the refusal simply never fires on a branch nobody turned it off on.

It fails the driver the grant was built for. A switch that is always on is still
a second permission system beside the host's, still named for an effect it does
not track, and still readable by three skills as a reason to skip work — and
`--deny-notify` would bring the deadlock back for anyone who used it.

## Decision

wfctl never refuses an action for reaching outside the repository. The host
agent's permission layer is the only gate on those actions. An attended session
asks before them exactly as its skills already say; an unattended run attempts
them, and a refusal from the host is reported rather than routed around.

wfctl keeps the half it can do and the host cannot: recording. Two verbs, both
the agent telling wfctl a fact wfctl could not observe:

```
wfctl report-action <action>                 this run took it
wfctl report-block  <action> --reason "…"    the host refused it; holds the step
```

For each action the most recent of the two decides whether a hold stands, so
taking the action lifts its own hold. That works only if both sides spell the
action the same way, so the name is fixed once: a tracker verb is
`issue-<verb>`, and `wfctl issue` records that name itself after every verb that
succeeds, `close` included. `report-action` is needed only for what no wfctl verb
performs, which today is a push.

`--allow-notify`, `--deny-notify`, `authority:notify`, `wfctl notify` (with its
`--declined`), `wfctl blocked` (with its `--clear`), the `notify` and
`notify_source` keys and the *outward actions authorized* fact are removed.

## Owns truth

The host owns *"may this command run, here, now?"*. wfctl cannot own it, because
it cannot compute the answer and cannot override it. The host decides from rules
and a classifier wfctl never sees, and it refuses before wfctl's process exists.
A second answer inside wfctl can only ever add refusals the host did not make,
and the person present can lift the host's but not wfctl's — the deadlock above.

wfctl owns *"what did this run do and fail to do outside the repo, and may the
pipeline advance past it?"*. The host cannot own it, because it keeps no record
that outlives the transcript. A refused command leaves no exit code, no event
and no artifact, and `/clear` or a restart discards the transcript. Only wfctl
writes somewhere that the next session and the pipeline read.

The agent supplies the two facts wfctl cannot observe — that a push happened,
and that the host refused something. That is the exception
`the-agent-reports-the-block-wfctl-never-saw` already makes, and this record
widens it by one verb. The ceiling is unchanged: tamper-evident, not
unforgeable. An agent could type `report-action` to lift its own hold, and it
could equally have typed `blocked --clear` before this record.

## Considered

- **The baseline: keep the grant, default it on.** Loses on the first driver,
  above. A default is not a removal. The switch keeps its readers and its name,
  and anyone who turns it off gets the deadlock back.
- **Narrow the grant to `create` alone.** It keeps the one refusal that deadlocked
  #384's own filing, and it is still a proxy: it names a verb list, not an
  effect, and the list was never the right one.
- **Remove `wfctl notify` outright, with no recorder**, as #384's body proposes.
  Sound when the issue was written. It loses on a fact that arrived afterwards:
  #371 folds a recorded push into the session summary before a restart clears the
  context, and with no recorder a push leaves no trace a restarted session can
  read. Tracker verbs would be unaffected, since `wfctl issue` writes its own.
- **Keep `blocked --clear` beside `report-action`.** Two spellings of "this
  action has now been taken". `--clear` existed because `notify`'s release was
  unreachable from a run that held no grant (#364's level-3 record), and that
  reason goes with the grant.
- **wfctl installs host permission rules (a `PreToolUse` hook) so the two layers
  agree.** It is the only option that prevents a host refusal instead of
  recording one. Not chosen: it rests on an unverified claim that a hook's allow
  overrides the host classifier, and installing rules into the host's layer is a
  person's act that #364 put outside its scope.

## Consequences

**The status payload loses two keys and a fact.** `pipeline-state-is-one-payload`
(accepted) makes the payload the contract, so `notify`, `notify_source` and the
fourth entry of `facts` leave every view in one change, never the JSON first.
`facts` goes from four entries to three, and any consumer indexing the fourth
breaks. The consumers in this repository are `end-session`,
`speckit-delivery-plan`, `speckit.analyze` and `scaffold-tracker`, and all four
change here.

**The CLI loses published verbs.** `wfctl notify`, `wfctl blocked` and the
`--allow-notify` flags are reached by installed skills and by agents, whose
calling code is not in this repository. A skill installed from an older wheel
fails with `No such command` until `install-skills` runs.

**The event log keeps its old names.** `report-action` writes `notify-action`,
and `report-block` writes `blocked`, so logs written before this change and
`_restart.py`'s reader go on working unchanged. The event names are storage and
the verb names are interface, so the two are allowed to differ.

**The action names change in the skills, not only in wfctl.** Today `wfctl issue
create` records `create` while the skills file a block as `issue-create`, and
`close` records nothing — so a successful retry never lifts its hold, and
`--clear` was the only exit. Removing `--clear` without fixing the names would
leave a hold nothing can lift.

Records affected:

- `a-human-grants-outward-facing-authority` → `superseded` by this record.
- `the-agent-reports-the-block-wfctl-never-saw` → its decision stands. The verb
  it chose is renamed here, and the `notify-refused` shape it reused no longer
  has a writer.
- `design/364-the-block-report-is-its-own-verb` → its title's reason is gone. The
  verb it justified survives under a new name, so a level-3 record on #384
  replaces its argument.
- `wfctl-classes-the-action-not-the-command` → its middle row, "prose, plus a
  check wherever one is cheap", loses its only check. The row's classification
  and its irreversible row are untouched.

`close` is still never gated. It was not gated before, and nothing here reaches
it.

## Log

- 2026-09-15  proposed    — #384 level 2; the grant refused the person it deferred
  to, and the host already gated every command it covered
