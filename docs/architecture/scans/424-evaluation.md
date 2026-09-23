# Evaluation scan — #424

An `evaluation` — the kind of scan file with no pipeline step behind it. This
branch ran none; the thing needing to reach a reviewer is an experiment's result.
`writing-a-scan-file` governs what a section carries and is followed here. The
one thing it delegates to "the wrapper that sent you here" is the coverage rows,
and no wrapper sent this one, so the rows below are this evaluation's own.

**Passes A through G were named before the run; H, I and J were not.** They are
marked as such in the table, because a coverage table's job is to show what a run
set out to cover — that is what makes an unreached pass visible — and a row
added afterwards cannot do that job. Removing them instead would hide findings 9 and 10
from the one place a reader checks for scope, so they are kept and labelled
rather than kept and passed off.

## Session 2026-09-22

- Verdict: **satisfied**
- Scope: #424's first half — install and evaluate `agent-dashboard` — was
  withdrawn in the issue's own comment of 2026-09-20 and was not run.
  `agent-dashboard` was never installed. What was run is the narrowed
  experiment that comment leaves standing.
- Ran against: 5 live `mode: session` worktrees and 12 tmux sessions in the first
  run; 11 sessions when the second run's mirror connected, and 12 again before it
  ended — a sixth worktree was created mid-run, which is finding 10's subject.
- Versions: cmux 0.64.25 (106), tmux 3.6a, workmux 0.1.211, wfctl 0.20.0.
- Detail: no `FEATURE_DIR` artifact — this branch ran no pipeline step, so
  there is no fuller document for this file to point at. Everything the
  evaluation established is here.

The experiment, as #424's comment states it:

> Can one cmux workspace attach to one existing workmux-owned tmux session and
> present `wfctl status` without taking ownership of that session?

**The answer is yes, and it took two runs to get there.** The first run
surveyed cmux's *local* tmux integration, which cannot do it — settled in
findings 1 and 2 — and left the verdict at `inconclusive` because cmux's second
integration, `ssh-tmux`, was not reachable on this machine. The machine's owner
then enabled Remote Login and cmux's "Remote tmux" beta setting, and the second
run exercised it. Finding 8 is that run: the mirror presents each workmux-owned
session it finds at connect time as a workspace, correlates on the session name,
takes no ownership, and carries a line of wfctl's own output on the row. What it
does *not* present is a session created afterwards, which is finding 10; and of
the ten rows read, five carry the wrong directory, which is finding 9.

**This section holds both runs**, because a second scan finding something is
only meaningful given what the first one found. Findings 1 through 7 are the
first run and stand as written; findings 8, 9 and 10 are the second. Where the
second contradicts the first, the first is left in place and the later finding
says so — a struck claim is the one thing a reader most needs to see, and
deleting it leaves nothing to disagree with. Finding 9 has since had to apply
that rule to itself.

### Coverage

| Pass | Status |
| --- | --- |
| A · `local-tmux` — can it see a workmux-owned session? | Clear (it cannot; finding 1) |
| B · `local-tmux` — does it act on one it was not given? | Clear (it cannot see one to act on; finding 2) |
| C · `ssh-tmux` / `mosh-tmux` — the control-mode path | Clear (it mirrors without owning; findings 3, 8) |
| D · Presenting `wfctl status` in a row | Clear (demonstrated on a mirrored row; findings 4, 8) |
| E · A sidebar as the presentation surface | Clear (it cannot fetch; finding 5) |
| F · `attention` as a supervisory column | Clear (finding 6) |
| G · The payload as a consumed contract across worktrees | Outstanding (finding 7) |
| H · What a mirrored row reports about its own worktree | Outstanding (finding 9) — **pass added after the run** |
| I · Whether a session created after connect gets a row | Outstanding (finding 10) — **pass added after the run** |
| J · Whether anything already writes wfctl status to a row | Outstanding (finding 11) — **pass added after the run** |

Pass C held the verdict at `inconclusive` through the first run, as `Deferred`:
nothing had been learned by running it, only that it could not be run here
without a change to this machine that was not an agent's to make. The second run
had that change and closes it.

Passes H and I are the second run's own, added when it found things the first run
had no way to see. A pass named after the fact is what the "name your rows before
you start" rule exists to prevent, so both are marked as what they are: the mirror
was not expected to say anything about a worktree beyond its name, and it does
(H); and the mirror was assumed to track the server it mirrors, which was never
stated as a pass because it was never in doubt (I). This file's opening says its
rows were named before it started. That was true of A through G and is not true
of H and I, which is the cost of an evaluation that kept running after its own
coverage map was written.

**The verdict stays `satisfied` with three of nine rows Outstanding, and the two
are not in tension.** `satisfied` answers #424's question, which is about *one*
workspace attaching to *one* session and presenting `wfctl status` without taking
ownership — finding 8 answers that end to end. H and I are about the *set* of
rows and what each says beyond its name, which that question never asked. A
reader wanting "is the screen good enough to rely on" is asking something this
verdict does not answer, and findings 9 and 10 are where that answer lives.

