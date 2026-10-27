# AGENTS.md

Context for an agent working on wfctl itself. Things that are expensive to learn
by reading the code — not a summary of `README.md`, and not a restatement of
`wfctl --help`.

## What this is

A CLI that tracks where a feature sits in a spec-driven pipeline
(brainstorm → specify → clarify → plan → tasks → analyze → decompose →
implement) and tells the agent what to run next. It also ships the skills and
slash commands that drive that pipeline, and installs them into a project.

Python 3.11+, `typer` + `rich`, no other runtime dependencies. Packaged with
setuptools; the skills tree is package data, not a separate download.

It ships three shell scripts as well, because the speckit skills run them. The
plan step runs `setup-plan.sh`, which creates `plan.md` from its template. The
tasks, clarify, analyze, implement, and checklist steps run
`check-prerequisites.sh`, which checks that the files the step needs are in the
feature's spec directory. Both source `common.sh`. The skills call them by the
fixed path `.specify/scripts/bash/`, so `install-skills` copies them into every
project beside the skills.

They come from Spec Kit, and most of what they did there is gone. They no
longer work out the spec directory themselves; they ask `wfctl feature-paths`.
The skills still call them by path because those skills are Spec Kit-derived,
and an in-place edit there is reverted by the next upstream pull
(`vendor-upstream-skills`).

## Setup

There is no setup step. `uv run` resolves the environment from `uv.lock` on
first use:

```bash
uv run pytest -q          # 1393 tests, ~2min
uv run ruff check wfctl/ tests/
uv run mypy               # wfctl/ and .github/scripts, from [tool.mypy]
```

Without uv: `pip install -e ".[dev]"`.

Use `uv run` rather than a bare `pytest`. Not because a bare run fails today — it
does not — but because the dev deps are pinned on purpose, `ruff` to a minor. An
unpinned linter "turns someone else's release into a red build on an untouched
branch" (`pyproject.toml`). `uv run` is what applies the pin.

## Definition of done

All three commands above green, and the branch committing its release note (see
Releasing). That is the whole bar for a code change. CI runs the three commands
on 3.11 and 3.13, and runs the release note check as its own `release-note` job.

Then `uv run wfctl doctor` — it reports drift between what wfctl installed in this
repo and what it now ships. Exit 1 means a finding that still stands.

`uv run`, and it is not optional. `doctor` compares the installed tree against
the bundle carried by the wfctl you invoked, and this repo has two of them: a
bare `wfctl` is whatever `uv tool install` put on PATH, `uv run wfctl` is the
working tree. Their bundles are never byte-identical, so they never both report
clean — **whichever one installed last is the one that reports green, and the
other reports drift.** Neither verdict is more true than the other; they are
answers to different questions.

So pick one and use it for `install-skills` and `doctor` both. `uv run` is that
one, because it is the only one that answers the question this repo cares about:
does the installed tree match the source I am editing. A worktree whose tree was
installed by the bare wheel will fail the step above until it is re-installed
with `uv run` once.

A change to anything under `wfctl/agents/` is not verified by the test suite
alone: run `uv run wfctl install-skills` and exercise the thing you changed. The
suite checks that skills ship and cross-reference correctly, not that they read
well.

A change to this repo's own `wfctl.json` — its `steps` key included — is
verified by `uv run wfctl check config`, not by `doctor`. `doctor`'s remit is
drift between what wfctl installed and what it now ships; a repository's own
configuration is neither, so a bad declaration there is invisible to it and
would otherwise ship silent.

`uv run` again, for the sharper half of the same reason. A bare `wfctl` installs
*its own* copy of the skill you just edited — the command succeeds, the tree
looks installed, and your change is nowhere in it. Only `.agents/` is overwritten,
never `wfctl/agents/`, so nothing you wrote is lost; what you lose is the ability
to exercise it, which is the entire point of the step.

## Session state

wfctl is the tool for this, so use it on itself. `/start-session` loads the
session context and runs the freshness check; `wfctl status` shows pipeline
position inferred from artifacts on disk; `wfctl resume` re-infers and writes the
next command. Session state lives in the XDG state dir — `wfctl state-dir` prints
it — not in the repo.

In a `claude`-layer worktree, your pane can be auto-restarted mid-session when
the context window fills (`wfctl hook session-restart`, a managed Stop hook —
default 200000 tokens, `WFCTL_RESTART_THRESHOLD=0` turns it off per-shell).
Nobody is at the prompt when it fires, so keep `session-summary.md`'s **Next
Session TODO** current — it may be the only thing the next session reads.

