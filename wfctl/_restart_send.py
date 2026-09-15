"""The session restart's sender: `python -m wfctl._restart_send '<json plan>'`.

Started detached by `wfctl hook session-restart` and never by anything else. It
types the restart's texts into the pane with `workmux send`, after the hook that
started it has exited, and records what each send did
(`design/371-the-session-restart-sends-from-a-detached-worker`).

**After the hook exits.** A send issued while the `Stop` hook is still running
lands in a pane that counts the hook as a task in progress; on Codex `/clear` was
refused outright, and the hook was then killed at its timeout taking the pending
send with it (#371 ledger entry 16). Waiting on the parent pid rather than on a
fixed sleep is what makes the wait as short as the hook actually was.

**Records what each send did.** `workmux send` exiting 0 is not a send that took —
a `/clear` exited 0 on 2026-09-14 and the session kept growing for a day — but it
does separate "sent and did not take" from "never sent", and the next reply end
has to say which. The record is how it knows.

**Decides nothing.** Which texts, to which pane, for which session all arrive in
the plan. A worker that re-derived any of it would be a second decision beside
the hook's, running a few seconds later against a log that has since moved.

Exits 0 on every path and writes nothing to stdout: nobody reads either.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

from wfctl._io import append_event
from wfctl._restart import SEND_EVENT

# Seconds. Defaults a plan may override, which is how the tests run in
# milliseconds; the hook never overrides them.
#
# `wait_cap` bounds a parent that never exits. `settle` is the gap after it does,
# for the harness to finish the reply end it was running. `gap` separates `/clear`
# from `/start-session`: the second has to reach a prompt the first has already
# emptied, and five seconds is what the personal script this replaced has used on
# Claude since 2026-09-11. `timeout` bounds a hung `workmux` — a detached process
# nobody watches must not be able to wait forever.
WAIT_CAP = 10.0
SETTLE = 2.0
GAP = 5.0
TIMEOUT = 10.0


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _send(handle: str, text: str, timeout: float) -> int:
    """`workmux send`'s exit status, or -1 when it could not run or timed out."""
    try:
        return subprocess.run(
            ["workmux", "send", handle, text],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        ).returncode
    except (OSError, subprocess.SubprocessError):
        return -1


def run(
    plan: dict,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """Wait for the hook, send each text, record each send.

    Stops at the first send that fails. A `/start-session` typed after a `/clear`
    that never went would run inside the session the clear was meant to end.
    """
    parent = plan["parent"]
    handle = plan["handle"]
    session = plan["session"]
    state_dir = Path(plan["state_dir"])
    texts = plan["texts"]
    wait_cap = float(plan.get("wait_cap", WAIT_CAP))
    settle = float(plan.get("settle", SETTLE))
    gap = float(plan.get("gap", GAP))
    timeout = float(plan.get("timeout", TIMEOUT))

    deadline = clock() + wait_cap
    while _alive(parent) and clock() < deadline:
        sleep(0.05)
    sleep(settle)

    for i, text in enumerate(texts):
        if i:
            sleep(gap)
        code = _send(handle, text, timeout)
        append_event(state_dir, SEND_EVENT, session=session, text=text, exit=code)
        if code != 0:
            return


def main(argv: list[str]) -> int:
    try:
        run(json.loads(argv[0]))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
