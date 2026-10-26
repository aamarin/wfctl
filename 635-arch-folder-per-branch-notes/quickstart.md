# Quickstart: checking the change by hand

Run these on a scratch branch after the implementation lands. Use `uv run` for
every wfctl command, so the working tree's code is what runs.

## 1. A boundary exception before `design.md`

```bash
uv run wfctl arch none --reason "Copy fix in one help string; nothing moves"
uv run wfctl feature-paths
uv run wfctl status --json
git status --short docs/architecture
```

Expect the success line and "Put the reason in the PR body.",
`exceptions/boundary.md` inside the folder `feature-paths` prints, `brainstorm` as
the current step, and nothing under `docs/architecture`.

## 2. Two pass exceptions beside it

With a `wfctl.json` declaring two passes, run `step none` on each, then:

```bash
ls "<FEATURE_DIR>/exceptions"
uv run wfctl status --json
```

Expect three files, both passes `skipped` with their reasons, and no pass named
`boundary`.

## 3. An old declaration doesn't count

Write `design.md` in the spec folder, remove `exceptions/boundary.md`, and add
`docs/architecture/declarations/<branch>.md`. Expect `brainstorm.architecture`
to read `in_progress`.

## 4. The Boundary line

Restore `exceptions/boundary.md` and run `uv run wfctl end`. Expect
`**Boundary**: answered` in `session-summary.md`.

## 5. The PR section

```bash
uv run wfctl check config
uv run wfctl check-body <a body without "## Moves a boundary?">
```

Expect `check config` green and `check-body` to report the section missing.

## 6. The skills

```bash
uv run wfctl install-skills --agent claude
grep -rn "declarations/" .agents .claude
```

Expect no match, and read `design-levels` level 2 and `opening-a-change`
Step 4 in the installed tree.
