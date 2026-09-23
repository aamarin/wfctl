# Evaluation scan — #424

An `evaluation` — the kind of scan file with no pipeline step behind it. This
branch ran none; the thing needing to reach a reviewer is an experiment's result.
`writing-a-scan-file` governs what a section carries and is followed here. The
one thing it delegates to "the wrapper that sent you here" is the coverage rows,
and no wrapper sent this one, so the rows below are this evaluation's own, named
before it started.

## Session 2026-09-22

- Verdict: **satisfied**
- Scope: #424's first half — install and evaluate `agent-dashboard` — was
  withdrawn in the issue's own comment of 2026-09-20 and was not run.
  `agent-dashboard` was never installed. What was run is the narrowed
  experiment that comment leaves standing.
- Ran against: 5 live `mode: session` worktrees; 12 tmux sessions on the
  default server, 11 at the time of the second run.
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
run exercised it. Finding 8 is that run: the mirror presents every workmux-owned
session as a workspace, correlates on the session name, takes no ownership, and
carries a line of wfctl's own output on the row.

**This section holds both runs**, because a second scan finding something is
only meaningful given what the first one found. Findings 1 through 7 are the
first run and stand as written; findings 8 and 9 are the second. Where the
second contradicts the first, the first is left in place and the later finding
says so — a struck claim is the one thing a reader most needs to see, and
deleting it leaves nothing to disagree with.

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
| H · What a mirrored row reports about its own worktree | Outstanding (finding 9) |
| I · Whether the mirror tracks the session set it presents | Outstanding (finding 10) |

Pass C held the verdict at `inconclusive` through the first run, as `Deferred`:
nothing had been learned by running it, only that it could not be run here
without a change to this machine that was not an agent's to make. The second run
had that change and closes it.

Passes H and I are the second run's own, added when it found things the first run
had no way to see. A pass named after the fact is what the "name your rows before
you start" rule exists to prevent, so both are marked as what they are: the mirror
was not expected to say anything about a worktree beyond its name, and it does
(H); and the mirror was assumed to track the server it mirrors, which was never
stated as a pass because it was never in doubt (I).

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

## Finding 9 — half the mirrored rows report the connecting terminal's directory

Five of the ten mirrored workspaces print a path that is not theirs, and all five
print the same one — the working directory of the cmux terminal the mirror was
launched from:

| Sidebar row | Path shown | `session_path` reports |
| --- | --- | --- |
| `wfctl__426-overlay-boundary-spike` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/wt/426-overlay-boundary-spike` |
| `wfctl__425-restart-holds-on-child-work` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/wt/425-restart-holds-on-child-work` |
| `wfctl__397-handoff-records-work-in-flight` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/wt/397-handoff-records-work-in-flight` |
| `pfms__pfms-specs` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `~/Development/pfms-specs` |
| `pfms__656-detail-panel` | `~/Development/wfctl/wt/424-observer-dashboard-e…` | `…/pfms/wt/656-detail-panel` |
| `wfctl__419-misfiled-record-check` | `~/Development/wfctl/wt/419-misfiled-record-check` | matches |
| `pfms__655-analyst-view` | `~/Development/pfms/wt/655-analyst-view` | matches |
| `pfms__654-variance-summary` | `~/Development/pfms/wt/654-variance-summary` | matches |
| `pfms__653-variance-ledger` | `~/Development/pfms/wt/653-variance-ledger` | matches |

`pfms__pfms-specs` is the row that makes the pattern legible: its real directory
is not under any `wt/` and is in a different repository, and it still shows this
worktree's path. Whatever the five have in common, it is not proximity to 424 —
it is that the mirror had no path for them and filled in the one it was standing
in.

**An earlier draft of this finding said two rows, with three showing no path.**
That was read off a narrower sidebar, where the subtitle was being truncated to
nothing. Re-read at full width, all five carry the same wrong value. The count is
corrected here rather than quietly: a finding that under-reports its own blast
radius by more than half is worth leaving a mark, and the lesson is that the only
evidence available for this finding is a rendered UI, which has a width.

tmux answers correctly for every session, by both `session_path` and
`pane_current_path`, so the wrong value is not being read from there.

**Why it matters more than a cosmetic bug.** The record's correlation clause says
the client correlates on the workmux handle or the worktree path, never on an id
it assigned. This mirror correlates on the handle, which is the clause satisfied
— and it *also* displays a path, which a reader will use to tell two rows apart.
A supervisory screen exists to answer "which worktree needs me?", and a row
carrying the right name over the wrong directory answers it wrongly in the one
way the reader cannot detect. `cwd` as a display hint is already demoted by
cmux's own doc; this is the demotion earning itself.

Not filed against cmux. One machine, one run, `localhost`, and no minimal
reproduction attempted.

## Finding 10 — the mirror is a snapshot, and a worktree created after it is invisible

`workmux add 459-poller-decision` created a twelfth tmux session while the mirror
was open. It did not appear. The sidebar still lists the eleven that existed when
`cmux ssh-tmux localhost` ran, and `tmux list-sessions` lists twelve.

Control mode emits `%sessions-changed` when the server's session set changes, so
the notification is available to a client that subscribes to it. Whether cmux
subscribes and drops it, or never subscribes, is not visible from outside and was
not determined here.

**Re-running the command does not fix it, and the error says why:**

```
$ cmux ssh-tmux localhost
Connecting to localhost…
ControlSocket /Users/andremarin/.cmux/ssh/tmux-localhost-….sock already exists,
  disabling multiplexing
