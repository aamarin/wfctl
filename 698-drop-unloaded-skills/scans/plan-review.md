# Plan review scan for #698

## Review 2026-11-04T00:59Z

- Verdict: satisfied
- Reviewed: plan.md d97db9e5b7e43628da16860687ecbfbee556d6da, spec.md f4973d6b2538e41dc133eeb1c6f3ddae9471a4a4, .specify/memory/constitution.md absent, design.md 61c6c7ff90d56fb55e93c5de4da98bd8e08c8012, docs/architecture/design/698-brainstorm-listed-once.md a656c78f4640b12fed18a3cc4cfbd664d0391733, research.md e110b50cc8540e32c7be8dcb98b673308f1298ca, quickstart.md 4c2ce0eb0252e6414c8b1994b3c7411de4cdf464, docs/architecture/level-4-owns-pattern-selection.md 980d55fce4082196100a3a8ddb12d575a843cc99, docs/architecture/mirror-supersedes-the-wrapper.md 012b728e6192189657f1216cad89b2c7a116e794
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 5 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/698-drop-unloaded-skills/plan-review.md

The review ran in a fresh-context subagent and focused on an upgrade over a
project that already has a dropped skill, with a hand-authored skill beside it.
It confirmed the plan's claim that the installer needs no code change, with the
one rare exception in PR-003.

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-001, PR-004) |
| Architecture and boundaries | Outstanding (PR-006, PR-007) |
| Adversarial implementation and verification | Outstanding (PR-002, PR-003, PR-005) |
| Security and reliability | Deferred (no trust boundary is touched; the change deletes shipped files and removes only paths the manifest recorded) |

### Findings

- **PR-001, MAJOR, open.** The plan's new test expects a bare install to report
  both layers' dropped paths. That's true only when the run passes `--agent
  claude`, since a run without it never diffs the Claude layer
  (`install_skills_cmd`'s orphan loop in `cli.py`). Stands because plan.md
  §Phase 2 item 2 and spec.md US2 AC1 don't name the flag.
- **PR-002, MAJOR, open.** The planned "no file names the bare `brainstorm`
  skill" test has no matcher, and the step's own name uses the same word in six
  or more shipped files, one of them `start-session`. Stands because plan.md
  §Phase 2 item 4 doesn't say how to tell the skill from the step.
- **PR-003, MINOR, open.** A project's own untracked
  `.claude/skills/speckit-brainstorm`, put back from backup by `--prune`, still
  has its `.agents/` twin, so `doctor` reports it as wfctl's leftover and exits 1
  (`_scan_owns` and the `proven` branch in `doctor`). Stands because the case
  needs a hand-authored skill under exactly that name, and the plan doesn't
  mention it.
- **PR-004, MINOR, open.** The new test covers a skill dropped from the bundle,
  not one only taken out of the mirror, which is the `speckit-brainstorm` case.
  The Summary also says the record's Verification list becomes three tests,
  but two of its items are manual checks. Stands because plan.md §Phase 2 item 2
  doesn't cover it. An existing test,
  `test_doctor_reports_a_mirror_left_behind_when_a_skill_stops_being_mirrored`,
  covers part of it.
- **PR-005, MINOR, open.** The shared `bundle` fixture has no tracker files and
  no wrapper beside a skill, so the new test has to add both. Nothing in the
  planned test checks what `doctor` prints. Stands because plan.md §Phase 2 item
  2 doesn't say so.
- **PR-006, MINOR, open.** `level-4-owns-pattern-selection.md` (accepted) and
  `mirror-supersedes-the-wrapper.md` (proposed) still describe the dropped
  skills as live. Stands because plan.md §Phase 1 §5 adds a Log line only to
  `vendor-upstream-skills.md`.
- **PR-007, MINOR, open.** The bob and copilot layers also carry copies of the
  dropped skills, and the orphan rule removes them the same way. Stands because
  plan.md §Technical Context names only Claude.
