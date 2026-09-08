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

Harvested at `eb61482`, wfctl 0.19.0, 2026-09-07 — every `ponytail:` in
`wfctl/**/*.py`, docstrings included. The first pass missed the three in
docstrings by grepping for a comment prefix, so this one keys on the marker
alone. Rows carry the symbol rather than a line number: a line number in a file
that is still being edited is wrong before the commit that writes it lands, and
three of the six here already were.

## Markers

| Where | Simplified | Ceiling | Upgrade trigger |
|---|---|---|---|
| `cli.status_cmd` | names the arch records and checks nothing | a line someone has to read, not a rule | move it into `check-body`, which already reads a PR description before `gh pr create` sees it |
| `cli._FORMER_ARCHIVE_COMMAND` | `archive-story` kept as a hidden alias | transition-only | the alias notice stops appearing during teardowns on every machine |
| `cli._AGENT_SKILL_EXTRAS` | a dispatch table with one entry | one entry | a second agent needs a mirror |
| `cli._ensure_gitignored` | one `git check-ignore` process per path | ~7 ms each, ~600 ms per install, against a ~15 s clone | #1 lands and the clone stops dominating; batch via `check-ignore --stdin` |
| `cli._last_exchange` | reads the whole transcript file | a few megabytes, once per turn | that stops being true; seek to the tail |
| `_paths.main_checkout` | recognises only a `.git` common dir | the standard non-bare layout, and nothing else | a bare or separate-gitdir layout needs one — then `--is-bare-repository` plus an explicit setting, never a looser check |
| `_paths.spec_root` | never checks the root exists, never creates it | a caller that needs it present must say so | nothing: adding the check back rebuilds the bug it was removed for |
| `_shape._LONG_WORDS` | a flat count of 250 | a threshold tuned on twenty replies from #208, not a measurement | it starts firing on replies that earned their length |
| `_archive._plan` | `.agent/` rescue read | transition-only | the rescue notice stops appearing during teardowns on every machine |

9 markers, 0 with no trigger.

The two transition-only markers are one end condition, not two: #52 shipped the
alias and the rescue with a shared trigger and says to delete them together.

Three markers are also audit findings — `_FORMER_ARCHIVE_COMMAND` and
`_archive._plan` are findings 5 and 6, `_AGENT_SKILL_EXTRAS` is finding 10.
Appearing in both ledgers is what it looks like when the source carries its own
argument: the next audit reads the comment instead of re-deriving the finding
against it. The remaining nine findings have no such anchor and live only in the
table below.

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

**5 and 6 are held because their end condition is not met, and it is checkable
rather than remembered.** #52 kept the `archive-story` alias and the `.agent/`
rescue with one trigger: silence during teardowns on every machine. The
condition is that no `.workmux.yaml` anywhere still names the retired command:

```bash
find <where your checkouts live> -name .workmux.yaml -exec grep -l archive-story {} +
```

`find`, not `**`. Bash leaves `globstar` off by default, so `~/**/.workmux.yaml`
matches one level below the home directory and nothing deeper — and a worktree
nested two levels down is exactly the shape this is looking for. The glob is
recursive in zsh and not in bash, so the same line means different things in two
shells and the shallow reading is the one that says *safe to delete*.

A non-empty result means a teardown of one of those worktrees would invoke a
command that no longer exists, get a non-zero exit swallowed by the hook's
`|| true`, and remove the worktree having archived nothing — the spec loss #52
kept the alias for. When it comes back empty, re-seed with `wfctl install-config`
if needed, then cut 5 and 6 together.

That grep was non-empty when this was written. Which repositories is not
recorded here: it is a fact about one developer's disk on one day, and a reader
running the check themselves gets a true answer instead of a stale one.

Findings 1-4 change what `install-skills` writes, and a consuming repo does not
get all of them back. The two templates are recorded per file, so dropping them
from the bundle makes them abandoned entries that `doctor` reports — the shape
#183 describes. The two scripts are not: `.specify/scripts/bash` is recorded as
one *directory* item, and the copy is `copytree(..., dirs_exist_ok=True)`, which
merges rather than mirrors. The directory still ships, so it never orphans,
`--prune` never reaches inside it, and `doctor`'s one-level scan sees only the
recorded `bash/`. Both scripts stay on disk in every consuming repo and nothing
reports them.

## Considered and not filed

`cli.py` is 4897 lines with a 730-line `install_skills_cmd`. It is the largest
structural cost in the tree and it is not here, because splitting it adds files
rather than cutting them — a reviewable diff of its own, not a deletion.

`wfctl/*.py` is 5016 lines of code against 4350 of comment and docstring, 46%
prose. That ratio is the house style `AGENTS.md` defends, and every block the
audit read was carrying rationale a reader needs. Left alone deliberately, and
recorded here so the next audit does not re-derive it as a finding.