Authenticated; opening remote tmux mirror for localhost…
Error: ssh-tmux: authentication did not open the connection to localhost
```

The first mirror's SSH control master is still running — `ssh -O check` on that
socket reports `Master running`. A second `ssh-tmux` to the same host finds the
socket, declines to multiplex over it, and fails. So refreshing the view means
tearing the existing mirror down first, not asking for another one.

**This is the sharpest limitation found in either run, and it is the one a
supervisory screen can least afford.** The worktree a person most wants to watch
is the one they just created; a screen that shows every worktree except that one,
and requires a teardown and reconnect to notice it, inverts its own purpose. Every
other gap in this file is something the screen does not yet say. This is something
it says wrongly — eleven rows presented as the set, with no indication the set is
stale.

For a poller, it is also the cheapest thing to work around and the easiest to get
wrong: the poller reads `workmux list --json`, so it knows about session twelve
immediately, and it will have nowhere to write that row. Detecting the mismatch
and saying so is better than silently writing eleven of twelve.

## What it would cost to get #424's screen anyway

Three pieces, none of them in wfctl. **Two of them now exist**, and the second
run is what moved them:

1. **A pane or a mirror per worktree.** `cmux ssh-tmux localhost` supplies it —
   one workspace per session, ownership untouched, finding 8. The alternative is
   an ordinary cmux terminal running `tmux attach -t wfctl__<handle>`, which also
   works but which cmux models as a shell rather than a session, so no attention
   ring or status lane is keyed to it. The mirror is the one that carries a row.

   **It supplies rows for the sessions that existed when it connected, and no
   others** (finding 10). A worktree created since is absent, and refreshing means
   tearing the mirror down rather than reconnecting over it. Whoever builds piece
   3 inherits this: the poller learns about a new worktree from `workmux list`
   one tick later and has no row to write it to.
2. **Correlation on the workmux handle.** Supplied by the mirror, which labels
   each workspace with the tmux session name and nothing else. This is what
   `a-client-attaches-to-a-runtime-it-never-owns` asks for, and it arrives for
   free rather than being configured. `cwd` is the tempting second key and cmux's
   own doc demotes it — "Title and cwd remain display and diagnostic hints only" —
   which finding 9 turns from a caution into an observed defect.
3. **A sidecar.** A process started inside cmux, or holding the socket password,
   polling `workmux list --json` and each worktree's `wfctl status --json`, and
   pushing rows with `cmux set-status` / `cmux log`. **This is the whole of what
   is left, and it is still the piece that does not exist.**

   **It cannot run in a mirrored pane.** Processes on the far side of the SSH hop
   are started by tmux, not by cmux, and receive none of the `CMUX_*` environment
   cmux injects into its own terminals — verified by reading `env` in a tmux pane
   and finding none of them. So the poller runs in a cmux-native terminal, or it
   holds the socket password. That is a real constraint on where the code can
   live, and it is not obvious from the outside: the mirrored pane looks exactly
   like a cmux terminal and fails with finding 4's `Access denied`.

So the shape of the answer has changed. It was "two of three pieces missing, and
one of those cannot be evaluated here"; it is now "one piece missing, and it is
the one the #424 comment declined" — a second orchestration plane wearing a
smaller name. The two pieces that now exist are not perfect: piece 1 misreports
half its paths and does not notice new sessions. A one-shot stands in for it in finding 8, where the pane wrote its
own row with a `printf`; what a sidecar adds is doing that on a schedule, for
every worktree, without a person in the loop.

Recorded as the cost, not as a proposal. The decision is whose it was before:
the piece is small, and being small was never the objection to it.

## Evidence

Every cmux and tmux transcript quoted above is reproducible by running the
quoted command; all of them are reads except the `local-tmux start`/`close`
pair, which is shown with its cleanup.

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

**The second run's evidence divides the same way.** Findings 8 and 9 rest on
three sources, and only the first is reproducible from a shell alone:

- `tmux list-sessions` / `tmux list-panes -a`, before and after the mirror, for
  the session count, the creation timestamps, the attach counts and every
  `session_path`. All reads, all re-runnable.
- `cmux ssh-tmux localhost` and `cmux workspace list --id-format both`, which
  must be run from a terminal *inside* cmux — the socket refuses an outside
  process, which is finding 4 met from the other side. Their output is quoted
  above as they printed it.
- The sidebar itself, for what a row displays. There is no CLI that reports a
  mirrored workspace's subtitle or its path — `workspace list` prints neither —
  so findings 9 and 10 rest on reading the rendered sidebar. That is the weakest
  evidence in this file and it is the whole basis of both, which is why neither
  is filed as a bug.

  **It is weak in a way that already cost this file a wrong number.** Finding 9
  first said two rows wrong and three blank; at full sidebar width it is five
  rows wrong and none blank. Nothing about the first reading was careless — the
  subtitles genuinely were not rendering at that width — and that is the point:
  a rendered UI answers differently depending on how wide it is, and there is no
  second source to check it against. Any later reader re-reading these two
  findings should say what width they read at.
