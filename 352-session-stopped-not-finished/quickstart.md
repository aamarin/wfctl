# Quickstart: Session Stopped, Not Finished

Exercises the feature end to end. The suite reaches
`wfctl/agents/skills/start-session/SKILL.md` only as far as its table rows, so
the manual halves below are not optional — and there are five, because the
routing rule turns on two facts and a run that exercised one of them has tested
half a table.

## Automated — the repository's definition of done

```bash
uv run --frozen --extra dev pytest -q
uv run --frozen --extra dev ruff check wfctl/ tests/
uv run --frozen --extra dev mypy wfctl/
uv run wfctl doctor
```

`uv run`, never a bare `wfctl`. This repo has two and they disagree
permanently; whichever installed last reports green.

## Manual — install from the working tree first

```bash
uv run wfctl install-skills --agent "$WFCTL_AGENT"
```

Without this the skill you exercise is whatever the release put on disk, the
command succeeds, and your change is nowhere in it. Naming the agent matters as
much as the install: a bare run rewrites `.agents/` and leaves `.claude/`
exactly as stale as it found it, which is the copy your session reads.

## A trunk state dir, so halves 2 and 3 do not need a checkout

`WFCTL_BRANCH` is what the issue key is read off, and `WFCTL_STATE_DIR` keeps
the log out of this branch's own:

```bash
export TRUNK=$(mktemp -d)
alias trunk='WFCTL_STATE_DIR=$TRUNK WFCTL_BRANCH=main uv run wfctl'
```

## Half 1 — an issue branch carries on, whatever the stop said

```bash
uv run wfctl start
uv run wfctl end
```

Expect `✓ Session closed — …` — a deliberate wrap-up, the case that used to ask.
Fill the handoff's `## Next Session TODO` with a real sentence naming a first
action, open a session, and run `/start-session`.

**Expect it to quote that sentence, say what it is doing, and begin — with no
question put to you.** A question here is the feature not working, and this is
the half that shows the branch outranks the stop: the last stop was a wrap-up
and it carried on anyway.

## Half 2 — a trunk branch whose last stop was a wrap-up still asks

```bash
trunk start
trunk end
printf '# Handoff\n\n## Next Session TODO\n\n- [ ] rebase onto main\n' > "$TRUNK/session-summary.md"
```

Run `/start-session` with `WFCTL_STATE_DIR=$TRUNK WFCTL_BRANCH=main` in the
environment.

**Expect it to ask "What are we working on today?"**, offering that item as the
default. Same handoff, same filled sentence, opposite behaviour to half 1: the
branch is the only input that changed. This is the half that protects `main`,
which collects a handoff from every session that ever ended on it, and it is the
half a hurried exercise skips.

## Half 3 — a trunk branch whose last stop was continued carries on

```bash
trunk start
trunk end --continued
```

Expect `✓ Session stopped, not finished — …`.

```bash
grep '"event": "end"' "$TRUNK/events.jsonl" | tail -1
```

Expect `"continued": true`, and the earlier `false` line still above it —
nothing rewrites a stop already recorded. Run `/start-session` against the same
trunk state dir and the same filled handoff.

**Expect it to begin.** This is the one place the stop's kind decides a row, and
it is #352's own case: a run cut off on `main`, with nobody there to confirm it.

## Half 4 — the quote is still the gate

Replace the handoff's next action with the template placeholder, on either
branch:

```
## Next Session TODO

- [ ] (fill in)
```

```bash
uv run wfctl end --continued
```

Expect the FR-013 warning. Then run `/start-session`.

**Expect it to ask**, on the issue branch and on trunk alike. Neither the branch
nor a continued stop relaxes the requirement to quote a literal sentence
(FR-006, SC-003).

## Half 5 — nothing else moved

```bash
uv run wfctl status
uv run wfctl status --json
```

Expect output identical to a branch with no stop recorded. FR-015: the branch
history is the only place a continued stop is reported.

```bash
uv run wfctl log | tail -5
```

Expect the stops as `end` rows in the existing colour, their kind in the detail
string beside `step=`. No new event kind appears.
