# Evaluation scan — #424

## Session 2026-09-22

- Verdict: **the attach experiment fails as posed.** cmux cannot present a
  workmux-owned tmux session as a cmux session, because it does not share a
  tmux server with one.
- Scope: #424's first half — install and evaluate `agent-dashboard` — was
  withdrawn in the issue's own comment of 2026-09-20 and was not run. What was
  run is the narrowed experiment that comment leaves standing, quoted below.
- Ran against: 5 live `mode: session` worktrees, 11 tmux sessions on the default
  server.
- Versions: cmux 0.64.25 (106), tmux 3.6a, workmux 0.1.211, wfctl 0.20.0.

The experiment, as #424's comment states it:

> Can one cmux workspace attach to one existing workmux-owned tmux session and
> present `wfctl status` without taking ownership of that session?

Answer, in three parts: it cannot attach, it cannot be made to attach through
the feature that looks like it should, and the presentation half is reachable
only by a sidecar process this repo would have to write and run.

## The handoff this branch carried was written against the withdrawn half

The handoff in the state dir instructs an evaluation of `agent-dashboard` and
names a negative result as a real deliverable. The issue comment predates it by
two days and withdraws that half outright — "`agent-dashboard` stays useful
prior art … but the project does not need a second orchestration plane beside
wfctl, Spec Kit, workmux and tmux. No new wfctl dashboard either."

Recorded here because the handoff file is not a durable artifact and the next
reader of this branch will otherwise find a PR whose scope does not match the
prose that produced it. `agent-dashboard` was never installed.

## Finding 1 — cmux's tmux integration runs on its own server, so a workmux-owned session is invisible to it

Two servers, two sockets, no overlap:

```
workmux's sessions            /private/tmp/tmux-501/default
  wfctl__397-…  wfctl__419-…  wfctl__424-…  wfctl__425-…  wfctl__426-…
  pfms__652-…   pfms__653-…   pfms__654-…   pfms__655-…   pfms__656-…
  0-0                                                     11 sessions

cmux local-tmux                /Users/andremarin/.cmux/local-tmux/server.sock
  (empty)                                                  0 sessions
```

`cmux local-tmux status` was asked about the session this evaluation was
running inside — live on the default socket at that moment:

```
$ cmux local-tmux status wfctl__424-observer-dashboard-eval --json
Error: local-tmux session not found: wfctl__424-observer-dashboard-eval
```

`attach` gives the same answer. The CLI contract carries no verb taking a socket
path or an external session, and the authoring docs describe `local-tmux` as an
opt-in *owner* rather than a client: "Opt in to a user-owned local tmux server."

This is not a configuration gap that a flag closes. cmux's session model is a
registry it writes, under a socket it creates, holding sessions it started.
A session workmux created has no row in it and no way to acquire one.

## Finding 2 — `local-tmux attach` refuses, `local-tmux start` collides

The record `a-client-attaches-to-a-runtime-it-never-owns` asks two things of a
presentation client. cmux passes one and sidesteps the other in a way the record
does not currently name.

| The record asks | cmux does |
| --- | --- |
| never create, recreate, rename or destroy a workmux-owned runtime | never touches it — it cannot see it |
| where workmux reports an environment and tmux has no session, surface and stop | `attach` errors rather than creating. Good half. |
| correlate on workmux handle or worktree path, never a client-assigned id | its registry keys on a client-assigned UUID, and carries `cwd` beside it |

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

Two sessions, one name, two servers, neither aware of the other. Nothing was
destroyed and the invariant as written was not broken — and a human reading
either surface still cannot answer "is this feature's runtime alive?" without
first being told which server they are looking at. The probe session was closed
(`cmux local-tmux close`); workmux's session is intact and the cmux registry is
back to zero.

The record's correlation-key clause is what covers this, and it covers it only
by implication. Worth a follow-up line: a client that names a runtime it did not
create has taken the name, which is the part of ownership that survives having
taken none of the powers.

## Finding 3 — the socket API is the only way in, and it is gated

Every cmux verb that would carry wfctl state into a row — `set-status`,
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
would own, and the second is a credential in a wrapper somewhere.

