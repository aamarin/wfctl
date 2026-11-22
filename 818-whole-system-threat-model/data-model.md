# Data model: Whole-system threat model

This feature adds no stored state. Every value below is read from files on disk or from git each time `wfctl status` runs (`session-state-is-re-derived`).

## Inputs the pass reads

| Input | Where it comes from | Who writes it |
| --- | --- | --- |
| Whether the branch changed anything under the arch root | `touched_on_this_branch(repo_root, arch, exclude=non_record_subtrees(arch))`, which returns `None` when git can't answer | The agent, during brainstorm |
| Records the branch adds or edits | `branch_records(repo_root, arch)`, level-2 records only, asked only once the line above returns `True` | The agent, during brainstorm |
| Whether a record has a per-control threat model | A line matching `^## Threat model` in `Record.body`, outside fenced code | The agent |
| Whether the baseline is committed | `git ls-tree --name-only HEAD -- THREAT_MODEL.md`: the name printed is committed, nothing printed is absent, a non-zero exit is git failing | `/threat-baseline`, which ends by committing the file |
| Whether `spec.md` exists | The feature's spec folder | `/speckit.specify` |
| The pass exception | `exceptions/` in the spec folder, written by `wfctl step none brainstorm.threat-baseline` | The user |
| Whether design-record checks are on | `design_record_checks(repo_root)` | The repository's `wfctl.json` |

## Pass states

The reader checks these conditions in order and returns the first that holds. `_pass_states` puts a claim ahead of all of them.

| Condition | State | Reason or display |
| --- | --- | --- |
| A `step none` claim exists | `skipped` | The user's reason |
| Design-record checks are off | `skipped` | The existing checks-off reason |
| The arch root is outside the working tree | `skipped` | Records are kept outside this repository |
| Git can't say what the branch changed under the arch root | `in_progress` | `GIT_UNANSWERED_REASON`, with `GIT_UNANSWERED_HELP` as the remedy |
| No record the branch adds or edits has `## Threat model` | `skipped` | No record on this branch has a threat model, or `DRAWINGS_UNCHECKED` when there's no trunk |
| `THREAT_MODEL.md` committed at the root | `done` | None |
| File missing | `in_progress` | `THREAT_MODEL.md` isn't committed at the repository root. The remedy names `/threat-baseline`, and labels the `step none` line as the user's to run |
| Git can't read `HEAD` | `in_progress` | `BASELINE_UNANSWERED_REASON` |

Past `spec.md`, every `in_progress` row above reads `done` instead and carries its reason and remedy as a warning (FR-012a). A branch with `spec.md` and no `design.md` never reaches the reader, since `brainstorm` reads `skipped` there, so it gets no warning.

## Files the feature ships

| File | Ownership | Notes |
| --- | --- | --- |
| `wfctl/agents/skills/threat-model/{SKILL.md,README.md,bootstrap.md,interview.md,schema.md}` | Upstream, Apache-2.0 | Unedited except the attribution line appended to `SKILL.md` |
| `wfctl/agents/skills/_lib/checkpoint.py` | Upstream, Apache-2.0 | Unedited, keeps its SPDX header |
| `wfctl/agents/skills/threat-baseline/SKILL.md` | wfctl | The layer over upstream |
| `wfctl/agents/commands/threat-baseline.md` | wfctl | Suppressed in the Claude layer by the mirror |
| `wfctl/agents/skills/LICENSE-Apache-2.0` | Upstream's license text | Required by Apache-2.0 §4(a) |

## Files the feature writes in a consuming repository

| File | Written by | Committed |
| --- | --- | --- |
| `THREAT_MODEL.md` at the repository root | Upstream's skill, then `threat-baseline`'s additions | Yes, by `threat-baseline`'s last step, and that's what the pass checks |
| `.threat-model-state/` | Upstream's helper during a bootstrap | No, `install-skills` ignores it |
