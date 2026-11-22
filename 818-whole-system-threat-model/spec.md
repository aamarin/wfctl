# Feature Specification: Whole-system threat model

**Feature Branch**: `818-whole-system-threat-model`  
**Created**: 2026-11-21  
**Status**: Draft  
**Input**: Pre-specify design context loaded from `design.md` in the feature's spec folder, and issue #818, "Ship a skill that builds a whole-system threat model".

## Clarifications

### Session 2026-11-21

- Q: What does `/threat-baseline` do when auto-approve is off? → A: It runs upstream's bootstrap and then upstream's interview with the user. The self-walkthrough runs only when auto-approve is on.
- Q: How does `/threat-baseline` run upstream's helper for an agent other than Claude, whose skills folder isn't `.claude/skills/`? → A: The pass works the same for every agent. `threat-baseline` tells the agent to run the helper from the `_lib` folder beside the skill it loaded, instead of the `.claude/` path upstream names.
- Q: Which level-2 records make the `threat-baseline` pass apply? → A: Records the branch adds or edits that carry a `## Threat model` section. An edit to an existing security record usually means its control is changing, so it's a fair point to build a missing baseline.

## User Scenarios & Testing _(mandatory)_

A per-control threat model describes one security control: who it defends against, which forms it must keep catching, and what it accepts. A whole-system threat model is the map underneath it, listing what the whole repository exposes, the threats against it, and the controls already in place. Since #799, every change to a security control writes the first kind. Nothing builds the second, so each per-control threat model assumes a map nobody drew.

This feature ships a skill that builds the whole-system threat model as `THREAT_MODEL.md` at the repository root, and a brainstorm pass that pauses a branch until that file is committed.

### User Story 1 - Brainstorm pauses until the baseline is committed (Priority: P1)

An agent on a branch that changes a security control writes a level-2 record with a `## Threat model` section. If the repository has no committed `THREAT_MODEL.md` at its root, `wfctl status` pauses brainstorm on the `threat-baseline` pass and names `/threat-baseline` as the next command. Once the agent commits the file, the pass is done and brainstorm continues. The agent saying the file is built doesn't finish the pass. Only the committed file does.

**Why this priority**: This is the check itself. Without it, the skill ships but nothing makes sure it runs before the first per-control threat model, and an agent that skips it leaves nothing that notices.

**Independent Test**: In a test repository, add a level-2 record with a `## Threat model` section on a branch and run `wfctl status`. The pass reads paused with `/threat-baseline` as the next command. Commit a `THREAT_MODEL.md` at the root and run it again. The pass reads done.

**Acceptance Scenarios**:

1. **Given** a branch whose level-2 record has a `## Threat model` section and no `THREAT_MODEL.md` at the repository root, **When** the user runs `wfctl status`, **Then** brainstorm is current, the `threat-baseline` pass is in progress with a reason naming the missing file, and the next command is `/threat-baseline`.
2. **Given** the same branch, **When** the agent commits `THREAT_MODEL.md` at the repository root, **Then** `wfctl status` shows the `threat-baseline` pass as done.
3. **Given** a branch whose level-2 record has a `## Threat model` section and a repository that already has `THREAT_MODEL.md` committed at its root, **When** the user runs `wfctl status`, **Then** the pass is done on the first read.
4. **Given** a branch with no level-2 record carrying a `## Threat model` section, **When** the user runs `wfctl status`, **Then** the `threat-baseline` pass reads skipped and doesn't hold brainstorm.
5. **Given** a branch where the pass is paused, **When** the user runs `wfctl step none brainstorm.threat-baseline --reason "…"`, **Then** the pass reads skipped with that reason, the way every claimed pass reads, and `wfctl check-body` asks for the reason in the PR body.

---

### User Story 2 - `/threat-baseline` builds the whole-system threat model (Priority: P2)

An agent sent to `/threat-baseline` runs Anthropic's `threat-model` skill against the repository root, unedited, and gets `THREAT_MODEL.md`. The `threat-baseline` skill then adds wfctl's three parts:

1. The file opens with one line saying it's a working map that gets revised, not a decision record.
2. A ninth section after upstream's eight lists fixes that were considered and rejected, with the trade-off for each.
3. If auto-approve is on, the agent still works through Shostack's four questions after the bootstrap. It answers them itself, prints each answer, and turns anything the code can't answer into an open question in the file.

If auto-approve is off, the agent runs upstream's bootstrap and then upstream's interview, which walks the user through the same four questions.