It will not fire while subagents you launched are still out: their results have
nowhere to land once the pane is cleared, so the restart waits for the last one
rather than handing off without them. A pane that has stopped restarting and
says so is usually that, and the line names the two commands that take it back.

`specs/` is gitignored, and this repo records a `spec_root` *outside* the working
tree. `<repo>/specs` is the default, not the truth: resolution is
`WFCTL_SPEC_DIR`, then this repo's manifest, then the main checkout's manifest,
then `<repo>/specs`. Ask `wfctl feature-paths` rather than assuming a path.

Specs reach durable storage on `specs-trunk`, an **orphan branch** — one directory
per feature branch, `specs(<issue>):` commits. Never purge it. Because it shares
no ancestor with `main`, every merge-based check reports its entire history as
unmerged, which is indistinguishable from an abandoned branch: `git cherry
origin/main origin/specs-trunk` counts all of it. `git merge-base origin/main
origin/<branch>` printing nothing is the tell that a branch is an orphan rather
than a stale one, and worth running before a branch sweep deletes anything.

## Worktrees

Create one with `workmux add <issue>-<slug> --base main`, never bare `git
worktree add`. The bare form skips `post_create`, which is what runs `wfctl
install-skills` — the skills tree is gitignored, so the worktree comes up with
none of it — and it registers no tmux session, which `workmux list` reports as
`MUX -`. Neither failure announces itself; the first sign is a session that has
no `/start-session` to run.

