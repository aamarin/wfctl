"""The session restart: decide, on each reply end, whether a full pane restarts.

`wfctl hook session-restart` is a `Stop` hook. Over the threshold it has the pane
run `/end-session restart`, and once a stop has been recorded after that it has
the pane run `/clear` and `/start-session` — so the context is only discarded
after the session has written its handoff (#371). What it replaces is a personal
script that cleared with no handoff between, three times on one branch in a day.

wfctl owns the decision and performs it (`wfctl-performs-the-session-restart`,
proposed): the agent loses its reading in the clear and is refused `/clear` and
pane-driving besides, and "has the handoff landed" is a fact in wfctl's own event
log, which a script outside wfctl would read with no test on either side.

Three shapes here are level-3 records under `docs/architecture/design/371-*`:

- the sends run in a detached worker, `wfctl/_restart_send.py`, which records
  each send's exit — the next reply end has to know what the last send did;
- `end-session` carries what a restart turn does differently, so the hook sends
  one word rather than an instruction;
- the threshold is `WFCTL_RESTART_THRESHOLD`, because it follows the model a
  person runs rather than the repo.

A fourth sits under `425-*`: the restart does not begin while this session still
has children out. A pane cleared mid-fan-out loses their results with no trace —
a panel that found six problems and one that never ran leave the same absence —
so `decide` reads the transcript for launches nothing has reported back and holds
before the handoff rather than before the clear.

**Every state is re-derived from `events.jsonl` on every reply end**
(`session-state-is-re-derived`). The personal script kept marker files; a marker
is a second copy of a fact the log already holds, and the two disagree the first
time a write lands in one and not the other.

**Order is line position, never `ts`.** `append_event` stamps to the second, and a
send and a short turn's `end` can share one. Append order is the order things
happened for every writer on one machine.

Imports stay stdlib plus `wfctl._paths` and `wfctl._io`: `_entry.py` reaches this
on every reply end without loading the CLI, the same fast path the worktree guard
takes, and for the same measured reason (`_hook.py`).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_THRESHOLD = 200000
THRESHOLD_ENV = "WFCTL_RESTART_THRESHOLD"

END_TEXT = "/end-session restart"
CLEAR_TEXT = "/clear"
START_TEXT = "/start-session"

# The hook writes the first, the worker the second. Two kinds rather than one
# with a `by` field because each has exactly one writer, and a reader that wants
# "what was sent" never has to filter out "what was decided".
DECISION_EVENT = "session-restart"
SEND_EVENT = "session-restart-send"

# Decision kinds. Strings rather than an enum because they are written into the
# event log as-is and read back by the next reply end; an enum would be a second
# spelling of the same values.
NOTHING = "nothing"
END = "end"
CLEAR = "clear"
HOLD = "hold"
HOLD_CHILDREN = "hold-children"
SKIP = "skip"
NOT_TAKEN = "not-taken"

_USAGE = (
    "wfctl hook session-restart reads a Claude Code Stop payload on stdin, e.g.\n"
    "  printf '{\"session_id\":\"s\",\"transcript_path\":\"t.jsonl\",\"cwd\":\".\"}' "
    "| wfctl hook session-restart\n"
)


def threshold(environ: Mapping[str, str]) -> int:
    """The token count a restart begins at. 0 turns the restart off.

    Digits only, after trimming. `int()` alone accepts underscores and `-5`, neither
    of which a person setting a threshold means, and an unreadable value falling
    back to the default is the documented behaviour rather than a guess: the
    alternative, treating it as off, would silently disable a hook someone was
    trying to tune.
    """
    raw = environ.get(THRESHOLD_ENV, "").strip()
    return int(raw) if raw.isdigit() else DEFAULT_THRESHOLD


def occupancy(transcript: Path) -> int | None:
    """Tokens in the window as of the last reply, or None when it cannot be read.

    The *last* usage record, not a sum: each assistant message's usage already
    describes the whole window as it stood, so summing counts the same context
    once per turn. Input, cache read and cache creation together are what the
    window holds; output is not yet part of it.

    None rather than 0 for every failure, so the decision can say "unreadable"
    without a reader mistaking it for an empty window.
    """
    last: int | None = None
    try:
        with transcript.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                message = record.get("message") if isinstance(record, dict) else None
                usage = message.get("usage") if isinstance(message, dict) else None
                if not isinstance(usage, dict):
                    continue
                counts = [
                    usage.get(key, 0)
                    for key in (
                        "input_tokens",
                        "cache_read_input_tokens",
                        "cache_creation_input_tokens",
                    )
                ]
                if all(isinstance(c, int) for c in counts):
                    last = sum(counts)
    except OSError:
        return None
    return last


# What the harness writes when a child is launched, and what it writes when that
# child reports back. Both spellings are Claude Code's rather than wfctl's, and
# neither is documented as an interface — so every reader below treats their
# absence as "this session fanned out to nothing", which is true of almost every
# session and is the only reading that cannot hold a restart on a guess.
_AGENT_ID = "agentId"
_NOTIFICATION = "<task-notification>"
_TASK_ID = re.compile(r"<task-id>([^<]+)</task-id>")

# A delivered notification opens a line of its own; prose naming the tag has it
# mid-sentence. The harness prefixes some deliveries with a caution paragraph —
# "[SYSTEM NOTIFICATION - NOT USER INPUT]", then a blank line — so the tag is not
# always the start of the string, and a reader anchored there threw the report
# away along with the `<task-id>` that was the whole point of reading it.
_DELIVERED = re.compile(r"(?:\A|\n)[ \t]*" + re.escape(_NOTIFICATION))

# A child with no description of its own. A fork records none, and the count is
# what the hold turns on, so an unnamed child still has to occupy a row.
UNNAMED_CHILD = "subagent"


def _notifications(record: dict) -> list[str]:
    """Every `<task-notification>` this transcript record delivered to the session.

    The harness writes a child's report into more than one record shape, and which
    one it picks turns on what the parent was doing when the child finished. A
    session sitting at its prompt gets a `user` record whose content is the
    notification. A session *mid-turn* has the notification absorbed into the
    running turn instead, and the only record of it is an `attachment`. Reading
    the first shape alone missed the second, which is the more common one — and a
    child read as outstanding forever holds the restart forever, because the hold
    has no automatic exit.

    A queued copy is not a delivery. The same notification also passes through
    `queue-operation` records, but a queued item can be removed unsent
    (`resume_failed`), so counting one would release the hold for a report that
    never reached the session — the one direction this reader must not fail in.

    The `attachment` is on the delivered side of that line, which its own
    `queued_command` type makes easy to doubt: the name says where the item came
    from, not what became of it. The queue's records settle it, in this order —
    `enqueue`, then `remove` with reason `absorbed_mid_turn`, then the attachment
    carrying the rendered notification. The record is written as the item leaves
    the queue *into* the turn, and a notification-bearing attachment that was
    never rendered does not occur.

    The notification has to *open a line*, not merely appear somewhere: an agent
    that writes about task notifications puts the same tags in its own prose, and
    a looser read would let a session talk itself out of the hold. Requiring it to
    open the whole string — which this did first — is the same rule one notch too
    tight: the harness prefixes some deliveries with a caution paragraph and a
    blank line, and those were discarded along with the `<task-id>` that was the
    only reason to read them. Measured across 1512 transcripts, the two
    populations separate cleanly on the line: 35 prefixed deliveries, every tag
    opening a line, against 4 prose mentions, every tag mid-sentence.
    """
    texts = []
    if record.get("type") == "user":
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str) and _DELIVERED.search(content):
            texts.append(content)
    attachment = record.get("attachment")
    if isinstance(attachment, dict):
        prompt = attachment.get("prompt")
        if isinstance(prompt, str) and _DELIVERED.search(prompt):
            texts.append(prompt)
    return texts


def outstanding_children(transcript: Path) -> list[str]:
    """Children this session launched that have not reported back, oldest first.

    A launch is a `toolUseResult` carrying an `agentId` — one shape for both an
    async subagent and a fork. The report is a later `<task-notification>` naming
    that id; `_notifications` owns which record shapes count as one.

    Descriptions, never ids. The launch result says in its own text that an
    `agentId` is internal metadata that must not reach a person, and this list
    feeds a message printed in the pane.

    A transcript that cannot be read reports nothing outstanding. Holding on a
    file wfctl could not open would hold every restart on the branch with nothing
    able to release it — and `occupancy` has already decided *nothing* on that
    same file, so the case does not reach here in the hook.
    """
    launched: dict[str, str] = {}
    reported: set[str] = set()
    try:
        with transcript.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if _AGENT_ID not in line and _NOTIFICATION not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(record, dict):
                    continue
                result = record.get("toolUseResult")
                if isinstance(result, dict):
                    agent_id = result.get(_AGENT_ID)
                    if isinstance(agent_id, str) and agent_id:
                        described = result.get("description")
                        launched[agent_id] = (
                            described if isinstance(described, str) and described
                            else UNNAMED_CHILD
                        )
                for text in _notifications(record):
                    reported.update(_TASK_ID.findall(text))
    except OSError:
        return []
    return [name for agent_id, name in launched.items() if agent_id not in reported]


def read_events(state_dir: Path) -> list[dict]:
    """Every well-formed record in the branch's event log, in line order.

    A malformed or non-object line is skipped rather than raising, as every other
    reader of this log does: a torn final append must not stop a hook that runs
    on every reply end.
    """
    try:
        text = (state_dir / "events.jsonl").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    events = []
    for line in text.splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            events.append(record)
    return events


@dataclass(frozen=True)
class Decision:
    """What one reply end decided. `send` is the send event a report is about.

    `end_pos` is set only on `CLEAR`: the index in `events` of the handoff's own
    `end` record, the moment `session-summary.md` was written. `run_hook` reads
    from there forward for anything the same turn recorded afterward, and folds
    it back in before the clear it is about to send (#371).

    `children` is set only on `HOLD_CHILDREN`, and carries descriptions rather
    than a count so the event log says *which* children held the restart. A
    tuple because the dataclass is frozen and tests compare whole decisions.
    """

    kind: str
    handle: str | None = None
    send: dict | None = None
    end_pos: int | None = None
    children: tuple[str, ...] = ()

    @property
    def texts(self) -> list[str]:
        """What the worker types, in order. Empty for every decision that sends nothing."""
        if self.kind == END:
            return [END_TEXT]
        if self.kind == CLEAR:
            return [CLEAR_TEXT, START_TEXT]
        return []


def decide(
    session: str,
    tokens: int | None,
    limit: int,
    events: Sequence[dict],
    find_handle: Callable[[], str | None],
    find_children: Callable[[], Sequence[str]],
) -> Decision:
    """The restart's whole decision, as a pure function of what the hook read.

    `find_handle` and `find_children` are callables rather than values because
    one is a subprocess and the other a second pass over the transcript, and only
    the reply ends that would begin a restart need either — most decide nothing
    and should not pay for them. Neither has a default: a correctness condition
    that a caller can omit is one that new callers will omit.

    The rules, first match wins, are `data-model.md`'s table, with one exception:
    the children hold is #425's and that table is #371's, so `hold-children` has
    no row there and the decision tree it draws has no branch for it. The comments
    below carry why each rule sits where it does.
    """
    # Off, and under the threshold, first. A restart in progress is always over
    # it — neither the handoff turn nor a clear that did not take shrinks the
    # window, and a clear that did take starts a session with no events — so the
    # common reply end reads no events at all.
    if limit == 0 or tokens is None or tokens < limit:
        return Decision(NOTHING)

    def last(kind: str, match: Callable[[dict], bool], after: int = -1) -> tuple[int, dict] | None:
        for i in range(len(events) - 1, after, -1):
            e = events[i]
            if e.get("event") == kind and e.get("session") == session and match(e):
                return i, e
        return None

    def decided(what: str, after: int = -1) -> tuple[int, dict] | None:
        return last(DECISION_EVENT, lambda e: e.get("decision") == what, after)

    def sent(text: str, after: int) -> tuple[int, dict] | None:
        return last(
            SEND_EVENT,
            lambda e: e.get("text") == text and isinstance(e.get("exit"), int),
            after,
        )

    planned_clear = decided(CLEAR)
    if planned_clear:
        pos = planned_clear[0]
        send = sent(CLEAR_TEXT, pos)
        # A reply end between the decision and its send is a person typing in the
        # seconds before the worker ran. Deciding now would report on a guess.
        if send is None or decided(NOT_TAKEN, pos):
            return Decision(NOTHING)
        return Decision(NOT_TAKEN, send=send[1])

    planned_end = decided(END)
    if planned_end:
        pos = planned_end[0]
        send = sent(END_TEXT, pos)
        if send is None:
            return Decision(NOTHING)
        if send[1]["exit"] != 0:
            # Never retried: a retry types into a pane a person may be using.
            if decided(NOT_TAKEN, pos):
                return Decision(NOTHING)
            return Decision(NOT_TAKEN, send=send[1])
        # Any stop after the send, continued or not. The clear depends on the
        # handoff being newer than every earlier one, and a wrapped-up stop typed
        # by hand in a held session is that too.
        end_after = [
            i for i in range(send[0] + 1, len(events)) if events[i].get("event") == "end"
        ]
        if end_after:
            handle = find_handle()
            if handle:
                return Decision(CLEAR, handle=handle, end_pos=end_after[0])
            return Decision(NOTHING) if decided(SKIP, pos) else Decision(SKIP)
        return Decision(NOTHING) if decided(HOLD, pos) else Decision(HOLD)

    # Nothing is under way, so this reply end would begin one. Children first,
    # and only here: the restart is held before the handoff rather than before
    # the clear, because the handoff is the artifact their results have to reach
    # and it is written by the turn `END` asks for. Holding the clear instead
    # would write the handoff while they were still out, and `END` is never
    # planned twice (#425) — so there would be no second turn to fold them into.
    children = tuple(find_children())
    if children:
        held = decided(HOLD_CHILDREN)
        # Said once per growth, not once per session. A panel reporting one at a
        # time shrinks this set on every reply end, and a message for each shrink
        # would bury the one that mattered — but a *new* panel sent later is a
        # new hold, and the first version stayed silent for it, leaving the only
        # copy of the escape hatch unprinted.
        #
        # The signal is a description the hold does not already account for, and
        # it is counted rather than set-tested: descriptions repeat. A panel names
        # its reviewers `r1`, `r2`, `r3` every run, so a set difference is empty
        # exactly when a new fan-out reuses an earlier name — and pairing it with
        # a rising total missed the case where one child reports as another
        # launches under its name, which shrinks the total while the set stays put.
        # The multiset answers both in one question.
        #
        # Identity is still the description, because that is all the event records
        # — two fan-outs named alike read as one, which is the cost of keeping
        # `agentId` out of the log.
        if held:
            # A row this reader cannot make sense of counts as no children held,
            # which speaks. `Counter` of a stray string would tally its characters
            # and answer a different question quietly, and every reader of this
            # log already treats a shape it did not write as absent.
            before = held[1].get("children")
            if not Counter(children) - Counter(before if isinstance(before, list) else ()):
                return Decision(NOTHING)
        return Decision(HOLD_CHILDREN, children=children)

    handle = find_handle()
    if handle:
        return Decision(END, handle=handle)
    return Decision(NOTHING) if decided(SKIP) else Decision(SKIP)


def message(decision: Decision, repo_root: Path) -> str | None:
    """What the pane shows for `decision`, or None for the ones that show nothing.

    Said to the person, not the model — these ride `systemMessage`, which Claude
    Code prints under `Stop hook feedback:` (#298). The model channel would invite
    the agent to act on the pane itself, which is the act it is refused.
    """
    if decision.kind == HOLD:
        return "session restart held: /end-session recorded no stop — context not cleared"
    if decision.kind == HOLD_CHILDREN:
        count = len(decision.children)
        noun = "subagent" if count == 1 else "subagents"
        # The escape hatch, named where the person who finds the held pane reads
        # it. There is no automatic one on purpose: a hold that expires is the
        # timeout #425 rejects, and the only party who can tell a slow child from
        # a dead one is whoever comes back to the pane.
        #
        # Both commands, because the hook will not supply the second. A hand-typed
        # `/end-session restart` records a stop but no *planned* end, so `decide`
        # never reaches the branch that sends the clear — it falls back here,
        # finds the hold already recorded and decides nothing. Naming one command
        # left the person holding half a sequence with nothing to say so.
        return (
            f"session restart held: {count} {noun} still running — context not "
            "cleared; run /end-session restart then /clear yourself if they "
            "never report"
        )
    if decision.kind == SKIP:
        return f"session restart skipped: no workmux pane for {repo_root}"
    if decision.kind == NOT_TAKEN and decision.send is not None:
        send = decision.send
        if send.get("exit") == 0:
            ts = send.get("ts")
            at = f"{ts[11:16]}Z" if isinstance(ts, str) and len(ts) >= 16 else "an earlier reply"
            return (
                f"session restart sent /clear at {at} and this session is still "
                "here — run /clear yourself, or /end-session first"
            )
        return (
            f"session restart never sent {send.get('text')} "
            f"(workmux exited {send.get('exit')}) — run it yourself"
        )
    return None


def find_handle(repo_root: Path) -> str | None:
    """The workmux handle whose worktree is `repo_root`, or None.

    Matched on `path` rather than on the directory's name, so a handle that is
    not its directory still resolves. `is_open` is not consulted: the main
    checkout lists `false` there and a send to it still reaches its pane.
    """
    try:
        out = subprocess.run(
            ["workmux", "list", "--json"],
            capture_output=True, text=True, timeout=5, check=True,
        )
        entries = json.loads(out.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if not isinstance(entries, list):
        return None
    root = repo_root.resolve()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path, handle = entry.get("path"), entry.get("handle")
        if isinstance(path, str) and isinstance(handle, str) and Path(path).resolve() == root:
            return handle
    return None


# The event `record_outward_action` writes (`_session.py`), for a push reported
# with `wfctl report-action` or a tracker write `wfctl issue` recorded itself.
# `notify-declined` was the other until #384 removed `--declined` with the grant
# it was a decline of; an old log's line of it is left where it is, unread.
_LATE_EVENTS = ("notify-action",)


def amend_summary_for_late_events(state_dir: Path, events: Sequence[dict], end_pos: int) -> None:
    """Fold an outward action recorded after the handoff back into it.

    `wfctl end` writes `session-summary.md` mid-turn (step 3 of `end-session`);
    anything the same turn does afterward — a `report-action push` at step 5,
    say — has no later step that revisits the file. Once `/clear` runs next,
    that fact is gone from everywhere a person or the next session would look
    (#371 ledger: a push at 14:24:38 traced real against `origin`, eight seconds
    after the summary it never reached). `events.jsonl` already has it; this
    reads from `end_pos` forward and appends what it finds, once, right before
    the clear that would otherwise outrun it.

    A missing summary file is not this function's problem to raise on — there
    is nothing to amend, and the restart still clears.
    """
    late = [e for e in events[end_pos + 1:] if e.get("event") in _LATE_EVENTS]
    if not late:
        return
    summary_file = state_dir / "session-summary.md"
    try:
        body = summary_file.read_text(encoding="utf-8")
    except OSError:
        return

    from wfctl._io import write_atomic

    lines = ["", "## Recorded After This Summary Was Written", ""]
    for e in late:
        lines.append(f"- {e.get('ts', '?')} — {e.get('action')}")
    write_atomic(summary_file, body.rstrip("\n") + "\n" + "\n".join(lines) + "\n")


def spawn_worker(plan: dict) -> None:
    """Start the sender in its own session and return without waiting.

    Its own session so the harness does not count it as the hook's work, and so
    nothing that kills the hook at its timeout takes the sends with it — both
    observed on Codex when the sends ran as a plain background child (#371 ledger
    entry 16).
    """
    subprocess.Popen(
        [sys.executable, "-m", "wfctl._restart_send", json.dumps(plan)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def _repo_root(cwd: str) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    top = out.stdout.strip()
    return Path(top) if top else None


def run_hook(
    stdin: bytes | str,
    environ: Mapping[str, str],
    spawn: Callable[[dict], None] = spawn_worker,
    handle_for: Callable[[Path], str | None] = find_handle,
) -> str | None:
    """One reply end, start to finish. The stdout to print, or None.

    The two callables are the hook's only effects past its own event, taken as
    arguments so a test can run the whole path without a pane or a process.
    """
    from wfctl._io import append_event
    from wfctl._paths import resolve_agent_dir, resolve_branch

    try:
        payload = json.loads(stdin or "{}")
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    session = payload.get("session_id")
    transcript = payload.get("transcript_path")
    cwd = payload.get("cwd")
    if not all(isinstance(v, str) and v for v in (session, transcript, cwd)):
        return None
    assert isinstance(session, str) and isinstance(transcript, str) and isinstance(cwd, str)

    limit = threshold(environ)
    transcript_file = Path(transcript).expanduser()
    tokens = occupancy(transcript_file) if limit else None
    if limit == 0 or tokens is None or tokens < limit:
        return None

    repo_root = _repo_root(cwd)
    if repo_root is None:
        return None
    state_dir = resolve_agent_dir(repo_root, resolve_branch(repo_root), create=False)
    # A branch wfctl never ran on has no log to remember a decision in, so every
    # reply end over the threshold would plan the restart afresh. Nothing is the
    # only answer that cannot repeat.
    if not state_dir.is_dir():
        return None

    events = read_events(state_dir)
    decision = decide(
        session,
        tokens,
        limit,
        events,
        lambda: handle_for(repo_root),
        lambda: outstanding_children(transcript_file),
    )
    if decision.kind == NOTHING:
        return None

    if decision.kind == CLEAR and decision.end_pos is not None:
        amend_summary_for_late_events(state_dir, events, decision.end_pos)

    # `children` only where there are any. `decide` reads this field back to tell
    # a second fan-out from the one it already held, and an empty list on every
    # other decision is a row that answers that question for a decision which was
    # never asked it.
    extra = {"children": list(decision.children)} if decision.children else {}
    append_event(
        state_dir,
        DECISION_EVENT,
        session=session,
        decision=decision.kind,
        occupancy=tokens,
        threshold=limit,
        handle=decision.handle,
        **extra,
    )
    if decision.texts:
        try:
            spawn({
                "parent": os.getpid(),
                "handle": decision.handle,
                "session": session,
                "state_dir": str(state_dir),
                "texts": decision.texts,
            })
        except OSError:
            # A worker that never started writes no send event of its own, and
            # `decide()` reads a decision with no send as "ambiguous, check
            # again" (#371 ledger). Left unrecorded, every later reply end would
            # retry that same read forever, silently, with no report on any of
            # them. Recording the failure here as a send with exit -1 is the
            # vocabulary `_send` already uses for "could not run" — it routes
            # into the existing not-taken report instead of a new state.
            append_event(
                state_dir, SEND_EVENT, session=session, text=decision.texts[0], exit=-1,
            )
    text = message(decision, repo_root)
    return json.dumps({"systemMessage": text}) if text else None


def hook_main() -> int:
    """`wfctl hook session-restart`. Exit 0 on every path.

    A non-zero exit on `Stop` blocks the stop, so a bug here would turn every
    reply end into a loop — and this hook types into the pane it would loop in.
    """
    if sys.stdin.isatty():
        # Run by hand with nothing piped, a read to EOF looks like a hang (#385).
        sys.stderr.write(_USAGE)
        return 0
    try:
        out = run_hook(sys.stdin.buffer.read(), os.environ)
    except Exception:
        return 0
    if out:
        print(out)
    return 0
