# Threat Model: wfctl

> This is a working map of what the system exposes, revised as the system changes. It is not a decision record, so a "risk accepted" status here doesn't accept anything in `docs/architecture/`.

## 1. System context

wfctl is a Python 3.11 command-line tool, built on typer and rich, with about 54 modules. The largest is `wfctl/cli.py`, at over 8,000 lines. A developer runs it beside CLI coding agents such as Claude Code, Codex, and Bob Shell, each agent in its own git worktree. wfctl tracks where a feature sits in a spec-driven pipeline and tells the agent what to run next. It also installs skills, slash commands, three shell scripts, hooks, and permission rules into a project, and the agent then runs those files as instructions and code. wfctl runs on the developer's machine with the developer's git, gh, and tracker credentials. It also runs in GitHub Actions on `aamarin/wfctl` for the `review`, import-check, and release jobs.

wfctl's security claim is that an agent can produce evidence but doesn't certify what the evidence proves. A small set of actions stays with a person:

1. Opening or merging a PR while a review group has unreviewed commits.
2. Accepting an architecture record.
3. Signing off a review.
4. Approving a change to the import map.
5. Turning auto-approve on.

wfctl enforces these with a PreToolUse hook that reads the agent's command text, a git-notes review record that CI checks, and permission rules it installs into the agent's settings. Its own documents state the limit: an agent that sets out to forge evidence with the user's credentials can do it. Most controls therefore make tampering visible in the PR diff rather than impossible. The main adversary is the agent itself, acting by mistake, by habit, or on instructions planted in text it reads, plus anyone who can put text in front of it.

## 2. Assets

| asset | description | sensitivity |
|---|---|---|
| review record | Git notes under `refs/notes/wfctl-review`, and the run records behind them, saying which review groups covered which commits. CI's required `review` check reads them. | critical |
| person-only decisions | Accepting an architecture record, a review sign-off, `approve-imports`, and turning auto-approve on. Each is meant to come from a person at a terminal. | critical |
| main branch and releases | The protected `main` branch, its hand-applied ruleset, `v*` tags, and the GitHub releases that `uv tool install` and `doctor` resolve by tag. | critical |
| developer machine and credentials | The developer's shell, git and gh credentials, and tracker access. Every hook, verify command, and reviewer command runs with them. | critical |
| installed agent instructions | Skills, commands, `.specify/scripts/bash/*.sh`, hooks, and permission rules that `install-skills` writes into a project and the agent executes. | high |
| peer worktrees and the main checkout | Other worktrees and the main checkout on the same machine, which the guard keeps one session from changing. | high |
| pipeline state | What `wfctl status` reports as done: spec-folder files, scan verdicts, design exceptions, verify records, and accepted records. | high |
| session handoff | `session-summary.md` and the event log in the state dir, which the next session reads and acts on without asking. | medium |
| consumer repository files | Hand-authored files, `.gitignore`, and settings in a project that `install-skills` or `uninstall-skills` writes or deletes. | medium |
| spec store | The orphan `specs-trunk` branch and the spec root outside the working tree, holding specs, plans, and scans. | medium |
| session and CI availability | A session's ability to proceed, and CI's ability to pass a correct PR. | low |

## 3. Entry points & trust boundaries

