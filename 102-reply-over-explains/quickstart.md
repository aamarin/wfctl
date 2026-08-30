# Verification runbook

What to run, in order, and what each step catches that the previous one cannot.

## 1. The suite

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
```

All three green. This is `CLAUDE.md`'s definition of done and exactly what CI
runs on 3.11 and 3.13.

Use `uv run`, not a bare `pytest` — the dev deps are pinned on purpose and
`uv run` is what applies the pin. A bare `python3 -m pytest` reports failures
that are not real.

**Catches**: a broken cross-reference, a dropped skill.
**Misses**: everything about whether the skill reads correctly. The suite checks
that skills ship and cross-reference, not their content.

## 2. Install and exercise

```bash
wfctl install-skills
wfctl doctor
```

`doctor` green or with no finding that still stands.

Then exercise the changed skill — a change under `wfctl/agents/` is not verified
by the suite alone.

**Catches**: a skill that ships but does not load.

## 3. The structural invariants

```bash
# C-7 — line ceiling
wc -l wfctl/agents/skills/conversation-response-shape/SKILL.md      # ≤ 450

# C-6 — no wfctl vocabulary inside examples
awk '/^```/{f=!f} f && /wfctl/' \
  wfctl/agents/skills/conversation-response-shape/SKILL.md          # expect empty

# C-5 — the selection table has exactly one home
grep -rc "The material is" wfctl/agents/ | grep -v ':0'             # expect one file

# C-3 — existing rule numbers did not move
grep -n "^## [0-9]\." wfctl/agents/skills/conversation-response-shape/SKILL.md
```

**Catches**: FR-005a, FR-006, FR-009 violations, and budget overrun.

## 4. The reply-quality criteria

The part no command covers. Five fixed tasks — issues #88, #90, #76, #85, #61 —
run against the edited skill in a fresh context.

Score #88 against `judgment-test.md` — seven yes/no questions, written before
any run. Any *no* in J1-J4 is a failure regardless of length.

The other four issues are read unscored, for J5 and J6 only. They have no
per-task baseline and inventing one would overstate what is known.

Word count is recorded, never reported alone (SC-012). It counts presence, not
correctness — a forty-word reply already failed a real reader on #556.

**This validates; it does not gate.** It runs after the edit. A bad result is an
issue against the design, not a blocked merge.

## What none of this can check

Whether the rules survive a long session. Every measurement above starts from a
fresh context, and the skill's documented failure is that its rules go missing
around forty turns in. #85 owns that, and this feature adds ~50 lines to the file
it happens to.
