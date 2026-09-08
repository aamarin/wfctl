---
status: proposed
---

# A human grants outward-facing authority, and an agent may only narrow it

## Context

`wfctl-classes-the-action-not-the-command` (proposed) decides what class an
action falls in and gives the middle row — push, comment on an issue, open one,
add a label — a stated default of *refused*. It builds no way to relax that
default and says so in its own consequences. #240 is parked on the gap:
`/speckit.decompose` creates issues, so flipping it to advance unprompted needs
the row relaxed for one feature, and there is nothing to relax it with.

The thread that would have decided this was #131, closed into #127 on the bet
that one switch would serve both. Building #127 settled it the other way, twice
and independently: `1d4eb8e`'s message says the auto flags answer *"whether a
step advances unprompted rather than who approves a design"*, and
`approval-mode-is-stored-intent` (proposed) refused the tracker's board
transition on the same mode — *"Considered because it looks like the same kind
of per-feature setup and is not."* So #131's five principles survive on a closed
issue, and nothing carries them.

The half nobody has answered is not *whether* the row can be relaxed. It is who
may relax it. #127 answered that for design approval by accepting agent
self-grant, in as many words — `grant_auto_approve`'s docstring:

> an agent can grant itself the mode. Nothing available here prevents that — the
> event is what makes it visible afterwards.

#280 asks whether the same acceptance holds once the consequence leaves the
repo.

## Direct baseline

Extend #127's answer unchanged. Add a second flag to `wfctl start`, a second key
beside `auto_approve` in `mode.json`, and a second `mode` event; whoever runs the
command may set it, agent or human, and the event makes a self-grant legible
afterwards. No new concept, no new surface, and it inherits a shipped and tested
precedent rather than arguing a second one from scratch. It would satisfy #240
on its own.

What it leaves is a switch that carries no information. `/start-session` runs
`wfctl start` on every worktree spin-up and every handoff, and its
`allowed-tools` line carries `Bash(wfctl start*)`, whose glob admits any flag.
So if the agent may set the switch, it sets it as part of starting, and
*granted* becomes indistinguishable from *started*. For a class defined by
"other people are notified, and deleting it later does not un-notify them", the
instrument that remains is a log read after the notification has already gone
out.

## Decision

Granting outward-facing authority is a human act. Declining or narrowing it is
not.

A human may widen an agent's authority to the outward-facing class for one
feature branch, in advance. The agent may always decline that authority, or
narrow it for a particular action; it may never widen it, including its own.
#131's principle 2 is the source and is carried in rather than re-derived:

> A human grants authority in advance, and an agent may always decline it.
> Carried from #100's escalate-never-waive. An agent that can widen its own
> authority is the failure the rule exists to prevent.

**"In advance" is the load-bearing phrase, and it is what makes the rule cost
nothing.** The grant is a setup-time act — typed once, before the run that uses
it — not a prompt the run stops at. The human sets it and leaves. An unattended
run under this rule stops exactly as often as one under the baseline: never. The
objection that a human-only grant blocks automation is an objection to a gate at
run time, and there is no gate at run time here.

Enforcement is **tamper-evident, not unforgeable**, and this record claims
nothing stronger. The state dir is writable by the agent that reads it; nothing
here makes the value unwritable, and `approval-mode-is-stored-intent` already
established that no wfctl verb is out of an agent's reach.
`wfctl-runs-the-verification` (accepted) set that ceiling for this repo
deliberately — *"tamper-evident rather than unforgeable, which is the honest
ceiling for a local CLI"* — and this is the same ceiling, not a weaker one.
What the rule buys is that the default of refused means something, that a skill
can be written to read the grant and refuse without one, and that a grant with
no human near it is legible after the fact as a violation rather than as a
second legitimate way to set it.

## Owns truth

wfctl owns *"is this feature branch granted outward-facing authority, and who
granted it?"*.

The agent cannot own the first half, for `wfctl-runs-the-verification`'s reason:
an actor authorizing its own action is making the claim the authorization exists
to check. The failure mode is not dishonesty — a self-grant made in perfectly
good faith is still a switch the constrained party flipped, and a switch the
constrained party can flip is not evidence that anyone else agreed. It is a
receipt, and this row's consequence has already reached people by the time a
receipt is read.

The harness cannot own it either. Permission rules match a command string
against a prefix, so the question they answer is "did someone list `git push`" —
which is per repo and per agent config, silent about which feature and which
agent, and answered identically for a branch nobody has looked at and a branch a
human deliberately handed over. "May *this feature's* agent notify people who
are not in the repo" has no expression in any of them. The surface it would have
to gate is not a command set in the first place: `gh issue comment`, a REST call
through `curl`, an MCP tool and a skill instructing a second agent are one act
under four strings.

The second half — *who* — is owned by rule rather than by observation, and the
distinction is the point. `approval-mode-is-stored-intent` already found that
nothing observable separates a person typing the flag from an agent running it:
both arrive as one process with the same argv, and a TTY check answers only the
half that was never in doubt. That finding is not reversed here. What changes is
what follows from it. There, the conclusion was to record the grant and let the
reader draw their own conclusion, because both setters were legitimate. Here
only one is, so the value being true *is* the claim that a human set it, and a
grant no human made is a violation with a rule to name it rather than an
ambiguity. An event with no rule beside it says something happened; the same
event beside this record says what was broken.

## Considered

