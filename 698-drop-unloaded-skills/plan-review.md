# Plan Review Report

Review state: completed
Review type: full

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | d97db9e5b7e43628da16860687ecbfbee556d6da | technical strategy |
| spec.md | f4973d6b2538e41dc133eeb1c6f3ddae9471a4a4 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 61c6c7ff90d56fb55e93c5de4da98bd8e08c8012 | design-record index |
| docs/architecture/design/698-brainstorm-listed-once.md | a656c78f4640b12fed18a3cc4cfbd664d0391733 | design record |
| research.md | e110b50cc8540e32c7be8dcb98b673308f1298ca | planning evidence |
| quickstart.md | 4c2ce0eb0252e6414c8b1994b3c7411de4cdf464 | planning evidence |
| docs/architecture/level-4-owns-pattern-selection.md | 980d55fce4082196100a3a8ddb12d575a843cc99 | accepted record the plan's level-4 edit touches |
| docs/architecture/mirror-supersedes-the-wrapper.md | 012b728e6192189657f1216cad89b2c7a116e794 | proposed record naming the mirror set |

## Review scope

- Full review: no earlier report at the report path, and no plan copy.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification.
- Conditional lenses: security and reliability applied narrowly, because
  `--prune` deletes files in a consumer repo. No trust boundary, secret or
  authorization path is touched.
- Focus asked for by the invoking command: `install-skills` over a project that
  already has a dropped skill installed, with a hand-authored skill beside it,
  checked against the installer and `doctor` code.
- Existing code inspected: `wfctl/cli.py` `_MIRRORED_SKILLS`,
  `_claude_native_skill_mirror`, `_mirror_supersedes_wrapper`,
  `_layered_targets`, `_plan_source`, `_AGENT_TARGETS`, `install_skills_cmd`
  (tracker carry-forward, orphan diff, prune and restore), the abandoned-path
  check in `doctor` (`flagged`, `not_in_bundle`, `_scan_owns`, the per-layer
  repair line); `wfctl/agents/skills/start-session/references/doctor-repair.md`;
  `tests/conftest.py` `bundle`; the orphan, prune, mirror and suppression tests
  in `tests/test_install_skills.py`; a grep of `wfctl/` for the dropped names.
- Reviewers: the three lenses above, run in sequence by one agent.
- No `[NEEDS CLARIFICATION` marker stands in `spec.md` or `plan.md`.

## Summary

BLOCKER: 0
MAJOR: 2
MINOR: 5

No BLOCKER findings identified in this review. The plan's central claim holds:
the existing orphan rule removes every dropped path on an `--agent claude
--prune` run, including the `speckit-brainstorm` mirror that leaves the set while
its skill keeps shipping, and it keeps the tracker config and a differently
named hand-authored skill. The two MAJOR findings are in the new tests. One
leaves "bare run" undefined where the two readings give different output, and
the other asks for a name check that a literal reading cannot pass without
editing `start-session`. The MINOR findings cover one edge where `doctor` stays
red after the repair, a case the new test does not exercise, test fixture
details, records that still name the dropped skills, and the other agent layers.

## Findings

