# spec_root: let a repo put its specs outside the repo

**Issue**: aamarin/wfctl#18
**Branch**: 18-spec-root-manifest-key
**Date**: 2026-08-05

## Problem

`wfctl feature-paths` is the single source of truth for branch → spec dir; every
speckit script routes through it (`.specify/scripts/bash/common.sh:45`). When no
spec dir exists yet it hardcodes the destination:

```python
# cli.py:352
feature_dir = spec_dir if spec_dir is not None else repo_root / "specs" / branch
```

`resolve_spec_dir` honors `WFCTL_SPEC_DIR`, so an *already existing* spec dir
outside the repo resolves fine. The create path never consults it. **Reads are
redirectable; creates are not.**

Consequence for pfms (`MarinVentures/pfms#499`): specs must live outside the
worktree so they survive worktree teardown, so every worktree needs a hand-made
symlink back, created before the pipeline runs, with a `../../../../` depth
recomputed per nesting level. Nothing automates it, so it gets forgotten, and a
real directory appears instead.

## Design

### 1. One resolver, two call sites

New function in `_paths.py`, the single place the spec root is decided:

```python
def spec_root(repo_root: Path) -> Path:
    """WFCTL_SPEC_DIR → manifest spec_root (this repo, then the main checkout) → repo_root/specs."""
```

Resolution order:

1. `WFCTL_SPEC_DIR` env var — unchanged, still wins. A per-invocation escape
   hatch (`WFCTL_SPEC_DIR=/tmp/x wfctl feature-paths`), never the persistent
   config: the only way to persist an env var is a shell profile, which sets it
   for *every* repo wfctl touches.
2. `spec_root` in `.wf-skills-manifest.json` — this repo root's manifest, then
   the main checkout's (see §2).
3. `repo_root / "specs"` — today's behavior, for every repo that sets nothing.

Both call sites use it:

- `resolve_spec_dir` (`_paths.py:166-167`) — replaces its inline root. The
  exact-match-then-key-glob logic and the ancestor-branch walk are unchanged;
  only the root moves.
- `feature_paths_cmd` (`cli.py:352`) — the fallback becomes
  `spec_root(repo_root) / branch`.

Fixing only one leaves the other hardcoded, which is the current state and the
reason the symlinks exist.

**Path form**: stored verbatim, expanded at read time. Absolute and `~` paths are
used as given. A relative path anchors to the directory of the manifest that
declared it — not cwd — so a relative root declared in the main checkout resolves
to one shared location for every worktree.

### 2. Main-checkout fallback

`.wf-skills-manifest.json` is gitignored (`.gitignore:15`) and untracked, and
`.workmux.yaml:72` runs `wfctl install-skills` in every fresh worktree — which
writes a brand-new manifest carrying `base`/`claude`/`tracker` and nothing else.
A worktree-local `spec_root` therefore cannot exist at pipeline time. Without a
shared read location, specs land back in `<worktree>/specs/` and die with the
worktree: the same failure this issue fixes, differently spelled.

So the lookup checks a second location:

```
1. <repo_root>/.wf-skills-manifest.json
2. git rev-parse --git-common-dir
   → if the common dir is named exactly ".git", its parent is the main checkout
   → <main-checkout>/.wf-skills-manifest.json
3. neither declares spec_root → repo_root/specs
```

The `.git` name check is the guard: in a bare or separate-gitdir layout the
common dir is `<something>.git` and its parent is a container directory that may
hold an unrelated project's manifest. Reading that would silently apply another
repo's spec root. When the name doesn't match, there is no fallback and behavior
is exactly today's.

This is a lookup for a *setting*. No branch, no git operation, no relation to
`resolve_spec_dir`'s ancestor-branch walk or to pfms#499's `specs-trunk` branch.

### 3. `spec_root` must be a non-layer key

```python
# cli.py:527
_NON_LAYER_KEYS = frozenset({"tracker", "spec_root"})
```

Required, not cosmetic. `_layer_keys` (`cli.py:530`) returns every key not in
this set, and `cli.py:728` does `manifest[key].get("items", [])`. With
`spec_root` a bare string, the next `install-skills` raises
`AttributeError: 'str' object has no attribute 'get'`. `doctor` (`cli.py:1361`)
iterates the same helper.

