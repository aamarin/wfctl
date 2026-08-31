# Quickstart — verifying session truth ownership

Five checks, each one a defect this feature closes. Run them in a scratch
worktree; none needs the real spec root.

## 1. The report tracks artifacts, not writes

```bash
wfctl start
# write design.md into the feature dir by hand
wfctl status
```

**Expect**: `specify ← current`. Nothing was run in between, and the report moved
anyway.

## 2. Nothing exists — two ways, one answer

```bash
# with no feature directory at all
wfctl status
mkdir -p "$(wfctl feature-paths | sed -n 's/^FEATURE_DIR=.//p' | tr -d "'")"
wfctl status
```

**Expect**: identical pipelines. `brainstorm ○  ← current` both times, never a
dash.

## 3. A finished pipeline says so

Populate a feature dir through `implement` with every task checked, in a repo
with no definition of done.

**Expect**: the last line reads ``next: Story complete — open PR or run
`/end-session`.`` — one spelling, shared with what `next-step.md` carries —
rather than the report ending with no cursor and no sentence.

## 4. `end` claims nothing

```bash
wfctl end
cat "$(wfctl state-dir)/session-summary.md"
```

**Expect**: pipeline position, boundary, tree state. The word "complete" appears
nowhere — a finished pipeline reads `every step done` — and an unfilled handoff
reads as unfilled.

## 5. Fossils do not survive an upgrade

```bash
touch "$(wfctl state-dir)/current.md" "$(wfctl state-dir)/current.json"
wfctl status
ls "$(wfctl state-dir)"
```

**Expect**: both gone. `events.jsonl` and `session-summary.md` remain.

## Definition of done

```bash
uv run --frozen pytest -q
uv run --frozen ruff check wfctl/ tests/
uv run --extra dev mypy wfctl/
```

Then, because skills are not verified by the suite: `wfctl install-skills` and
run `/start-session` in a worktree, confirming it reads the pipeline report
rather than a file that no longer exists.