## The handoff this branch carried was written against the withdrawn half

The handoff in the state dir instructs an evaluation of `agent-dashboard` and
names a negative result as a real deliverable. The issue comment predates it by
two days and withdraws that half outright — "`agent-dashboard` stays useful
prior art … but the project does not need a second orchestration plane beside
wfctl, Spec Kit, workmux and tmux. No new wfctl dashboard either."

Recorded here because the handoff file is not a durable artifact, and the next
reader of this branch will otherwise find a change whose scope does not match
the prose that produced it.

## Finding 1 — `local-tmux` runs its own server, so a workmux-owned session is invisible to it

Two servers, no overlap:

| | socket | sessions |
| --- | --- | --- |
| workmux's | `/private/tmp/tmux-501/default` | 12 |
| cmux's `local-tmux` | `~/.cmux/local-tmux/server.sock` | 0 |

The twelve are `0-0`, `pfms__pfms-specs`, five `pfms__<feature>` and five
`wfctl__<feature>`. Only the ten feature sessions belong to a workmux
environment. `0-0` and `pfms__pfms-specs` do not — and `pfms__pfms-specs` wears
a workmux prefix while corresponding to no feature worktree, which is the
second and better example of the hazard
`a-client-attaches-to-a-runtime-it-never-owns` names in its own Context: a name
carrying the prefix is not evidence that workmux created the thing wearing it.

`local-tmux status` was asked about the session this evaluation was running
inside — live on the default socket at that moment:

```
$ cmux local-tmux status wfctl__424-observer-dashboard-eval --json
Error: local-tmux session not found: wfctl__424-observer-dashboard-eval
```

`attach` gives the same answer. This is not a configuration gap that a flag
closes: no `local-tmux` verb takes a socket path or an external session, and
upstream `docs/local-tmux.md` describes the profile as an owner rather than a
client — "`cmux local-tmux` is an explicit, opt-in persistence profile for local
terminal processes. It starts one user-owned tmux server under
`~/.cmux/local-tmux`" (L3-4), and "The owner is a local tmux server, not the
cmux GUI" (L60).

One qualification on "holding sessions it started": the same doc says `list`
"reports unmanaged sessions found on the profile socket" (L85). Unmanaged, but
still on cmux's own socket — which is the point, and not workmux's.

**This settles an open item in the record.** `a-client-attaches-to-a-runtime-it-never-owns`
records its own Direct baseline as "claimed by cmux's `docs/local-tmux.md` …
unverified here, because cmux is not installed" (L64). cmux is installed now and
the claim holds.

## Finding 2 — `local-tmux attach` refuses; `local-tmux start` collides

The record — `status: proposed`, so a constraint this project has drawn and not
yet accepted, and absent from `wfctl arch context` — asks three things of a
presentation client. One is passed vacuously and two are never exercised:

| The record asks | cmux does | |
| --- | --- | --- |
| never create, recreate, rename or destroy a workmux-owned runtime | never touches it — it cannot see it | passed, vacuously |
| where workmux reports an environment and tmux has no session, surface and stop | never evaluates that condition; `attach` errors because its own registry is empty | not exercised |
| correlate on workmux handle or worktree path, never a client-assigned id | assigns a UUID to a session it started itself; never presented a workmux-owned one, so never correlated a view to a feature at all | not exercised |

Row two is not a pass. The recovery protocol fires where *workmux reports an
environment and tmux has no session*; what was observed is a session missing
from cmux's registry while the tmux session exists — finding 1 restated, not
the protocol answered.

Row three is not a failure either, and calling it one was the headline verdict's
error repeated inside the table. The clause governs the key a client uses to
correlate *its view* to *a feature*; the transcript below shows cmux naming a
session it created, carrying a name and a UUID side by side. A UUID in a registry
is a data-model fact, not a correlation key exercised against a workmux-owned
runtime — and `local-tmux` never presented one. Which key a mirrored workspace
would correlate on is the `ssh-tmux` question, finding 3's, and it is open.

The hazard that remains is a name collision rather than a mutation. Asked to
start a session under a name already live on the default server, cmux creates
its own and reports success:

```
$ cmux local-tmux start wfctl__424-observer-dashboard-eval --cwd <this worktree> --detached
OK session=wfctl__424-observer-dashboard-eval id=FB39F4BA-…  state=detached
   socket=/Users/andremarin/.cmux/local-tmux/server.sock

$ tmux list-sessions | grep 424           # workmux's, untouched
wfctl__424-observer-dashboard-eval: 2 windows (created Tue Sep 22 08:45:00 2026)
```

The probe deliberately took the live handle's name rather than a throwaway,
because the name is what was under test. Two sessions, one name, two servers,
neither aware of the other. Nothing was destroyed and the invariant as written
was not broken — and a human reading either surface still cannot answer "is this
feature's runtime alive?" without first being told which server they are looking
at. The probe session was closed (`cmux local-tmux close`); workmux's session is
intact and the cmux registry is back to zero.

