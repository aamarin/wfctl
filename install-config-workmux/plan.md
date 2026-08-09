# Implementation Plan: `wfctl install-config`

**Spec:** `specs/install-config-workmux/spec.md`
**Branch:** install-config-workmux
**Date:** 2026-07-21

> **Scope note.** No `.specify/` scaffolding exists here; this repo's speckit
> convention is a single `spec.md` (+ this `plan.md`) per feature. The feature is
> one CLI subcommand + one shipped config file + tests, with no external
> dependencies or interfaces to research — so the multi-artifact plan template
> (research/data-model/contracts/quickstart) is omitted deliberately. This file
> is the whole plan.

## Two-repo change

Same shape as the `tracker-check` pair:

1. **wf-skills** — add the canonical source config the command copies from.
2. **wfctl** — add the `install-config` command + tests.

## Part 1 — wf-skills: `.agents/configs/workmux/.workmux.yaml`

New file. The repo-agnostic skeleton (per spec "The shipped config" section):

```yaml
# workmux project configuration — wfctl standard starter.
# Repo-agnostic conventions; fill in project-specific hooks where noted.
# Global settings live in ~/.config/workmux/config.yaml.

#-------------------------------------------------------------------------------
# Naming & Paths
#-------------------------------------------------------------------------------
worktree_dir: wt          # worktrees land in ./wt/<handle> (gitignored by installer)
worktree_naming: full

# Per-project tmux session/window name prefix (workmux default: "wm-").
# window_prefix: "<project>__"

#-------------------------------------------------------------------------------
# Tmux
#-------------------------------------------------------------------------------
mode: session

windows:
  - name: agent
    panes:
      - command: <agent>
        focus: true
  - name: term
    panes:
      - command: ''

#-------------------------------------------------------------------------------
# Agent
#-------------------------------------------------------------------------------
agent: claude

#-------------------------------------------------------------------------------
# Hooks
#-------------------------------------------------------------------------------
# Require branch/handle to start with an issue number (e.g. 359-my-feature),
# matching wfctl's issue-number branch model. Aborts creation otherwise.
pre_create:
  - |
    ISSUE=$(echo "$WM_HANDLE" | grep -oE '^[0-9]+')
    if [[ -z "$ISSUE" ]]; then
      echo "Error: '$WM_HANDLE' must start with an issue number (e.g. 359-my-feature)."
      exit 1
    fi

# Project-specific setup (ports, .env rewrites, db URLs) goes here.
# Example — derive a port from the issue number and patch a .env:
# post_create:
#   - |
#     ISSUE=$(echo "$WM_HANDLE" | grep -oE '^[0-9]+')
#     sed -i '' "s|^PORT=.*|PORT=${ISSUE}|" "$WM_WORKTREE_PATH/.env"
#     exit 0

pre_remove: []

#-------------------------------------------------------------------------------
# Files
#-------------------------------------------------------------------------------
# Files to copy into each new worktree (e.g. a gitignored .env):
# files:
#   copy:
#     - .env
```

## Part 2 — wfctl: the `install-config` command

New command in `wfctl/cli.py`, placed near `install-skills`.

**Known configs** — a small map keeps `<name>` validation and the "available
names" error in one place:

```python
_CONFIG_SOURCES = {"workmux": ".agents/configs/workmux"}  # name -> src dir in wf-skills
```

**Signature:**

```python
@app.command("install-config")
def install_config_cmd(
    name: str = typer.Argument(..., help=f"Config to seed: {', '.join(_CONFIG_SOURCES)}"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    repo: str = typer.Option("https://github.com/aamarin/wf-skills", "--repo", help="wf-skills repo URL"),
    ref: str = typer.Option("main", "--ref", help="Branch or tag to install from"),
) -> None:
```

**Flow:**

1. `name` not in `_CONFIG_SOURCES` → red error listing available names, exit 1.
2. `get_repo_root()` (red error + exit 1 if not a git repo — mirror
   `install_skills_cmd`).
3. `git clone --depth=1 --branch <ref> <repo>` to a `TemporaryDirectory` (reuse
   the exact clone+error pattern from `install_skills_cmd`). Source dir =
   `tmp/<src_rel>`; error if it's absent in the clone.
4. **Clobber check:** for each file under the source dir, compute its dest at
   `repo_root/<relpath>`. Collect dests that already exist. If any and not
   `--force` → red error listing them + "pass --force to overwrite", exit 1.
   Nothing written.
5. **Copy** each source file to its dest (mkdir parents).
6. **workmux post-step** — ensure `wt/` gitignored: if `.gitignore` lacks a `wt/`
   line, append one (create the file if absent). Idempotent. (Guard on
   `name == "workmux"` so it stays config-specific, not a generic hook.)
7. Success: `✓ Seeded <name> config (N file(s)) from <repo>@<ref>`.

**No** manifest write, backup dir, uninstall, or `doctor` wiring — seed-once.

### Optional cleanup (only if trivial)

`install_skills_cmd` already contains the clone+error block. If lifting it into a
small `_clone_wf_skills(repo, ref, tmp) -> bool` helper is a clean 1:1 extraction,
do it and call from both. If it risks disturbing the tested install-skills path,
**duplicate the ~8 lines** in `install-config` instead and move on.
`# ponytail: dup'd clone; extract a helper if a 3rd caller appears`

## Part 3 — Tests

New file `tests/test_install_config.py` (install-skills tests live in
`test_tracker.py`, but this is a distinct command — its own file is cleaner).
Reuse the `_make_wf_skills_repo_*` pattern: build a throwaway git repo containing
`.agents/configs/workmux/.workmux.yaml`, then invoke with
`--repo file://<src> --ref master`.

Cases (from spec Testing):

1. Clean repo → `.workmux.yaml` written; content byte-matches the source.
2. `.gitignore` idempotency: (a) absent → created with `wt/`; (b) present without
   `wt/` → appended; (c) already has `wt/` → unchanged, no duplicate line.
3. Existing `.workmux.yaml`, no `--force` → exit != 0, file unchanged, output
   names the path.
4. `--force` → overwrites existing `.workmux.yaml`.
5. Unknown name (`install-config nope`) → exit != 0, output lists `workmux`.
6. Not a git repo → exit != 0.

## Verification

- `uv run pytest tests/test_install_config.py -q` green.
- `uv run pytest -q` (full suite) green.
- Manual smoke in a temp git repo: `wfctl install-config workmux --repo
  file:///Users/andremarin/Development/wf-skills --ref main` → `.workmux.yaml`
  present, `wt/` in `.gitignore`; re-run → refuses; `--force` → overwrites.

## Landing order

1. Commit `.agents/configs/workmux/.workmux.yaml` in wf-skills.
2. Implement command + tests in wfctl; run suites.
3. (Merge wfctl branch when approved; reinstall not required — this command
   doesn't touch installed skills.)
