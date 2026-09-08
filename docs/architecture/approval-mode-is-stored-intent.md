---
status: proposed
---

# The approval mode is stored intent, and the payload carries it beside inference

## Context

`wfctl status` reports one payload and every field on it is computed from
artifacts at the moment of the read:

| Field | Where it comes from |
| --- | --- |
| `steps` | ten branches of `_infer_steps` over the spec artifacts |
| `current` | the same inference |
| `session_started` | folds `events.jsonl` |
| `next_command` | `_STEPS[step][0]`, a literal in the table |
| `auto` | `_STEPS[step][1]`, likewise |

#127 adds a per-feature switch that moves where design approval happens — with
it off, the agent stops at each `design-levels` gate; with it on, the agent
states the gate's answer into a record and descends, and the approval moves to
the PR. The value that switch sets would be the first thing on that payload that
no artifact can produce. It is intent, and nothing on disk implies it.

`session-state-is-re-derived` (accepted) anticipates this and does not object to
storing it — what a session file holds is what re-derivation cannot reach. But
it names exactly one occupant of that carve-out, *"the handoff prose a human or
agent wrote deliberately."* A mode is not prose. It is a short machine-read
value, which is the category that record was written to empty out: `current.json`
held the branch, the issue and the step, every one of which git and the spec
tree answered live, and the file could disagree with all three.

#127's scope item 1 still names `current.json` as the home. That file no longer
exists — `_remove_session_fossils` (`cli.py:99`) unlinks it from any state dir
that still has one, on every command that resolves a state dir.

## Direct baseline

Store nothing. A human types "run this unattended" into the session, and the
agent obeys for as long as it remembers. No file, no flag, no payload field, and
the mode is a fact about a conversation.

It is a real option and it is what happens today if you simply ask. It loses on
one property: the instruction and the feature have different lifetimes.
`speckit-orchestrate` drives a feature across the whole pipeline, and a design
pass that begins at `brainstorm` and ends at a PR routinely spans a `/clear` —
`start-session` and `end-session` exist because it does. The mode has to survive
a boundary the instruction does not, and an agent that remembers it across one
has a memory rather than a fact.

The narrower half is mechanical: `speckit-orchestrate` branches on
`wfctl status --json`. An instruction living in a conversation cannot reach a
payload, so the baseline can change what the agent believes and never what the
tooling reports.

## Decision

wfctl stores the approval mode as a named value in the session state dir, and
`PipelineReport` carries it beside the inferred fields. It is written when
`wfctl start --auto-approve` runs, and read on every subsequent report. Each
write also appends an event, for the reason under **Owns truth**: the value
answers *what mode is this feature in*, and the event answers *who put it there*.

`start` gets the flag because nothing is closer, not because it is the natural
home. The tempting argument — that `start` is where a human deliberately opens a
feature, so a second deliberate choice belongs beside the first — does not
survive contact with how `start` is actually invoked. `/start-session` runs it,
`/start-session` runs on every worktree spin-up and every handoff, and its
`allowed-tools` line carries `Bash(wfctl start*)`, whose glob admits any flag. In
practice an agent runs this command far more often than a person does.

That makes the flag self-grantable, and no alternative surface fixes it. A
dedicated verb was the obvious escape and it fails twice: `wfctl config -u`
renders correctly and lies about its scope, because every tool a reader arrives
with — git, npm, gh — spells repo-or-global persistence `config`; and any verb at
all is equally reachable, since this machine's settings allow `Bash(wfctl *)`
outright. There is no wfctl command an agent cannot run unprompted, so choosing
one for its inaccessibility is choosing an illusion.

What replaces prevention is evidence, which is #100's shape rather than a new
one: the grant is recorded, so a run that granted itself autonomy says so in its
own log.

`start` therefore becomes the first per-feature setting point, and founds that
category with exactly one member. No shape is built for the second: per-feature
configuration does not otherwise exist — the repo's settings live in
`.wf-skills-manifest.json` and the six `WFCTL_*` overrides are resolved before a
state dir exists, so neither can move here — and a format, a precedence order
and a read path designed against a sample of one would be guesses the second
setting is what tests.

