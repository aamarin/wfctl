# Tasks: deployment key metadata

**Input**: Design documents from this feature's `FEATURE_DIR` (`wfctl feature-paths`)
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md
**Revision**: remediated after `/speckit.analyze` — see `checklists/analysis-report.md`

**Tests**: Three new tests are required, not optional. FR-005, FR-008 and FR-010
each exist because the failure they catch is silent — a skill that quietly stops
being discoverable, a mechanism that quietly starts trusting installed state, and
a non-spec key that ships clean until someone runs an external validator by hand.

**Organization**: Grouped by user story. Phase 2 is deliberately
behaviour-neutral so that removing the frontmatter keys in Phase 3 cannot
silently un-mirror six skills.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3, mapping to spec.md's user stories
- All paths are repository-relative to the worktree root
- Requirement identifiers are cited inline so coverage is declared, not inferred

## Path Conventions

Single Python package. `wfctl/` holds source and the shipped skill bundle;
`tests/` sits at the repository root; `docs/architecture/` holds the records.

⚠️ **Every `wfctl` invocation below is `uv run wfctl`.** A globally installed
`wfctl` resolves to the released wheel, not this branch (#75), so a bare `wfctl`
would install the old bundle and every manual check would pass for the wrong
reason.

---

## Phase 1: Setup

**Purpose**: Pin the before-state, so SC-001 and SC-002 are measured rather than
asserted.

- [X] T001 Confirm the local build is what runs: `uv run wfctl --version` matches `version` in `pyproject.toml`; record the value
- [X] T002 [SC-001] Capture the conformance baseline using the sweep in `quickstart.md` §2, saving output to the scratch dir; expect `21 valid · 7 failed` (6 × `deployment`, 1 × `disable-model-invocation`)
- [X] T003 [SC-006] Capture the byte-level baseline for the untouched agents: install the **pre-change** build into four scratch repos, one each for `--agent none`, `codex`, `bob`, `copilot`, and keep them for the comparison in T019

**Checkpoint**: baselines recorded. Nothing in the repo has changed yet.

---

## Phase 2: Foundational (blocking prerequisite for all stories)

**Purpose**: Move the switch from frontmatter into the installer **without
changing behaviour**. The declared set holds the same six names the frontmatter
key holds today, so `.claude/skills/` is byte-identical before and after this
phase. The now-inert `deployment:` lines stay in the skill files until Phase 3.

**⚠️ CRITICAL**: No user story can start until this phase completes.

- [X] T004 Refound the four mirror tests in `tests/test_install_skills.py` onto `monkeypatch.setattr("wfctl.cli._MIRRORED_SKILLS", frozenset({"native-skill"}))`, replacing the frontmatter-writing fixtures at lines ~196–250; follow the autouse pattern at `tests/conftest.py:107`; verify they fail with `AttributeError` under `uv run pytest -q -k mirror` — the constant does not exist yet
- [X] T005 [FR-002] Add `_MIRRORED_SKILLS` to `wfctl/cli.py` as a `frozenset` of the six names currently carrying `deployment: skill`, sited beside `_AGENT_SKILL_EXTRAS`, and rewire `_claude_native_skill_mirror()` (`wfctl/cli.py:1064`) to test `item.name in _MIRRORED_SKILLS`; verify with `uv run pytest -q -k mirror`
- [X] T006 [FR-002] Delete `_skill_deployment()` from `wfctl/cli.py:1048`; verify no callers remain with `grep -rn '_skill_deployment' wfctl/ tests/` returning nothing, then `uv run pytest -q`
- [X] T007 [FR-008] Add a test to `tests/test_install_skills.py` proving the installed tree is a destination and never a source: create a skill directory under the destination `.agents/skills/` that exists in **no** bundle, run `install-skills --agent claude`, and assert it never appears in `.claude/skills/`. Docstring names why this is worth a test — the mirror set is computed from the wheel's own bundle, and a future change that consulted installed state would make the declaration and its reader disagree with nothing failing. Verify with `uv run pytest -q -k mirror`
- [X] T008 [FR-003] Confirm behaviour is unchanged: install into a scratch repo per `quickstart.md` §3 and assert `.claude/skills/` still holds exactly the same six entries as before this phase
- [X] T009 Validate Phase 2 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: the mechanism is swapped, behaviour is identical, and the
frontmatter keys are dead code awaiting removal.

---

## Phase 3: User Story 1 — Shipped skills pass a conformance check (P1) 🎯 MVP

**Goal**: No skill wfctl authors carries a frontmatter key outside the Agent
Skills allowed set, and nothing lets that regress.

**Independent Test**: Run the conformance sweep from `quickstart.md` §2. Failures
drop from 7 to 1, and the survivor is the vendored skill. Delivers value whether
or not US2 and US3 ship.

**Verification**: `tests/test_skill_frontmatter.py` (new, offline) plus the
one-off sweep against the T002 baseline.

- [X] T010 [P] [US1] [FR-001] Remove the `deployment: skill` line from the five skills that carry nothing else wfctl-specific — `wfctl/agents/skills/architecture-decisions/SKILL.md`, `design-levels/SKILL.md`, `receiving-code-review/SKILL.md`, `using-superpowers/SKILL.md`, `verification-before-completion/SKILL.md`; add nothing in its place; verify with T012
- [X] T011 [US1] [FR-001] In `wfctl/agents/skills/conversation-response-shape/SKILL.md`, remove the `deployment: skill` line **and** rewrite the frontmatter comment beneath it — the comment added by #107 explains the file in terms of the removed key and becomes false; state the same intent against the new mechanism; verify with T012 and by reading the rendered frontmatter
- [X] T012 [US1] [FR-010] [SC-002] Add `tests/test_skill_frontmatter.py` asserting that for every directory under `wfctl/agents/skills/` except the vendored exemption, the top-level frontmatter keys are a subset of `{allowed-tools, compatibility, description, license, metadata, name}`.

      **Parser contract — get this right or the test reds out a quarter of the bundle.** Seven shipped skills (`speckit-*`) carry `metadata:` with nested `author:` and `source:` children. The scan MUST count only **unindented** lines, and MUST stop at the **closing** `---` rather than reading into the body. `_skill_deployment()` did both before deletion; the replacement must not lose either. A red run naming `speckit-checklist` or `speckit-constitution` means the parser is wrong — **do not widen the allowed set to make it pass.**

      Exempt `i-have-adhd` by name with a docstring saying why (`vendor-upstream-skills` forbids editing it). Read the package path directly rather than `BUNDLE_ROOT`, so the autouse `bundle` fixture does not interfere. Verify with `uv run pytest -q tests/test_skill_frontmatter.py`, and separately confirm all seven `speckit-*` skills pass.
- [X] T013 [US1] [SC-001] Re-run the conformance sweep from `quickstart.md` §2 and diff against the T002 baseline; expect `27 valid · 1 failed`, the single failure being `i-have-adhd :: disable-model-invocation`
- [X] T014 Validate Phase 3 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: SC-001 and SC-002 met and guarded. The feature is shippable here.

---

## Phase 4: User Story 2 — A vendored skill can be made natively discoverable (P2)

**Goal**: `i-have-adhd` joins the discoverable set without its file being edited,
and the inclusion survives an upstream replacement.

**Independent Test**: Install for the Claude agent; the vendored skill appears in
`.claude/skills/`. Overwrite its source file with a copy containing nothing wfctl
wrote, reinstall, and it is still there.

**Verification**: a new automated test that a skill with no wfctl key mirrors
when named, plus the manual exercises in `quickstart.md` §4, §5 and §6.

- [X] T015 [US2] [SC-003] Add `"i-have-adhd"` to `_MIRRORED_SKILLS` in `wfctl/cli.py`, keeping the set alphabetically ordered; verify with T016
- [X] T016 [US2] [FR-004] Add a test to `tests/test_install_skills.py` that a bundle skill whose frontmatter carries no wfctl-specific key at all is mirrored when its name is in the declared set — the property FR-004 turns on, and the one the frontmatter mechanism could not provide; verify with `uv run pytest -q -k mirror`
- [X] T017 [US2] [FR-004] Run the upstream-replacement exercise in `quickstart.md` §4: overwrite `wfctl/agents/skills/i-have-adhd/SKILL.md` with a bare upstream-shaped copy, reinstall, confirm it still mirrors, then `git checkout --` the file; verify the restore with `git status --short` showing the file unmodified
- [X] T018 [US2] [FR-007] [SC-003] Run the uninstall exercise in `quickstart.md` §6: `uv run wfctl uninstall-skills --agent claude` removes `.claude/skills/` entirely while `.agents/skills/` retains all 28 — confirms FR-007 needs no code change.

      Record in the task notes that SC-003's 6 → 7 count is verified **manually here and nowhere else**, and why: the autouse `bundle` fixture replaces the real bundle, so an automated assertion on the real set's contents would be testing the fixture. The gap is chosen, not missed.
- [X] T019 [US2] [FR-006] [SC-006] Prove the other agents are untouched at byte level, not by presence. Install the **post-change** build into four fresh scratch repos — `--agent none`, `codex`, `bob`, `copilot` — and `diff -r` each against its T003 pre-change counterpart, excluding `.git/`. Expect no differences for any of the four. Additionally confirm the `bob` repo has no `.claude/` directory at all and 28 entries under `.bob/skills/`
- [X] T020 Validate Phase 4 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: `.claude/skills/` holds 7 entries. SC-003 met, with the narrowed
claim — listed and loadable on request, not self-invoking. SC-006 proven by diff.

---

## Phase 5: User Story 3 — The discoverable set is one auditable list (P3)

**Goal**: The set is readable in one place, a wrong entry fails loudly, and no
accepted record describes the mechanism that was removed.

**Independent Test**: Read the declaration in one place. Introduce a name
matching no shipped skill and confirm the suite fails and names it. Read the
architecture records and find none describing frontmatter as the switch.

**Verification**: the declaration guard test, plus reading the amended record.

- [X] T021 [US3] [FR-005] [SC-005] Add a guard test to `tests/test_install_skills.py` asserting every name in `_MIRRORED_SKILLS` is a directory under `wfctl/agents/skills/`; resolve that path from the installed package rather than `BUNDLE_ROOT`, so the autouse fixture does not mask it; docstring names the failure it catches — a renamed skill silently ceasing to be discoverable; verify by temporarily adding a bogus name and confirming a red run that names the entry
- [X] T022 [US3] [FR-009] Amend `docs/architecture/layer-model.md`: the sentence "Only skills whose frontmatter carries `deployment: skill` are mirrored into `.claude/skills/`" and the paragraph added by #107 stating "a vendored skill cannot opt in … the next upstream pull would drop it" are both now false; replace them with the installer-owned mechanism, naming `_MIRRORED_SKILLS` without restating its contents (`knowledge-placement` — one home per fact); verify by re-reading the record against `wfctl/cli.py`
- [X] T023 [US3] [FR-009] Confirm no other record or document describes the removed mechanism: `grep -rn 'deployment' docs/ AGENTS.md wfctl/agents/` returns only intended matches; verify each remaining hit is deliberate
- [X] T024 Validate Phase 5 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: all three stories complete. FR-009 satisfied.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T025 Run the full definition-of-done from `AGENTS.md`: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`; verify all three exit zero and the suite reports no failures — this is the whole bar for a code change, and CI runs exactly these on 3.11 and 3.13
- [X] T026 Run `uv run wfctl doctor`. Skills in this repo are installed from the released wheel, so the expected result is a **cyan ⬆ line naming the `base` layer as behind**, not a red `✗`. Capture the literal line; if it renders as an error rather than as available drift, that is a finding, not a pass
- [X] T027 Reinstall this repo's own skills with `uv run wfctl install-skills` and re-run `uv run wfctl doctor`; expect the green `✓ base: skills current` line and no findings
- [X] T028 Confirm no vendored file was modified: `git diff --stat wfctl/agents/skills/i-have-adhd/` is empty — `vendor-upstream-skills` is a merge gate, not a preference
- [X] T029 Confirm `pyproject.toml`'s `version` is untouched — bumping it on `main` ships a release, and this change is not one; verify with `git diff pyproject.toml` showing no change to the `version` key
- [X] T030 Comment on issue #59 recording that its proposal was reversed during design: the `metadata` relocation was rejected for a hand-rolled-parser cost and an ownership conflict with `layer-model`, and the implementation names the discoverable skills in the installer instead — so a reviewer reading the issue and then the diff is not looking at two different changes; verify by re-reading the issue thread and confirming the comment states both the rejected proposal and the reason
- [X] T031 [SC-004] [SC-007] Final review of the diff against `contracts/skill-frontmatter-and-layout.md`: both external contracts changed as documented and no third one moved. In the same pass, confirm `git diff --stat` shows a net-negative line count for `wfctl/` excluding tests (SC-007), and that `_MIRRORED_SKILLS` reads in under ten lines (SC-004)

---

## Dependencies

```
Phase 1  Setup ── captures both baselines (conformance + per-agent bytes)
   │
   ▼
Phase 2  Foundational ── behaviour-neutral mechanism swap
   │                     BLOCKS everything below
   ├──────────────┬──────────────┐
   ▼              ▼              ▼
Phase 3 (US1)  Phase 4 (US2)  Phase 5 (US3)
 P1 · MVP       P2             P3
   │              │              │
   └──────────────┴──────────────┘
                  ▼
            Phase 6  Polish
```

**Story independence after Phase 2**: US1, US2 and US3 touch disjoint surfaces —
skill frontmatter, the set's membership, and the guard plus the record. Any one
can ship alone.

**One real ordering constraint inside Phase 2**: T004 before T005. The tests are
written against a constant that does not exist yet and must be seen failing;
writing them after the implementation proves nothing about whether they bind.

**One real constraint across phases**: Phase 3 must not precede Phase 2. Removing
the frontmatter keys while the parser still reads them un-mirrors six skills
silently, which is the exact failure class this change exists to reduce.

**One constraint spanning the whole run**: T003's four pre-change scratch repos
must survive until T019 compares against them. Do not clean them up at the end of
Phase 1.

## Parallel Execution

- **T010** covers five files with an identical one-line deletion and can be split
  across agents or done in one pass; nothing else touches those files.
- **Phases 3, 4 and 5** are fully parallel once Phase 2 lands. US1 edits
  `wfctl/agents/skills/*`, US2 edits one line of `wfctl/cli.py` plus a test, US3
  edits `docs/architecture/layer-model.md` plus a test. The three stories touching
  `tests/test_install_skills.py` (T016, T021, and Phase 2's T007) append
  independent test functions; order them if the same agent holds the file.
- **T003's four installs** are independent scratch repos and can run
  concurrently, as can **T019's four**.
- **T017 and T018** are independent scratch repos.

## Implementation Strategy

**MVP is Phase 1 + Phase 2 + Phase 3.** That closes #59 — the defect the issue
was filed for — with the conformance guard in place. US2 and US3 are additive.

**Recommended increments**:

1. Phases 1–2: mechanism swap, provably behaviour-neutral. Reviewable on its own.
2. Phase 3: the keys come out, conformance guarded. Ship-worthy.
3. Phase 4: the vendored skill joins; closes the reachable half of #108.
4. Phase 5: the guard and the record catch up with the code.

**Not decided here**: whether these become one PR or several. That is
`/speckit.decompose`'s call via `speckit-delivery-plan`. The phase boundaries
above are reviewable slices, not a PR plan.

## Task Summary

| Phase | Story | Tasks | Count |
| --- | --- | --- | --- |
| 1 Setup | — | T001–T003 | 3 |
| 2 Foundational | — | T004–T009 | 6 |
| 3 | US1 (P1) | T010–T014 | 5 |
| 4 | US2 (P2) | T015–T020 | 6 |
| 5 | US3 (P3) | T021–T024 | 4 |
| 6 Polish | — | T025–T031 | 7 |
| **Total** | | | **31** |

---

## Execution notes — 2026-08-30

Three tasks did not run exactly as written. Each is recorded here rather than
silently absorbed, because the task text is what a reviewer reads next.

**T002 / T013 — external validator not run.** The `uvx --from git+https://…`
sweep fetches and executes remote code and was refused by the sandbox. An
equivalent offline scan over the same allowed key set produced the predicted
counts exactly: `21 valid · 7 failed` before, `27 valid · 1 failed` after, the
survivor being `i-have-adhd :: disable-model-invocation`. The upstream
validator's own verdict remains unconfirmed and is the one thing here taken on
the offline scan's word.

**T018 — `.claude/skills/` is emptied, not removed.** Uninstall deletes all 7
native copies and leaves the parent directory behind; `.agents/skills/` keeps
its 28. Pre-existing and not a regression — `.claude/commands/` is left the same
way — so FR-007 holds as written. `quickstart.md` §6's "No such file or
directory" describes the contents, not the directory.

Also, as T018 requires: SC-003's 6 → 7 count is verified **manually here and
nowhere else**. The autouse `bundle` fixture replaces the real bundle, so an
automated assertion on the real set's membership would be testing the fixture.
The gap is chosen, not missed.

**T019 — "no differences" was unachievable as stated.** The six edited
`SKILL.md` files ship to every agent through `.agents/skills/`, so their bytes
necessarily change in all four trees. The claim FR-006 actually makes is that no
agent gains or loses a path, and that was measured: **0 paths added or removed**
for `none`, `codex`, `bob` and `copilot`. The only differing files are those six
plus `.wf-skills-manifest.json` (`content_hash`, `installed_at`). `bob` has no
`.claude/` at all and 28 entries under `.bob/skills/`.

**Beyond the task list.** T006 and T023 turned up three stale references the
tasks did not name: docstrings in `wfctl/_arch.py` and `tests/test_arch_records.py`
citing the deleted `_skill_deployment`, and `README.md:220` still describing the
frontmatter mechanism. All three rewritten.