**Why this priority**: The pass in story 1 names this command, so the command has to produce the file the pass checks for. It comes second because the pass is what makes it run at the right time.

**Independent Test**: After `uv run wfctl install-skills --agent claude` in a repository with no threat model, run `/threat-baseline`. The result is a `THREAT_MODEL.md` at the root with upstream's eight sections, the rejected-fixes section, and the opening line.

**Acceptance Scenarios**:

1. **Given** a repository after `wfctl install-skills --agent claude`, **When** the user lists `.claude/skills/`, **Then** `threat-model`, `threat-baseline`, and `_lib` are present, and upstream's files match upstream's commit except for the attribution line appended to `SKILL.md`.
2. **Given** the installed tree, **When** the agent runs `python3 .claude/skills/_lib/checkpoint.py load ./.threat-model-state`, **Then** it prints `{"status": "absent"}`.
3. **Given** the installed tree, **When** the agent runs `/threat-baseline`, **Then** `THREAT_MODEL.md` is written at the repository root with the opening line and the rejected-fixes section after upstream's eight.
4. **Given** auto-approve is on, **When** the agent runs `/threat-baseline`, **Then** the agent prints its answer to each of the four questions, and each question the code can't answer appears as an open question in the file.
5. **Given** auto-approve is off, **When** the agent runs `/threat-baseline`, **Then** upstream's interview runs after the bootstrap and asks the user the four questions.
6. **Given** a repository after install, **When** the user runs `git status` after a bootstrap run, **Then** `.threat-model-state/` doesn't appear as untracked.

---

### User Story 3 - A design session on one control doesn't load the whole-system skill (Priority: P3)

An agent writing the `## Threat model` section for one control follows `design-levels`, which names `threat-baseline` as the skill for the whole-system map and tells the agent not to load `threat-model` while writing one control's section. The agent writes the section in the record and doesn't write a `THREAT_MODEL.md` in its place.

**Why this priority**: Upstream's description fires on phrases such as "threat model" and "map the attack surface", which a per-control design session uses. Its description stays as upstream wrote it, so wfctl separates the two from its own side.

**Independent Test**: Run a design-time prompt about one control against an installed tree. The session writes a `## Threat model` section in a level-2 record and doesn't load `threat-model`.

**Acceptance Scenarios**:

1. **Given** an installed tree, **When** an agent works a design-time prompt about one security control, **Then** it writes a `## Threat model` section in the level-2 record and doesn't load the `threat-model` skill.
2. **Given** the shipped `design-levels` skill, **When** a reader opens its security-control part, **Then** it names `threat-baseline` as the whole-system skill and says not to load `threat-model` while writing one control's section.

---

### User Story 4 - wfctl has its own whole-system threat model (Priority: P4)

wfctl's own repository has three per-control threat models and no whole-system one. The last step of this branch runs `/threat-baseline` on wfctl from the installed tree and commits the result as `THREAT_MODEL.md` at the repository root.

**Why this priority**: This is the first real run of the skill, and it closes the gap that started the issue. It depends on stories 1 to 3 being in place.

**Independent Test**: After the branch merges, `THREAT_MODEL.md` exists at the root of wfctl's repository, with the opening line and the rejected-fixes section.

**Acceptance Scenarios**:

1. **Given** this branch with stories 1 to 3 implemented, **When** the agent runs `/threat-baseline` from the installed tree, **Then** `THREAT_MODEL.md` is committed at the repository root.
2. **Given** that commit, **When** the user runs `wfctl status` on a later branch whose level-2 record has a `## Threat model` section, **Then** the `threat-baseline` pass is done on the first read.

---

### Edge Cases