Unauthenticated callers get exactly one verb: `cmux <path>`, which opens a
directory as a workspace. It takes no command, so it cannot be used to seed a
pane with `tmux attach`.

## Finding 4 — a custom sidebar cannot fetch what it would display

The obvious home for a joined row is cmux's custom sidebar — a file in
`~/.config/cmux/sidebars/`, refreshed about once a second. It cannot do the job:
interpreted sidebars "cannot import frameworks or start child processes", and
"the context has no filesystem, network, or timers."

So the sidebar cannot run `wfctl status --json`. Something outside has to run
it and push the result in over the socket, which is finding 3 again. A compiled
ExtensionKit extension can run external tools, inside the macOS App Sandbox —
a different and much larger piece of work.

## Finding 5 — `attention` is usable as shipped, and answers a different question than the lamp it resembles

Joined across every live worktree, reading each one's own `wfctl status --json`:

| worktree | runtime | payload version | `current` | `attention` |
| --- | --- | --- | --- | --- |
| 397-handoff-records-work-in-flight | detached | 1.0 | brainstorm | `null` |
| 419-misfiled-record-check | detached | *absent* | brainstorm | *key absent* |
| 424-observer-dashboard-eval | detached | 1.0 | brainstorm | `null` |
| 425-restart-holds-on-child-work | attached | 1.0 | brainstorm | `null` |
| 426-overlay-boundary-spike | detached | 1.0 | brainstorm | `null` |

`attention` was null on every worktree that has the field. That is not a defect —
`_derive_attention` fires on three conditions and none of them held: a reported
block, an outstanding pass with no command, or a stall. The suite covers all
three and their ranking.

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

Two columns, never one verdict. The row holds both and the evaluation found no
pressure to collapse them — if anything the null column makes the pressure
worse, because a uniform `attention` invites a designer to drop it and let the
runtime state stand alone.

Second observation from the same table: `current` was `brainstorm` for all five,
because none of these branches has a spec dir and this repo deliberately routes
most changes around the pipeline. As a supervisory column it distinguished
nothing across the whole sample. A row that carried only `current` would look
populated and say nothing.

## Finding 6 — the contract version cannot identify a payload older than itself

`419-misfiled-record-check` branched before #441 and its own source tree
produces a payload with **neither** `attention` nor `version`. A naive adapter
raises `KeyError`; one reading `payload.get("version")` gets `None`.

A supervisory view spans worktrees at different base commits by construction —
that is what makes it supervisory — so this is the normal case, not an edge. The
rule an adapter has to encode is that an absent `version` means *older than 1.0*,
and it has to encode it as a constant rather than read it from anywhere. This is
a line for #423's follow-up, not a change to
`wfctl/contracts/status-payload.json`, which was not touched.

## What it would cost to get #424's screen anyway

Three pieces, none of them in wfctl:

1. **A pane per worktree.** An ordinary cmux terminal running `tmux attach -t
   wfctl__<handle>` against the default socket. cmux is a terminal emulator, so
   this works — and cmux models it as a shell, not a session. No attention ring,
   no unread badge and no status lane is keyed to the tmux session, because cmux
   does not know there is one.
2. **A sidecar.** A process started inside cmux, or holding the socket password,
   polling `workmux list --json` and each worktree's `wfctl status --json`, and
   pushing rows with `cmux set-status` / `cmux log`. This is the whole of the
   join, and it is the piece that does not exist.
3. **Correlation on `cwd` or the workmux handle**, never on cmux's workspace
   UUID — `a-client-attaches-to-a-runtime-it-never-owns` already says so, and
   cmux's registry hands out a UUID as its primary key.

Piece 2 is a second orchestration plane wearing a smaller name, which is the
thing the #424 comment declined. Recorded as the cost, not as a proposal.

## Evidence

Commands are in the session transcript. The join was produced by a throwaway
probe in the session scratchpad — it reads `workmux list --json`, `tmux
list-sessions` and each worktree's `wfctl status --json`, and it is not
committed, because a repo-side joiner is the thing #424's comment ruled out.