Worth a follow-up line on the record: a client that *names* a runtime it did not
create has taken the name, which is the part of ownership that survives having
taken none of the powers.

## Finding 3 — the path that might answer yes was not reachable in the first run

`cmux ssh-tmux` is a second integration, and it does the thing finding 1 says
`local-tmux` cannot:

> Mirror a remote host's tmux sessions into the current window's sidebar over
> SSH tmux control mode (tmux -CC). Each session becomes a workspace, each
> window a tab, and each multi-pane window a native split. Requires the
> "Remote tmux" beta setting.

A tmux server reached over SSH is one cmux neither created nor owns, and
`localhost` is a host like any other — so `cmux ssh-tmux localhost` points that
machinery at the default socket, where workmux's sessions live. Control mode
attaches as a *client*, which is the shape the record's invariant asks for.
`cmux mosh-tmux --session <name>` is a narrower form of the same idea.

It was not run, for two reasons that are the machine's rather than the tool's:

```
$ ssh -o BatchMode=yes -o ConnectTimeout=5 localhost true
ssh: connect to host localhost port 22: Connection refused
```

Remote Login is off on this Mac, and turning it on opens an SSH listener on a
personal machine — a security posture change that belongs to whoever owns the
machine, not to an evaluation. The second reason is the "Remote tmux" beta
setting, which is a cmux Settings change and cheap by comparison.

**That held the verdict at `inconclusive` rather than `unsatisfied`** for the
duration of the first run: the local path was closed and the control-mode path
untested, which is not the same as cmux being unable to do it. Two questions
stayed open, both cheap to answer once Remote Login was on:

- Does a mirrored workspace carry cmux's attention ring, unread badge and status
  lane, or are those keyed to surfaces cmux created?
- Control mode can issue `kill-session`. Does cmux's mirror ever do so — on
  workspace close, on disconnect, on reconcile? That is the record's invariant
  asked of the one path that can actually break it.

Both are answered in finding 8. This finding is left as written rather than
folded into that one, because what it records is why an evaluation stopped where
it did, and that reason is still true of any machine with Remote Login off.

## Finding 4 — the state-carrying verbs are gated; the `local-tmux` family is not

Every cmux verb that would put wfctl state in a row — `set-status`,
`list-status`, `set-progress`, `log`, `todo`, `notify`, `new-workspace
--command` — goes through the Unix socket, and the socket refuses an outside
caller:

```
$ cmux list-workspaces
Error: ERROR: Access denied - only processes started inside cmux can connect
```

The documented alternatives are `--password`, `CMUX_SOCKET_PASSWORD`, or a
password saved in Settings. So an adapter is either a child of a cmux pane or a
process holding a shared secret. Neither is fatal; both are setup this repo
would own.

The gate is narrower than it first appears, and finding 2's own transcript is
the proof: every `local-tmux` verb ran from an ordinary shell with no cmux
ancestry and no `CMUX_*` in the environment, as did `cmux <path>`, `cmux --help`
and `cmux docs`. `docs/local-tmux.md` says so outright — "A session can also be
attached directly from a non-cmux terminal" (L21). What is gated is the state
the presentation layer holds, which is exactly the part a join would need.

## Finding 5 — a custom sidebar cannot fetch what it would display

The obvious home for a joined row is cmux's custom sidebar — a file in
`~/.config/cmux/sidebars/`, refreshed about once a second. It cannot do the job:
interpreted sidebars "cannot import frameworks or start child processes", and
"the context has no filesystem, network, or timers."

So the sidebar cannot run `wfctl status --json`. Something outside has to run it
and push the result in over the socket, which is finding 4 again. A compiled
ExtensionKit extension can run external tools, inside the macOS App Sandbox — a
different and much larger piece of work.

## Finding 6 — `attention` is usable as shipped, and answers a different question than the lamp it resembles

Joined across every live worktree, reading each one's own `wfctl status --json`:

| worktree | runtime | payload version | `current` | `attention` |
| --- | --- | --- | --- | --- |
| 397-handoff-records-work-in-flight | detached | 1.0 | brainstorm | `null` |
| 419-misfiled-record-check | detached | *absent* | brainstorm | *key absent* |
| 424-observer-dashboard-eval | detached | 1.0 | brainstorm | `null` |
| 425-restart-holds-on-child-work | attached | 1.0 | brainstorm | `null` |
| 426-overlay-boundary-spike | detached | 1.0 | brainstorm | `null` |

The `runtime` column is a snapshot and has already inverted since; it is in the
table to show that the column *varies*, which is the one thing the other two
columns did not do.

`attention` was null on every worktree that has the field. That is not a defect.
`_derive_attention` fires on three conditions, and on this branch two of the
three were unreachable rather than merely absent: this repo's `wfctl.json`
declares no `steps`, so no pass can be outstanding and `manual` cannot fire at
all; and no state dir holds a `report-block` event, so `blocked` had nothing to
report. Only `stalled` was live and did not trigger.