With the key registered, the setting survives upgrades: `install_skills_cmd`
loads the existing manifest (`cli.py:717`), rewrites only layer entries
(`cli.py:894`), and saves (`cli.py:927`) — unknown keys pass through untouched,
as `tracker` already does. `uninstall` deletes only its own agent key
(`cli.py:1023`), so `spec_root` survives that too.

### 4. `wfctl spec-root` command

```bash
wfctl spec-root                          # show effective root and its source
wfctl spec-root ~/Development/pfms-specs # set it
wfctl spec-root --unset                  # remove the key
```

No existence check, no `mkdir`: the directory not existing yet is the entire bug,
and `setup-plan.sh` already `mkdir -p`s the feature dir.

**Writes to the main checkout**, printing the path it wrote. `spec_root` is a
repo-wide setting, and a write to a worktree's gitignored manifest evaporates
with the worktree — a silently ephemeral setting is the failure mode this issue
is about. Falls back to the current repo root when no main checkout is
detectable, using the same `.git`-name guard as the read path.

## Key assumptions

1. **The main checkout is the durable location.** True for the
   `<project>/.git` + `<project>/wt/<branch>` layout wfctl and pfms both use.
   Bare-clone and separate-gitdir layouts get no fallback by design — silently
   reading a sibling project's manifest is worse than doing nothing.
2. **`install-skills` passes unknown manifest keys through.** Verified by reading
   `cli.py:717/894/927`; `tracker` is the existing precedent. A test pins it.
3. **One spec root per repo is enough.** No per-branch or per-epic override.
   `WFCTL_SPEC_DIR` covers the one-off case.
4. **Nobody wants the root auto-created.** `setup-plan.sh` already `mkdir -p`s
   the feature dir, and validating a path that legitimately doesn't exist yet is
   what broke the create path in the first place.

## Files touched

| File | Change |
|------|--------|
| `wfctl/_paths.py` | new `spec_root()`; `resolve_spec_dir` uses it |
| `wfctl/cli.py` | `feature_paths_cmd` fallback; `_NON_LAYER_KEYS`; `spec-root` command |
| `README.md` | document the key and the command |

`_paths.py` importing `_load_manifest` from `cli.py` follows the existing lazy
in-function import pattern (`_tracker.py:129`), which avoids the import cycle.

No change to `.specify/scripts/bash/*` — they already delegate correctly.

## Acceptance criteria

- [ ] A repo with `spec_root` set writes new spec dirs to that root, not `repo_root/specs`
- [ ] `wfctl feature-paths` reports the configured root for a branch with no spec dir yet
- [ ] A worktree whose own manifest lacks `spec_root` inherits the main checkout's
- [ ] A bare / separate-gitdir layout does not read a manifest outside the repo
- [ ] A repo without `spec_root` behaves exactly as today
- [ ] `WFCTL_SPEC_DIR` still wins, and is not made process-global for writes
- [ ] `install-skills` and `doctor` run clean over a manifest carrying `spec_root`
- [ ] `wfctl spec-root <path>` in a worktree writes the main checkout's manifest
- [ ] pfms can drop its per-worktree symlink step entirely

## Tests

- `feature-paths` honors `spec_root` for a branch whose spec dir does **not**
  exist — the case `WFCTL_SPEC_DIR` currently fails, and the core regression
- worktree with no local `spec_root` resolves the main checkout's value
- common dir not named `.git` → no fallback read, `repo_root/specs`
- `~` and relative values expand as specified (relative anchors to its manifest's dir)
- `install-skills` over a manifest containing `spec_root` does not raise and
  preserves the key
- `WFCTL_SPEC_DIR` overrides a set `spec_root`
- no `spec_root` anywhere → unchanged paths

Manual: set `spec_root` in a pfms checkout, run `/speckit.specify` in a fresh
worktree, confirm the spec lands in `~/Development/pfms-specs/` with no symlink.

## Out of scope

- Migrating pfms's existing specs (`MarinVentures/pfms#499`)
- Any change to the speckit bash scripts
- Creating or validating the spec root directory
