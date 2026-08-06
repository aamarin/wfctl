# Delivery Plan: update-install-skills-default (005)

**Feature**: `005-update-install-skills-default` | **Date**: 2026-08-01
**Source**: `specs/005-update-install-skills-default/tasks.md` (39 tasks)
**Parent issue**: [#5](https://github.com/aamarin/wfctl/issues/5)

---

## File-Touch Matrix

| File | Tasks | Operation |
|---|---|---|
| `wfctl/cli.py` | T004–T008, T012–T014, T019, T020, T025–T027 | MODIFY |
| `tests/test_install_skills.py` | T003, T006, T010, T011, T014, T015, T017, T018, T020, T022–T024 | MODIFY |
| `README.md` | T036 | MODIFY |
| `pyproject.toml` | T037 | MODIFY |
| `wfctl/__init__.py` | T037 | MODIFY |
| *(none — read-only or scratch repo)* | T001, T002, T009, T016, T021, T028–T035, T039 | — |
| *(gitignored spec artifacts)* | T038 | MODIFY |

**5 repo source files → S size.**

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 | T001–T039 | `wfctl/cli.py` (mod), `tests/test_install_skills.py` (mod), `README.md` (mod), `pyproject.toml` (mod), `wfctl/__init__.py` (mod) | S | `uv run pytest -q` green + full `quickstart.md` pass (T039) |

**Rationale**: **Single PR.** All four signals point the same way:

1. **File conflict risk** — 15 of 39 tasks edit `wfctl/cli.py` and 13 edit
   `tests/test_install_skills.py`. Splitting produces two PRs racing on the same
   two files. They sequence cleanly, so one PR.
2. **Reviewability** — the layer split (T004), the default flip (T012), and the
   union check (T019) cannot be assessed apart. A reviewer seeing only the
   default flip cannot tell whether existing repos survive it.
3. **Mergeable increment** — **this is the decisive one.** US1 alone is not
   safely mergeable: flipping the default without US2's union check makes every
   existing repo's first upgrade prompt to overwrite ~25 files wfctl installed
   itself. The MVP boundary in `tasks.md` is a *demo* boundary, not a merge
   boundary.
4. **Story independence** — the four stories share `_BASE_TARGETS`,
   `_AGENT_TARGETS`, and one function. Not independent at runtime.

**PR closes**: `Closes #5`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #5 | T001–T039 | `feat(install-skills): default to agents-only, add --agent copilot target` | 3–5 h | PR 1 |

**Grouping pattern**: Single issue.
**Rationale**: One PR delivering one coherent capability, at S size — the default
case in the grouping table.

**No new issues are created by this decompose.** The branch already carries its
issue key (`005` → GitHub #5), which `speckit-specify` required before the spec
existed. Creating sub-issues here would break the one-PR-one-issue rule, since a
single PR would then close several.

Issue #5's body needs four corrections before the PR lands — the design diverged
from it during brainstorming, and the divergences are recorded in `spec.md`
Assumptions:

| Criterion | Issue #5 says | Built instead |
|---|---|---|
| 1 | bare install → `.agents/skills` only | `.agents/skills` **and** `.agents/commands` |
| 3 | `.github/agents/<name>.agent.md` + frontmatter transform | `.github/skills/<name>/SKILL.md`, plain copy |
| 4 | `--agent codex` errors | informs and installs the base layer, exit 0 |
| 5 | fix the cross-attribution | delete it — layers write disjoint paths |

Estimate in #5 ("Medium — the real work is the Copilot frontmatter transform")
is also stale; that transform disappeared with the skills layout.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 | Touch no repo files — baseline suite run and reference-layout capture in a scratch repo |
| 1 | Sequential | T003 → T004 → T005 → T006 → T007 → T008 → T009 | Foundational. All in `cli.py` / test module; T004 depends on T003 failing first |
| 2 | Sequential | T010 → T011 → T012 → T013 → T014 → T015 → T016 | US1. Tests before implementation |
| 3 | Sequential | T017 → T018 → T019 → T020 → T021 | US2. T017 must FAIL before T019 |
| 4 | Sequential | T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 | US3. T028 is the external Copilot check and gates the design |
| 5 | Parallel | T030 ‖ T031 ‖ T032 ‖ T033 ‖ T034 → T035 | US4 is verification-only; all five are assertions over existing tests and can run as one `pytest` invocation |
| 6 | Parallel | T036 ‖ T037 → T038 → T039 | `README.md` and `pyproject.toml`/`__init__.py` share no file; T038 depends on T028's outcome |

**Single-agent order** (recommended): T001 → T002 → T003 → … → T039, straight through.

### On the thin parallelism

The skill's red-flag list treats "no parallelism detected" as a signal to
re-examine task definitions. Re-examined; the finding stands. This feature is a
sequential refactor of two files — `_AGENT_TARGETS` cannot be restructured
concurrently with the loop that consumes it, and two agents editing
`tests/test_install_skills.py` would conflict on every task. The parallelism
that exists (waves 0, 5, 6) is real; manufacturing more would mean splitting
tasks that share a file, which the framework explicitly warns against.

---

## Agent Fanning Instructions

Single agent recommended. At S size with two hot files, fan-out costs more in
merge conflicts than it saves in wall-clock time. The wave table above is for
sequencing and gate placement, not for dispatch.

**Fan-in gates** (each must be green before the next wave):

| After wave | Command |
|---|---|
| 1 | `uv run pytest -q` (T009) |
| 2 | `uv run pytest -q` + `quickstart.md` §1 (T016) |
| 3 | `uv run pytest -q` + `quickstart.md` §2 (T021) |
| 4 | `uv run pytest -q` + `quickstart.md` §3–§5 (T029) |
| 5 | `uv run pytest -q` + `quickstart.md` §6 (T035) |
| 6 | `uv run pytest -q` + full `quickstart.md` (T039) |

---

## Risk

**T028 can invalidate the plan.** The live Copilot discovery check is the only
task whose failure changes the design rather than the code. Its fallback — the
`.agent.md` transform from issue #5 — touches only the `copilot` entry in
`_AGENT_TARGETS` plus an extras hook, and leaves waves 0–3 and 5–6 intact. It
sits in wave 4 rather than wave 0 because it cannot run until T025 has installed
something for Copilot to discover.

**Scope note.** This branch already carries seven commits, six of which are
adjacent fixes unrelated to #5 (tracker consent, two `_paths` fixes, the
speckit-artifact gitignore, the archive script, the state-dir flatten). The PR
will therefore be wider than this delivery plan describes. Worth deciding before
opening it whether those ride along or move to their own branch.
