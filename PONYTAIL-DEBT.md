# Ponytail debt

Two ledgers, and they are not the same list.

**Markers** are `ponytail:` comments in the source: shortcuts taken on purpose,
each naming the ceiling it accepts and the trigger to revisit it. They are
harvested by `/ponytail-debt` from the tree itself, so the source is the record
and this file is a view of it.

**Audit findings** are what `/ponytail-audit` proposed cutting on a whole-tree
scan. Nothing in the source records them, which is why they are written down
here — a finding that lives only in a transcript is a finding that expires with
the session.

Scanned at `9807303`, wfctl 0.18.0, 2026-09-07, plus one marker added the same
day and not yet committed.

## Markers

| Where | Simplified | Ceiling | Upgrade trigger |
|---|---|---|---|
| `wfctl/cli.py:243` | `status` names the arch records and checks nothing | a line someone has to read, not a rule | move it into `check-body`, which already reads a PR description before `gh pr create` sees it |
| `wfctl/cli.py:590` | `archive-story` kept as a hidden alias | transition-only | the alias notice stops appearing during teardowns on every machine |
| `wfctl/cli.py:1747` | `_AGENT_SKILL_EXTRAS` kept as a table with one entry | it reads as speculative generality and gets proposed for collapse on every audit | a second agent never needs a mirror |
| `wfctl/cli.py:2091` | one `git check-ignore` process per path | ~7 ms each, ~600 ms per install, against a ~15 s clone | #1 lands and the clone stops dominating; batch via `check-ignore --stdin` |
| `wfctl/_shape.py:111` | `_LONG_WORDS = 250`, a flat count | a threshold tuned on twenty replies from #208, not a measurement | it starts firing on replies that earned their length |
| `wfctl/_archive.py:205` | `.agent/` rescue read in `_plan` | transition-only | the rescue notice stops appearing during teardowns on every machine |

6 markers, 0 with no trigger.

The two transition-only markers are one end condition, not two: #52 shipped the
alias and the rescue with a shared trigger and says to delete them together.

Three markers are also audit findings — `cli.py:590` and `_archive.py:205` are
findings 5 and 6, `cli.py:1747` is finding 10. Appearing in both ledgers is what
it looks like when the source carries its own argument: the next audit reads the
comment instead of re-deriving the finding against it. The remaining nine
findings have no such anchor and live only in the table below.

## Audit findings

From `/ponytail-audit` on 2026-09-07. Ranked biggest cut first. Nine applied,
two held, one answered in the source.

| # | Tag | Cut | Replacement | Path | Status |
|---|---|---|---|---|---|
| 1 | delete | 800 lines of vendored spec-kit bash that writes agent context files. No skill, command, test or doc invokes it; `_RUNTIME_TARGETS` copies it into every consuming repo | nothing | `wfctl/specify/scripts/bash/update-agent-context.sh` | **applied** |
| 2 | delete | 298 lines. `speckit-specify` reads `spec-template.md` itself; only `check-prerequisites.sh` and `setup-plan.sh` are ever called | nothing | `wfctl/specify/scripts/bash/create-new-feature.sh` | **applied** |
| 3 | delete | 112 lines, the one file in that tree wfctl owns. `vendor-upstream-skills.md` says it describes `/speckit.decompose`; neither the wrapper nor `speckit-delivery-plan/SKILL.md` names it | nothing | `wfctl/specify/templates/github-issue-template.md` | **applied** |
| 4 | delete | 28 lines, read only by finding 1 | goes with it | `wfctl/specify/templates/agent-file-template.md` | **applied** |
| 5 | delete | the `archive-story` alias, its notice, and `pre_remove_wired`'s allowance for it | nothing | `wfctl/cli.py:595,656` · `wfctl/_workmux.py:59,233` | **held** |
| 6 | delete | the `.agent/` rescue: `_LEGACY_DEST_PREFIX`, the `legacy_dir` walk, the rescue count | nothing | `wfctl/_archive.py:80,211-225` | **held** |
| 7 | shrink | three fence walkers with three shapes (40 + 24 + 22 lines) | one walker yielding `(lineno, line, inside)`; each caller keeps its own filter | `wfctl/_shape.py:135` · `wfctl/_body.py:169` · `wfctl/_arch.py:338` | **applied** |
| 8 | shrink | the same 20-line mkstemp/replace/unlink body twice | one `write_atomic(path, text, newline=None)`; the two JSON callers pass `json.dumps(data, indent=2)` | `wfctl/_io.py:11,29` | **applied** |
| 9 | delete | `load_agentconfig` — zero callers in `wfctl/`, zero in `tests/` | nothing | `wfctl/_io.py:58` | **applied** |
| 10 | yagni | `_AGENT_SKILL_EXTRAS`, a dispatch table with one entry, plus the `agent in _AGENT_SKILL_EXTRAS` indirection that avoids naming claude | **answered in the source** — a `ponytail:` marker now names the ceiling and the trigger; `_mirror_supersedes_wrapper` keying on membership is what an inlined call would cost | `wfctl/cli.py:1747,1786` | **answered in source** |
| 11 | delete | `_RESULT_CELLS = 3` and its four-line comment — defined, never read | nothing | `wfctl/_body.py:118` | **applied** |
| 12 | delete | `storyctl` names a tool that no longer exists, and it installs into every consuming repo | `wfctl` | `wfctl/agents/skills/speckit-analyze/SKILL.md:212` | **applied** |

net: -1440 lines proposed, -1256 applied.

**5 and 6 are held, and the reason is on this machine.** #52 kept the
`archive-story` alias and the `.agent/` rescue with one end condition — silence
across every machine during teardowns. Four `.workmux.yaml` files under
`~/Development/wf-skills` still wire `wfctl archive-story` into `pre_remove`,
guarded by `|| true`, so deleting the alias would make every one of those
teardowns archive nothing and swallow the error. That is the loss #52 named,
still live. Re-seed those four with `wfctl install-config`, watch the notice go
quiet, then cut both together.

Findings 1-4 change what `install-skills` writes, so a consuming repo carries
the removed paths until the next install. They fall out of the manifest as
abandoned entries rather than being deleted — `doctor` reports them and
`install-skills --prune` removes them, which is the same shape #183 describes
for any dropped path.

## Considered and not filed

`cli.py` is 4897 lines with a 730-line `install_skills_cmd`. It is the largest
structural cost in the tree and it is not here, because splitting it adds files
rather than cutting them — a reviewable diff of its own, not a deletion.

`wfctl/*.py` is 5016 lines of code against 4350 of comment and docstring, 46%
prose. That ratio is the house style `AGENTS.md` defends, and every block the
audit read was carrying rationale a reader needs. Left alone deliberately, and
recorded here so the next audit does not re-derive it as a finding.
