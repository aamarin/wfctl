# Phase 0 — research

No `NEEDS CLARIFICATION` markers survived specify. The one genuinely open
question — how uninstall recognises an unmarked entry as wfctl's — was answered
at the level-2 gate before the spec was written, and is recorded at
`docs/architecture/the-manifest-owns-what-carries-no-marker.md`.

What follows is the record of what was read in the code rather than assumed, and
what is still a bet. The design records carry the same split for the decisions
they cover; this is the plan's own.

## Verified

| Claim | Where |
|---|---|
| `merge_hook` sets only `command` and `type` when replacing in place; `matcher` is never read | `_settings.py:110-118` |
| `_unmerge_hooks` reads `record["event"]` with no guard | `cli.py:1995` |
| `install_skills` builds its carry-forward map as `{(m["path"], m["event"]): m}` | `cli.py:2733` |
| `_merge_hooks` re-reads the settings file inside its per-target loop, so the file is already opened once per managed event | `cli.py:1937` |
| `_merge_hooks` runs *after* the skill copies, so a refusal raised there leaves a half-installed tree | `cli.py:2738`, copies above it |
| `created` is read back defensively as `.get("created", False)` | `cli.py:1926` |
| A `⚠` line in `_check_managed_hooks` prints without setting `drift`, so a warning tier already exists that leaves the exit code alone | `cli.py:4470-4474` |
| `_check_managed_hooks` returning `True` is what sets `exit_code = 1` | `cli.py:4986-4990` |
| `--force` is the house name for "proceed over a conflict" | `install-config --force` |
| `install-skills` has no `--force` today | `wfctl install-skills --help` |
| The guard refuses `cd` to an absolute path in another worktree already; `cd ../sibling` is the gap the deny rule closes | `_guard.py:35-39` |
| `permissions` in a settings file is an object of string lists | the user's own global settings carries `permissions.allow` in that shape |
| The manifest already holds repo choices beside wfctl's records | `_manifest.py:10` — "bare scalars recording a repo's choices (`tracker`, `spec_root`)" |
| Nothing implements the speckit extension hooks or consumes `EXECUTE_COMMAND` | no `extensions.yml`; no `wfctl/*.py` match |

## Assumed

| Bet | What falsifies it |
|---|---|
| Claude Code matches a `permissions.deny` string by exact equality, so `Bash(cd:*)` cannot be decorated | the matcher turning out to normalise or glob the rule text — which would make a marked variant possible and send the level-2 record back for revision |
| No consumer keeps a `permissions` value that is not an object | a file in the wild; the cost is a `ValueError` surfaced as a merge problem, the arm `merge_hook` already uses for a malformed `hooks` key |
| A worktree's `post_create` install cannot meet a drifted rule, because its `.claude/` is created fresh by that same install | a workflow that seeds `.claude/settings.json` before `install-skills` runs. This is what makes the refusal safe in the one unattended install path, so it is the bet worth re-checking if `post_create` ever changes |

## Retired

The perf objection recorded on #136 — that the guard costs ~119 ms per Bash call
and seeding it makes that cost everyone's. #135 closed COMPLETED: measured on
`main`, 81.7 → 33.8 ms/call once the guard stopped importing `wfctl.cli` and
stopped shelling out to git twice, against a 27.1 ms bare-Python floor. Recorded
here so it is not re-litigated from the issue comment, which still carries the
old number.
