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

## Verification

```bash
uv run pytest -q          # 521 tests, ~27s
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
```

Use `uv run`, not a bare `pytest`. Not because a bare run fails today — it does
not — but because the dev deps are pinned on purpose, `ruff` to a minor. An
unpinned linter "turns someone else's release into a red build on an untouched
branch" (`pyproject.toml`). `uv run` is what applies the pin.

`testpaths = ["tests"]` exists so collection does not walk `wt/` and hit
`ImportPathMismatchError` once worktrees exist. Leave it set.

## The layer model

This is the thing most often got wrong.

| Path | Owner | Committed |
|---|---|---|
| `wfctl/agents/`, `wfctl/specify/` | **source** — package data, edit here | yes |
| `.agents/` | base layer, installed output | no |
| `.claude/`, `.bob/`, `.github/skills/` | one agent's native layer, additive | no |
| `.specify/` | speckit runtime, installed output | no |

The dotted directories at the repo root are this repo's own *install output*.
Editing them changes nothing that ships — edit `wfctl/agents/` and re-run
`wfctl install-skills` to try it. The vendored copies carry no leading dot
precisely because `.gitignore` ignores `.agents/` and `.specify/` unanchored,
so a dotted source tree would be silently untracked.

Only skills whose frontmatter carries `deployment: skill` are mirrored into
`.claude/skills/`. Everything else reaches Claude as a slash command only. A
skill that is an always-on output style is deliberately *not* auto-invocable.

## Rules that are not obvious

**Do not edit `i-have-adhd`.** It is vendored — the one skill with `license:` in
its frontmatter — and an upstream pull overwrites it. Layer a new skill over it
instead, the way `conversation-response-shape` does.

**Never hardcode an agent in committed config.** `.workmux.yaml` is committed,
and the agent is per-developer with no correct value to infer, which is why
`patch_seed` leaves `agent:` commented rather than guessing
(`_workmux.py:88-97`). Use `${WFCTL_AGENT:+--agent "$WFCTL_AGENT"}`.

**Specs may live outside the repo.** `<repo>/specs` is the default, not the
truth. Resolution order is `WFCTL_SPEC_DIR`, then this repo's manifest, then the
main checkout's manifest, then `<repo>/specs`. Ask `wfctl feature-paths` rather
than assuming a path. This repo records a `spec_root` outside the working tree.

**Install artifacts are gitignored, so a fresh worktree has none of them.**
`.workmux.yaml`'s `post_create` reinstalls them; its `pre_remove` archives specs
before teardown, because they would otherwise be destroyed with the worktree.

**`install-skills` is a managed mirror; `install-config` is seed-once.** The
first is tracked in `.wf-skills-manifest.json` with a content hash and can be
uninstalled. The second hands the file to the repo and never touches it again —
which means a fix to a seeded template reaches only repos seeded afterwards.

## Conventions

Conventional-ish subjects (`fix(scope):`, `feat:`, `docs:`, `chore:`, `test:`),
written as a statement of what changed and why, not a label. Bodies explain the
reasoning that is not visible in the diff — why this shape, what was rejected.

Comments inform the next reader of the file; they do not narrate the change to a
reviewer. If a comment only makes sense next to the diff, it belongs in the
commit message.

One PR closes one issue. `.github/pull_request_template.md` is the shape.

Not every change needs the spec pipeline. `design-levels` excludes "bug fixes,
copy edits and other trivial changes that introduce no new state" — a change
that draws no new boundary does not need one drawn for it.

## Checking your own work

`wfctl doctor` reports drift between what wfctl installed here and what it now
ships. Exit 1 means a finding that still stands. A check belongs there only if
it describes something wfctl installed or seeded and can name the command that
repairs it — see `doctor_cmd`'s docstring before adding one.
