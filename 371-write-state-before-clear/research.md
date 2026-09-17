# Research: Session restart that writes its handoff first

Every item is Decision / Rationale / Alternatives. Sources are file:line in this
worktree at 0fe553a, the brainstorm ledger (entries cited by number, in
`session-summary.md`), or a command run during planning.

## R1 — How the hook learns the context size

**Decision**: Read the transcript at `transcript_path` line by line and take the
*last* record carrying `message.usage`; occupancy is
`input_tokens + cache_read_input_tokens + cache_creation_input_tokens`. A missing
file, no usage record, or any parse failure is "unreadable", which decides nothing.

**Rationale**: Each assistant message's usage already describes the whole window
as it stood, so summing across messages double-counts (the personal script's own
comment, `20a8241b-…/recycle/recycle-hook.sh`). Measured on this branch: 0.02 s
for a 1.6 MB transcript (ledger entry 23).

**Alternatives**: Read only the tail of the file — faster on very long transcripts,
but a usage record can be followed by many non-usage lines (tool results), so a
fixed tail can miss it; not worth the edge case at 0.02 s. Parse
`last_assistant_message` from the Stop payload — carries text, not usage.

## R2 — What the hook needs from the Stop payload

**Decision**: `session_id`, `transcript_path`, `cwd`. Nothing else is read.

**Rationale**: Probe log `bfa026e1-…/clearprobe/probe.log` shows Claude's Stop
payload carries `session_id`, `transcript_path`, `cwd`, `stop_hook_active`,
`last_assistant_message`, `background_tasks` (ledger entry 27). `session_id`
changes on `/clear` (entry 1), which is what makes "same session is still here"
(state F) observable and what scopes every once-only rule.

**Alternatives**: Key on the transcript file name, as the personal script did —
equivalent on Claude, but the payload already names the session, and the event
log is keyed by what the payload calls it.

## R3 — Where the state dir comes from, and not creating one

**Decision**: `git -C <cwd> rev-parse --show-toplevel` → `_paths.resolve_branch`
→ the state dir path computed the way `_paths.resolve_agent_dir` does, **without**
its `mkdir`. The hook reads occupancy first and returns before resolving anything
when it is under the threshold. It only appends events when a state dir already
exists (a branch wfctl has run on).

**Rationale**: `resolve_agent_dir` (`_paths.py:687`) creates the directory. Called
from a hook on every Stop in every repo with the claude layer, it would litter the
XDG state tree with a directory per branch anyone ever replied on. Ordering the
cheap threshold check first keeps the common Stop to one file read.

**Alternatives**: Call `resolve_agent_dir` as-is — simplest, and the littering
is the cost. A new `resolve_agent_dir(create=False)` parameter — the chosen shape;
it is one flag on an existing function rather than a second copy of its path logic.

## R4 — Does a Stop hook's message reach the person in the pane?

**Decision**: Yes; emit `{"systemMessage": "<text>"}` on stdout.

**Rationale**: `hook_response_shape_cmd`'s docstring (`cli.py:4948-4955`, #298)
records that `systemMessage` on Stop now prints under `Stop hook feedback:` — it
was removed from that hook *because* the reader saw it twice. That settles the
spec's assumption for FR-008 without a probe. `additionalContext` is the wrong
channel here: it reaches the model, and states D/E/F are for the person.

**Alternatives**: `additionalContext` — reaches the model only, and would prompt
it to act on the pane's behalf, which the classifier refuses. stderr — the Stop
entry is installed `2>/dev/null`.

## R5 — How the hook knows there is a pane to send to

**Decision**: On a path that would send, run `workmux list --json` and look for an
entry whose `path` equals the repo root; its `handle` is the send target. No entry
→ *skip* (state E). Checked only on the Stops that would send.

**Rationale**: `workmux list --json` (run during planning) returns `handle`,
`branch`, `path`, `is_open` per worktree; this worktree's handle is
`371-write-state-before-clear`. Matching on `path` rather than on the directory
basename survives a worktree whose handle is not its directory name. `is_open` is
**not** used: the main checkout lists `is_open: false` and the personal script's
send still found its pane (its own comment), so `is_open` would produce false skips.

**Alternatives**: `basename(cwd)` as the personal script does — no subprocess, and
wrong for a handle that differs from the directory. Let the send fail and report
it on the next Stop — merges E into "never sent", losing the one message that says
*why*.

## R6 — Sending after the hook has exited