| entry_point | description | trust_boundary | reachable_assets |
|---|---|---|---|
| agent shell commands | The Bash command text a coding agent sends. The PreToolUse worktree guard (`wfctl/guard/_hook.py`, `_guard.py`, `wfctl/_review_gate.py`) reads it and refuses by matching that text. | agent output → developer shell | review record, person-only decisions, peer worktrees and the main checkout, developer machine and credentials |
| person-only commands | `wfctl arch accept`, `review sign-off`, `arch approve-imports`, and `auto-approve on`. They're gated by the guard's text rules, a TTY check on accept, and Claude Code `ask` rules. | agent → human authority | person-only decisions, review record |
| review runs and notes | Reviewer reports parsed for `Reviewed` and `Verdict` lines, run records in the state dir, and the notes wfctl writes and pushes to `origin` (`wfctl/_review.py`, `_review_notes.py`). | reviewer agent output and local git state → review record | review record, main branch and releases |
| CI review job | A `pull_request_target` job that runs the base branch's wfctl and `check_imports.py` over the PR head's git objects, notes, and `wfctl.json` as data (`.github/workflows/review.yml`). | PR-controlled data → required merge check | review record, main branch and releases |
| CI pull_request and tag jobs | `ci.yml` runs the PR's own code with a read-only token. On `main`, a tag job with `contents: write` tags the `chore(release)` commit and publishes its body (`.github/scripts/tag_release.py`). | PR code and merged `main` → published release | main branch and releases |
| GitHub repository settings | The ruleset in `.github/rulesets/main.json`, applied by hand, the merge-method settings, and the absence of tag or notes-ref protection. | repository admin settings → merge and release policy | main branch and releases, review record |
| repository config | `wfctl.json`'s `verify`, `steps`, and `review.commands`, plus a committed `.wf-skills-manifest.json` source that `doctor` turns into `install-skills --from`. | committed repository content → commands run on the developer machine | developer machine and credentials, installed agent instructions |
| install-skills | Copies the bundle into `.agents/`, `.claude/`, and `.specify/scripts/bash/`, merges hooks and permission rules into settings, edits `.gitignore`, and backs up overwritten files. | wfctl bundle → consumer repository and agent | installed agent instructions, consumer repository files |
| vendored upstream content | Skills and scripts taken from Spec Kit, Superpowers, and Anthropic's `defending-code-reference-harness`, shipped as package data. | upstream repositories → agent instructions in every consumer | installed agent instructions, developer machine and credentials |
| tracker text | Issue and PR titles and bodies that `wfctl status --session`, `start`, `check-body`, and the tracker verbs read (`wfctl/_tracker.py`). | anyone who can file or edit an issue → agent context | session handoff, person-only decisions, developer machine and credentials |
| pipeline evidence files | `spec.md`, `plan.md`, `tasks.md`, scans, design exceptions, and records that wfctl parses to decide which step is done and whether a gate opens. | agent-written markdown → pipeline state | pipeline state, person-only decisions |
| state dir files | `events.jsonl` (including auto-approve mode events), `verify.json`, review run records, and `session-summary.md` under the XDG state dir. | agent-writable files → gates and the next session | pipeline state, person-only decisions, session handoff, review record |
| shared spec and state roots | Folders outside every worktree that the guard lets feature sessions write to, including the spec store checkout. | one session → folders shared with every session | peer worktrees and the main checkout, spec store |
| workmux worktree hooks | `post_create` runs `uv run wfctl install-skills` and `issue start` from the new branch, and `pre_remove` runs `wfctl archive-specs`, which pushes to the spec store. | checked-out branch code → developer machine | developer machine and credentials, spec store |
| process environment | `WFCTL_*` and XDG variables that place the spec and state roots, and the `wfctl` first on `PATH` that every hook runs. | environment → guard exemption and hook binary | peer worktrees and the main checkout, person-only decisions |

## 4. Threats

The coding agent acts as `local_user`: it runs as the developer, with the developer's credentials, on the developer's machine.

