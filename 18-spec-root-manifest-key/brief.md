# Active feature: spec-root-manifest-key (#18)

**Branch**: `18-spec-root-manifest-key` · **Step**: plan complete → `/speckit.tasks`
**Spec**: `specs/18-spec-root-manifest-key/spec.md` · **Plan**: `.../plan.md`

## What

Let a repository record where its specs live, so they can sit outside the repo
and survive worktree teardown. Today `resolve_spec_dir` honors `WFCTL_SPEC_DIR`
but `feature_paths_cmd` hardcodes `repo_root / "specs" / branch` when nothing
exists yet — reads are redirectable, creates are not, and every speckit script
routes through that one line.

## How

- `spec_root(repo_root) -> Path` in `wfctl/_paths.py`: `WFCTL_SPEC_DIR` →
  `spec_root` in this repo's `.wf-skills-manifest.json` → the main checkout's →
  `repo_root / "specs"`. Both `resolve_spec_dir` and `feature_paths_cmd`
  (`cli.py:352`) consume it; they must never resolve a root independently again.
- Main-checkout fallback guarded on the git common dir being named exactly
  `.git`. The manifest is gitignored and regenerated per worktree, so without
  this the setting is unreachable when it matters; without the guard, a bare
  layout could read an unrelated project's manifest.
- `_NON_LAYER_KEYS = frozenset({"tracker", "spec_root"})` — required, or
  `install-skills` raises `AttributeError` at `cli.py:728`.
- `wfctl spec-root [PATH] [--unset]`, writing the main checkout and printing
  where. `doctor` reports a recorded root co-existing with in-repo specs.

## Constraints

- `cli.py` imports `_paths` at module level, so `_paths` reaches for
  `_load_manifest` via a lazy in-function import (`_tracker.py:129` pattern).
- `feature-paths` stdout is `eval`'d — never add a line to it.
- Path stored verbatim (`~` expanded at read); relative anchors to its declaring
  manifest's directory. Never created, never existence-checked — that check is
  what broke the create path.
- Unparseable manifest raises; it is never treated as "not recorded".
- A repo recording nothing must resolve byte-identical paths.

## Files

`wfctl/_paths.py`, `wfctl/cli.py`, `tests/test_paths.py`,
`tests/test_install_skills.py`, `README.md`.
