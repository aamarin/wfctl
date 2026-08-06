# Phase 1 Quickstart: update-install-skills-default

How to exercise the feature by hand, and the one check automated tests cannot
cover.

## Scratch repo

```bash
cd "$(mktemp -d)" && git init -q . && git commit -q --allow-empty -m init
```

## 1. Default install

```console
$ wfctl install-skills
No issue tracker configured. wf-skills ships a GitHub backend
(.agents/trackers/github.json, via the `gh` CLI).
Install it? [Y/n]: y
✓ Installed from https://github.com/aamarin/wf-skills@main
  base     25 skills · 23 commands · 8 runtime · 1 tracker

Installed to .agents/ — skills and commands in their canonical, agent-agnostic
form. If your agent needs its own native paths:
  Claude   wfctl install-skills --agent claude
  Bob      wfctl install-skills --agent bob
  Copilot  wfctl install-skills --agent copilot
```

Verify:

```bash
test ! -d .claude && echo "SC-001 ok: no assistant-specific files"
python3 -c "import json;m=json.load(open('.wf-skills-manifest.json'));\
assert list(m)==['base','tracker'],list(m);\
assert all(i['path'].startswith(('.agents/','.specify/')) for i in m['base']['items'])" \
  && echo "manifest ok"
```

## 2. Add the Claude layer

```console
$ wfctl install-skills --agent claude
✓ Installed from https://github.com/aamarin/wf-skills@main
  base     25 skills · 23 commands · 8 runtime · 1 tracker
  claude   23 commands · 3 skills
```

The absence of a `ℹ Backed up N pre-existing file(s)` line is the point — it is
today's bug not firing. Verify the Claude layout is unchanged from before this
feature:

```bash
ls .claude/commands | wc -l    # 23
ls .claude/skills   | wc -l    # 3 — only `deployment: skill` entries
```

## 3. Copilot

```console
$ wfctl install-skills --agent copilot
✓ Installed from https://github.com/aamarin/wf-skills@main
  base     25 skills · 23 commands · 8 runtime · 1 tracker
  copilot  25 skills
```

```bash
diff -r .agents/skills .github/skills && echo "byte-identical, no transform"
```

## 4. Codex informs, does not fail

```console
$ wfctl install-skills --agent codex
ℹ Codex has no repo-local command path — its prompts live in ~/.codex/prompts
  (never shared through a repo) and its repo entry point is AGENTS.md.
  Installing the base layer only.
✓ Installed from https://github.com/aamarin/wf-skills@main
  base     25 skills · 23 commands · 8 runtime · 1 tracker
$ echo $?
0
```

## 5. Uninstall leaves the base alone

```bash
wfctl uninstall-skills --agent claude
test ! -e .claude/commands/speckit.plan.md && test -d .agents/skills && echo "base survived"
```

Uninstall removes the items it recorded, not their parent directories, so empty
`.claude/commands` and `.claude/skills` remain. Pre-existing behavior — master
does the same — so the check targets a file rather than the directory.

## 6. Non-interactive

```console
$ wfctl install-skills < /dev/null
✓ Installed from https://github.com/aamarin/wf-skills@main
  base     25 skills · 23 commands · 8 runtime
```

No prompt, no `.agents/trackers/`. This is the shape a workmux `post_create`
hook or a CI step sees.

## 7. The check tests cannot do — Copilot discovery

`research.md` records that `.github/skills` was chosen from spec-kit's source,
not from an observed Copilot session. Close that with a live run:

```bash
cd "$(mktemp -d)" && git init -q . && git commit -q --allow-empty -m init
wfctl install-skills --agent copilot
copilot   # then ask it to list available skills, and to run `start-session`
```

**Pass**: Copilot lists the installed skills and can run one.
**Fail**: fall back to `.github/agents/<name>.agent.md` with the frontmatter
transform from issue #5 — a change to the `copilot` entry in `_AGENT_TARGETS`
plus an extras hook, touching nothing else in the plan.

Second thing to watch in the same session: whether Copilot auto-invokes a skill
carrying `disable-model-invocation: true`, which is Claude-specific. If it does,
skills meant to be user-triggered will fire on their own — note it, it does not
block this feature.

## Regression suite

```bash
uv run pytest -q     # 194 passing before this feature's tasks begin
```