- **The baseline: agent may self-grant, and the event log makes it visible.**
  Its strongest form is not laxity, and it deserves stating: a human started this
  session, pointed it at this feature, and left it running, so authority to do
  the feature's work is already implied — a flag the agent then sets is
  bookkeeping on a decision made upstairs. That conflation is precisely what
  #280 exists to break apart. Starting a session is a decision about a piece of
  work; granting the outward-facing row is a decision about people who are not
  in the repo, and nothing about the first implies the second. #127's trade is
  right where #127 made it: the cost of a bad self-grant there is a design
  decision recorded without a human reading it, and the PR is where that gets
  read. The cost here is a notification that deleting later does not un-notify,
  and there is no later reader who can undo it. #280's own body says as much —
  *"outward-facing actions may not warrant the same acceptance."*
- **Human-only, with no decline clause.** Rejected. An agent that reaches
  something it should not do has to be able to narrow the authority it holds,
  and #131 says so directly: *"an agent may always decline it."*
  Escalate-never-waive is asymmetric on purpose, and a rule that constrains
  widening has to leave narrowing free or it stops being that rule and becomes
  an instruction to use everything granted.
- **A second global default rather than a per-feature grant.** Rejected on #131
  principle 5 — the unit is the piece of work, because that is the unit the human
  is or is not invested in. It is also the one shape under which "in advance"
  stops being free: set once, a global grant applies to work nobody has looked at
  yet, which is the thing the phrase was doing the work of preventing. At fleet
  scale the escape hatch is not a global flag but a move of the setting point:
  the grant goes to whatever launches the worktrees, still human, still in
  advance, still one value per feature.
- **Folding this into `--auto-approve`.** Rejected, and it is a door two
  arguments already closed from opposite sides — `1d4eb8e`'s commit message and
  `approval-mode-is-stored-intent`'s last considered entry, neither of which was
  written with this issue in view. #127's flag answers where design approval
  happens. This answers whether an action may reach people outside the repo. A
  feature can want either without wanting the other, and a run that answers its
  own design gates into a record is exactly as ready to be reviewed as one that
  did not.
- **Asking at the moment of the action instead of granting in advance.** This is
  the attended run, it is what happens today, and it is sound — it is also the
  thing #240 exists to remove, and it cannot serve a batch of small-fry issues
  worked overnight. It loses on fit, not on merit.

## Consequences

**#240 is not unblocked by this record.** The question it was parked on now has
an answer, which unblocks it in principle; the parked branch still needs a grant
to read, and this record decides who may set one rather than where it is stored
or what it is called. PR #282's review panel caught exactly this overstatement in
the sibling record, and it is not repeated here.

Storage is deliberately not decided — a second field on `mode.json` against a
second file is a real design call with arguments on both sides. One verified
fact bears on it: `grant_auto_approve` writes `{"auto_approve": granted}` through
`write_json_atomic`, which replaces the file wholesale, so a second key on
`mode.json` needs a read-merge-write or whichever grant runs second clears the
first. That is a constraint the design pass has to satisfy, not an argument for
either shape.

The grant needs a surface a human would plausibly be the one to use, and
`wfctl start` is not obviously it — `/start-session` runs it, so in practice an
agent runs it far more often than a person does. The surface cannot be chosen
for inaccessibility, because `approval-mode-is-stored-intent` already established
there is no wfctl verb an agent cannot reach; it is chosen for whether a human
would ever type it deliberately. `.workmux.yaml`'s `post_create` is the moment a
worktree is created and looks like the natural home, and is not one: it is
committed to the repo, so a grant written there would be repo-wide and set by a
file rather than by a person, which are the two properties this record refuses.

**The surface this record points the design pass at is the tracker, with a local
command as the degradation under it.** A label on the feature's issue is set
where triage already happens, and *may this one run unattended* is a triage
judgment about a piece of work rather than a runtime one. It is per feature by
construction — the issue is the feature — and the verbs exist: `label` is `gh
issue edit {id} --{action}-label {label}`, and `view` already returns what is
set.

It also narrows, for this one surface, what the section above conceded. Adding a
label is itself in the row being gated, so an agent holding no grant may not set
one through wfctl, and the grant comes to live inside the authority it confers.
Not unforgeable — `gh` is reachable directly by anything that can run a command,
and the ceiling above still holds — but the self-grant path stops being the same
command that starts the session, which is the specific collapse the baseline was
rejected for.

The degradation is not optional. wfctl supports a repo with no tracker
configured, where `wfctl issue` no-ops on the absent backend, so a grant readable
only from a tracker is unreadable in exactly those repos. A local setter has to
exist beneath it, and is the smaller of the two to build first.

`post_create`'s `wfctl issue start` is a tracker write taken unprompted on every
worktree creation, and it is not a violation of this record.
`wfctl-classes-the-action-not-the-command` places an action by who is notified,
and a Projects v2 `Status` field write leaves no entry on the issue timeline and
notifies nobody — `wfctl issue stop` moves it back. It reads as a violation only
under *outward-facing means it leaves the machine*, which that record
deliberately does not say, and this is the case that pulls the two readings
apart: a label on the same issue does reach the timeline, which is why the
surface above sits inside the row it gates.

Nothing reads the grant mechanically until something is built to, so between
this record and #240's design pass the rule is prose. And while this record is
`proposed`, `wfctl arch context` does not project it — the projection is
`accepted` records only — so it reaches a reader through the file rather than
through the contract.

## Log

- 2026-09-07  proposed    — #280 level 2; #131's principle 2 had no home, and the
  middle row had no grant