`end` does not clear the mode. Bracket symmetry argues it should; the issue's
premise overrules — a run pointed at eight small-fry issues overnight spans
session boundaries, and a mode that evaporates at `end` cannot serve one.

The payload gains a field whose provenance differs from every other field on it.
That asymmetry is the decision, not an accident of it: a mode nothing can infer
must still reach the same views, because `pipeline-state-is-one-payload`
(accepted) makes the payload the only route to `status` and `resume` both.

## Owns truth

wfctl owns *"which approval mode is this feature in, and when was it granted?"*.

The agent cannot compute either half. There is no artifact to infer the mode
from — that is what makes it intent rather than state — and the only copy the
agent could otherwise hold is a memory of a turn in a conversation that may since
have been cleared, in a worktree another session may have changed.
`session-state-is-re-derived` makes exactly this argument about the fields it
deleted; the conclusion here runs the other way for the same reason. Those fields
had live answers on disk and the file could go stale against them. This one has
no live answer anywhere, so there is nothing for it to drift from. Rot requires a
truth to drift from.

The second half is owned for a different reason, and it is the half #127 does not
contain. #100 fixes escalate-never-waive — an agent may raise the bar and never
lower it — and the surface analysis above shows nothing enforces that here. An
agent cannot be the witness to its own grant: a self-report is exactly the
unfalsifiable claim `wfctl-runs-the-verification` (accepted) already removes from
the agent's side for the verification verdict. So wfctl writes the grant into the
log itself, at the moment it happens.

*Who* granted it is deliberately not claimed. Nothing observable separates a
person typing the flag from an agent running it — both arrive as one process with
the same argv, and a TTY check answers only the half that was never in doubt. The
event records that autonomy was granted and when, in a log that already carries
`start`, `next` and `resume` around it, and leaves the reader to draw the
conclusion. Naming a setter it cannot observe is the move #70 removed from
`wfctl end`, and it is not reintroduced here for a field that would look more
authoritative with a name on it.

**Neither side owns *"did the agent honour the mode?"***. It is not observable.
No artifact records a pause, so a run that stopped when it should not have and a
run that did not stop when it should are both invisible after the fact, whichever
side is asked. `a-rule-is-expressed-as-a-check` (accepted) settles what follows:
a rule whose violation is not visible in an artifact the work already produces
stays prose delivered at the moment it binds, and that is not a defect. The mode
is therefore advisory to the skills that read it, deliberately.

What *is* observable is whether the records exist, and `design_block` already
holds a design step that produced none. That check is unchanged by this record
and by #127, in both modes — what changed under #287 is where it reports, not
whether it stops.

## Considered

- **An event in `events.jsonl` alone, the current value read by folding the
  log.** Rejected as the sole store, and adopted as half of one. Against #127 as
  written it loses on fit: nothing in its five scope items or four comments asks
  when the mode was set or what it was before, and the issue's own principle —
  *"the human sets the switch, always in advance"* — makes it a single write, at
  which point the log and a file hold identical information. What reopens it is
  not in the issue: because an agent can set the flag, *who set it* becomes a
  question worth answering, and only the log answers it. So the log carries the
  grant and the file carries the value, and neither is asked the other's
  question.
- **A named file alone, with no event.** The shape a current value wants, and
  the one this record would have taken before the self-grant finding. It leaves
  an agent's grant indistinguishable from a human's, which is the single thing
  #100 asks a gate to make visible.
- **A field on the repo manifest.** Wrong cardinality. The mode is per-feature
  and the manifest is per-repo, so one value would set every branch at once —
  which is the batch workflow #127 defers to #86 behind its tracker abstraction,
  and explicitly does not want first.
- **A second flag on `_STEPS`.** Refused upstream:
  `brainstorm-is-one-step-with-addressable-levels` (proposed) says #127 and #151
  inherit the addressability problem and that neither may put it in `_STEPS`,
  and #127's own out-of-scope list separates the per-step `auto` axis from this
  per-feature one.