**Decision**: The hook spawns `sys.executable -m wfctl._restart_send` with
`start_new_session=True`, stdio to `DEVNULL`, passing a JSON plan on argv: parent
pid, handle, session id, state dir, and the ordered texts. The worker polls until
the parent pid is gone (capped at 10 s), sleeps 2 s, then for each text runs
`workmux send <handle> <text>` under `subprocess.run(timeout=10)`, appends one
`session-restart-send` event, and sleeps 5 s before the next text.

**Rationale**: Level-3 record `371-the-session-restart-sends-from-a-detached-worker`.
Entry 16: on Codex a send issued while the Stop hook ran was refused as "a task in
progress", and the hook was killed at its timeout taking the pending send with it;
`os.setsid` plus a post-exit delay fixed it. The 5 s gap between `/clear` and
`/start-session` is the personal script's, which has worked on Claude since
2026-09-11 (its comment). A timeout is the record's own Consequence.

**Alternatives**: Recorded in the level-3 record (detached `sh -c`, synchronous
send, re-invoking `wfctl hook session-restart --send`, a log file).

## R7 — Ordering "a stop after the send"

**Decision**: By position in `events.jsonl`, not by `ts`.

**Rationale**: `append_event` stamps `ts` to the second (`_io.py:73`). A send and
a short turn's `end` can share a second, and a `ts` comparison would then need a
tie rule that has no right answer. Line order is append order, which is the order
things happened for every writer on one machine.

**Alternatives**: `ts` with `>=` — misreads an `end` from the same second as the
Stop *before* the send. Sub-second `ts` — changes a format every reader shares,
for one consumer.

## R8 — The hot path's import cost

**Decision**: Route `hook session-restart` through `_entry.py`'s fast path, as
`hook worktree-guard` is, so a Stop that decides nothing never imports `typer` or
`rich`. `wfctl/_restart.py` imports only stdlib plus `wfctl._paths` and `wfctl._io`.

**Rationale**: `_hook.py`'s docstring measured `typer` + `rich` at ~74 ms of an
82 ms guard call. This hook runs on every Stop. SC-004's 0.2 s holds either way,
but the guard already paid for the pattern and `_entry.py` names the argv to match.

**Alternatives**: A plain typer command — simplest, ~75 ms more per reply end.
Still registered on `hook_app` so `--help` and the hook listing name it.

## R9 — The installer's identity

**Decision**: `MANAGED_HOOKS` becomes a tuple of `(event, command)` pairs; a
row's subcommand is the first whitespace-delimited word after `wfctl hook `.
`merge_hook` gains a `subcommand` argument and matches only rows with it. A new
`prune_unshipped(settings, event, shipped)` removes wfctl rows on `event` whose
subcommand is not in `shipped`. `managed_command` takes `subcommand`. `remove_hooks`
is unchanged — uninstall already removes every wfctl row on an event.

**Rationale**: Level-2 record `a-managed-hook-is-owned-by-its-subcommand`. Call
sites found by grep: `cli.py:2807` (install targets), `:2849` (merge), `:3084`
(uninstall — unchanged), `:5723` and `:5772` (doctor). `prior` in `_merge_hooks` is
keyed `(rel, event)` and becomes `(rel, event, subcommand)`; records gain nothing
new because `command` already carries the subcommand.

**Alternatives**: In the record.

## R10 — `end-session` receiving an argument

**Decision**: Add a `## User Input` block carrying `$ARGUMENTS` to
`wfctl/agents/commands/end-session.md`, and a section to
`wfctl/agents/skills/end-session/SKILL.md` that applies when the input is exactly
`restart`.

**Rationale**: Level-3 record `371-the-session-restart-instruction-lives-in-end-session`
verified that no wrapper reads `$ARGUMENTS` today; `speckit.clarify.md` shows the
block shape wfctl's wrappers already use for commands that do. The wrapper's
`allowed-tools` already covers `Bash(wfctl end*)`.

**Alternatives**: In the record.

## R11 — Which default the threshold reads

**Decision**: `WFCTL_RESTART_THRESHOLD`; `int(value)` for a string of digits
(`str.isdigit()` after strip), else 200000. `0` is off. 200000 is written once, as
`_restart.DEFAULT_THRESHOLD`.

**Rationale**: Level-3 record `371-the-session-restart-threshold-is-an-environment-variable`.
`isdigit` rejects `-5`, `1e5`, `200_000` and empty in one test; `int()` alone
accepts `200_000` and ` 5 `, which the spec does not name.

**Alternatives**: In the record.