The handle has to start with the issue number, because wfctl derives both the
spec dir and the state dir from it. `wfctl start` is what enforces that, not
workmux: in a linked worktree it refuses a session when the branch names no
issue, when the issue is closed or missing, or when the worktree has no wfctl
install, and it prints the command that fixes each. workmux has no hook that
runs before creation, so the `pre_create` block this repo once carried never
ran (#497).

That is not the only way a worktree comes up short of skills, and the other way
is quieter. `post_create` passes `--agent` only when `WFCTL_AGENT` is set
(`no-hardcoded-agent` — a committed hook may not name one), so with it unset the
worktree gets `.agents/` and no `.claude/`, and the hook still exits 0. Set
`WFCTL_AGENT=claude` in your shell profile once; `wfctl doctor` says which layers
a worktree actually has, and is what `/start-session` runs.

## Architectural constraints

Not here. `wfctl arch context` prints the in-force set; the records live in
`docs/architecture/`.

`docs/architecture/views/current-state.md` draws the modules and the bands they
fall into. It describes rather than constrains, and says in its own opening
paragraph why it sits below the records rather than among them.

`docs/architecture/scans/` is a third thing again — one file per scan per issue,
carrying what that scan covered and what it found. Two kinds are written by a
review step, `<issue>-clarify.md` and `<issue>-analyze.md`; the third,
`<issue>-evaluation.md`, is written by a branch that ran no pipeline step at all
— a spike, an experiment, a tool evaluation whose result is the whole
deliverable. They share a shelf because they share a failure: what those steps
write lands in `FEATURE_DIR`, which resolves outside the working tree, and what
an evaluation learns is not written down anywhere, so a scan that found six
problems and one that never ran are the same pull request. The kinds differ in
who names the coverage rows — a wrapper for the first two, the evaluation itself
for the third, before it starts. The instruction lives in the command wrappers under
`wfctl/agents/commands/` rather than in `speckit-clarify/SKILL.md` or
`speckit-analyze/SKILL.md`, which are spec-kit-derived: an in-place edit there is
reverted by the next upstream pull with no conflict to notice. Ask
`wfctl arch-root` for the parent rather than writing `docs/architecture` in — a
repo can declare it elsewhere.

A scan file is not a record, and neither is an implementation note; three readers
of the arch root have to agree about that. `wfctl arch context` does so for free
— `load_records` globs one level, which is what already keeps `design/`,
`declarations/` and `views/` out of the projection. The other two ask git about
the whole root, and a git pathspec naming a directory is recursive, so both are
handed the exclusions by name: `records_on_this_branch`, which prints `record:`
lines saying what an unattended run decided, and `_observe`, whose `boundary`
says whether the boundary question was answered. A fourth reader added later has
to make the same exclusion, and `_paths.non_record_subtrees` is where it finds
out — a list rather than a constant per directory, because `scans/` was named at
each call site and `implementation/` then had to find all of them (#370).
`declarations/` and `step-claims/` are on the list too. wfctl 0.23.0 and older
wrote `arch none`'s and `step none`'s answers there, and a file left behind
shouldn't answer the design gate (#635).

## Testing conventions

Tests assert on console output, so anything touching output pins `NO_COLOR` —
rich colorizes based on the terminal otherwise and assertions become
machine-dependent. `conftest.py` explains the presence-only semantics.

Test names are sentences and docstrings say *why the test exists*, usually
naming the failure it caught. A test that only restates its assertion in prose
is not carrying its weight.

Register a marker in `pyproject.toml` rather than reaching around a fixture; see
`real_version_check` for the pattern.

## Code style

The ruff rule set is deliberately narrow — `E4`, `E7`, `E9`, `F`. `I`, `UP`,
`PL` and `RUF` are each defensible and each their own reviewable diff (#14). Do
not enable them as a drive-by.

mypy runs with `disallow_untyped_defs` but **not** `strict`. What strict adds
here is two shapes: `type-arg`, on annotations that say `dict` where they mean
`dict[str, str]`, and `no-any-return`, where a function declares a return type
and hands back whatever `json.loads` produced. Neither is tracked as an issue,
and no number is written down here on purpose — `uv run mypy --strict wfctl/`
is the count, and it drifts with every file added. Annotate new functions.

Comments inform the next reader of the file; they do not narrate the change to a
reviewer. If a comment only makes sense beside the diff, it belongs in the commit
message. Existing comments are dense with rationale — match that, and explain
*why this shape*, not what the line does.

## Declaring what a change must carry

`wfctl.json` holds a `change_check` list beside `verify` — field names
`wfctl change check <pr>` requires on every open change, whatever its issue
happens to carry:

```json
{ "verify": [ … ], "change_check": ["assignees"] }
```

Leave the key out to inherit from the issue alone, which is the right answer in a
repo whose triage you do not control. The names are the *backend's* spelling, as
its `fields` verb emits them — `assignees`, not `assignee` — and a name the
backend never reports is a finding rather than silence, so a typo shows up on the
first run instead of never.

It lives in `wfctl.json` and not the tracker config because `.agents/` is
gitignored and rewritten by `install-skills`: a policy written there works for one
session and then vanishes with no error.

`change_sections` sits beside `change_check` and lists the headings every PR
body has to answer. `wfctl check-body` reports a listed section that is missing,
empty, N/A or None, or only a yes or no with no reason:

```json
{ "change_check": ["assignees"], "change_sections": ["Needs a spec?"] }
```

wfctl names no section itself, so a repo that leaves the key out sees no change.
It lives in `wfctl.json` for the same reason `change_check` does. `wfctl check
config` validates it, including that every PR template in the repo carries each
listed heading, since a template without one produces a PR that can never pass.

**An in-place change to a tracker config travels by `--tracker <name>`.** A bare
`install-skills` fills a missing tracker file and never refreshes a present one,
deliberately — it cannot tell a stale copy from one the project edited, and the
copy loop takes no backup for a path already on record. So a verb added upstream
sits unreachable until `wfctl install-skills --tracker github` is run, and
`tracker-check` printing a short verb list is the tell.

## Declaring a stage of your own

`wfctl.json` holds a `steps` key beside `verify` and `change_check` — a
repository's own passes, keyed by the built-in step they belong to:

```json
{
  "steps": {
    "brainstorm": [
      { "name": "ui-design",
        "command": "/pfms-ui-design-workflow",
        "evidence": "ui-design-contract.md" }
    ]
  }
}
```

It lives here for the same reason `change_check` does: `.agents/` is
gitignored and rewritten by `install-skills`, so a policy written there works
for one session and vanishes with no error. `evidence` is sugar — it builds a
reader that reports the pass done once that path exists under the feature
directory — and it is the whole of what this file can express; a pass whose
output is not a file at a fixed path needs a different mechanism, not a grep
taught to `wfctl.json`.

Every rule a declaration must satisfy is a `wfctl check config` finding
instead of a silent drop — an unknown step name, a pass with both `command`
and `manual`, an uninstalled command, an unsatisfiable `before`/`after` order.
Run it after editing `wfctl.json`, the same way `tracker-check` earns its own
run after a tracker config. `doctor` says nothing about a declared pass: its
remit is state wfctl installed that has since drifted, and a repository's own
configuration is neither.

A pass declared inapplicable to one change is `wfctl step none <step>.<name>
--reason "…"`. It writes one file per pass to `exceptions/` in the branch's
spec folder, beside the file `wfctl arch none` writes there. It's a second verb
rather than an option on `arch none`, because a branch makes as many pass
exceptions as it has passes and only one boundary answer. The spec folder isn't
part of the PR, so the reviewer reads each reason in the PR body, and `wfctl
check-body` reports any reason the body is missing.

## Declaring reviewers

`wfctl.json` holds a `review` key beside `steps` and `change_check`. It sets
which models review each change and which custom review groups the repository
adds:

```json
{
  "review": {
    "commands": { "codex": "codex exec --sandbox read-only" },
    "groups": [
      { "group": "security",
        "reviewers": [ { "name": "claude", "count": 2 }, { "name": "codex", "count": 2 } ] },
      { "group": "money-rules", "skill": "money-rules-review",
        "reviewers": [ { "name": "claude", "count": 2 } ] }
    ]
  }
}
```

`commands` maps each model other than Claude to the command that starts it.
Claude runs inside the current agent, so it needs none. `groups` lists the
review groups, and each group names its reviewers as a model and a count. wfctl
expects exactly that many reports and keeps the run incomplete until they
arrive. A group's counts must add up to 20 or fewer.

By default, `security` and `code` each have three Claude reviewers, so a
repository that leaves the key out still gets both groups. A custom group has
no default and must list its own reviewers. A built-in group gets the default
only when its `reviewers` key is missing, so listing `security` to change its
skill keeps its reviewers. An empty `reviewers` list is a finding, not a way to
skip a group.

`security` and `code` always run first, in that order, whether or not the list
names them. The code group reviews the security group's fixes. Every other
group follows in list order and reviews the result of both. By default, the
`security` group runs the `reviewing-security` skill and every other group
runs `code-review`. Any group can name its own skill with `skill`.

A reviewer's ID is its group's first letter and its position in the group's
list. The file above gives `s1` to `s4`, with `s3` and `s4` on Codex,
then `c1` to `c3`, then `m1` and `m2`. That's why no two groups may share a
first letter.

`wfctl check config` reports every problem in the key, such as a model with no
command or a count below 1. `wfctl review start` refuses to start a run until
you fix them. `check config` doesn't check whether a command is installed,
since that depends on the machine running the review, not the repository.
Instead, `review start` looks the command up on `PATH`. If it's missing,
`review start` leaves that model's reviewers out of the run and prints a `⚠`
line naming them.

The `review` key lives in `wfctl.json` for the same reason `steps` does.
`.agents/` is gitignored and rewritten by `install-skills`, so a reviewer list
written there works for one session and then vanishes with no error.

## Releasing

**Every change commits a release note, and a release is cut from those notes.**
The note is a file under `changes/` named for the issue and a category, such as
`changes/571.change.md`. `wfctl verify` and the `release-note` CI job both fail a
branch that adds none for its own issue. Create one with:

```bash
uv run towncrier create 571.change.md --content "What a user of wfctl will notice."
```

Pick the category by what an existing user notices once the change ships.
`change` is for something they rely on that behaves differently, `addition` for
something new, `fix` for something broken that now works, and `none` for a change
they would not notice. A branch with no issue in its name uses
`changes/+<what-changed>.<category>.md`. The categories are the
`[[tool.towncrier.type]]` tables in `pyproject.toml`, and that table is the one
list the check and the release script both read.

**Bumping `version` in `pyproject.toml` on `main` ships a release,** and only a
release pull request does it. From an up-to-date `main`, run:

```bash
uv run python .github/scripts/release.py
```

The script proposes a version from the notes, lists any merged pull request that
came with no note, and opens the draft in your editor. It then commits the
version bump, the relocked `uv.lock`, and the removal of the notes as one commit
on `release/v<version>`, pushes that branch, and opens a pull request. It never
pushes `main` and never merges.

Merge that pull request as a merge commit once its checks pass. CI tags the
merge and publishes the release commit's body as the GitHub release. To change
the release text after the pull request is open, amend the commit on
`release/v<version>` with `git commit --amend --cleanup=verbatim` and force-push
that branch. Without `--cleanup=verbatim`, git's default cleanup deletes every
line starting with `#`, which removes each heading from the release text.
Editing the pull request's
description changes nothing, because the tag job reads the commit.

`doctor` and `uv tool install` both resolve releases by tag, so an untagged bump
would report a stale build as current, which is why the tag job exists (#55). It
checks the release commit's subject, version, and body before it tags anything,
so a failure leaves neither a tag nor a release.

**`main` is protected by a ruleset committed as `.github/rulesets/main.json`.**
It has no bypass, so a push straight to `main` is refused for everyone, and it
requires `test (3.11)`, `test (3.13)`, `wheel`, `lint`, and `release-note` to pass
and merge commits to be the only merge method. The release script finds merged
pull requests that came with no note through their merge commits, so a squash or
rebase merge would hide them. The ruleset is applied by hand, not by CI. Apply it
once, then read it back, because nothing checks that what GitHub holds still
matches the file:

```bash
gh api -X POST repos/{owner}/{repo}/rulesets --input .github/rulesets/main.json
gh api -X PATCH repos/{owner}/{repo} -F allow_squash_merge=false -F allow_rebase_merge=false
gh api repos/{owner}/{repo}/rules/branches/main
gh api repos/{owner}/{repo}/rulesets --jq '.[] | select(.name == "main") | .id'
gh api repos/{owner}/{repo}/rulesets/<id> --jq '.bypass_actors'
gh api repos/{owner}/{repo} --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'
```

The first two apply it. The last four read it back: the rules in force with their
five checks, an empty bypass list, and merge commits as the only method. A later
edit to the file is applied with `-X PUT repos/{owner}/{repo}/rulesets/<id>`.
Renaming a CI job that the ruleset requires means editing the file and applying it
again, since a required check that never reports blocks every merge.

## Safety

**wfctl gates one outward action, opening or merging a PR, and your agent's
permission layer gates the rest.** `wfctl issue comment`, `create`, `label` and
`close` run when you run them, and a refusal you meet comes from the host — Claude Code's auto-mode classifier or its
equivalent — before wfctl's process starts. Do not route around one with `gh` or
another client: that is the one gate there is. Report it instead, with
`wfctl report-block <action> --reason "…"`, which holds the step until the action
is taken (`wfctl-records-outward-actions-and-never-gates-them`, #384 removed the
grant that used to stand in front of these).

**The review and record checks are the refusals wfctl makes.** The worktree
guard is a hook wfctl installs. While a review group has commits it hasn't
reviewed, the guard refuses `gh pr create` and `gh pr merge` and lists those
commits under each group. That refusal comes from wfctl, not the host, so don't
report it with `wfctl report-block`. Instead, run the review groups it names, as
`opening-a-change` Step 1 says, and open the PR again.

Once the reviews are done, the guard checks the level-2 records the branch
changes. It refuses when the branch's own spec folder still says no boundary
moved, and prints the `rm` that deletes that answer, since the record replaces
it. It also refuses while any of those records is still `proposed`. That one
waits on a person: ask them to accept or reject the record, and don't run `wfctl
arch accept` yourself. `opening-a-change` says what to do for each.

If the check refuses with an error instead, it couldn't reach an answer, for
example because a `gh` call timed out. Stop and tell the person. Running the
same command in their own terminal, where the hook doesn't run, is their call.
So is `wfctl review sign-off`, which the guard refuses when an agent runs it.

What wfctl keeps is the record. `wfctl issue` logs each write that succeeded as
`issue-<verb>`, and `wfctl report-action push` logs a push, which is the only
trace of one a restarted session can read.

`close` is the irreversible row, and it stays the human's: an agent closes an
issue when a person has said to, never on its own reading of the work.

`install-skills` writes into a project and can overwrite hand-authored files; it
lists them and asks first. `--yes` skips that prompt — originally for CI, and now
also for `/start-session`, which refreshes a stale mirror unattended. What it
skips is the listing, not the backup: the overwritten originals are copied under
`.wf-skills-backup/` and the run prints where, so the prompt is a chance to stop
rather than the only thing standing between a hand-authored file and loss. Hooks seeded
into a repo execute shell commands on worktree create and remove — read them
before running an unfamiliar one.

`.wf-skills-manifest.json` is gitignored by convention, and a repo can commit one
anyway. Since #146 it names the *source* a layer was installed from, and `doctor`
turns that into `update: wfctl install-skills --from <path>` — a line
`/start-session` runs with `--yes` before reporting anything. In an unfamiliar
repo, read a committed manifest before the first `doctor`, for the same reason as
the hooks: what it can install is agent instructions and `.specify/scripts/`,
which speckit commands execute.

The same applies to `review.commands` in a committed `wfctl.json`. `wfctl
review start` prints each command beside its reviewers, and the review skill
runs it. In an unfamiliar repo, read the key before running a review there.

## Conventions

Conventional-ish subjects (`fix(scope):`, `feat:`, `docs:`, `chore:`, `test:`),
written as a statement of what changed and why, not a label. Bodies explain the
reasoning that is not visible in the diff — why this shape, what was rejected.

Not every change needs the spec pipeline. A change that draws no new boundary
and adds no new state, such as most bug fixes and copy edits, skips it. Every
change runs the design passes, either through the pipeline or through
`.agents/skills/design-passes`.

Every change commits a release note under `changes/`, whatever its size. See
Releasing for the file name and the categories.