What it means for a supervisory row is the finding. #424's wanted view has a
`NEEDS HUMAN` lamp, and the thing that lamp is for — an agent sitting at a
prompt right now — is not one of `attention`'s three conditions, and should not
become one. `attention` says *the evidence shows a person is wanted*; the ring
in a terminal dashboard says *this pane is blocked on input*. A worktree can be
either without being the other:

```
agent waiting at a permission prompt
  └─► runtime: WAITING        attention: null
      (nothing is recorded yet — the block has not been reported)

agent exited cleanly after `wfctl report-block push`
  └─► runtime: IDLE           attention: blocked
      (nothing is running, and a person is still wanted)
```

Two columns, never one verdict. The evaluation found no pressure to collapse
them — if anything the null column makes the pressure worse, because a uniform
`attention` invites a designer to drop it and let the runtime state stand alone.

Second observation from the same table: `current` was `brainstorm` for all five,
because none of these branches has a spec dir and this repo deliberately routes
most changes around the pipeline. As a supervisory column it distinguished
nothing across the whole sample. A row that carried only `current` would look
populated and say nothing.

## Finding 7 — the contract version cannot identify a payload older than itself

`419-misfiled-record-check` branched before #441 and its own source tree
produces a payload with **neither** `attention` nor `version`. A naive adapter
raises `KeyError`; one reading `payload.get("version")` gets `None`.

A supervisory view spans worktrees at different base commits by construction —
that is what makes it supervisory — so this is the normal case, not an edge. The
rule an adapter has to encode is that an absent `version` means *older than
1.0*, and it has to encode it as a constant rather than read it from anywhere.
`wfctl/contracts/status-payload.json` was not touched.

This finding and finding 6's consumer-facing half are filed as **#452**. They
were first written down as "for #423's follow-up", which was wrong twice over:
#423 is closed, and it named no successor — so both would have been parked
where nothing picks them up.

## Finding 8 — the mirror attaches without owning, and a wfctl line reaches the row

The machine's owner enabled Remote Login and cmux's "Remote tmux" beta setting —
cmux Settings → Beta Features → Remote tmux, a GUI toggle with no key in
`cmux.json` and none in the app's `defaults` — and `cmux ssh-tmux localhost`,
run from a terminal inside cmux, produced:

```
Connecting to localhost…
Authenticated; opening remote tmux mirror for localhost…
OK host=localhost workspaces=11 window=C78A7B17-4E1B-4767-A531-71AA332B7B3E
```

Eleven sessions on the default socket, eleven workspaces in the sidebar. This is
the thing finding 1 says `local-tmux` cannot do, done by the other integration.

**Ownership was not taken, which is the record's invariant.** Measured before
and after, from the tmux side:

| What was checked | Before | After |
| --- | --- | --- |
| sessions on the default server | 11 | 11 |
| `session_created` on each | — | unchanged on all 11 |
| `wfctl__426-overlay-boundary-spike` | `attached=0` | `attached=0` |

The detached session is the one that carries the weight. A client that reconciles
by recreating what it cannot see would have attached or replaced it; the mirror
left it detached, which is what a client that owns nothing does. No
`kill-session` was issued on any path exercised here — opening the mirror,
selecting workspaces, leaving it open across the rest of this session.

**The correlation key is the tmux session name, which is the workmux handle.**
`cmux workspace list --id-format both` labels every mirrored workspace with the
session name and nothing else:

```
  workspace:2 F194C2CE-…  wfctl__426-overlay-boundary-spike
* workspace:3 21F91121-…  wfctl__425-restart-holds-on-child-work  [selected]
  workspace:4 6DB3275D-…  wfctl__424-observer-dashboard-eval
```

A UUID exists per workspace, as it does for every cmux workspace. What the record
forbids is correlating *to a feature* by a client-assigned id, and the name is
what carries that correlation here — `wfctl__<handle>`, which is workmux's own.
The one local workspace in the same window is labelled by path instead, which is
the visible difference between a workspace cmux created and one it is mirroring.

**A line of wfctl's own output reaches the row.** An OSC 9 notification written
to a mirrored session's idle pane arrives in cmux's sidebar as that workspace's
subtitle, and the workspace sorts to the top of the list:

```
$ uv run wfctl status --json | …                 # in the 424 worktree
#424 · brainstorm · next /speckit.brainstorm

$ printf '\033]9;#424 · brainstorm · next /speckit.brainstorm\007' > /dev/ttys034
```

rendered as:

```
wfctl__424-observer-dashboard-eval
#424 · brainstorm · next /speckit.brainstorm
~/Development/wfctl/wt/424-observer-dashboard-e…
```

