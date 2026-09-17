# Session restart that writes its handoff first

## Problem Statement

How might a Claude pane that fills its context window restart itself without
discarding the session's reasoning — so the next session starts from *this*
session's handoff, not an earlier one that reads exactly like it?

## Recommended Direction

wfctl ships `wfctl hook session-restart`, a managed Stop hook in the claude layer.
On each reply end it reads the window's occupancy from the transcript and the
branch's `events.jsonl`. Over the threshold (200000 by default) it sends
`/end-session restart`; on a later Stop, once an `end` event newer than that send
exists, it sends `/clear` and `/start-session`. The sends come from a detached
worker that starts after the hook exits and records each send's exit code.

This replaces a personal script (`~/.claude/recycle-hook.sh`) that sends `/clear`
and `/start-session` with no `/end-session` between them. `recycle-hook.log`
shows it clearing this branch at 18:57Z, 19:29Z (2026-09-14) and 09:40Z
(2026-09-15), each taking a session's reasoning with it, and sending a `/clear`
to `619-flexible-budget` that exited 0 and never took.

Scope was narrowed twice during brainstorm, both by the user. Only the
token-limit restart inside the SDD workflow is handled; a hand-typed `/clear` is
out (ledger entry 14). Claude only; Codex and Copilot are deferred with no issue
filed (entries 18, 21), and entries 15–17 are their evidence when that happens.
The platform fact that makes this the shape: no agent's `/clear` reaches a hook
while the model is still present (Claude `SessionEnd` discards output and runs
after the model is gone — entry 1), so prose can only be written by a turn the
hook asks for *before* the clear.

### Level 1 — what the pane shows

| State | Pane shows |
|---|---|
| A — under the threshold | nothing |
| B — over the threshold, first Stop | `> /end-session restart` |
| C — handoff landed (an `end` newer than B), next Stop | `> /clear`, `> /start-session`; the new session's report takes row 1 on "the last stop was continued" |
| D — the `/end-session` turn recorded no stop (asked a question, errored) | `session restart held: /end-session recorded no stop — context not cleared` |
| E — no workmux pane to send to | `session restart skipped: no workmux pane for <handle>` |
| F — `/clear` was sent to this session and a Stop from the same session arrives | once: `session restart sent /clear at <time> and this session is still here — run /clear yourself, or /end-session first`; no retry |
| off — `WFCTL_RESTART_THRESHOLD=0` | nothing, at any occupancy |

D and F were lies in the personal script (D quotes the previous handoff as
current; F logs "already recycled" for a day). E was silent. No retry on F
because a retry types `/clear` into a pane a person may be typing into (entry 26).

## Boundaries and Ownership

| Truth | Owner | Why the other side cannot |
|---|---|---|
| "Is this pane due to restart, and has the handoff it asked for landed?" | wfctl (`hook session-restart`) | The agent loses the reading in the clear and is refused `/clear` and pane-driving by the classifier. A script outside wfctl would parse `events.jsonl`, a format wfctl owns and changes, with no test on either side. |
| Window occupancy | Claude Code, written into the transcript | wfctl only reads the last usage record. |
| What the restart turn must do differently (`--continued`, skip commit/tracker questions) | `end-session` skill | A string in Python overriding steps of a skill it does not live beside drifts silently when the skill changes. |
| Which wfctl feature a hook row is | the subcommand after `wfctl hook ` | The event cannot tell two features apart once Stop carries two; the full command string changes suffix across versions. |
| The threshold | the person's environment | It follows the model's window, which is per person, not per repo — `no-hardcoded-agent`'s axis. |

## Software design decisions

- docs/architecture/wfctl-performs-the-session-restart.md — wfctl decides and performs the restart from a Stop hook in the claude layer (level 2, proposed)
- docs/architecture/a-managed-hook-is-owned-by-its-subcommand.md — installer identity is the subcommand, so Stop can carry two wfctl entries (level 2, proposed)
- docs/architecture/design/371-the-session-restart-sends-from-a-detached-worker.md — sends run in a detached Python worker that records each send's exit
- docs/architecture/design/371-the-session-restart-instruction-lives-in-end-session.md — `end-session` gains a `restart` section; the hook sends one word
- docs/architecture/design/371-the-session-restart-threshold-is-an-environment-variable.md — `WFCTL_RESTART_THRESHOLD`, default 200000, `0` is off

## Key Assumptions to Validate

- [ ] A send started after the Stop hook exits lands in a Claude pane — live restart, transcript id changes after the `/clear` (observed on Codex only, entry 16).
- [ ] Text after `/end-session` reaches the skill on Claude — live restart whose `end` event carries `"continued": true` and leaves the tree unchanged (checked on Codex and Copilot, entry 15).
- [ ] A Stop hook's `systemMessage` renders in the pane (D, E, F depend on it) — probe before building those states.
- [ ] A value exported in the shell profile reaches the hook in a workmux pane — restart fires at the exported value.
- [ ] The classifier lets the agent author the send code inside `wfctl/` — it refused the equivalent in a scratch dir (entry 17); if refused, the person writes those lines.

## MVP Scope

In:
- `wfctl/_restart.py` — pure decision function over Stop payload, occupancy, parsed events, threshold → nothing / send end / send clear+start / hold / skip / report F.
- `wfctl hook session-restart` in `cli.py` — thin caller; exits 0 on every path.
- `wfctl/_restart_send.py` — detached worker (`start_new_session=True`), waits for the hook to exit, `workmux send` with a timeout per send, appends `session-restart-send` per send.
- Events `session-restart` (hook: session id, time, what it sent; F reported) and `session-restart-send` (worker: session, text, exit code).
- Installer: `MANAGED_HOOKS` event → subcommands; `merge_hook`, uninstall record and doctor keyed per subcommand; prune a wfctl row whose subcommand is no longer shipped under its event.
- `end-session` skill: a `restart` section (`wfctl end --continued`, full summary, skip steps 6–7, note tree left as found); any other argument ignored.
- `WFCTL_RESTART_THRESHOLD` read with default 200000 written once.
- Tests from each record's Verification section.

Out: see below.

## Not Doing (and Why)

- Hand-typed `/clear` — out of scope by user decision (entry 14); it would need a per-agent transcript reader (entry 13's C).
- Codex and Copilot — deferred (entries 18, 21); hooks, occupancy fields and skill spelling differ per agent (entry 15).
- Retrying a `/clear` that did not take — it types into a pane a person may be using (entry 26).
- A repo-wide off switch in `wfctl.json` — no caller yet; an addition to the env var if ever needed, not a replacement.
- Deriving the threshold from the model's window — the transcript carries no window size.
- Printing the threshold in force from `wfctl doctor` — named in the env-var record as where the silent-default question gets answered; small, but not needed to test the core assumption.

## Open Questions

- #371's body still puts a hand-typed `/clear` in scope and asks for a record "a later session can tell apart from an older handoff". Entry 14 narrowed that. Re-scoping the issue is a comment on GitHub — outward, asked for when reached.
- `~/.claude/recycle-hook.sh` is still installed and still clears with no `/end-session` (entry 26). It has to be removed from `~/.claude/settings.json` by the user once the shipped hook is in, or two hooks will race on the same pane.
