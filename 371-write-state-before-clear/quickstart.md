# Quickstart: exercising the session restart

## Suite

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
```

## Install into this worktree

```bash
uv run wfctl install-skills --agent claude --yes
uv run wfctl doctor
jq '.hooks.Stop' .claude/settings.json      # two wfctl rows: response-shape, session-restart
```

## Decide by hand, no pane

```bash
T=$(ls -t ~/.claude/projects/*371-write-state-before-clear/*.jsonl | head -1)
printf '{"session_id":"probe","transcript_path":"%s","cwd":"%s"}' "$T" "$PWD" \
  | WFCTL_RESTART_THRESHOLD=1 WFCTL_STATE_DIR="$(mktemp -d)" PATH="$PWD/tests/stubs:$PATH" \
    uv run wfctl hook session-restart
```

With a stub `workmux` on `PATH` that logs its argv, the first run prints nothing
and the stub logs `/end-session restart` a few seconds later; `events.jsonl` in the
temp state dir carries `session-restart` then `session-restart-send`.

## Live, in a Claude pane (the checks the suite cannot reach)

1. Remove `~/.claude/recycle-hook.sh` from `~/.claude/settings.json` so two hooks do not race on this pane.
2. `export WFCTL_RESTART_THRESHOLD=<current occupancy + 5000>` in the shell, and relaunch the pane from it.
3. Work a few turns. Expect `/end-session restart` typed into the pane after the crossing reply.
4. After that turn ends, expect `/clear` then `/start-session`.
5. Check: the new session's report quotes the handoff just written; `grep '"event": "end"' "$(uv run wfctl state-dir)/events.jsonl" | tail -1` carries `"continued": true`; `git status` is unchanged by the restart turn; the transcript id changed.
6. Unset the variable and relaunch.