That is #424's question answered end to end: wfctl's own verdict, on a row that
names a workmux handle, in a client that owns none of it. It was done with a
`printf` into a tty and nothing was committed — the pane wrote its own row, which
is the one shape that needs no joiner and also the one that cannot scale, since a
pane running an agent is not going to describe itself on a schedule.

**The mirror is a client with a keyboard, not a view.** Each tmux window arrives
as a tab named after it — `term`, `deploy`, `agent` — and the `agent` tab renders
the running agent's live output. It also accepts input, which reaches the real
pane. Observed by typing `tmux a` into a mirrored `term` tab and getting tmux's
own refusal back:

```
sessions should be nested with care, unset $TMUX to force
```

That refusal is the evidence, not the failure: `$TMUX` is set inside a mirrored
pane, so the pane is a genuine client of the session rather than a rendering of
one, and `tmux a` there asks tmux to attach a session to itself.

This is worth stating because the record's invariant is about what a client may
*do* to a runtime, and it is written in terms of session lifecycle — create,
recreate, rename, destroy. A client that issues none of those and still puts a
keyboard on every agent's pane satisfies the invariant as written. Whether that
is the whole of what the invariant meant to protect is a question for the record,
not for this scan: a supervisory screen answering "which worktree needs me?" with
eleven live input surfaces behind it is a different object from a dashboard, and
the difference does not appear anywhere in the clause it passes.

**What this does not establish.** The escape was written directly to the pane's
tty rather than emitted by a program running in it, so nothing here shows that an
agent's own OSC notifications survive the control-mode hop; `allow-passthrough`
governs that and was not varied. The mirror was also exercised over `localhost`
only, where the SSH hop is degenerate.

## Finding 9 — five of the ten rows read print a directory that is not theirs

Of the eleven mirrored workspaces finding 8 records, **ten were read and five of
those ten print a path that is not theirs.** All five print the same one. The
eleventh, `0-0`, was below the fold of the capture this was read from and is not
counted in either number.

| Sidebar row | Path shown | `session_path` reports |
| --- | --- | --- |
| `wfctl__426-overlay-boundary-spike` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/wt/426-overlay-boundary-spike` |
| `wfctl__425-restart-holds-on-child-work` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/wt/425-restart-holds-on-child-work` |
| `wfctl__397-handoff-records-work-in-flight` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/wt/397-handoff-records-work-in-flight` |
| `pfms__pfms-specs` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `~/Development/pfms-specs` |
| `pfms__656-detail-panel` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/pfms/wt/656-detail-panel` |
| `wfctl__424-observer-dashboard-eval` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | matches — **and cannot distinguish** |
| `wfctl__419-misfiled-record-check` | `~/Development/wfctl/wt/419-misfiled-record-check` | matches |
| `pfms__655-analyst-view` | `~/Development/pfms/wt/655-analyst-view` | matches |
| `pfms__654-variance-summary` | `~/Development/pfms/wt/654-variance-summary` | matches |
| `pfms__653-variance-ledger` | `~/Development/pfms/wt/653-variance-ledger` | matches |
| `0-0` | not read | — |

**424's own row is in the table and counted as correct, and it is the row that
can least bear that.** Its real directory and the value the five wrong rows show
are the same string, so it reads as correct under either explanation and
distinguishes nothing. It is listed rather than dropped because a table that
silently omits the one ambiguous row is how the previous draft's count went wrong.

`pfms__pfms-specs` is the row that carries the most information: its real
directory is not under any `wt/` and is in a different repository, and it still
shows this worktree's path. Whatever the five share, it is not proximity to 424.

**The hypothesis, stated as one.** The value the five print is the same string as
the working directory of the cmux terminal `cmux ssh-tmux localhost` was run
from — its prompt read `424-observer-dashboard-eval` in the transcript finding 8
quotes. That is an equality between two observed strings. It is *not* an
observation that the mirror fell back to that directory, and no run that would
separate the two was made: launching the mirror from a different directory and
seeing whether the five rows follow would settle it in one attempt and was not
done. Finding 10 in this same session declines to infer cmux's internals from
outside, and the same restraint applies here.

**The alternative this replaced, struck rather than deleted.** ~~The five wrong
rows' sessions were created within thirty seconds of each other and of 424's.~~
Falsified by `pfms__pfms-specs`, which is the oldest session on the server and in
a different repository, and by `pfms__656-detail-panel`, created an hour apart
from the wfctl three. It is kept here because it was the only alternative this
finding ever carried, and a reader who cannot see what was ruled out cannot tell
a considered answer from a first guess.

**What the earlier draft got wrong, including about its own method.** It said two
rows wrong and three showing no path. It also said, in as many words, *"Read at
full sidebar width, so this is not truncation"* — and that was the false part.
The sidebar was narrower than the claim, three subtitles were truncated to
nothing, and the assertion of a control is what made the wrong count look
checked.

So the remedy is not "say what width you read at": the first draft effectively
did, and was wrong about it. What would have caught this is a second source, and
there is none — no cmux verb reports a mirrored workspace's subtitle or path.
Until there is, this finding's numbers are a reading of a picture, and any later
reader should treat the count as the weakest claim in it.

