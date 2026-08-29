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
uv run pytest -q          # 521 tests, ~27s
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

Then `wfctl doctor` — it reports drift between what wfctl installed in this repo
and what it now ships. Exit 1 means a finding that still stands.

A change to anything under `wfctl/agents/` is not verified by the test suite
alone: run `wfctl install-skills` and exercise the thing you changed. The suite
checks that skills ship and cross-reference correctly, not that they read well.

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

## Architectural constraints

Not here. `wfctl arch context` prints the in-force set; the records live in
`docs/architecture/`.

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

mypy runs with `disallow_untyped_defs` but **not** `strict`; the 26 findings
strict adds are one shape and tracked separately. Annotate new functions.

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
lists them and asks first. `--yes` skips that prompt and is for CI. Hooks seeded
into a repo execute shell commands on worktree create and remove — read them
before running an unfamiliar one.

## Conventions

Conventional-ish subjects (`fix(scope):`, `feat:`, `docs:`, `chore:`, `test:`),
written as a statement of what changed and why, not a label. Bodies explain the
reasoning that is not visible in the diff — why this shape, what was rejected.

Not every change needs the spec pipeline. `design-levels` excludes "bug fixes,
copy edits and other trivial changes that introduce no new state" — a change that
draws no new boundary does not need one drawn for it.
