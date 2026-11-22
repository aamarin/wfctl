# Research: Whole-system threat model

Each entry records what was decided, why, and what else was weighed. Facts were checked against the code at `3fa1119b` and upstream at `anthropics/defending-code-reference-harness@d3bea6b5`.

## R1. Which upstream mode `threat-baseline` invokes

- **Decision**: Attended, it invokes upstream's `bootstrap-then-interview` mode against `.`. With auto-approve on, it invokes `bootstrap` against `.` and then runs wfctl's self-walkthrough.
- **Rationale**: Upstream's `SKILL.md` already offers three modes, and `bootstrap-then-interview` chains the code-derived draft with the owner interview. That is the attended answer clarify settled (Q1), with no wfctl logic needed to sequence the two. Unattended, `interview` would wait on a person who isn't there.
- **Alternatives considered**: Running `bootstrap` and then `interview` as two invocations. We didn't choose this because upstream's combined mode exists for this case and seeds the interview from the draft.
- **Where the flag comes from**: The skill reads the top-level `auto_approve` key of `wfctl status --json`, the same key `plan-walkthrough` reads, and branches on it before invoking upstream.
- **How it ends**: The skill commits `THREAT_MODEL.md` with `git add THREAT_MODEL.md` and `git commit -m "<subject>" -- THREAT_MODEL.md`. The pathspec on `commit` keeps anything else staged out of the commit. Its frontmatter grants `Bash(wfctl status*) Bash(git add THREAT_MODEL.md) Bash(git commit*)`, beside upstream's helper grant, following `speckit-brainstorm`'s `git add*` and `git commit*` grants. The pass reads done only on a commit (R5), so a skill that wrote the file and stopped would send an unattended run back to a full bootstrap on every pass until the stall count stopped it (FR-007a).
- **The per-control section afterwards**: When the branch already has a record with a `## Threat model` section, the skill's last step has the agent re-read that section against the committed baseline and update it where the baseline names something the section missed (FR-015a). That edit is to the record, so it doesn't touch the baseline commit.
- **The exception stays the user's**: The skill and its wrapper say that `wfctl step none brainstorm.threat-baseline` is the user's decision and the agent doesn't run it, the way the `plan-review` command says an option and doesn't take it. Neither grants the command in `allowed-tools`, and no other shipped skill does either (FR-007b). `step none` has no check on who runs it (`wfctl/cli.py:2690-2748`), so this instruction and the missing grant are what keep the answer with the user. The PR body carrying the reason is the backstop.

## R2. How the helper resolves for each agent

- **Decision**: `_lib/` ships under `wfctl/agents/skills/`, so the base layer copies it to `.agents/skills/_lib/`, Bob's layer to `.bob/skills/_lib/`, Copilot's to `.github/skills/_lib/`, and Claude's mirror to `.claude/skills/_lib/` once `_lib` is in `_MIRRORED_SKILLS`. `threat-baseline` tells the agent to run `python3 <folder this skill was loaded from>/../_lib/checkpoint.py` wherever upstream names `.claude/skills/_lib/checkpoint.py`.
- **Rationale**: Clarify Q2. `_AGENT_TARGETS` at `wfctl/cli.py:3856` copies `agents/skills` whole for Bob and Copilot, and Codex reads `.agents/` directly, so the helper is already beside the skill for every agent. Only upstream's text is Claude-specific.
- **Alternatives considered**: Editing upstream's path (reverted by the next pull), and installing `_lib` into `.claude/` for every agent (writes into a folder a non-Claude repo doesn't use). Installing through agent plugin marketplaces was split out as #847.
- **Known cost**: Upstream's `allowed-tools` pre-approves only the `.claude/` path, and only Claude Code reads that key, so other agents ask permission the first time the helper runs.

## R3. A skill folder with no `SKILL.md`

- **Decision**: Ship `_lib/` as a folder under `agents/skills/` with no `SKILL.md`, and check every loop over that directory that assumes one.
- **Rationale**: `test_skill_frontmatter.py` already skips a folder with no `SKILL.md` (`if not skill_md.exists(): continue`). `MANIFEST.in` grafts `wfctl/agents` with `os.walk`, so `checkpoint.py` ships in the wheel. The remaining risk is Claude Code listing `_lib` as a broken skill, which the spec records as an assumption with its fallback.
- **Alternatives considered**: Moving the helper inside `threat-model/`. We didn't choose this because upstream's paths name `_lib` beside the skill, and moving it is an edit.

## R4. Where the pass's reader lives and what it reads

