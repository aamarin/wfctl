# Reachable spec roots, and an archive that knows what it is for

Closes #26, #27.

## Problem Statement

How might we make `spec_root` reachable by the repos that need it, and stop
`archive-story` from copying files that were never at risk?

The two are one problem seen from either end. `wfctl spec-root` shipped in PR #25
and nothing points a new project at it, so repos take the default
`<repo>/specs/<branch>` and discover it was wrong when `workmux remove` deletes a
spec — the exact failure the setting exists to prevent. Meanwhile the repos that
*do* set it get a lossy, flattened second copy of files teardown could never
reach, drifting from the originals from the moment either changes.

## The decision that unblocks both

`archive-story` is a **rescue**. Copying is justified by risk, not by
presentation.

This was genuinely contested. `_archive.py:10-14`, written in #24 *after* #27 was
filed, argues the opposite:

> A repo with a spec root outside the worktree is not exposed that way — teardown
> cannot reach those files. Archiving still runs, and is still worth running: the
> archive is the flattened, numbered snapshot, which the live tree is not.

Implementing #27 without settling this would have silently reverted a reviewed
decision. It is settled deliberately, in favour of rescue: the numbered ordering
and generated index remain a real feature — they are how the archive *reads* —
but they stop being the justification for duplicating files that cannot be lost.
The docstring gets rewritten to say so.

## Recommended Direction

**One predicate does three jobs.**

```
at_risk(src) = src is inside the worktree
```

Placed in `_plan` (`_archive.py:98`), which already assembles the file list, it
decides what gets copied, whether a failure blocks teardown, and what the message
says.

### What gets archived

| Source | At risk? | Archived |
|---|---|---|
| `<spec_dir>/*` under the default `<repo>/specs` | yes | yes — unchanged from today |
| `<spec_dir>/*` under an external `spec_root` | no | no |
| `<worktree>/.agent/spec.md` (legacy) | yes | yes → `extra/legacy-agent-spec.md` |

Path containment, not "is `spec_root` set". A `spec_root` that resolves back
inside the worktree is still at risk and still archived — an on/off flag would
get that case wrong.

A durable-`spec_root` repo with no legacy file produces **no archive directory at
all**. `archive()` already returns `(None, [])` for an empty plan. No
copy-vs-reference tagging, no index rows pointing at live files: under rescue,
the absence *is* the correct output. The message carries the reason so it does
not read as a failure:

```
✓ spec dir is durable (~/Development/wfctl-specs/26-…) — nothing was at risk
```

### Failure semantics

Today the hook ends in `|| true` (`.workmux.yaml:84`) and the command promises
"Never exits non-zero" (`cli.py:293`). Together they guarantee that a failed
archive is silent and the worktree is destroyed anyway — the failure the command
exists to prevent, delivered by its own error handling.

workmux is documented to abort removal when `pre_remove` fails, so blocking
appears available — this is assumption 1 below and must be confirmed before any
code is written, because the rest of this section depends on it. Two layers:

| Layer | Rule |
|---|---|
| wfctl's exit code | Non-zero **only** when at-risk files existed and copying them failed. Durable `spec_root`, nothing to archive, gone worktree, non-git dir → 0. |
| The hook | Any non-zero blocks removal, including crashes wfctl could not catch. |

The second layer is deliberate rather than a gap. wfctl cannot honour a "warn and
proceed" rule for failures that happen before its code runs — a broken install,
an import error, bad args. Those exit non-zero regardless of intent. Under rescue
that is correct: we cannot prove nothing was at risk, so we do not proceed.

`workmux remove` has no hook-skip flag, so blocking must always print the manual
escape hatch:

```
✗ 4 spec files could not be archived — removal aborted, nothing lost.
  Retry:         workmux remove <handle>
  Remove anyway: git worktree remove <path> && git branch -D <branch>
```

The one case that proceeds on failure is wfctl not being installed at all — where
the config exists but the tool does not, and blocking would strand every worktree
on that machine.

```yaml
pre_remove:
  - if command -v wfctl >/dev/null; then wfctl archive-specs "$WM_WORKTREE_PATH" "$WM_HANDLE"
    else echo "⚠ wfctl not on PATH — specs in $WM_WORKTREE_PATH not archived"; fi
```

### Rename: `archive-story` → `archive-specs`

The command archives `spec_dir` plus one hardcoded legacy path. Nothing else.
"Story" overclaims, and it collides conceptually with `checkpoint`, which
captures the other half of a branch's story.

**`archive-story` stays as a hidden alias.** Not optional. `.workmux.yaml` is
repo-local and older copies persist; without the alias they hit "unknown command"
→ non-zero → aborted removals in every repo that has not re-installed.

### The install prompt (#26)

`install-skills` asks once, on first interactive install, beside the tracker
question it already asks (`cli.py:803`). The prompt is the `rich` render in issue
#26 — three numbered panels, working code, taken as specified. Option 2's
follow-up prints the `git clone` / `mkdir` commands rather than running them.

| | tracker (`cli.py:803`) | spec_root (new) |
|---|---|---|
| Asked when | first interactive install, key absent | same |
| Skipped when | `--yes`, no tty, key present | same |
| Decline recorded as | `manifest["tracker"] = None` | *nothing* — absence **is** the default |
| Written to | this repo's manifest | **main checkout's**, like `wfctl spec-root` (`cli.py:424`) |

Two deliberate differences. Option 1 records no `spec_root`, because the default
*is* the absence of the key — a repo that answers "keep them here" must resolve
byte-identically to one that never answered. And the value goes to the main
checkout, since a worktree's manifest is gitignored and dies with the worktree.

