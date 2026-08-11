# CLI Contract: spec-root prompt and durable-spec skip

The user-facing surface this feature changes. Exit statuses are part of the
contract now — a teardown hook consumes them (R-001).

---

## `wfctl archive-specs [WORKTREE] [HANDLE]`

Renamed from `archive-story`, which remains a working hidden alias (FR-019).

**Arguments** — unchanged.

| Argument | Default |
|---|---|
| `WORKTREE` | `$WM_WORKTREE_PATH`, then the current repo |
| `HANDLE` | `$WM_HANDLE`, then the branch |

**Exit status** — new; previously always 0.

| Code | Condition |
|---|---|
| 0 | nothing was at risk, or everything at risk was preserved |
| 1 | at-risk artifacts existed and preserving them failed |

**Output — default layout, artifacts preserved** (unchanged):

```
✓ archived 9 files to ~/.local/state/wfctl/<project>/<branch>/archive/
```

**Output — durable spec location, nothing at risk** (new, FR-004):

```
✓ spec dir is durable (/Users/you/Development/myproject-specs/42-feature)
  — nothing was at risk, nothing archived
```

Names the resolved location, not just the fact of skipping. Without the path the
message is indistinguishable from a lookup that silently found nothing.

**Output — preservation failed** (new, FR-006/FR-008):

```
✗ 4 spec files could not be archived — removal aborted, nothing lost.
  Cause: [Errno 28] No space left on device

  Retry:         workmux remove 42-feature
  Remove anyway: git worktree remove <path> && git branch -D 42-feature
```

Both routes are mandatory. `workmux remove --force` does **not** bypass the hook
(R-001), so the manual route is the only escape and must not be left implicit.

**Output — nothing to archive at all** (unchanged): normal, exit 0.

---

## `wfctl install-skills` — spec location prompt

Asked once, on first interactive install, alongside the existing tracker
question.

**When asked** (all must hold): interactive stdin · `--yes` absent · no
`spec_root_asked` in this checkout's manifest or the primary checkout's.

**Prompt** — the rendered form is fixed by issue #26 and adopted as specified:
three numbered panels at 78 columns, closing with

```
Change any time with `wfctl spec-root`. Skipping keeps option 1.

Choose [1/2/3] (1):
```

**Option 1 — keep them in the repo (default)**

```
{spec_root_asked: true}
```

No `spec_root` written. Resolution is byte-identical to a repo never asked
(FR-012).

**Option 2 — a specs repo cloned here**

```
Choose [1/2/3] (1): 2
Directory (myproject-specs):

✓ wrote /…/myproject/.wf-skills-manifest.json
✓ gitignored myproject-specs/ in /…/myproject/.gitignore

Not created yet — when you have a specs repo:
  git clone <url> myproject-specs

Or start one:
  mkdir -p myproject-specs/specs && git -C myproject-specs init
```

**Option 3 — somewhere else on disk**: prompts for a path with no default;
otherwise identical, minus the gitignore line.

**Guarantees**

- Never creates, clones, or checks the existence of the chosen path (FR-014).
- Writes the **primary checkout's** manifest and reports every file touched
  (FR-013).
- Non-interactive, `--yes`, or already-asked → silent, nothing written (FR-011).

---

## `wfctl doctor` — stale configuration check

New non-fatal drift report (FR-020).

```
⚠ .workmux.yaml still calls `wfctl archive-story` — renamed to `archive-specs`.
  The old name still works. Update the hook, or re-run `wfctl install-config`.
```

Never affects the exit code, matching the superseded-path checks beside it.
Transitional by construction; its removal is tracked as separate work.

---

## `.workmux.yaml` — `pre_remove`

```yaml
pre_remove:
  - if command -v wfctl >/dev/null; then wfctl archive-specs "$WM_WORKTREE_PATH" "$WM_HANDLE"
    else echo "⚠ wfctl not on PATH — specs in $WM_WORKTREE_PATH not archived"; fi
```

`|| true` and the `command -v` short-circuit guard are both gone.

| Situation | Hook exit | Removal |
|---|---|---|
| tool absent | 0 (warns) | proceeds — blocking would strand every worktree on that machine |
| tool present, nothing at risk | 0 | proceeds |
| tool present, preservation succeeded | 0 | proceeds |
| tool present, preservation failed | 1 | **refused** |
| tool present but broken | non-zero | **refused** |

**Behaviour change to announce.** Under `|| true` no user has ever seen this hook
block a removal. Afterwards, a full disk stops teardown instead of silently
destroying a spec. Belongs in the pull request description and the command's own
documentation.

---

## `wfctl spec-root` — unchanged

Neither reads nor writes `spec_root_asked`. Its contract stays "show, set, or
clear one key."