- **Decision**: A new reader, `brainstorm_threat_baseline`, in `wfctl/_evidence.py`, registered as `SubStep("threat-baseline", "/threat-baseline", _AUTOMATIC, ...)` between `architecture` and `software-design` in `wfctl/_pipeline.py:126`. It reads records in two steps, as `fact_architecture_accepted` does:
  1. It asks `touched_on_this_branch(repo_root, arch, exclude=non_record_subtrees(arch))` first. That function returns `None` when git can't answer, when there's no trunk and nothing uncommitted, or when the arch root is outside the tree. `branch_records` returns an empty mapping in all three cases, which the reader would otherwise read as "no record has a threat model" and skip silently (its docstring at `wfctl/_evidence.py:1336-1338`).
  2. Only when that returns `True` does it call `branch_records(repo_root, arch)` with `added_only=False`, which lists level-2 records the branch added or modified (`wfctl/_evidence.py:1309`).

  It then looks in each `Record.body` for a line matching `^## Threat model` outside fenced code blocks. That is the pattern `reviewing-security` greps for (`git grep -l '^## Threat model'`, pinned by `tests/test_threat_model_skills.py:71`), so the pass and the security reviewers agree on which records carry a threat model. Excluding fenced code keeps a record that quotes the heading as an example from counting, which the reviewer's grep can't do. A record whose only match is fenced is the one case where the two differ, and the reviewer then reads one extra record.
- **Rationale**: Clarify Q3 settled "adds or edits", and `branch_records` without `added_only` is that set. `Record.body` already holds the file as read (`wfctl/arch/_records.py:80`), so the reader opens no file of its own. Asking `touched_on_this_branch` first is what `branch_records`' own docstring tells a caller to do when it has to tell "nothing" apart from "couldn't ask".
- **Alternatives considered**: Scanning every record in the arch root. We didn't choose this because clarify Q3 rejected it.

## R5. How "committed at the repository root" is read

- **Decision**: `git ls-tree --name-only HEAD -- THREAT_MODEL.md` from the repository root, run with `subprocess.run` in the reader, as `touched_on_this_branch` and the other git reads in `wfctl/_paths.py` do. `_evidence.py` has no git helper of its own. Exit 0 with the name printed is committed. Exit 0 with nothing printed is absent. Any non-zero exit, such as a repository with no commits or a git that can't run, is "git couldn't answer".
- **Rationale**: The spec's assumption defines committed as tracked at HEAD. `ls-tree` on `HEAD` answers exactly that, and ignores the working tree and the index, so an uncommitted file reads absent. It also keeps absence and failure apart by exit code, which `git cat-file -e HEAD:<path>` doesn't: that command exits 128 both for a missing path and outside a repository, so absence would read as git failing (checked during plan review).
- **The reason when git can't answer**: A new constant, `BASELINE_UNANSWERED_REASON = "git can't see whether THREAT_MODEL.md is committed"`. `GIT_UNANSWERED_REASON` is about whether the branch wrote a record, so it fits the record read in R4 and not this one.
- **Alternatives considered**: `git ls-files --error-unmatch`, which also accepts a staged file. We didn't choose this because a staged file isn't in the PR either. `git cat-file -e`, the first choice, for the exit-code reason above.

## R6. What the pass reads in each state

- **Decision**: The reader works out its verdict in this order:
  1. `design_record_checks` off → `skipped` with the existing checks-off reason, as both sibling readers do.
  2. The arch root is outside the working tree → `skipped`, with the display line "records are kept outside this repository", as `fact_architecture_accepted` reads it. Nothing failed here, since git is being asked about a path it doesn't track.
  3. `touched_on_this_branch` returns `None` → `in_progress` with `GIT_UNANSWERED_REASON` and `GIT_UNANSWERED_HELP`. That covers git failing and a repository with no trunk and nothing uncommitted, which the help text tells the user how to fix.
  4. No record the branch adds or edits has `## Threat model` → `skipped`, with a display line saying no record on this branch has a threat model. When `trunk_branch` returns `None`, the display line is `DRAWINGS_UNCHECKED` instead, since only uncommitted records were listed, the same as `_judge_drawings` does. The pass cascade treats a reader's own `skipped` as not outstanding (`_pass_states`, `wfctl/_pipeline.py:521`).
  5. Such a record exists and the file is committed → `done`.
  6. Such a record exists and the file is missing → `in_progress` with a reason naming the file and a remedy naming `/threat-baseline`, plus the `step none` line labeled as the user's (see the contract).
  7. Such a record exists and the `HEAD` read fails → `in_progress` with `BASELINE_UNANSWERED_REASON` (R5).
  8. Last, if `spec.md` exists and rows 3, 6, or 7 produced `in_progress`, the reader returns `done` carrying that reason and remedy instead. `collect_warnings` then reports it as a warning without holding anything (`wfctl/_pipeline.py:974`).