- **`current.json`, as #127 scope item 1 says.** Not available. The next command
  to resolve a state dir deletes it, and nothing would report that the mode had
  gone.
- **A dedicated verb, in `spec-root`'s show/set/clear shape.** Reads back and
  reverses cleanly, and it is the shape a settable value usually wants. It was
  rejected first on the reader's model — `spec-root` writes the *main checkout's*
  manifest because a repo-level value must outlive a worktree, and a second
  settable verb beside it writing per-branch state would teach two scopes under
  one grammar — and then again, decisively, on the permission finding: a new verb
  is no less reachable by an agent than `start` is, so it buys a verb and nothing
  else.
- **Teaching the mode by editing `brainstorming` and `idea-refine`.** The direct
  reading of #127 scope items 3 and 4, and it was written that way first. Both
  files are upstream-derived, and `vendor-upstream-skills` (accepted) says
  *"Prefer layering to editing"* and *"A file carrying a line is not evidence
  that editing it was fine"* — the prior in-place edits it lists predate the
  record and are grandfathered, not precedent. The failure it describes is this
  feature's exactly: the next upstream pull reverts the branch with no conflict,
  the attribution test still passes because it checks the line and not the
  divergence, and unattended runs quietly resume stopping while `design-levels`
  keeps telling them to descend. So the whole branch lives in
  `speckit.brainstorm.md` and `design-levels`, both wfctl's own, and the derived
  files stay unedited and unconditional beneath it.
- **Moving the tracker's board transition here too.** Considered because it looks
  like the same kind of per-feature setup and is not. `.workmux.yaml`'s
  `post_create` already runs `wfctl issue start`, paired with `wfctl issue stop`
  on `pre_remove`, and the column it moves answers *is this work in flight* —
  the worktree's lifetime, not the session's. Rehoming it here would key a
  worktree-scoped fact to a session-scoped command and strand its partner.

## Consequences

`PipelineReport.__post_init__` pairs `current`, `next_command` and `auto` as
None-together. The mode joins none of that group: it is defined whether or not a
step remains, so a finished story still reports the mode it ran under. It needs a
default, because two tests construct `PipelineReport` directly with all five of
today's fields.

The file's path and shape belong to `_session`, not `_io`.
`io-owns-durability-not-domain-files` (proposed) is heading the other way with
`load_agentconfig` — the one function in `_io` that names a state-dir file, dead
with zero callers — and a new reader added beside it would be a second thing for
that move to unpick. `verify.json` is the pattern to copy instead: a named JSON
file in the state dir, one writer, one reader, its path and its field names
spelled in the domain module that means something by them.

The write cannot sit inside `start`'s `if report.session_started and not force`
early return, or `wfctl start --auto-approve` on a running session would report
"Already initialized" and drop the flag with nothing saying so.

`speckit.brainstorm.md` must gain `Bash(wfctl status*)`. Its `allowed-tools` line
does not carry it today, so the one command that has to read the mode cannot ask
for it, and the omission fails silently — the skill simply never sees a switch.

The mode is advisory prose, so the skill files are the implementation and every
pause has to be found rather than compiled. Four of them sit in the derived
files: `brainstorming`'s HARD-GATE, its one-question-at-a-time step, its
per-level approval and the `dot` flow that draws it, and — the one that would
otherwise strand the whole mode — `idea-refine`'s *"Only save if they confirm"*,
which guards the single write of `design.md`. A run that descends every gate and
stops there has done all the work and produced none of the artifact the reviewer
was going to read.

`design-levels` reads the mode itself rather than taking it from its caller. It
is description-triggered and fires outside `/speckit.brainstorm`, so a mode
passed down the wrapper would be absent exactly when the wrapper was not
involved; and every inconclusive read — key absent, command failing, no wfctl —
resolves to attended, because the mode is what removes a human and a read that
cannot establish it has to leave one in.

## Log

- 2026-09-07  proposed    — #127 level 2; the payload's first non-inferred field
