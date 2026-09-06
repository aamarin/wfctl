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

## Setup

There is no setup step. `uv run` resolves the environment from `uv.lock` on
first use:

```bash
uv run pytest -q          # 653 tests, ~45s
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
```

Without uv: `pip install -e ".[dev]"`.

Use `uv run` rather than a bare `pytest`. Not because a bare run fails today — it
does not — but because the dev deps are pinned on purpose, `ruff` to a minor. An
unpinned linter "turns someone else's release into a red build on an untouched
branch" (`pyproject.toml`). `uv run` is what applies the pin.

## Definition of done

All three commands above green. That is the whole bar for a code change, and CI
runs exactly these on 3.11 and 3.13.

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

The handle has to start with the issue number. `pre_create` rejects anything
else, because wfctl derives both the spec dir and the state dir from it.

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

## Releasing

**Bumping `version` in `pyproject.toml` on `main` ships a release.** CI tags the
commit and creates the GitHub release when the version key changes, gated behind
test, wheel and lint. Do not bump it as part of an unrelated change.

`doctor` and `uv tool install` both resolve releases by tag, so an untagged bump
would report a stale build as current — which is why the tag job exists (#55).

## Safety

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

## Conventions

Conventional-ish subjects (`fix(scope):`, `feat:`, `docs:`, `chore:`, `test:`),
written as a statement of what changed and why, not a label. Bodies explain the
reasoning that is not visible in the diff — why this shape, what was rejected.

Not every change needs the spec pipeline. `design-levels` excludes "bug fixes,
copy edits and other trivial changes that introduce no new state" — a change that
draws no new boundary does not need one drawn for it.