- **Rationale**: Row 8 follows `brainstorm_architecture`, which folds a held verdict into a `done` reading past specify, so a branch already past specify when this check ships isn't sent backwards (FR-012a). It applies to the git-failure rows too, as `brainstorm_software_design`'s `spec.md` escape does. Rows 3 and 7 follow `promised-evidence-blocks-on-silence`: the evidence is `repo-declared`, so a failed read holds rather than lets the branch through. Row 3 also closes the silent skip `branch_records` would otherwise produce (R4).
- **Limit on row 8**: With `spec.md` and no `design.md`, `brainstorm` reads `skipped` and `_pass_states` gives every pass an inherited `skipped` without calling its reader (`wfctl/_evidence.py:1762-1767`). FR-012a's warning doesn't show on such a branch. The architecture pass has the same limit, and its docstring says so (`wfctl/_evidence.py:1593-1594`). A security change writes `design.md`, so this case is rare.
- **Note**: A `wfctl step none brainstorm.threat-baseline` claim is read by `_pass_states` before the reader runs, and reads `skipped` with the claim's reason. That is why the spec says `skipped`, not `done`, for an exception.

## R7. The command wrapper

- **Decision**: Ship `wfctl/agents/commands/threat-baseline.md` beside the skill, and add `threat-baseline` and `threat-model` to `_MIRRORED_SKILLS`.
- **Rationale**: For Claude, the mirrored skill answers `/threat-baseline`, and `_mirror_supersedes_wrapper` suppresses the wrapper there. Every other layer gets the wrapper, which is how `design-levels` ships today.
- **Alternatives considered**: A `/threat-model` wrapper, rejected in the level-3 record.

## R8. Attribution and the Apache-2.0 notice

- **Decision**:
  1. Append `Derived from [anthropics/defending-code-reference-harness](https://github.com/anthropics/defending-code-reference-harness) (Apache-2.0, © 2026 Anthropic PBC).` as the last line of upstream's `SKILL.md`, as every derived skill carries.
  2. Add a `threat-model` row to the first table in `vendor-upstream-skills.md`, and an `agents/skills/_lib/checkpoint.py` row to the second, credited by `NOTICES.md` the way the `/security-review` prompt is. `checkpoint.py` keeps upstream's SPDX header unedited.
  3. Add an `anthropics/defending-code-reference-harness` section to `wfctl/agents/skills/NOTICES.md` naming `threat-model` and `_lib/checkpoint.py`, with the copyright line, and ship upstream's `LICENSE` text beside it as `LICENSE-Apache-2.0`, since Apache-2.0 §4(a) asks for a copy of the license.
  4. `NOTICES.md`'s opening says its upstreams are MIT-licensed, and that sentence changes to cover this one.
- **Rationale**: `vendor-upstream-skills.md` says a file taken from elsewhere gets its line and its row in the same change, and `tests/test_skill_attribution.py` checks the two against each other.
- **To fix in the test**: `tests/test_skill_attribution.py` needs four changes, each written to fail first:
  1. `_ROW`'s path pattern is `[a-z0-9./-]+`, which can't match `_lib`, so the pattern accepts `_`.
  2. `_sections` sets every notice section's licence to `_licence_the_notices_carry()`, which is `LICENSE`'s first line, `MIT` (lines 286-289). So `test_every_attribution_line_agrees_with_its_notice_entry` fails on the new Apache-2.0 line. Each section instead reads its licence from the notice, and `NOTICES.md` gives each section a licence line. The test's own docstring at lines 367-378 names this as the change a first Apache-2.0 upstream needs.
  3. The test that checks the MIT permission block against `LICENSE` gains a twin that checks the Apache-2.0 section against `LICENSE-Apache-2.0`. Loosening the licence comparison instead would remove the check that a line and its notice agree.
  4. `_reference_claims` only reads paths with a `references/` segment (lines 188-199), so moving the helper's row into `_NOTICED_ROWS` alone would leave it with no check. A claim pattern for `_lib/` paths joins it, so the notice naming `_lib/checkpoint.py` is checked against the record's row (FR-001).

## R9. The ignore entry

- **Decision**: Add `.threat-model-state/` to the paths `install-skills` passes to `_ensure_gitignored` (`wfctl/cli.py:6080`).
- **Rationale**: Upstream's bootstrap writes its checkpoints to `./.threat-model-state/` in the working directory, and a bootstrap run on wfctl itself would otherwise leave it untracked.

## R10. The test fixes for the vendored files

- **Decision**:
  1. `ALLOWED_KEYS` in `tests/test_skill_frontmatter.py:19` gains `argument-hint`, with a comment saying it's a Claude Code key upstream carries.
  2. `_OWN_FILE` in `tests/test_skill_cross_references.py:94` also matches "Read `X` in this directory".
  3. A new test reads every `.claude/skills/<path>` a shipped skill names and checks that `<path>`'s first segment is a mirrored item that ships.
- **Rationale**: FR-016 to FR-018. Each test is written to fail against the vendored files first.
