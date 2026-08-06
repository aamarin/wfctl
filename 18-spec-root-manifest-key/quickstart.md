# Quickstart: putting your specs outside the repo

## Set it once

From anywhere in the project — including a worktree:

```bash
wfctl spec-root ~/Development/pfms-specs
```

It writes the main checkout's `.wf-skills-manifest.json` and prints the file it
wrote. The directory does not need to exist.

Check it:

```bash
$ wfctl spec-root
spec root: /Users/x/Development/pfms-specs
source:    /Users/x/Development/pfms/.wf-skills-manifest.json
```

## What changes

Every new spec directory is created under that root instead of `<repo>/specs/`:

```bash
$ wfctl feature-paths | grep FEATURE_DIR
FEATURE_DIR='/Users/x/Development/pfms-specs/18-spec-root-manifest-key'
```

New worktrees inherit it with no setup. Nothing to symlink, nothing to add to
`.workmux.yaml`'s `post_create`.

## Migrating a repo that already has specs

Recording a root does **not** move anything. Existing `<repo>/specs/*` directories
stop being found, so move them yourself:

```bash
mv specs/* ~/Development/pfms-specs/
```

`wfctl doctor` reports the case where both exist, so a half-finished migration is
visible rather than silent:

```
⚠ spec_root is set, but <repo>/specs/ still holds 3 spec directories —
  they will not be found. Move them to /Users/x/Development/pfms-specs or remove them.
```

## Path forms

| You type | Meaning |
|---|---|
| `~/Development/pfms-specs` | stored verbatim, expanded when read — portable across machines |
| `/srv/specs` | absolute, used as-is |
| `../pfms-specs` | relative to the directory of the manifest that declares it, never your shell's cwd |

## Precedence

1. `WFCTL_SPEC_DIR` — a one-off override for a single command, not configuration:
   ```bash
   WFCTL_SPEC_DIR=/tmp/scratch wfctl feature-paths
   ```
   Exporting it from a shell profile redirects **every** repo's specs. Don't.
2. `spec_root` in this repo's manifest.
3. `spec_root` in the main checkout's manifest — how worktrees inherit it.
4. `<repo>/specs` — the default when nothing is recorded.

## Turning it off

```bash
wfctl spec-root --unset
```

Resolution returns to `<repo>/specs`. Specs already written under the old root
stay there; move them back if you want them found.

## Notes

- The manifest is gitignored, so this is per-machine configuration, not something
  your collaborators inherit from a clone. Each machine records it once.
- A repo in a bare-clone or separate-gitdir layout has no main checkout to
  inherit from; record `spec_root` in the repo you run from, or use
  `WFCTL_SPEC_DIR` per invocation.
- A corrupt manifest fails loudly and names the file. It is never treated as "no
  setting recorded" — that would silently put specs back in the worktree.
