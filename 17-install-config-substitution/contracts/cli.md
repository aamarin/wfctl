# Contracts: CLI surface and internal transforms

**Feature**: install-config substitution (#17)

Two contract layers: the commands a developer invokes, and the pure functions
behind them. The output strings are part of the contract — they are the entire
delivered value of the health check, and tests assert on them.

---

## 1. Command: `wfctl install-config workmux`

**Surface change**: none. No new flags, no changed arguments, no changed exit
codes. Existing behavior (seed-once, refuse without `--force`, `agent:`
resolution) is unchanged.

### Added behavior

After the file is copied and patched:

| Condition | stdout | Exit |
| --------- | ------ | ---- |
| Prefix substituted, name unchanged by sanitizing | *(existing summary line only)* | 0 |
| Prefix substituted, name was sanitized | `ℹ window_prefix: 'my.proj' → 'my_proj' — tmux rewrites . and : in session names` | 0 |
| `<project>` survives in the written file | `⚠ .workmux.yaml still contains '<project>' — the prefix was not substituted.`<br>`  The template's window_prefix key may have been renamed or reformatted upstream.`<br>`  Fix: set window_prefix: 'wfctl__'` | 0 |
| Expected key absent, no placeholder left behind | *(silent — FR-009)* | 0 |

Seeding never fails on account of these conditions (FR-009). The warning informs;
it does not gate.

### Written result

Given template lines:

```yaml
# Per-project tmux session/window name prefix (workmux default: "wm-").
# window_prefix: "<project>__"
```

seeded into a project named `wfctl`, the file contains:

```yaml
# Per-project tmux session/window name prefix (workmux default: "wm-").
window_prefix: 'wfctl__'
```

The explanatory comment line is preserved; only the key line is rewritten, and it
is written **active**, not commented (D1).

---

## 2. Command: `wfctl doctor`

**Surface change**: none. No new flags (FR-012b). Exit code is **never** altered
by this feature (FR-016), matching the existing `⚠ no pinned commit` precedent at
`cli.py:1253`.

### Decision table

| `.workmux.yaml` | Interactive | Behavior |
| --------------- | ----------- | -------- |
| absent | either | silent (FR-017) |
| hook invokes archiving | either | silent |
| `archive-story` only inside a comment | either | treated as **not** wired (FR-011) |
| `archive-story` outside the `pre_remove` block | either | treated as **not** wired (FR-011) |
| `pre_remove: []` | yes | warn → prompt → on `y`, patch |
| `pre_remove: []` | no | warn + reachability line, no write (FR-013/013a) |
| `pre_remove` has custom entries | either | warn + manual instruction, no write (FR-015) |
| file not writable | yes, confirmed | warn, continue (`OSError` swallowed) |
| session prefix unsubstituted | either | **silent — never reported** (FR-013b) |

### Output — interactive, fixable

```
⚠ .workmux.yaml: pre_remove does not call `wfctl archive-story` — removing a
  worktree will discard its specs, plan, and tasks.
  Archives would be written to: ~/.local/state/wfctl/pfms/<branch>/archive/
Wire it now? [Y/n] y
✓ pre_remove wired — .workmux.yaml
```

The destination line is required (FR-012a): consent to a change whose whole value
is a destination the developer cannot otherwise see.

### Output — non-interactive

Identical warning, then:

```
  Run `wfctl doctor` from a terminal to wire it.
```

No prompt, no write, exit unchanged. This is the path `/start-session` takes.

### Output — custom hook, refuses

```
⚠ .workmux.yaml: pre_remove does not call `wfctl archive-story`, and holds custom
  steps I won't rewrite. Add this line to pre_remove yourself:
    - command -v wfctl >/dev/null && wfctl archive-story "$WM_WORKTREE_PATH" "$WM_HANDLE" || true
```

### Idempotence

Running twice applies the change once. After a successful patch the file wires the
hook, so the next run takes the silent branch. Declining is **not** recorded — the
warning returns next run (FR-018).

---

## 3. Module: `wfctl/_workmux.py`

Pure functions. **Imports nothing from `wfctl.*`; never calls `subprocess`.**
Every value comes in as an argument, so tests need no git repo, no network, and no
temp directory.

```python
def patch_seed(text: str, *, agent: str | None, project: str) -> str
def tmux_safe(name: str) -> str
def pre_remove_wired(text: str) -> bool
def wire_pre_remove(text: str) -> str | None
```

### `patch_seed(text, *, agent, project) -> str`

Rewrites at most two lines. Returns the full file text.

| Input condition | Result |
| --------------- | ------ |
| line matches `^\s*#?\s*window_prefix:` | replaced with `window_prefix: '<project>__'` |
| `project` contains `'` | escaped by doubling (`it's` → `'it''s__'`) |
| line starts `agent:`, `agent` is not `None` | replaced with `agent: <agent>` |
| line starts `agent:`, `agent` is `None` | replaced with the commented per-developer form |
| either key absent | that line untouched; no key appended |

`project` MUST arrive already sanitized. `patch_seed` does not call `tmux_safe`
itself — doing so would hide the substitution from the only caller able to report
it (FR-007).

### `tmux_safe(name) -> str`

`re.sub(r"[.:]", "_", name)`. Exactly the two characters tmux rewrites (research
R3); everything else passes through.

| Input | Output |
| ----- | ------ |
| `wfctl` | `wfctl` |
| `my.project` | `my_project` |
| `a:b.c` | `a_b_c` |
| `my project` | `my project` |
| `my-proj_x$` | `my-proj_x$` |

### `pre_remove_wired(text) -> bool`

True when a **non-comment line inside the `pre_remove:` block** contains
`archive-story`. The block is that key's own line plus the lines belonging to it
— indented or blank — ending at the next line in column 0.

| Input | Result |
| ----- | ------ |
| `pre_remove:` + `  - ... wfctl archive-story ...` | `True` |
| wired hook, then a blank line, then `files: {}` | `True` |
| `pre_remove: []` | `False` |
| `pre_remove:` + `  # - wfctl archive-story ...` | `False` |
| `archive-story` in a pane command, `pre_remove: []` | `False` |
| `# we deliberately skip archive-story` above the key | `False` |

**Scoped deliberately.** An earlier version scanned the whole file, so
`archive-story` appearing anywhere non-comment — a pane command, a `post_create`
step — reported the hook as wired while `pre_remove: []` left teardown
unprotected. That is the check failing *open* on the one question it exists to
answer, and no test failed while it was wrong (review finding on PR #19).

Scoping introduces the opposite risk — reading too little and missing a real
hook — so rows 2 and 5 above are both pinned by tests, and the fix was verified
by confirming those tests fail against the previous implementation.

### `wire_pre_remove(text) -> str | None`

Patches exactly one shape: a line matching `^pre_remove:\s*\[\]\s*$`. Returns the
new text, or `None` when the file does not have that shape.

| Input | Result |
| ----- | ------ |
| contains `pre_remove: []` | patched text (one line → two) |
| `pre_remove:` with list entries | `None` |
| no `pre_remove` key | `None` |

Returning `None` is the contract for "refuse" — the caller prints manual
instructions. It never appends a key to an unparsed file.

---

## 4. Function: `wfctl._paths.project_name(repo_root) -> str`

Rename of the existing private `_project_name`. **No behavior change.** One
internal caller (`_paths.py:228`) updates with it.

| Invoked from | Returns |
| ------------ | ------- |
| main checkout `~/dev/wfctl` | `wfctl` |
| linked worktree `~/dev/wfctl/wt/17-foo` | `wfctl` |
| `--git-common-dir` unavailable | `repo_root.name` (existing fallback) |

The second row is the regression this feature must not lose: `--show-toplevel`
would return `17-foo`, which would be written into a committed file.