tmux answers correctly for every session, by both `session_path` and
`pane_current_path`, so the wrong value is not being read from there.

**Why it matters more than a cosmetic bug.** The record's correlation clause says
the client correlates on the workmux handle or the worktree path, never on an id
it assigned. This mirror correlates on the handle, which is the clause satisfied
— and it *also* displays a path, which a reader will use to tell two rows apart.
A supervisory screen exists to answer "which worktree needs me?", and a row
carrying the right name over the wrong directory answers it wrongly in a way the
reader has no way to check. `cwd` as a display hint is already demoted by cmux's
own doc; this is the demotion earning itself.

Not filed against cmux. One machine, one run, `localhost`, and no minimal
reproduction attempted.

## Finding 10 — a session created after connect never gets a row

The rows are live — finding 8's keyboard and the agent's own output prove that.
What was tested is one direction of *which sessions have rows*: a session created
after the mirror connects does not get one. Removal was never exercised, so
nothing here says the set is fixed — only that it does not grow.

`workmux add 459-poller-decision` created a twelfth tmux session while the mirror
was open. It did not appear. The sidebar still lists the eleven that existed when
`cmux ssh-tmux localhost` ran, and `tmux list-sessions` lists twelve.

Control mode emits `%sessions-changed` when the server's session set changes
(`tmux(1)`, CONTROL MODE), so the notification is available to a client that
subscribes to it. Whether cmux subscribes and drops it, or never subscribes, is
not visible from outside and was not determined here.

**Re-running the command does not fix it:**

```
$ cmux ssh-tmux localhost
Connecting to localhost…
ControlSocket /Users/andremarin/.cmux/ssh/tmux-localhost-….sock already exists,
  disabling multiplexing
Authenticated; opening remote tmux mirror for localhost…
Error: ssh-tmux: authentication did not open the connection to localhost
```

**The cause is adjacent, not shown.** The first mirror's SSH control master is
still running — `ssh -O check` on that socket reports `Master running` — and
the warning names it. But `disabling multiplexing` is a fall-back, not a failure:
ssh proceeds, and the transcript's own next line is `Authenticated;`. What failed
is the phase after authentication, which is cmux's mirror-open. The control master
is the obvious suspect and it is not the observed cause.

**The remedy is likewise untried.** `ssh -O exit` on that socket followed by a
fresh `cmux ssh-tmux localhost` is the obvious repair and no run of it is
recorded, so "tear it down and reconnect" is a proposal in this file and not a
result.

**What this does to the record.** The recovery clause covers one direction —
*workmux reports an environment and tmux has no session, so surface and stop*.
This is the mirror image: tmux has a session and the client has no row for it,
which the record has no clause for. Finding 8 established the client destroys
nothing; this establishes it can also fail to *notice*, and a client that shows a
stale set while creating and destroying nothing violates no clause the record
currently writes. Worth a clause, and that is the record's to add rather than
this scan's.

**How it compares to finding 9.** Both are wrong information rather than missing
information, and finding 9 is the more dangerous of the two: a row carrying the
right name over the wrong directory is a claim the reader cannot check, while an
absent row at least leaves a person who knows they just made a worktree asking
where it is. What makes this one worth its own finding is that no amount of
correct row content fixes it — the poller can write perfect verdicts onto eleven
rows and the twelfth worktree is still invisible.

For a poller it is the cheapest thing to work around and the easiest to get
wrong: `workmux list --json` reports session twelve immediately, and there will
be no row to write it to. Detecting the mismatch and saying so beats silently
writing eleven of twelve — and the mismatch is worth detecting in both
directions, since the removal case is untested and a row for a session that no
longer exists would fail the same way round.

**Limits.** One machine, one run, `localhost`. Only the additive case was
exercised — a session created after connect. Whether a *killed* session's row
disappears, and whether a new *window* inside an already-mirrored session shows
up as a tab, were not tested; the heading and the conclusion above are narrowed
to the case that was, which is why neither says the set is frozen. Not filed
against cmux for the same reasons as finding 9.

## Finding 11 — six rows carry a wfctl status line, from a source this run could not identify

Later the same day, after the tmux server had turned over, the sidebar looked
like this:

```
…/wfctl/wt/424-observer-dashboard-eval
  424-observer-dashboard-eval
  PR #460  open                            ← cmux's own git metadata

Orchestrator
  ~/Development/pfms
  ~/Development/wfctl

wfctl__424-observer-dashboard-eval
  #424 · brainstorm · next /speckit.brainstorm
pfms__pfms-specs
  #unknown · brainstorm · next /speckit.brainstorm
pfms__669-eyebrow-utility
  #669 · brainstorm · next /speckit.brainstorm
pfms__565-chart-writable
  #565 · done
pfms__564-chart-follows-interview
  #564 · done
pfms__561-chart-of-accounts-screen
  #561 · brainstorm · next /speckit.brainstorm
```

