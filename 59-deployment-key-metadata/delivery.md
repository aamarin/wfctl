# Delivery Plan: deployment key metadata (59)

**Feature**: `59-deployment-key-metadata` | **Date**: 2026-08-30
**Source**: this feature's `tasks.md` (31 tasks) — resolve via `wfctl feature-paths`
**Parent issue**: #59

---

## File-Touch Matrix

Eleven files change. Six of them are the same one-line deletion, which is why the
raw count overstates the reviewable surface — see the size note below.

| Task | File | Action |
|------|------|--------|
| T005, T006, T015 | `wfctl/cli.py` | MODIFY — delete `_skill_deployment()`, add `_MIRRORED_SKILLS`, rewire the mirror hook |
| T004, T007, T016, T021 | `tests/test_install_skills.py` | MODIFY — refound 4 mirror tests, add 3 new ones |
| T012 | `tests/test_skill_frontmatter.py` | CREATE — offline conformance assertion |
| T010 | `wfctl/agents/skills/architecture-decisions/SKILL.md` | MODIFY — drop one line |
| T010 | `wfctl/agents/skills/design-levels/SKILL.md` | MODIFY — drop one line |
| T010 | `wfctl/agents/skills/receiving-code-review/SKILL.md` | MODIFY — drop one line |
| T010 | `wfctl/agents/skills/using-superpowers/SKILL.md` | MODIFY — drop one line |
| T010 | `wfctl/agents/skills/verification-before-completion/SKILL.md` | MODIFY — drop one line |
| T011 | `wfctl/agents/skills/conversation-response-shape/SKILL.md` | MODIFY — drop one line, rewrite the #107 frontmatter comment |
| T022 | `docs/architecture/layer-model.md` | MODIFY — two sentences amended |
| — | `docs/architecture/declarations/59-deployment-key-metadata.md` | ADD — already written during design; currently untracked and must be committed with the PR |

Twenty of the 31 tasks touch no file at all: baselines, scratch-repo installs,
greps, gates and the polish sweep.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| single | T001–T031 | `wfctl/cli.py` (mod), `tests/test_install_skills.py` (mod), `tests/test_skill_frontmatter.py` (new), 6 × `SKILL.md` (mod), `docs/architecture/layer-model.md` (mod), `docs/architecture/declarations/59-…md` (add) | **L by count, M by surface** | `uv run pytest -q`, `ruff`, `mypy` all green; conformance sweep reports `27 valid · 1 failed`; four-agent byte diff clean (T019) |

**Rationale**: **Single PR.** Three of the four boundary signals point to
bundling, and the fourth is weak.

1. **File conflict risk — bundle.** `wfctl/cli.py` is edited in Phase 2 (T005,
   T006) and Phase 4 (T015). `tests/test_install_skills.py` is edited in Phases
   2, 4 and 5 (T004, T007, T016, T021). Splitting by phase means three PRs
   editing the same two files, serialised by rebase.
2. **Reviewability — bundle.** Read apart, each half misleads. Phase 2 alone
   looks like a constant nobody uses; Phase 3 alone looks like deleting live
   configuration. The change only reads as correct when the swap and the removal
   are seen together.
3. **Mergeable increment — bundle.** Phase 2 is behaviour-neutral and *could*
   merge alone, but it would leave `layer-model.md` on `main` describing
   frontmatter as the switch while the code no longer reads it. An accepted
   record false on the default branch is precisely what FR-009 exists to prevent.
4. **Story independence — weak split signal.** The three stories have separate
   acceptance criteria and touch mostly disjoint files, but they share one
   runtime path (`_claude_native_skill_mirror`) and each leaves a different
   artifact untrue if shipped alone.

**Size note — flagged rather than auto-split.** Eleven files puts this in the L
band, where the skill requires surfacing the scope rather than splitting on my
own judgement. The count is inflated by an identical one-line deletion repeated
across six skill files, which reviews as one decision, not six. Effective
reviewable units: the installer change, the test suite, the skill-frontmatter
sweep, and one record amendment — four. Recommendation is to proceed as a single
PR; the decision is the author's.

