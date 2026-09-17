# Feature Specification: Session restart that writes its handoff first

**Feature Branch**: `371-write-state-before-clear`
**Created**: 2026-09-15
**Status**: Draft
**Input**: User description: "Nothing writes a session's state before /clear, so a session that is not formally ended leaves nothing behind" (#371), narrowed during brainstorm to the automatic restart of a Claude pane that has filled its context window.

## Clarifications

### Session 2026-09-15

- Q: Which recorded stop counts as the handoff having landed — any stop, or only a continued one? → A: Any stop recorded after the `/end-session restart` send, continued or not.
- Q: What happens when the `/end-session restart` send itself fails? → A: The next reply end reports once that it was never sent, and it is not resent.
- Q: What does a reply end from the same session decide while a planned send has not yet been recorded? → A: Nothing — wait until the send's own event exists.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A full session restarts itself and the next one picks up where it stopped (Priority: P1)

A developer runs a long spec-pipeline session in a Claude pane, attended or not. The
context fills past the threshold. Instead of the harness compacting it, or a
personal script clearing it with no handoff, the pane is asked to run
`/end-session` in restart mode. That turn writes the handoff and records a
continued stop. On the next reply end the pane is cleared and `/start-session`
runs, and the new session reports that the last stop was continued and quotes
the handoff this session just wrote.

**Why this priority**: This is the failure #371 was filed for. On 2026-09-14 and
15 the personal restart script cleared this branch three times with no handoff,
and each time the next session re-derived decisions that had already been made.

**Independent Test**: In a workmux Claude pane with the threshold set low, run
turns until it is crossed. The pane receives `/end-session restart`, then `/clear`
and `/start-session`. The new session's report quotes a line from the handoff
written by the restart turn, and the branch's event log carries a continued stop
between the two sends.

**Acceptance Scenarios**:

1. **Given** a pane whose context is below the threshold, **When** a reply ends, **Then** nothing is sent and nothing is shown.
2. **Given** a pane whose context has reached the threshold and no restart has begun for this session, **When** a reply ends, **Then** `/end-session restart` is sent to the pane, once.
3. **Given** `/end-session restart` was sent and the session has since recorded a stop, **When** the next reply ends, **Then** `/clear` and then `/start-session` are sent to the pane.
4. **Given** `/end-session` is invoked with `restart`, **When** it runs, **Then** it records a continued stop, writes the summary in full, asks nothing about committing or the tracker, leaves the working tree as it found it and says so in the summary.
5. **Given** the repo's Claude settings already carry wfctl's reply-check hook on reply end, **When** skills are installed for Claude, **Then** both wfctl hooks are present on that event and a second install leaves exactly one of each.

---

### User Story 2 - A restart that cannot finish safely says so in the pane (Priority: P2)

The restart runs into one of three conditions that the personal script handled
by lying or saying nothing: the handoff turn did not record a stop, there is no
pane to type into, or a `/clear` was sent and the session is still there. Each is
reported once, in the pane the developer is looking at, and nothing is cleared
that would lose work.

**Why this priority**: Without these, the P1 flow is a regression in exactly the
cases where it matters. A clear after a handoff turn that asked a question makes
the next session quote the *previous* handoff as current; a `/clear` that exited
0 and never took left one pane growing from 225k to 283k tokens for a day.

**Independent Test**: With the sender stubbed, drive the decision with an event log
that has a restart send and no newer stop; with no workmux pane for the branch;
and with a reply end from a session that `/clear` was already sent to. Each
produces its message once and no clear.

**Acceptance Scenarios**:

1. **Given** `/end-session restart` was sent and no stop has been recorded since, **When** a reply ends, **Then** nothing is sent and the pane shows `session restart held: /end-session recorded no stop — context not cleared`, once for that send.
2. **Given** a held restart, **When** a stop is later recorded and a reply ends, **Then** `/clear` and `/start-session` are sent.
3. **Given** the restart would send and no workmux pane exists for the branch, **When** a reply ends, **Then** nothing is sent and the pane shows `session restart skipped: no workmux pane for <repo root>`, once per session.
4. **Given** `/clear` was sent to a session and exited 0, **When** a reply ends from that same session, **Then** nothing is sent and the pane shows, once, `session restart sent /clear at <time> and this session is still here — run /clear yourself, or /end-session first`.
5. **Given** `/clear` was attempted and the send itself failed, **When** a reply ends from that session, **Then** the message says the clear was never sent, not that it was sent and did not take.

---

### User Story 3 - A developer moves the threshold or turns the restart off (Priority: P3)

A developer whose panes run a larger or smaller context window sets the
threshold in their shell environment. A developer who does not want automatic
restarts sets it to zero. Neither edits wfctl or the repo's settings, and a
reinstall does not undo it.

**Why this priority**: The default is on at 200000 tokens in every repo with the
Claude layer. At least one of this user's panes already runs past 200000
(283068 tokens in one transcript), so a default nobody can change is a hook
people remove.

**Independent Test**: Run the decision with the environment unset, set to a
number, set to `0`, and set to text; confirm the threshold in force each time.

**Acceptance Scenarios**:

1. **Given** `WFCTL_RESTART_THRESHOLD` is unset, empty or not a whole number, **When** a reply ends, **Then** the threshold is 200000.
2. **Given** `WFCTL_RESTART_THRESHOLD=0`, **When** a reply ends at any context size, **Then** nothing is sent and nothing is shown.
3. **Given** `WFCTL_RESTART_THRESHOLD=150000` exported in the shell that launched the pane, **When** the context reaches 150000, **Then** the restart begins.

---

### Edge Cases

- **Context size unreadable** — no usage record yet (first turn), or the transcript is missing or unparseable: the reply end decides nothing.
- **Still over the threshold after a held restart** — `/end-session restart` is not sent a second time for the same session; the restart stays held until a stop lands.
- **A person ends the held session by hand with a plain `/end-session`** — that stop counts as landed and the next reply end clears. The restart turn asks for a continued stop, but a wrapped-up one is still a handoff newer than every earlier one, which is the property the clear depends on.
- **The `/end-session restart` send itself fails** — the next reply end from that session reports once that it was never sent, and does not resend it, for the same reason a `/clear` is never retried.
- **A reply end arrives between a decision to send and the send being recorded** — a person typed in the seconds before the sender ran. The reply end decides nothing and reports nothing; the send's own record decides the next one.
- **A person types `/end-session restart` by hand** — they get the unattended close, the same as a sent one; the skill cannot tell the two apart and does not try.
- **`/end-session` with any other argument** — ignored, as today, so a typo never becomes a restart.
- **The send hangs** — each send is bounded by a timeout; a hung pane driver cannot leave a process waiting forever.
- **The hook itself fails** — it never blocks the reply from ending, on any path.
- **Two panes on one branch** — the event log is per branch, so a stop recorded by the other pane counts as landed. Assumed rare (one pane per worktree is the workmux model); not guarded.
- **The personal `~/.claude/recycle-hook.sh` is still installed** — both hooks send to the same pane. Out of wfctl's reach; the developer removes it (see Assumptions).
- **A wfctl row on reply end whose subcommand this wfctl no longer ships there** — removed on install, so a renamed hook is replaced rather than left beside its successor.
- **A consumer's own hook on the same event** — untouched, as today.

## Requirements _(mandatory)_

### Functional Requirements

**Deciding and sending**

- **FR-001**: wfctl MUST provide a reply-end hook for Claude, `wfctl hook session-restart`, installed by `install-skills --agent claude`.
- **FR-002**: On each reply end the hook MUST read the context size from the session's transcript and the branch's event log, and decide exactly one of: nothing, send `/end-session restart`, send `/clear` then `/start-session`, hold, skip, or report a clear that did not take.
- **FR-003**: The hook MUST send `/clear` only when the event log carries a stop — continued or not — recorded after this session's `/end-session restart` send.
- **FR-004**: The hook MUST send `/end-session restart` at most once per session, including while the session stays over the threshold after a hold.
- **FR-005**: Sends MUST begin only after the hook has exited, from a process that does not belong to the hook's process group.
- **FR-006**: Each send MUST be recorded in the branch's event log with the session it was sent to, the text sent, and its exit status.
- **FR-007**: Each decision that sends MUST be recorded in the branch's event log with the session and time, so a later reply end can tell what was sent to whom.
- **FR-008**: The hold, skip and did-not-take messages MUST appear in the pane, each at most once per the condition that caused it (per send for hold, per session for skip and did-not-take).
- **FR-009**: The did-not-take message MUST distinguish a send that exited successfully from one that failed, for both `/end-session restart` and `/clear`.
- **FR-010**: The hook MUST never retry a send that failed or did not take — neither `/end-session restart` nor `/clear`.
- **FR-010a**: While a decision to send has been recorded and its send has not, a reply end from that session MUST decide nothing and show nothing.
- **FR-011**: The hook MUST exit successfully on every path, including internal errors, so it never blocks a reply from ending.
- **FR-012**: Each send MUST be bounded by a timeout.

**Threshold**

- **FR-013**: The threshold MUST be read from `WFCTL_RESTART_THRESHOLD`; unset, empty or not a non-negative whole number means 200000.
- **FR-014**: A threshold of `0` MUST turn the restart off: every reply end decides nothing.
- **FR-015**: The default 200000 MUST be written in exactly one place in wfctl.

**The restart turn**

- **FR-016**: `end-session` MUST, when invoked with the argument `restart`, record a continued stop, write the summary in full, skip the commit and tracker questions, and state in the summary that the tree was left as found.
- **FR-017**: `end-session` MUST treat any other argument as it does today.
- **FR-018**: The text the hook sends MUST be exactly `/end-session restart`, and a test MUST tie it to the skill's restart section so the two cannot drift.

**Installing alongside the other hooks**

- **FR-019**: A managed hook row MUST be identified by its event and the subcommand after `wfctl hook `, so one event can carry more than one wfctl hook.
- **FR-020**: Install MUST replace a wfctl row in place when its subcommand matches, collapse duplicate rows of the same subcommand, and remove a wfctl row whose subcommand this wfctl no longer ships under that event.
- **FR-021**: Uninstall MUST remove every wfctl row it installed, per subcommand, and leave consumer rows untouched.
- **FR-022**: `wfctl doctor` MUST report a missing or drifted wfctl hook per subcommand, so a missing restart hook and a missing reply check are reported separately.

## Key Entities _(include if feature involves data)_

- **Restart decision event** — written by the hook when it sends or reports: session id, time, what was decided, and whether a hold or did-not-take has already been reported.
- **Restart send event** — written by the sender per send: session id, the text sent, exit status.
- **Stop event** — the existing `end` event; its `continued` field is what `/start-session` reads to take row 1.
- **Managed hook row** — an entry in the repo's Claude settings, identified by event plus subcommand.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In a live restart, the session after the clear quotes a line from the handoff written by the restart turn — not an earlier one — and its report names the last stop as continued.
- **SC-002**: Zero clears are sent without a stop recorded after the `/end-session restart` send for that session, across every decision test.
- **SC-003**: Every hold, skip and did-not-take condition produces its message exactly once, and no condition produces none.
- **SC-004**: A reply end that decides nothing adds under 0.2 seconds and no model tokens (measured on this branch: 0.07–0.10 s to start wfctl, 0.02 s to read a 1.6 MB transcript).
- **SC-005**: Installing skills for Claude twice leaves exactly one row per wfctl hook subcommand on each event, and the reply check survives the restart hook's arrival.
- **SC-006**: A developer changes the threshold or turns the restart off with one environment variable and no file edit, and a reinstall does not undo it.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` — all green.
- `uv run wfctl install-skills --agent claude --yes`, then `uv run wfctl doctor` exits 0 and `.claude/settings.json` carries both Stop hooks.
- Unit tests over the decision function for every level-1 state (below threshold, send end, send clear, hold, skip, did-not-take in both forms, off) and for the threshold parsing in FR-013–FR-015.
- A test that the hook returns before the sender sends, using a stub `workmux` on `PATH` that records its parent pid and a timestamp.
- A test that the send text is exactly `/end-session restart` and that `end-session`'s restart section names `--continued`.
- Installer tests: two wfctl subcommands on Stop survive a reinstall; a duplicate collapses; an unshipped subcommand is pruned; consumer rows are untouched; doctor reports per subcommand.
- Live checks in a workmux Claude pane with a low threshold, which the suite cannot reach: the sent `/clear` changes the transcript id; the `end` event from the restart turn carries `"continued": true` and the tree is unchanged; a hook message renders in the pane; an exported threshold is the one in force.

## Assumptions

- Pre-specify design context loaded from `specs/371-write-state-before-clear/design.md`. Level-2 and level-3 decisions are the five proposed records it lists.
- Scope is the automatic restart only; a hand-typed `/clear` is out (brainstorm ledger entry 14). Claude only; Codex and Copilot deferred (entries 18, 21).
- A send started after the Stop hook exits lands in a Claude pane (observed on Codex, entry 16; unprobed on Claude).
- Text after `/end-session` reaches the skill on Claude (checked on Codex and Copilot, entry 15).
- A Stop hook's message renders in the Claude pane (unprobed; FR-008 depends on it).
- The shell environment that launched the pane reaches the hook.
- One pane per branch; the event log is per branch, not per pane.
- The developer removes `~/.claude/recycle-hook.sh` once the shipped hook is installed; wfctl does not edit user-level settings.
- Unattended specify run (`auto_approve: true`): no clarification markers were raised; every default above is recorded here or in the design records rather than asked.