**Every mirrored row carries a wfctl status line. Neither non-mirrored row
does.** Six rows, two repositories, and sessions this evaluation never touched.
The `done` rows even render a shorter form than the rest, which a naive
formatter would not: a row whose step is `done` has no next command, and these
omit it rather than printing an empty tail.

**What wrote them is not established.** Finding 8 put one such line on one row
with a `printf` into a pane's tty, by hand. These are six, in two repositories,
in a tmux server that had restarted since. Checked and ruled out:

| Candidate | Result |
| --- | --- |
| a poller process | `ps` shows cmux and its seven `ssh -CC` mirror clients, nothing else |
| wfctl emitting OSC itself | no escape sequence anywhere under `wfctl/` |
| a hook in either repo's `.claude/settings.json` | wfctl's four are `user-prompt`, `response-shape`, `session-restart`, `worktree-guard`; pfms declares none that touch a terminal |
| a script in the shell profile or the dev tree | nothing matching, and no shell script modified that day |

So the line between this and finding 8 is not a difference of mechanism but of
knowledge: there, a command was run and its effect observed; here, an effect is
observed and no command is known. **An evaluation that reports the second as
though it were the first is the failure this file has already made twice**, so it
is written down as what it is — a real observation with an unidentified cause,
which someone with access to how these sessions are started can probably resolve
in a minute.

**It bears directly on #459**, which asks whether to build a poller. If something
is already doing this job, the question is not "build it" but "find what is doing
it and decide whether to keep it". That is the first thing that branch should
establish, and it is cheaper than the decision it was filed to make.

**One thing this run did settle.** `cmux workspace list` was run against the new
state and printed eight workspaces by title alone — no subtitle, no path:

```
* workspace:1  …/wfctl/wt/424-observer-dashboard-eval  [selected]
  workspace:9  Orchestrator
  workspace:3  wfctl__424-observer-dashboard-eval
  …
```

That confirms the Evidence ledger's claim rather than relieving it: the verb
reports which rows exist, which is the half finding 10 needed, and reports
nothing about what a row *displays*, which is the half finding 9 needed. Finding
9's counts still have no second source.

**Not re-testable here.** The session set turned over completely between the runs
— `425`, `426`, `419`, `397` and the `459-poller-decision` session are gone;
`561`, `564`, `565`, `669` and `Orchestrator` are new, all reconnected at 09:21.
Finding 10's question cannot be re-asked against this state without creating a
worktree on purpose, which was not done.

## What it would cost to get #424's screen anyway

Three pieces, none of them in wfctl. **Two of them now exist**, and the second
run is what moved them:

1. **A pane or a mirror per worktree.** `cmux ssh-tmux localhost` supplies it —
   one workspace per session, ownership untouched, finding 8. The alternative is
   an ordinary cmux terminal running `tmux attach -t wfctl__<handle>`, which also
   works but which cmux models as a shell rather than a session, so no attention
   ring or status lane is keyed to it. The mirror is the one that carries a row.

   **It supplies rows for the sessions that existed when it connected, and adds
   none afterwards** (finding 10). A worktree created since is absent, and reconnecting
   over the top of the existing mirror fails. Tearing it down first is the
   obvious repair and is untried, so treat it as the next thing to check rather
   than as a known step. Whoever builds piece 3 inherits the gap either way: the
   poller learns about a new worktree from `workmux list` one tick later and has
   no row to write it to.
2. **Correlation on the workmux handle.** Supplied by the mirror, which labels
   each workspace with the tmux session name and nothing else. This is what
   `a-client-attaches-to-a-runtime-it-never-owns` asks for, and it arrives for
   free rather than being configured. `cwd` is the tempting second key and cmux's
   own doc demotes it — "Title and cwd remain display and diagnostic hints only" —
   which finding 9 turns from a caution into an observed defect.
3. **A sidecar.** A process started inside cmux, or holding the socket password,
   polling `workmux list --json` and each worktree's `wfctl status --json`, and
   pushing rows with `cmux set-status` / `cmux log`. **This is the whole of what
   is left** — and finding 11 is six rows that look exactly like its output,
   from a source this evaluation could not identify. So "the piece that does not
   exist" is what this file established and no longer what it can claim: the
   first thing to settle is whether something already does this.

   **It cannot run in a mirrored pane.** `cmux ssh-tmux localhost`, typed into a
   mirrored pane, returned finding 4's refusal:

   ```
   Error: ERROR: Access denied - only processes started inside cmux can connect
   ```

   Reading `env` in a tmux pane confirms no `CMUX_*` is set there, though that
   alone proves little — the pane predates the mirror, so it shows what an
   ordinary shell has rather than anything about the hop. The two together are
   what support the claim: the processes a mirrored pane hosts were started by
   tmux on the host, not by cmux, so they get none of the environment cmux injects
   into its own terminals.

   So the poller runs in a cmux-native terminal, or it holds the socket password —
   and the second raises a question this evaluation does not answer, namely where
   that secret would live for a process nobody starts by hand. A real constraint
   on where the code can live, and an invisible one: a mirrored pane looks exactly
   like a cmux terminal until a command fails.

   **Verified over `localhost` only**, like everything else in the second run. A
   genuinely remote host may differ, and no claim here reaches one.