### PR-001: "The bare run reports both layers' paths" holds only when the run names `--agent claude`

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §User Story 2, Acceptance Scenario 1`: "When a bare `install-skills`
    runs, Then it lists each dropped path as no longer shipped".
  - `plan.md §Phase 2, item 2`: "Assert that the bare run reports both layers'
    paths and removes nothing, that `--prune --agent claude` removes…".
  - `wfctl/cli.py` `install_skills_cmd`, the orphan diff: `orphans` iterates
    `for layer in items`, the layers this run wrote. A run without `--agent`
    writes only `base`, so `.claude/skills/*` paths recorded under `claude` are
    never diffed. The comment above `flagged` in `doctor` says the same: "a bare
    `--prune` cannot reach a path under `.claude/`".
  - `quickstart.md §The upgrade, step 3` uses `--agent claude` for that run.
- Finding: "Bare" means "without `--prune`" in the quickstart and in the
  plan's second assertion, but in `doctor-repair.md` and the cli.py comments it
  means "without `--agent`". Under the second reading, the run reports the six
  `.agents/` paths and none of the four `.claude/skills/` ones. In the real
  upgrade path, those reach the reader only through `doctor`'s
  `not_in_bundle` check and its `--agent claude --prune` line.
- Why it matters: an implementer who writes the first install as
  `install-skills --yes` gets a failing assertion, and has to choose between
  adding `--agent claude` and weakening what is asserted. The spec's AC1 is
  also false for a project whose post-create hook runs without `WFCTL_AGENT`.
- Suggested response: Name the flags on each run in the test steps (`--agent
  claude --yes` for the report run). Add one line saying a run without
  `--agent` reports only the base layer's paths, and that `doctor` names the
  Claude ones.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-002: The "no file names the bare `brainstorm` skill" test has no matcher a literal reading can pass

- Priority: MAJOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Phase 2, item 4`: "no file under `wfctl/agents/` names
    `using-superpowers`, `verification-before-completion`, or the bare
    `brainstorm` skill".
  - `spec.md §FR-004`: "No file wfctl ships MUST name a dropped skill *as
    something to load or read*".
  - `` `brainstorm` `` names the step, not the skill, in
    `wfctl/agents/skills/start-session/references/rationale.md:277`,
    `speckit-orchestrate/SKILL.md:78`, `speckit-delivery-plan/SKILL.md:28`,
    `speckit-delivery-plan/assets/delivery-plan-template.md:63`,
    `worktree-handoff/SKILL.md:79`, and the `speckit-brainstorm` description.
    The separate `brainstorming` skill keeps shipping.
  - `plan.md §Technical Context, Constraints`: "don't edit `start-session`".
- Finding: the step and the dropped skill share one token. A test matching the
  name fails on at least six step references, one of them in `start-session`,
  which the plan forbids editing. A test matching only path forms such as
  `skills/brainstorm/` or `Skill(brainstorm)` passes, but the plan does not say
  which forms count. The plan's item is also stricter than FR-004, which limits
  the rule to naming the skill as something to load or read.
- Why it matters: two implementers write two different tests. One of them goes
  red and invites an edit to `start-session` or a quiet loosening of the test.
- Suggested response: State the forms the test fails on for `brainstorm` (for
  example `skills/brainstorm/`, `commands/brainstorm.md`, `/brainstorm` not
  preceded by `speckit.`, `Skill(brainstorm)`), and keep the full-name match
  for the other two names.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-003: A project's own `.claude/skills/speckit-brainstorm`, restored by `--prune`, reads to `doctor` as wfctl's leftover

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `spec.md §Edge Cases`: "`--prune` puts the project's original back from the
    backup"; `§User Story 2, Acceptance Scenario 3`: "…and `doctor` is green".
  - `plan.md §Phase 1 §6`: "No code change."
  - `wfctl/cli.py` `_scan_owns`: under `.claude/skills` an unrecorded child is
    wfctl's when `.agents/skills/<name>` exists. `doctor` puts such a child in
    `proven` and exits 1 with "Delete … by hand".
  - `install_skills_cmd` adds every planned path to `.gitignore`
    (`gitignore_targets`), so the restored original is usually untracked and
    passes `_tracked_paths`.
- Finding: for the three skills dropped from the bundle, `--agent claude
  --prune` removes the base twin in the same run, so a restored same-name
  original is not reported. `speckit-brainstorm` keeps its base twin. A project
  that had its own untracked `.claude/skills/speckit-brainstorm` before wfctl
  installed has it restored, and `doctor` then reports it as no longer shipped
  and says to delete it by hand. That is the #183 shape, and AC3's green
  `doctor` does not hold there.
- Why it matters: this is rare, but it is the one place where "no installer
  change" does not hold, and `/start-session` would carry a red `doctor` into
  its report.
- Suggested response: Add it to the plan's assumptions as an accepted edge, or
  narrow AC3 to exclude it. Leave the code alone unless a project reports it.
- Corroborated by: adversarial implementation

### PR-004: The new test pins a skill dropped from the bundle, not one only taken out of the mirror

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Phase 2, item 2`: "install a bundle carrying a mirrored skill …
    then install a bundle without that skill".
  - `docs/architecture/design/698-brainstorm-listed-once.md §Verification`,
    item 2: after `--agent claude --prune`, `.claude/skills/` has no
    `speckit-brainstorm`. `plan.md` lists that as a manual step only.
  - `plan.md §Summary`: the record's "Verification list becomes three of the
    tests", although two of its three items are manual runs.
  - `tests/test_install_skills.py::test_doctor_reports_a_mirror_left_behind_when_a_skill_stops_being_mirrored`
    covers the report half of the mirror-only case. No test covers the prune
    half, where `.claude/skills/<name>` goes and `.agents/skills/<name>` stays.
- Finding: the new test does not duplicate an existing one. No current test
  combines a mirrored skill leaving the bundle, both layers, a sibling skill and
  the tracker (`test_prune_deletes_a_path_the_install_no_longer_ships` and
  `test_prune_puts_back_the_file_it_overwrote_when_it_drops_the_path` use a
  renamed command on the Claude layer). But the mirror-only shape this branch
  ships for `speckit-brainstorm` gets no automated prune check.
- Why it matters: the same orphan diff handles both shapes today, so the risk
  is low. But the one that ships is the one left to manual checking.
- Suggested response: Parametrize the new test over both shapes (removed from
  the bundle, and removed from `_MIRRORED_SKILLS` through `monkeypatch`, as the
  existing doctor test does). In the shape removed from the set, assert that
  `.agents/skills/<name>` survives. Fix the "three of the tests" wording.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-005: The new test's fixture holds no tracker files, and the test asserts nothing about `doctor`

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Constitution Check`: "the one new test reuses the existing install
    fixtures"; `§Phase 2, item 2`: "select the github tracker … `.agents/trackers/github.json` remain".
  - `tests/conftest.py::bundle`: the autouse fake bundle holds one skill and
    one command, with no `agents/trackers/`. Tests that need a tracker seed it,
    for example `tests/test_install_skills.py` around line 1280 and line 1753.
  - `spec.md §User Story 2, Acceptance Scenarios 2 and 3`: `doctor` reports each
    path with a `--prune` line per layer, and is green afterwards.
- Finding: with the fixture as it is, `--tracker github` prints "missing from
  the source" and installs nothing, so the tracker assertion fails, or passes
  only if it checks absence. The test needs every `_GITHUB_TRACKER_FILES` entry
  seeded, plus a wrapper `<name>.md` beside the mirrored skill for the
  `.agents/commands/` assertion. FR-007 requires neither `doctor` assertion.
  AC2 and AC3 are left to the quickstart, apart from what
  `test_the_prune_doctor_advises_names_the_layer_it_has_to_reach` already
  covers.
- Why it matters: if a fixture is left out, the test can pass without testing
  what its name says. The spec's `doctor` scenarios have no automated check
  beyond the existing per-layer test.
- Suggested response: Name the fixture additions in the test step. Either
  assert `doctor`'s two repair lines before the prune, or say that the
  existing per-layer test and the quickstart cover AC2 and AC3.
- Corroborated by: adversarial implementation

### PR-006: Two records still describe the dropped skills as live, and the plan amends only `vendor-upstream-skills`

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: open
- Evidence:
  - `docs/architecture/level-4-owns-pattern-selection.md` (accepted) §Context:
    level 4's two verification skills "are `verification-before-completion` and
    `code-review`".
  - `docs/architecture/mirror-supersedes-the-wrapper.md` (proposed) §Context:
    the mirrored-skill count, and `speckit-brainstorm` named as mirrored.
  - `plan.md §Phase 1 §5`: only `vendor-upstream-skills.md` gets a Log line.
- Finding: neither record is shipped, so FR-004 is not breached, and a record's
  Context is allowed to be historical. But the next reader of either record has
  nothing telling them that #698 moved level 4 to `wfctl verify` and took
  `speckit-brainstorm` out of the mirror.
- Why it matters: it's small, but both records are ones a later change to the
  mirror set or to level 4 would read first.
- Suggested response: Add an `amended` Log line to each, or say in the plan
  that they are left as historical context on purpose.
- Corroborated by: architecture and boundaries

### PR-007: The bob and copilot layers hold the dropped skills too, and the plan names only Claude

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `wfctl/cli.py` `_AGENT_TARGETS`: `bob` copies `agents/skills` to
    `.bob/skills`, and `copilot` copies it to `.github/skills`.
  - `plan.md §Technical Context, Target Platform`: "through the base layer and
    the Claude layer"; `§Phase 1 §6` and `quickstart.md` name Claude only.
- Finding: a project with either layer has `<root>/brainstorm`,
  `using-superpowers` and `verification-before-completion` recorded under that
  layer. The same orphan diff reports and prunes them on an `--agent bob` or
  `--agent copilot` run, and `doctor` prints that layer's repair line. So
  nothing breaks. But the plan doesn't state that those layers are covered, or
  that their copy of `speckit-brainstorm` stays, since only the Claude mirror
  is selective.
- Why it matters: it holds up nothing. One sentence would stop the next reader
  from re-deriving it.
- Suggested response: Add one line to §Phase 1 §6.
- Corroborated by: architecture and boundaries

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Phase 1 §1, §2 | covered |
| FR-002 | plan.md §Phase 1 §2; §Phase 2 item 3 | covered; prune half of the mirror-only shape is PR-004 |
| FR-003 | plan.md §Phase 1 §4; §Phase 2 item 3 | covered |
| FR-004 | plan.md §Phase 1 §3; §Phase 2 item 4 | covered; test matcher is PR-002 |
| FR-005 | plan.md §Phase 1 §5 | covered |
| FR-006 | plan.md §Phase 1 §6 | covered by the existing orphan rule; PR-001, PR-003 |
| FR-007 | plan.md §Phase 2 item 2 | covered; PR-004, PR-005 |
| FR-008 | plan.md §Technical Context, Constraints | covered by omission; no test pins the four names stay in `_MIRRORED_SKILLS` beyond the existing suppression pin |
| SC-001 | plan.md §Phase 2, the "hi" measurement | covered, manual |
| SC-002 | plan.md §Phase 2, the "hi" measurement; item 3 | covered, manual |
| SC-003 | none | needs no technical action beyond FR-001; the plan does not say so |
| SC-004 | plan.md §Phase 2 item 2; quickstart.md §The upgrade | covered; PR-003 is the edge where it fails |

## Assumptions challenged

- "The dropped wrappers leave `.claude/commands/`." They were never there. All
  three names are in `_MIRRORED_SKILLS` today, so `_mirror_supersedes_wrapper`
  keeps them out of the Claude layer. Only `.agents/commands/<name>.md` is on
  record, under `base`, and every run rewrites `base`, so every run reports it.
  A record from before #170 would already carry `orphaned` and is pruned the
  same way. Removing the names from the set unsuppresses nothing, because no
  wrapper of the same name survives. `speckit.brainstorm.md` is a dot away from
  `speckit-brainstorm` and was never suppressed. Verified.
- "`.claude/skills/speckit-brainstorm` becomes an orphan." On an `--agent
  claude` run, yes: it is recorded under `claude`, this run's `claude` items no
  longer include it, and `.agents/skills/speckit-brainstorm` stays installed.
  On a run without `--agent`, no: the `claude` layer is not diffed. `doctor`
  then finds it through `not_in_bundle`, since `.claude/skills` is in
  `_planned_dirs()`, and prints `install-skills --agent claude --prune`, which
  `doctor-repair.md` runs with `--yes`. Verified.
- "A hand-authored skill beside it stays." A differently named
  `.claude/skills/my-own` is not on record, so prune never touches it, and
  `_scan_owns` finds no `.agents/skills/my-own` twin, so `doctor` does not
  report it. Verified. The same-name case is PR-003.
- "The tracker config is never an orphan." The `active_tracker` block carries
  every recorded `_tracker_files(active_tracker)` path forward on a run that
  named no tracker, before the orphan diff. Verified.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `plan.md §Phase 1 §6` keeps removal inside `install-skills --prune` and
  adds no bare-run removal. That matches `deletion-follows-recorded-files` and
  the orphan comment in `cli.py`: what makes the deletion safe is wfctl's own
  record under a layer the run just rewrote.
- The plan swaps `_mirror_supersedes_wrapper`'s `/brainstorm` example for
  `/design-levels`, a wrapper that still ships and is still suppressed, so the
  docstring's argument still points at a real file.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