Asked-once is tracked by a separate `spec_root_asked: true` marker, written on
any answer including option 1. `spec_root: null` was rejected: `_manifest_spec_root`
already treats empty as undeclared, so the key would be pure bookkeeping under a
name implying behaviour.

## Implementation details that bite

Both found in the code, neither mentioned in the issues.

1. **`_NON_LAYER_KEYS` must gain `spec_root_asked`** (`cli.py:604`). `_layer_keys`
   returns every manifest key not in that set and callers do
   `manifest[key].get("items", [])`. A bare `True` there is an immediate
   `AttributeError` in `doctor` and `install-skills`, not a subtle bug.

2. **The marker must be read the way `spec_root` is resolved.** `post_create` runs
   `install-skills` in every fresh worktree, where the manifest is regenerated
   from scratch. `_interactive()` is `sys.stdin.isatty()` (`cli.py:729`) so a
   workmux hook will not prompt — but running `install-skills` by hand inside a
   worktree would re-ask, because that manifest has no marker. Read via the same
   walk as `spec_root_declaration` (`_paths.py:222`): this repo's manifest, then
   the main checkout's. Write to the main checkout. No new machinery.

3. **FR-013 needs reconciling in the same pass.** `aamarin/wf-skills#11` requires
   "Tooling MUST read exactly one artifact location — the new one. No component
   reads both." `_archive.py:114` reads the superseded `.agent/spec.md`. The code
   is correct — `pre_remove` declining to archive that file *is* deleting it, and
   nothing infers pipeline state from it — but the requirement as written says
   otherwise and that epic is closed, so the contradiction has no home. It lives
   in `_plan`, the function this change edits.

## Key Assumptions to Validate

- [ ] **workmux aborts removal when `pre_remove` exits non-zero.** Sourced from a
      strings dump of the binary's embedded README (`| pre_remove | Before worktree
      removal (aborts on failure) |`), not from observed behaviour. The entire
      blocking design rests on it. Test with a throwaway worktree and a hook that
      exits 1 **before writing any code**.
- [ ] **`workmux remove`'s uncommitted-changes guard** (`Worktree has uncommitted
      changes. Use --force to delete anyway.`) — does it count untracked files?
      Determines how much of the separate rescue issue is already solved.
- [ ] **The `archive-story` alias is reachable in typer** without duplicating the
      command body, and a hidden alias still dispatches from a hook.

## MVP Scope

**In:**

1. Containment predicate in `_plan`; durable spec dirs skipped with a message
   naming the resolved root.
2. Conditional non-zero exit; escape hatch printed on block.
3. `.workmux.yaml` hook rewritten; `|| true` removed.
4. `archive-story` → `archive-specs` with hidden alias.
5. `install-skills` spec-root prompt, `spec_root_asked` marker, `_NON_LAYER_KEYS`
   updated.
6. Docstrings rewritten: `_archive.py:1-24` (rescue framing, predicate) and
   `cli.py:285-299` (narrow non-zero rule). FR-013 wording reconciled.

**Tests** — `tests/test_archive_story.py` → `tests/test_archive_specs.py`, one
per containment row:

1. No `spec_root` → archives exactly what it archives today (regression guard).
2. `spec_root` outside the worktree → legacy design doc only, nothing from spec_dir.
3. `spec_root` resolving back *inside* the worktree → spec_dir still archived,
   proving containment rather than "is it set".
4. At-risk files exist and copying fails → non-zero, escape hatch printed.
5. `archive-story` alias still dispatches.

`tests/test_install_skills.py`: prompt fires on first interactive install; skipped
on `--yes`, non-tty, and when the marker exists; option 1 leaves `spec_root`
absent; options 2/3 write the main checkout's manifest; a marker in the main
checkout suppresses the prompt from a worktree.

**Estimate:** half a day if assumption 1 confirms; +2h if the rename's call sites
are messier than the ~20 test invocations grep found.

## Not Doing (and Why)

- **Untracked/uncommitted rescue** — real gap (`checkpoint` uses `git diff HEAD`,
  which misses untracked files entirely), but a fourth concern touching git
  plumbing and needing size and secret guards. Its own issue, filed alongside this
  design. Likely resolves to fixing `checkpoint` rather than a new mechanism, and
  possibly to nothing if workmux's existing guard already covers it.
- **Putting checkpoints inside `archive/`** — `_archive.py:164-166` renames the
  whole directory aside on every re-archive, burying anything inside it.
  Checkpoints live at the state-dir root and accumulate independently, which is
  already right. Restorable and forensic artifacts also do not belong in one
  container that the index calls non-restorable.
- **Index-only rows for durable specs** — considered and dropped. Keeps the full
  numbered reading order for every repo at zero drift, but costs a
  copy-vs-reference tag on every `_plan` entry to preserve a presentation the
  rescue decision says is not the point.
- **Cloning or creating the spec root during install** — network I/O and repo
  creation mid-install is a large blast radius and a bad failure mode. wfctl
  resolves paths; the prompt prints the commands.
- **Orphan-branch spec layouts** — break tooling that assumes shared history
  (`git log --all`, CI diffing against a base, PR UIs offering to merge the specs
  branch) for no benefit the cloned-repo layout does not already give.
- **Making the hook fatal unconditionally** — a repo with a durable `spec_root`
  loses nothing on archive failure, so blocking it would be strictly wrong.

## Open Questions

- Does the alias get a deprecation warning, or stay silent until `doctor` can
  prove nobody calls it? A warning on every teardown is noise; silence risks the
  alias outliving its purpose.
- Should `doctor` grow a check for `.workmux.yaml` still calling `archive-story`,
  the way it already lints the teardown hook and the legacy `.agent/` directory?
  That is what would eventually make removing the alias safe.