- If `THREAT_MODEL.md` exists at the root but isn't committed, the pass stays paused. The PR wouldn't carry an uncommitted file, so the reviewer couldn't read the baseline the per-control threat model cites.
- If `THREAT_MODEL.md` exists somewhere other than the repository root, such as under the arch root, the pass stays paused. The user can run `wfctl step none brainstorm.threat-baseline` with a reason naming where the baseline is kept.
- If the branch recorded "no spec" with `wfctl spec none`, the pass is skipped along with the rest of the brainstorm row. A change to a security control writes a level-2 record, which already sends it through the spec pipeline.
- If a `## Threat model` section sits only in a record already on the trunk, which the branch didn't add or edit, the pass reads skipped. The pass is about the per-control threat model this branch writes.
- If `THREAT_MODEL.md` is committed but empty or malformed, the pass reads done. wfctl checks that the file exists, never its contents, since upstream enforces its own schema when it writes the file.
- If the branch already has `spec.md`, the pass doesn't move the branch back to brainstorm. A missing baseline shows as a warning on the finished pass instead, the same way a refusable drawing does past specify. That way, a branch already past specify when this check ships isn't sent backwards.
- If auto-approve is on, the pass still pauses. A missing baseline isn't a check that needs a person, so the agent runs `/threat-baseline` itself. The agent doesn't run `wfctl step none` on this pass, even though the remedy names it, since that line is the user's to run (FR-007b).
- If git can't say what the branch changed, or can't read `HEAD`, the pass reads in progress with a reason saying git couldn't answer, rather than skipped. A check that lets a branch through because its read failed is a check nobody knew had stopped running (`promised-evidence-blocks-on-silence.md`). Past `spec.md`, that reason is a warning instead, as FR-012a describes.
- If a person types `/threat-model` directly, they get upstream's version without wfctl's additions. That's intended, since outside the pipeline nothing depends on them.

## Requirements _(mandatory)_

### Functional Requirements

**Shipping the upstream skill**

- **FR-001**: wfctl MUST ship upstream's `threat-model` skill (`SKILL.md`, `README.md`, `bootstrap.md`, `interview.md`, `schema.md`) and its `_lib/checkpoint.py` helper unedited, except for the attribution line wfctl appends to every derived `SKILL.md`. `NOTICES.md` credits upstream under Apache-2.0 and names the helper by path.
- **FR-002**: `install-skills --agent claude` MUST mirror `threat-model`, `threat-baseline`, and `_lib` into `.claude/skills/`, so upstream's fixed `.claude/skills/...` paths resolve without editing upstream's files.
- **FR-003**: `install-skills` MUST add `.threat-model-state/` to the ignore entries it writes.
- **FR-004**: `vendor-upstream-skills.md`'s table of derived skills MUST list `threat-model` and its helper.

**The `threat-baseline` skill**

- **FR-005**: wfctl MUST ship a `threat-baseline` skill that runs upstream's `threat-model` against the repository root, then adds the opening line and the rejected-fixes section described in User Story 2. After the bootstrap, it runs upstream's interview with the user when auto-approve is off, and the self-walkthrough when auto-approve is on.
- **FR-005a**: The `threat-baseline` skill MUST tell the agent to run upstream's helper from the `_lib` folder beside the skill it loaded, so the helper resolves for Claude (`.claude/skills/`), Codex (`.agents/skills/`), Bob (`.bob/skills/`), and Copilot (`.github/skills/`) without editing upstream's files.
- **FR-006**: The `threat-baseline` skill MUST say at its top that upstream's `threat-model` does the work, so a reader looking for the threat model's behavior knows to read both.
- **FR-007**: The rejected-fixes section MUST come after upstream's eight sections, since upstream tells consumers to find sections by heading and to tolerate extras at the end.
- **FR-007a**: The `threat-baseline` skill MUST end by committing `THREAT_MODEL.md`, and only that file, since the pass reads done only on a commit. Without this, an unattended run that writes the file and stops is sent back to `/threat-baseline`, which reruns a bootstrap of several minutes until the stall count stops it.
- **FR-007b**: The `threat-baseline` skill and its command wrapper MUST tell the agent not to run `wfctl step none brainstorm.threat-baseline`, and no shipped skill's `allowed-tools` grants that command. Declaring the pass doesn't apply is the user's decision, and an agent that declares it is grading its own work.

**The pass**

- **FR-008**: The brainstorm row MUST gain a `threat-baseline` pass between `architecture` and `software-design`, with `/threat-baseline` as its command.
- **FR-009**: The pass MUST read skipped when no level-2 record that the branch adds or edits has a `## Threat model` section.
- **FR-010**: The pass MUST read in progress, with a reason naming the missing file, when such a record exists and no `THREAT_MODEL.md` is committed at the repository root.
- **FR-011**: The pass MUST read done when such a record exists and `THREAT_MODEL.md` is committed at the repository root, whether the file arrived on this branch or was already on the trunk.
- **FR-012**: The pass MUST read skipped, carrying the user's reason, when the user has recorded `wfctl step none brainstorm.threat-baseline --reason "…"`, and `wfctl check-body` MUST ask for that reason in the PR body, the same as for every other pass exception.
- **FR-012a**: Once the branch has `spec.md`, the pass MUST read done and carry the missing baseline as a warning, rather than reading in progress.
- **FR-013**: wfctl MUST check only that the file exists and is committed, never its contents.
- **FR-014**: The pass MUST behave the same whether auto-approve is on or off.