So the shape of the answer has changed. It was "two of three pieces missing, and
one of those cannot be evaluated here"; it is now "one piece missing, and it is
the one the #424 comment declined" — a second orchestration plane wearing a
smaller name. The two pieces that now exist are not perfect: piece 1 misreports
half its paths and does not notice new sessions.

A one-shot stands in for the missing piece in finding 8, where the pane wrote
its own row with a `printf`; what a sidecar adds is doing that on a schedule, for
every worktree, without a person in the loop.

Recorded as the cost, not as a proposal. The decision is whose it was before:
the piece is small, and being small was never the objection to it.

## Evidence

Every cmux and tmux transcript quoted above is reproducible by running the
quoted command. All of them are reads except two: the `local-tmux start`/`close`
pair, which is shown with its cleanup, and the `workmux add` that created finding
10's twelfth session — a write that was made for its own reasons and that this
finding observed rather than staged.

**Finding 6's table is the exception, and deliberately so.** The probe that
produced it read `workmux list --json` and then each worktree's `wfctl status
--json`, and it is not committed, because a repo-side joiner is the thing #424's
comment ruled out. It is also not re-runnable from here by any documented route:
this repo's own `wfctl hook worktree-guard` refuses a command that runs in
another worktree, which is correct and is why the probe reached them through a
Python `cwd=` rather than a shell `cd`. A reader checking a row runs `uv run
wfctl status --json` inside that worktree's own pane — `workmux send wfctl
"…"` — rather than reproducing the join.

Two rows are checkable without any of that, and both were confirmed
independently: 424's own row by running the command here, and 419's absent
`version` and `attention` from git, since `STATUS_PAYLOAD_VERSION` entered in
#441 and `419`'s branch point predates it.

**The second run's evidence divides four ways, and the four are not equally
strong.** Findings 8, 9 and 10 draw on all of them:

- `tmux list-sessions`, `tmux list-panes -a` and `ssh -O check`, for the session
  count, the creation timestamps, the attach counts, every `session_path`, and
  whether the mirror's SSH control master is alive. All reads, all re-runnable
  from any shell.
- `cmux ssh-tmux localhost` and `cmux workspace list --id-format both`, which
  must be run from a terminal *inside* cmux — the socket refuses an outside
  process, which is finding 4 met from the other side. Their output is quoted
  above as they printed it, the failing re-run included.
- `env` read in a tmux pane, for the absence of `CMUX_*`. Weak on its own: the
  pane predates the mirror, so it shows that an ordinary shell has no `CMUX_*`
  rather than anything about the SSH hop. What carries that claim is the
  `Access denied` transcript beside it, from a command actually run in a
  mirrored pane.
- **The sidebar itself, for what a row displays and which rows exist — and this
  is the weak one.** No cmux verb reports a mirrored workspace's subtitle or its
  path; `workspace list` prints neither, and it was not re-run after the twelfth
  session was created. So finding 9's counts and every path in its table, and
  finding 10's "still eleven rows", are readings of a rendered picture with no
  second source. Neither is filed as a bug for that reason.

  **That check was later run, and it only half helps.** `cmux workspace list`
  prints which rows exist — the half finding 10 needed — and prints nothing
  about what a row displays, which is the half finding 9 needed. Finding 11
  carries the output. So finding 9's numbers still have no second source, and
  the reason is now a verified property of the CLI rather than an assumption.

  **It is weak in a way that has already cost this file a wrong number, twice
  over.** Finding 9 first said two rows wrong and three blank; it is five wrong
  and none blank. The first draft also asserted it had been *"read at full
  sidebar width"* — so the count was wrong and the stated control was wrong with
  it. That is why the remedy is not "say what width you read at": the draft that
  failed said exactly that. Until cmux reports these values through some
  interface, the honest position is that finding 9's numbers are its weakest
  claim and are labelled as such in the finding itself.

  **Finding 10 is partly in this bucket, and an earlier draft of this ledger
  denied it.** Half of it — a re-run that fails, a control master still alive,
  twelve sessions on the server — rests on the first two sources above and is
  reproducible. The other half is "and the sidebar still shows eleven", which is
  a reading of the picture and is load-bearing: it is the observation that the
  new session did not appear.

  `workspaces=11` does **not** corroborate it. That line was printed when the
  mirror connected, before the twelfth session existed, so a mirror that added
  the row dynamically would have printed exactly the same thing. The earlier
  draft offered it as corroboration, which was the same mistake finding 9 is
  about: a number that is easy to check, cited for a claim it cannot reach.