**PR closes**: `Closes #59`

**#108 is not closed by this PR.** It gets a comment instead. The change delivers
the reachable half — the vendored skill becomes listed and loadable on request —
but not unprompted self-correction, which its own `disable-model-invocation` key
prevents and which wfctl cannot remove without forking a vendored file. Closing
it would overstate what shipped.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #59 | T001–T031 | `[59] Move the mirror switch out of skill frontmatter into the installer` | M — 1 session | PR (single) |

**Grouping pattern**: Single issue.
**Rationale**: One PR delivers the whole feature, and #59 already exists as the
branch's issue — nothing to create. One PR closes exactly one issue.

No sub-issue worktrees are involved, so the spec dir needs no relocation.

---

## Parallelization Waves

Every one of the 31 tasks appears in exactly one wave.

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 ‖ T003 | No edits. **T003's four scratch repos must survive until Wave 6** — they are the byte baseline T019 diffs against. |
| 1 | Sequential | T004 | Refounded mirror tests must be seen failing with `AttributeError` before the constant exists. Skipping the red proves nothing about whether they bind. |
| 2 | Sequential | T005 → T006 | Same file, and T006 deletes the function T005's rewiring orphans. Order is not negotiable. |
| 3 | Parallel | T007 ‖ T008 | T007 appends a test; T008 is a scratch-repo install. **Fan-in gate: T009** (`pytest && ruff && mypy`). |
| 4 | Parallel | T010 ‖ T011 ‖ T015 ‖ T022 | Four genuinely disjoint files: five skill files, one skill file, one line of `cli.py`, one record. The widest parallel wave in the plan. |
| 5 | Mixed | T012 ‖ (T016 → T021) | T012 creates a new file and is free. T016 and T021 both append to `tests/test_install_skills.py` and must be sequenced if one agent holds it. |
| 6 | Parallel | T013 ‖ T017 ‖ T018 ‖ T019 ‖ T023 | Independent scratch repos and greps. **Fan-in gates: T014, T020, T024.** |
| 7 | Sequential | T025 → T026 → T027 → T028 → T029 → T030 → T031 | Polish. T026 and T027 are ordered on purpose: `doctor` before reinstall, then after. |

**Single-agent order** (recommended): T001 → T031 in numeric order. The wave table
is where the parallel structure lives if it is wanted; sequential execution is
correct and simpler for a feature this size.

---

## Agent Fanning Instructions

Single agent recommended. The feature is M by reviewable surface and the two
widest waves (4 and 6) are short.

If Wave 4 is fanned, the split is clean because the four tasks share no file:

**Agent A** — `T010`: remove the `deployment: skill` line from the five skill
files listed in `tasks.md`. Add nothing. Do not touch
`conversation-response-shape`.

**Agent B** — `T011`: `conversation-response-shape/SKILL.md` only. Remove the
line *and* rewrite the frontmatter comment beneath it — the comment from #107
explains the file in terms of the removed key and becomes false.

**Agent C** — `T015`: add `"i-have-adhd"` to `_MIRRORED_SKILLS` in
`wfctl/cli.py`, keeping the set alphabetically ordered. One line.

**Agent D** — `T022`: `docs/architecture/layer-model.md` only. Amend the two
sentences named in `tasks.md`. Name `_MIRRORED_SKILLS` without restating its
contents.

**Fan-in gate after Wave 4**: `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`

---

## Verification Checklist

- [x] `delivery.md` written to this feature's spec dir
- [x] PR count justified with rationale — single, 3 of 4 signals
- [x] Issue count equals PR count — 1 = 1
- [x] Every task assigned to exactly one wave — 31/31
- [x] GitHub issue exists and is numbered — #59, created before the branch
- [x] The PR's `Closes` line references exactly one issue — `Closes #59`
- [x] No sub-feature split, so no parent epic linkage needed
- [ ] L-size scope flagged to the author for a proceed/split decision
