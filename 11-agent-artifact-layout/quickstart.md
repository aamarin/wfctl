# Quickstart: validating the artifact layout change

**Branch**: `11-agent-artifact-layout` | **Date**: 2026-08-05

Runnable checks, ordered so a failure points at one story. Every command is
copy-pasteable; none needs a scratch repo except the last section.

## Preconditions

Both repositories checked out, tooling installed from the branch under test:

```bash
uv tool install --force --editable /path/to/wfctl
wfctl --version
```

## Story 1 — one directory holds a branch's artifacts

**The old path is gone from both repositories.**

```bash
git -C /path/to/wf-skills grep -nE '\.agent/'          # expect: no output
git -C /path/to/wfctl    grep -nE '\.agent/|"\.agent"' # expect: no output
```

The second pattern matters: `_pipeline.py` builds the path from components
(`repo_root / ".agent" / "spec.md"`), so a search for the literal `.agent/`
misses it. That is how it escaped the original issue's entry-point list.

**The archive numbers the design document first.**

```bash
cd /path/to/wfctl && uv run pytest tests/test_archive_story.py -q
```

**Step inference advances past brainstorm.**

```bash
cd <a worktree with specs/<branch>/design.md>
wfctl status        # expect: brainstorm ●, not ○
```

If this reports `brainstorm ○` while the file exists, check that
`specs/<branch>/` itself exists — `_infer_steps` short-circuits to all-incomplete
when the spec directory is absent, which masks the design document entirely.

## Story 2 — project overrides survive being committed

```bash
cd <a scratch repo>
printf '# Agent Guidelines\n\nAlways address the user as "Captain".\n' > AGENTS.md
git add AGENTS.md && git commit -m "add project overrides"
```

Run `/brainstorm` and confirm the instruction takes effect. Then confirm absence
is silent:

```bash
git rm AGENTS.md && git commit -m "remove"
```

Run `/brainstorm` again — it must proceed without error and must not recreate the
file.

## Story 3 — exactly one writer per artifact

```bash
cd /path/to/wf-skills
git grep -nE 'specs/<branch>/design\.md|design\.md' -- .agents/ | grep -iE 'write|save'
git grep -nE 'brief\.md' -- .agents/ | grep -iE 'write|save'
```

Each must return exactly one writing instruction. Before this change the second
returns two — `agent-brief` and `speckit-plan` — which is the collision the
feature removes.

Behavioural check: write a brief, run `/speckit.plan`, confirm the brief is
unchanged.

```bash
shasum specs/<branch>/brief.md      # before
# run /speckit.plan
shasum specs/<branch>/brief.md      # must match
```

## The skew diagnostic

```bash
cd <a scratch repo>
mkdir -p .agent && touch .agent/spec.md
wfctl doctor        # expect: ⚠ naming the superseded path and the fix
rm -rf .agent
wfctl doctor        # expect: the warning is gone
```

The check keys on the directory's presence, not on a version comparison, so it
self-clears once no installed component writes there.

## Full pipeline smoke

In a scratch repo with the tooling installed, on a branch named for a real
tracker issue:

```bash
wfctl start
# /brainstorm → /speckit.specify → /speckit.clarify → /speckit.plan
ls specs/<branch>/          # design.md, spec.md, plan.md, research.md, …
test ! -e .agent && echo "no .agent/ — pass"
```

Then remove the worktree and confirm the archive survived it:

```bash
wm remove <handle>
ls "$(wfctl state-dir)/archive/"     # 1-design.md … plus README.md index
```

## Known-good baseline

Recorded 2026-08-05 on this branch, before implementation — useful for telling a
regression from a pre-existing condition:

- `git grep -cE '\.agent/'` in wf-skills → 21 across 6 files
- `.agent/` references in wfctl → 4 source, 4 test
- `wfctl status` on this branch → `brainstorm ●  specify ●  clarify ●  plan ○`
