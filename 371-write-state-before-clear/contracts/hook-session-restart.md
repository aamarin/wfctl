# Contract: `wfctl hook session-restart`

An installed interface: the command string is written into consumers'
`.claude/settings.json`, so the subcommand name, the stdin shape it reads and the
stdout shape it writes are versioned with wfctl.

## Invocation

```
wfctl hook session-restart 2>/dev/null || true
```

Installed on `Stop` by `wfctl install-skills --agent claude`, beside
`wfctl hook response-shape`. Exactly argv `["hook", "session-restart"]` takes
`_entry.py`'s fast path; anything longer reaches typer.

## Stdin

Claude Code's Stop payload, JSON. Read: `session_id` (str), `transcript_path`
(str), `cwd` (str). Any other shape, a missing field, or undecodable bytes →
decide nothing.

A terminal on stdin (run by hand) → print one usage line to stderr naming an
example pipe, exit 0. (#385's fix, applied to this subcommand from the start.)

## Environment

| Variable | Meaning |
|---|---|
| `WFCTL_RESTART_THRESHOLD` | digits → that many tokens; `0` → off; anything else or unset → 200000 |
| `WFCTL_STATE_DIR`, `WFCTL_BRANCH` | honoured as everywhere else in wfctl |

## Stdout

Nothing, or exactly one JSON object:

```json
{"systemMessage": "<one of the messages below>"}
```

| Decision | Message |
|---|---|
| hold | `session restart held: /end-session recorded no stop — context not cleared` |
| skip | `session restart skipped: no workmux pane for <repo root>` |
| not-taken, exit 0 | `session restart sent /clear at <HH:MMZ> and this session is still here — run /clear yourself, or /end-session first` |
| not-taken, exit ≠ 0 | `session restart never sent <text> (workmux exited <n>) — run it yourself` |

`<text>` is `/end-session restart` or `/clear`. `<HH:MMZ>` is the `ts` of the
`/clear` send event. Skip names the repo root because no handle was found.

## Exit

Always 0, including on an exception inside the decision or the spawn.

## Pane sends

Performed by `python -m wfctl._restart_send '<json plan>'`, detached
(`start_new_session=True`), never by the hook process itself.

Plan: `{"parent": <pid>, "handle": str, "session": str, "state_dir": str,
"texts": [str, ...]}`.

| Decision | `texts` |
|---|---|
| end | `["/end-session restart"]` |
| clear | `["/clear", "/start-session"]` |

Each text: `workmux send <handle> <text>`, timeout 10 s, then one
`session-restart-send` event. 2 s after the parent exits before the first text,
5 s between texts. The worker exits 0 on every path and writes nothing to stdout.

## `/end-session restart`

The only argument `end-session` acts on. Its section: close with
`wfctl end --continued`, fill the summary in full, skip steps 6 and 7, and state
in the summary that the tree was left as found. Any other argument: behaviour as
without one.