**Keeping the two skills apart**

- **FR-015**: The security-control part of `design-levels` MUST name `threat-baseline` as the whole-system skill and say not to load `threat-model` while writing one control's `## Threat model` section. It MUST also tell the agent that, if no `THREAT_MODEL.md` is committed at the repository root, it runs `/threat-baseline` before writing that section. This instruction is the primary route, and the pass catches a run that skips it (`security-record-needs-baseline.md`).
- **FR-015a**: When the pass forced the baseline after a `## Threat model` section was already written, the `threat-baseline` skill MUST have the agent re-read that section against the new baseline and update it where the baseline names a threat, actor, or control the section missed.

**Tests the shipped skills must pass**

- **FR-016**: A test MUST fail when a path a shipped skill names under `.claude/skills/` doesn't resolve to a mirrored item after install.
- **FR-017**: The test that checks a skill's own files MUST recognize upstream's "in this directory" wording, so it fails when `interview.md`, `bootstrap.md`, or `schema.md` is missing.
- **FR-018**: The frontmatter test MUST allow `argument-hint`, which upstream's `SKILL.md` carries as a Claude Code key.

**wfctl's own baseline**

- **FR-019**: This branch MUST commit wfctl's own `THREAT_MODEL.md` at the repository root, built by `/threat-baseline` from the installed tree.

## Key Entities _(include if feature involves data)_

- **Whole-system threat model**: `THREAT_MODEL.md` at the repository root. It lists the system's assets, actors, threats, and controls in upstream's eight sections, plus wfctl's opening line and rejected-fixes section. wfctl reads only whether it exists and is committed.
- **Per-control threat model**: the `## Threat model` section of a level-2 record. Its presence on a record the branch adds or edits is what makes the `threat-baseline` pass apply.
- **Pass exception**: the file `wfctl step none brainstorm.threat-baseline` writes to `exceptions/` in the branch's spec folder, holding the user's reason the pass doesn't apply.
- **Checkpoint state**: `.threat-model-state/` in the working directory, written by upstream's helper during a bootstrap run. It's scratch state and is never committed.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a branch whose level-2 record has a `## Threat model` section and no committed baseline, brainstorm doesn't advance until the baseline is committed or the user records an exception, in 100% of runs.
- **SC-002**: On a branch with no `## Threat model` section, the new pass adds no stop. The pipeline advances exactly as it did before this feature.
- **SC-003**: A fresh install of the Claude layer runs upstream's helper from its installed path on the first try, with no edits to upstream's files.
- **SC-004**: A design-time session on one control writes its `## Threat model` section in the record and doesn't load the whole-system skill.
- **SC-005**: wfctl's own repository has a committed whole-system threat model once this branch merges.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` are green.
- Unit tests for the pass cover skipped, in progress, done from a committed file, done from a file already on the trunk, done from an exception, and still paused for an uncommitted file.
- The tests in FR-016, FR-017, and FR-018 fail against the vendored files before the change that fixes each one.
- After `uv run wfctl install-skills --agent claude`, `python3 .claude/skills/_lib/checkpoint.py load ./.threat-model-state` prints `{"status": "absent"}`, and `uv run wfctl doctor` is green.
- A design-time prompt about one control, run against the installed tree, writes a `## Threat model` section and doesn't load `threat-model`.
- `/threat-baseline` builds wfctl's `THREAT_MODEL.md` from the installed tree, with the opening line and the rejected-fixes section.
- `wfctl verify` passes, and `changes/818.addition.md` carries the release note.

## Assumptions

- Pre-specify design context loaded from `design.md` in the feature's spec folder.
- The pass applies only to level-2 records the branch adds or edits, as settled under Clarifications. A `## Threat model` section already on the trunk, in a record the branch doesn't edit, doesn't pause the branch, since that branch isn't changing a security control.
- "Committed" means the file is tracked at the branch's HEAD. A file that exists only in the working tree or the index doesn't count.
- Claude Code skips a folder under `.claude/skills/` that has no `SKILL.md`, as upstream ships `_lib/`. If it lists `_lib` as a broken skill, the helper moves and the mirror entry changes with it.
- Claude Code reads `allowed-tools` written as a YAML list, as upstream writes it. If it ignores the list form, the checkpoint calls prompt for permission instead of running.
- Upstream's broken references to `../../../docs/security.md` and a `vuln-pipeline` are accepted as written, the same as `security-and-hardening`'s citations, since editing them breaks the plain upstream diff.
