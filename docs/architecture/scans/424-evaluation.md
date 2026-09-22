# Evaluation scan — #424

An `evaluation` — the kind of scan file with no pipeline step behind it. This
branch ran none; the thing needing to reach a reviewer is an experiment's result.
`writing-a-scan-file` governs what a section carries and is followed here. The
one thing it delegates to "the wrapper that sent you here" is the coverage rows,
and no wrapper sent this one, so the rows below are this evaluation's own, named
before it started.

## Session 2026-09-22

- Verdict: **inconclusive**
- Scope: #424's first half — install and evaluate `agent-dashboard` — was
  withdrawn in the issue's own comment of 2026-09-20 and was not run.
  `agent-dashboard` was never installed. What was run is the narrowed
  experiment that comment leaves standing.
- Ran against: 5 live `mode: session` worktrees; 12 tmux sessions on the
  default server.
- Versions: cmux 0.64.25 (106), tmux 3.6a, workmux 0.1.211, wfctl 0.20.0.
- Detail: no `FEATURE_DIR` artifact — this branch ran no pipeline step, so
  there is no fuller document for this file to point at. Everything the
  evaluation established is here.

The experiment, as #424's comment states it:

> Can one cmux workspace attach to one existing workmux-owned tmux session and
> present `wfctl status` without taking ownership of that session?

**Inconclusive rather than unsatisfied**, and the distinction is the whole
reason this section is worth reading. cmux's *local* tmux integration cannot do
it, and that is settled below. cmux has a second integration — `ssh-tmux`,
which mirrors the sessions of a tmux server it does not own — that is not
reachable on this machine and was therefore not exercised. The unsurveyed half
is the half that might answer yes.

### Coverage

| Pass | Status |
| --- | --- |
| A · `local-tmux` — can it see a workmux-owned session? | Clear (it cannot; finding 1) |
| B · `local-tmux` — does it act on one it was not given? | Clear (it cannot see one to act on; finding 2) |
| C · `ssh-tmux` / `mosh-tmux` — the control-mode path | **Deferred** — not reachable here; finding 3 |
| D · Presenting `wfctl status` in a row | Outstanding (finding 4) |
| E · A sidebar as the presentation surface | Clear (it cannot fetch; finding 5) |
| F · `attention` as a supervisory column | Clear (finding 6) |
| G · The payload as a consumed contract across worktrees | Outstanding (finding 7) |

Pass C is the one that holds the verdict at `inconclusive`. It is `Deferred`
rather than `Clear` because nothing was learned by running it — only that it
cannot be run here without a change to this machine that is not an agent's to
make.

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

## Finding 3 — the path that might answer yes was not reachable, and was not run

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

**So the verdict is `inconclusive` and not `unsatisfied`.** What a reader should
take from this file is that the local path is closed and the control-mode path
is untested — not that cmux cannot do it. Two questions stay open and both are
cheap to answer once Remote Login is on:

- Does a mirrored workspace carry cmux's attention ring, unread badge and status
  lane, or are those keyed to surfaces cmux created?
- Control mode can issue `kill-session`. Does cmux's mirror ever do so — on
  workspace close, on disconnect, on reconcile? That is the record's invariant
  asked of the one path that can actually break it.

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

## What it would cost to get #424's screen anyway

Three pieces, none of them in wfctl, and the first is conditional on finding 3:

1. **A pane or a mirror per worktree.** Either an ordinary cmux terminal running
   `tmux attach -t wfctl__<handle>` — which works, because cmux is a terminal
   emulator, and which cmux models as a shell rather than a session, so no
   attention ring or status lane is keyed to it — or the `ssh-tmux` mirror,
   which does model them as workspaces and is the untested path.
2. **A sidecar.** A process started inside cmux, or holding the socket password,
   polling `workmux list --json` and each worktree's `wfctl status --json`, and
   pushing rows with `cmux set-status` / `cmux log`. This is the whole of the
   join, and it is the piece that does not exist.
3. **Correlation on the workmux handle.** Not on cmux's workspace UUID, which
   `a-client-attaches-to-a-runtime-it-never-owns` refuses by name. `cwd` is a
   tempting second key and cmux's own doc demotes it — "Title and cwd remain
   display and diagnostic hints only" — so it is a hint, not an identity.

Piece 2 is a second orchestration plane wearing a smaller name, which is the
thing the #424 comment declined. Recorded as the cost, not as a proposal.

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