| id | threat | actor | surface | asset | impact | likelihood | status | controls | evidence |
|---|---|---|---|---|---|---|---|---|---|
| T1 | An agent forges a review record, by writing or pushing notes or by hiding commits from the reviewed range, so CI passes commits no reviewer read | local_user | review runs and notes, CI review job | review record, main branch and releases | critical | possible | partially_mitigated | The guard refuses `git notes` writes, notes-ref pushes, `--mirror`, `update-ref` into `refs/notes/`, replace refs, and grafts; wfctl pushes notes itself; sign-off refuses an unknown trunk. CI trusts any note it finds (#658). | d1b1eaef, 1c9d9a86, b584eedb, c1cec048 |
| T2 | Opening or working in an unfamiliar repository runs commands its committed config names, with the developer's credentials | remote_auth | repository config, workmux worktree hooks | developer machine and credentials, installed agent instructions | critical | possible | partially_mitigated | `review.commands` is read from the trunk, not the branch; `verify` takes argv lists with no shell; AGENTS.md says to read hooks, the manifest, and `review.commands` first. `/start-session` runs a manifest's `--from` line with `--yes`, and `post_create` runs the branch's own code. | |
| T3 | A PR passes the required `review` check without a review, by adding a job named `review` to its own copy of `ci.yml` | local_user | CI pull_request and tag jobs | review record, main branch and releases | critical | possible | unmitigated | The ruleset pins `review` to the GitHub Actions app (`integration_id` 15368), which a job in the PR's workflow also reports under. The new job shows in the PR diff. | |
| T4 | A merged commit or a moved tag publishes a release nobody cut, which `uv tool install` and `doctor` then serve | insider | CI pull_request and tag jobs, GitHub repository settings | main branch and releases | critical | rare | partially_mitigated | The tag job checks the release commit's subject, version, and body before tagging; `main` needs a merge commit and green checks. No tag ruleset exists, and Actions are pinned by tag, not SHA. | |
| T5 | An agent opens or merges a PR while a review group has unreviewed commits, through a command form the guard's text match doesn't recognize | local_user | agent shell commands | review record, main branch and releases | high | likely | partially_mitigated | The guard refuses `gh pr create` and `gh pr merge` in the forms it parses, reads comments, braces, globs, and redirects the way the shell does, and refuses on a NUL byte. CI's `review` check blocks the merge, not the opening. | 0f5c3c73, 7eebda4d, 842f8dea |
| T6 | An agent takes a person-only decision (record acceptance, review sign-off, import approval, or auto-approve on) through a form the guard or the `ask` rules don't recognize | local_user | person-only commands, agent shell commands | person-only decisions | high | likely | partially_mitigated | The guard refuses literal accept forms, sign-off, and `approve-imports`; `arch accept` needs a TTY; four `ask` rules cover the `auto-approve on` spellings. Words built at run time are refused only best-effort (#819), and the guard doesn't back the `ask` rules. Bob Shell gets no `ask` rules. | ca60e36a |
| T7 | One session deletes or changes a peer worktree or the main checkout through the guard's shared-root write exemption | local_user | shared spec and state roots, agent shell commands | peer worktrees and the main checkout | high | likely | partially_mitigated | The exemption is an allowlist granted to a whole command or not at all; paths are judged as written and as landed; git, relative climbs, and comments are declined. Six rounds of fixes show the text check keeps finding new forms. | eda54aca, 02f72185, 4b3c4297, 363fc42c, 09bc28b1, 7881b9ea |
| T8 | An agent writes state-dir records directly to grant auto-approve, mark `verify` passed, or plant a handoff the next session acts on | local_user | state dir files | person-only decisions, pipeline state, session handoff | high | possible | partially_mitigated | The verify record carries the commit and a dirty flag; mode events carry the session that wrote them; wfctl re-derives what it can from disk. Nothing authenticates a file the agent can write. | |
| T9 | Text planted in an issue or PR steers the agent into an outward action or a forged handoff | remote_unauth | tracker text | session handoff, person-only decisions, developer machine and credentials | high | possible | partially_mitigated | `wfctl status` indents issue bodies so they can't forge report headings; skills say tracker text is data, never instructions; start-session never runs a command or URL named in an issue; the host's permission layer prompts on outward writes. | 33b6f85c, 3d967c6f |
| T10 | A permission grant wfctl ships pre-approves an outward or person-only command, so the agent runs it with no prompt | supply_chain | install-skills | person-only decisions, developer machine and credentials | high | possible | partially_mitigated | `/store-specs` now asks before the push; a test fails on any shipped grant that would approve `step none brainstorm.threat-baseline`; upstream's `threat-model`, which grants `Bash(git:*)` and `Bash(gh api:*)`, isn't installed where Claude honors grants; a test fails on any grant Claude honors that approves a push, a git alias, `git grep -O`, or a `gh` write. `threat-baseline` grants only reading and searching files, since one unprompted write to `.git/config` would turn every later git command into a command the repository's text chose. No test covers the other person-only commands, and wfctl's own prefix grants such as `git commit*` still approve variants like `--amend`. | ae4efd3a |
| T11 | PR content gets past the import-map check or the review check because the base branch's CI code misreads data the PR controls | remote_auth | CI review job | review record, main branch and releases | high | possible | partially_mitigated | CI runs `main`'s copy of the script and of wfctl, with `python3 -I` and a read-only token, and treats the PR checkout as data. Widening the map needs a person's `approve-imports`. | 0a443425 |
| T22 | An agent moves the local trunk ref so `review start` reads `review.commands`, `review.rounds`, or `trunk` from a commit the agent chose | local_user | repository config, agent shell commands | developer machine and credentials, review record | high | possible | partially_mitigated | `review start` warns when the branch's values differ from the trunk's, and CI reads the base from the GitHub event. The guard refuses `update-ref` only into `refs/notes/`, so `refs/remotes/origin/<trunk>` can be moved. | |
| T12 | Compromised or altered upstream content ships in a release and reaches every consumer's agent as instructions | supply_chain | vendored upstream content, install-skills | installed agent instructions, developer machine and credentials | high | rare | partially_mitigated | Upstream files are vendored at a recorded commit, attributed, and diffed on each pull; `doctor` reports drift between installed and shipped files. | |
| T13 | A crafted record name, path, or branch name injects shell into a remedy line that the agent or the user then runs | remote_auth | pipeline evidence files, tracker text | developer machine and credentials | high | rare | mitigated | Printed remedies shell-quote interpolated values; record listings are NUL-separated. | 64d12b65, 27bb4656, 3d967c6f |
| T14 | The ruleset on GitHub drifts from `main.json` and drops a required check, and nothing notices | insider | GitHub repository settings | main branch and releases, review record | high | rare | unmitigated | AGENTS.md lists read-back commands to run by hand. Nothing in CI compares the two. | |
| T15 | The environment or `PATH` points every hook at a different wfctl, or moves the shared roots to widen what the guard lets a session write | local_user | process environment | peer worktrees and the main checkout, person-only decisions | high | rare | partially_mitigated | A shared root that contains a worktree isn't honoured. The hook trusts whichever `wfctl` is first on `PATH`. | |
| T16 | An agent marks a step done by writing evidence files that satisfy the parser without doing the step | local_user | pipeline evidence files | pipeline state | medium | likely | partially_mitigated | Scans need a `Verdict` line and a coverage row; an exception needs a reason, which `check-body` requires in the PR body; stale `step-claims/` files are excluded. | fc2df010, e67ff57b |
| T17 | Guard false positives or a broken `review` key on `main` block every session or every PR | local_user | agent shell commands, repository config | session and CI availability | medium | likely | partially_mitigated | The accept rule stopped refusing literal mentions in messages; AGENTS.md documents recovery from a broken `review` key. | ca60e36a |
| T18 | `install-skills` or `uninstall-skills` writes or deletes through a symlink, or overwrites a hand-authored file, in a consumer repository | supply_chain | install-skills | consumer repository files | medium | rare | mitigated | Writes and deletions below a symlinked folder are left alone; overwritten files are backed up to `.wf-skills-backup/`; the prompt lists them unless `--yes` is passed. | 860da983, 0171ae81 |
| T19 | Escape codes in git output, or a failed diff, keep the person from seeing what they approve in `approve-imports` | remote_auth | person-only commands | person-only decisions | medium | rare | mitigated | git and gh stderr and paths are escaped before printing; the command stops when `git diff` fails. | df025422, 7f8b1ea1 |
| T20 | One session's spec push or archive overwrites or deletes another feature's specs in the shared store | local_user | shared spec and state roots, workmux worktree hooks | spec store | medium | rare | partially_mitigated | Spec dirs are keyed by branch; symlinks in a spec dir are copied as links and followed on removal. | b48dd2f4 |
| T21 | An agent resets the review round cap or drops a sign-off by renaming its branch | local_user | review runs and notes | review record | low | rare | mitigated | Round counts and sign-offs are keyed by issue, and review refuses a branch that names no issue. | f07b54cd |

## 5. Deprioritized

| threat | reason |
|---|---|
| A network attacker reaches wfctl directly | wfctl serves nothing and opens no port. Its network calls go through git and gh. |
| Credentials stolen from wfctl's own storage | wfctl stores no token. It uses the ambient git and gh auth, which T2 and T9 cover from the attacker's side. |
| Unsafe deserialization of repository content | wfctl parses only JSON and markdown from local files and git, with no pickle and no dynamic import of repository content. |
| Repudiation of tracker writes and pushes | wfctl logs each successful issue write, and each push reported with `report-action`. A push the agent doesn't report is still in the remote's own log. |
| A payload that crashes the guard and lets the command run | A NUL byte now refuses instead of crashing (842f8dea), and a review check that raises refuses. A payload the hook can't decode as JSON is allowed, but the host writes that payload, not the agent. |

## 6. Open questions

- Who merges to `main` in practice: only the maintainer, or agents through the merge API as well? The answer moves the likelihood of T1, T3, and T5.
- When was the ruleset on GitHub last read back against `main.json` (T14)?
- Should a public repository commit `THREAT_MODEL.md` at all, since it lists the threats and gaps in the open? This is tracked in #852.
- Do Codex and Bob Shell run the worktree guard hook? If not, which person-only commands have no check at all on those hosts (T6)?
- Is auto-approve expected under Bob Shell, which gets no `ask` rule for `auto-approve on` (T6)?
- Does anyone other than the maintainer install wfctl from a fork, a `--from` path, or an unfamiliar repository's manifest (T2, T12)?
- Is a blocked session acceptable when a guard false positive stops an unattended run (T17)?
- Can GitHub Actions create and move `v*` tags in this repository, and is that limited to the tag job (T4)?
- Does the worktree guard run for the Bash calls of subagents an agent spawns, on every host wfctl supports (T5, T6, T7)?

## 7. Provenance

- mode: bootstrap
- date: 2026-11-21
- target: . @ dfee8c43
- inputs: git-log and `changes/` mined, public advisories (none listed)
- owner: unset

## 8. Recommended mitigations

| mitigation | threat_ids | closes_class | effort |
|---|---|---|---|
| Post the `review` check from an identity a PR's own workflow can't use, such as a GitHub App or a workflow required by file | T3 | yes | M |
| Run the reviewers in CI, or require a credential only the person holds, before a review note counts | T1, T5 | partial | L |
| Confirm every person-only command interactively on the terminal, as `arch accept` does, instead of relying on command text | T6, T8 | partial | M |
| Require a one-time approval, keyed to the content hash, before running commands a repository's committed config names | T2 | yes | M |
| Add a tag ruleset limiting `v*` creation and updates to the release job, and pin Actions in write-token jobs by commit SHA | T4 | partial | S |
| Read the live ruleset in CI and fail when it differs from `main.json` | T14 | yes | S |
| Test every shipped `allowed-tools` grant against the full list of outward and person-only commands | T10 | yes | S |
| Judge every path after shell expansion, or remove the shared-root write exemption and route spec writes through wfctl commands | T7, T20 | partial | L |
| Shell-quote every value interpolated into a printed command, enforced by a test over the remedy constants | T13 | yes | S |
| Fail closed on any input the CI checks can't place, and keep them reading the PR checkout as data only | T11 | partial | S |
| Read the trunk's config from the remote at review start, or refuse `update-ref` on `refs/remotes/` as the guard does for `refs/notes/` | T22 | yes | S |

## 9. Rejected fixes

| fix | threat_ids | trade_off |
|---|---|---|
| Sign state-dir records with a key the agent can't read | T8 | The agent runs as the same OS user as wfctl, so any key wfctl can read, the agent can read too. A signature would look like protection without adding any. |
| Replace the guard's text rules with a full shell parser | T5, T6, T7 | Words built at run time, such as through `eval`, `xargs`, or a Python subprocess list, still can't be seen before the command runs. Each review round on the guard moved the gap rather than closing it, so `accept-check-threat-model.md` accepts the residual and relies on the PR diff to show it. |
| Drop the local guard and enforce everything in CI | T5 | CI can block a merge, but not the opening of a PR, a push, or a change to a peer worktree. The local guard is the only check that refuses at the moment of the action. |
| Check `THREAT_MODEL.md`'s contents in the `threat-baseline` pass | T12 | wfctl would then own upstream's schema, and every upstream schema change would become a wfctl release. The pass checks only that the file is committed (`security-record-needs-baseline.md`). |
