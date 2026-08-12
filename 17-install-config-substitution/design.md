# Spec: `install-config` — wire `pre_remove`, substitute the `<project>` placeholder

**Issue:** #17
**Branch:** `17-install-config-substitution`
**Status:** Approved (brainstorm)
**Date:** 2026-08-02

---

# Summary

**How might we** make `wfctl install-config workmux` seed a config that protects
a repo's specs and names its tmux sessions correctly, without a human editing the
file afterward?

**Direction:** fix the template so new repos are born correct; lint and offer for
repos already seeded. All substitution logic becomes pure `str → str` functions in
a new `_workmux.py`, with values injected by the caller.

## Honest value ranking

Not all three parts are worth the same, and the spec should say so:

| Part | Kind | Why |
|---|---|---|
| `pre_remove` wired in template | **Painkiller** | Silent, unrecoverable data loss. `pfms` is exposed right now. |
| `doctor` lint + retrofit | **Painkiller** | The only path by which an already-seeded repo ever gets protected. |
| `window_prefix` substitution | **Vitamin** | Saves one hand-edit that both existing repos already made once. |

`window_prefix` is the least valuable third of this work. It survives because it
is one line inside a function being written anyway — not because it earns its own
issue.

## Key assumptions to validate

- [x] **Project names are tmux-safe.** — **FALSIFIED, and resolved (D3).** tmux
      silently rewrites `.` and `:` to `_` in session names, and then targeting by
      the original string fails (`can't find pane: dot__x`). Measured: those two
      characters and no others — spaces, `$`, `-`, `_` all survive verbatim.
- [ ] **workmux replaces rather than merges the `pre_remove` default.** If it
      replaces, a seeded Node repo loses the built-in `node_modules` fast-delete.
      Mitigating: the template already ships `[]`, so this is not a regression
      against today — but it means the wired hook inherits an existing cost
      rather than introducing one. Test: seed a Node repo, `wm remove`, observe.
- [ ] **`pre_remove: []` is the only shape in the wild.** Observed in exactly two
      repos. Degrades safely if wrong (`wire_pre_remove` returns `None` → manual
      instruction), so this is a convenience bet, not a correctness one.
- [ ] **Humans run `wfctl doctor` in a TTY.** The retrofit only fires
      interactively, and `/start-session` runs doctor through a non-TTY shell. If
      that is the only place it ever runs, the warning prints forever and the fix
      never applies. Test: after shipping, check whether `pfms` actually gets
      wired within a week.
- [ ] **A non-persistent decline is not annoying enough to matter.** Someone who
      deliberately does not want `archive-story` gets warned on every run with no
      way to silence it. Revisit if it draws a complaint.

## Open questions

1. Does the doctor prompt ever fire in practice? Answered by shipping, not by
   discussion — see the assumption above.

Full problem statement, design, and "Not Doing" rationale follow.

---

## Problem

`wfctl install-config workmux` seeds a `.workmux.yaml` from the wf-skills
template. That template ships two defects:

1. **`pre_remove: []`** (template line 54). This is not an empty default — it is
   an explicit opt-out. workmux's own reference documents the default as
   "auto-detects Node.js projects and fast-deletes node_modules", with
   `pre_remove: []` given as the documented way to disable it. So the seeded
   config actively turns the hook off, and `wfctl archive-story` — the whole
   point of #10 — never runs. `specs/` and `.agent/` are gitignored, so removing
   a worktree silently destroys its spec, plan, tasks, and analysis.

2. **`# window_prefix: "<project>__"`** (template lines 11-12). `<project>` is a
   literal a human is expected to replace. Nobody does at seed time; both real
   repos edited it by hand afterwards.

The logic for archiving already upgrades with the tool (`wfctl archive-story`,
commit e64d047). The *invocation* does not — it is repo-local config, seeded
from a template with the hook off.

### Evidence

Confirmed against the live system, not inferred:

- wf-skills `main` → `.agents/configs/workmux/.workmux.yaml:54` is `pre_remove: []`
- `pfms/.workmux.yaml:224` is `pre_remove: []` — the seeded value, never edited
- `pfms/.workmux.yaml:25` is `window_prefix: 'pfms__'` — hand-edited
- `wfctl/.workmux.yaml:27` is `window_prefix: 'wfctl__'` — hand-edited
- `tmux ls` shows `pfms__490-budget-actuals-wiring`, `wfctl__17-install-config-substitution`

Every repo that uses the template ends up with a project-prefixed session name.
None of them get the archive hook.

## Decisions

### D1 — `window_prefix` ships live, not commented

The value is git-derived in both cases; the only question was the comment state.
Chose **live**: `window_prefix: 'wfctl__'`.

Rationale: `pfms` and `wfctl` have both already hand-edited to exactly this, so
uncommenting codifies observed practice rather than imposing a new default. The
"behavior change for anyone relying on workmux's `wm-` default" that #17 worried
about is a change to a default nobody keeps.

This differs from `agent:`, which stays commented when it cannot be resolved.
`agent:` is per-*developer* and has no correct value to infer. A project name is
per-project and is derivable, which is why the same conservatism does not apply.

### D2 — Retrofit is opt-in, surfaced by `doctor`

`install-config` is seed-once and refuses to overwrite without `--force`;
`--force` replaces the whole file, which would destroy the ~230 lines `pfms` has
customized. So the template fix cannot reach already-seeded repos.

Chose: **`wfctl doctor` warns, and offers to apply a targeted patch.** Detection
is free and automatic; mutation is opt-in and interactive.

This addresses the failure #17 names precisely — "a repo seeded today gets zero
protection *and no signal*". The template fix covers new repos (zero
protection); the doctor lint covers existing ones (no signal).

Today the retrofit backlog is exactly one file (`pfms`; `wfctl` is already wired
by hand). The lint earns itself on the third repo, and on any repo that drifts.

### D3 — Sanitize tmux-illegal characters, and say so only when it fires

Measured against a live tmux server: session names have `.` and `:` silently
rewritten to `_`, after which targeting by the original string fails with
`can't find pane: <fragment>`. No other character is touched — spaces, `$`, `-`
and `_` all survive verbatim, so the substitution set is exactly `[.:]`.

Chose: **sanitize, and print a one-line notice only when the name actually
changed.** The common path stays silent; a repo at `~/dev/my.project` gets one
`ℹ` line explaining why its prefix reads `my_project__`.

Rejected: a silent rewrite (leaves an unexplained discrepancy between the
directory name and the config), an explanatory comment written into
`.workmux.yaml` (permanently pollutes a committed file to explain a one-time
event), and prompting for a prefix (`install-config` is a seed command; blocking
on a rare edge case is the wrong trade).

Sanitizing is part of *resolving* the value, not part of patching text, so it
lives at the call site rather than inside `patch_seed`:

```python
# _workmux.py — pure, unit-testable
def tmux_safe(name: str) -> str:
    return re.sub(r"[.:]", "_", name)

# cli.py — resolves, reports, injects
raw = project_name(repo_root)
project = _workmux.tmux_safe(raw)
if project != raw:
    console.print(
        f"[dim]ℹ window_prefix: '{raw}' → '{project}' — tmux rewrites . and : "
        "in session names[/dim]"
    )
```

Neither `wfctl` nor `pfms` is affected today. This is insurance against a failure
mode tmux reports as a *missing pane* rather than a bad name.

## Design

### Components

| Where | Change |
|---|---|
| wf-skills template | wire `pre_remove`; leave `window_prefix` for substitution |
| `wfctl/_workmux.py` | **new** — pure `str → str` transforms |
| `wfctl/_paths.py` | `_project_name` → `project_name` (public; one caller at `_paths.py:228`, no logic change) |
| `wfctl/cli.py` | `install-config` calls `patch_seed`; `doctor` gains lint + retrofit |

`_workmux.py` is an internal seam alongside `_paths` / `_tracker` / `_archive` —
the same extraction e64d047 applied to `_archive`. It is **not** a plugin
boundary: no Protocol, no registry, no interface. See Out of Scope.

### Dependency injection

`_workmux.py` imports nothing from `wfctl.*` and never calls `subprocess`. The
caller resolves values and passes them in:

```python
# cli.py — resolves, then injects
chosen  = _resolve_config_agent(repo_root, agent)   # reads the manifest
project = project_name(repo_root)                   # runs git
wf.write_text(_workmux.patch_seed(wf.read_text(), agent=chosen, project=project))
```

Injection is by plain keyword argument. No container, no injected callables, no
framework. `_interactive()` (`cli.py:658`) remains the one seam of its kind and
is unchanged.

The payoff is testability: string substitution currently requires two git repos
and a `file://` clone to assert `"agent: bob" in text`
(`tests/test_install_config.py:91`). Injected, the same assertion is a plain
function call with no fixtures.

### `_workmux.py` API

```python
def patch_seed(text: str, *, agent: str | None, project: str) -> str
def tmux_safe(name: str) -> str
def pre_remove_wired(text: str) -> bool
def wire_pre_remove(text: str) -> str | None
```

`patch_seed` receives an already-sanitized `project` (D3). It does not sanitize
internally — that would hide the substitution from the caller, which is the one
place able to report it.

**`patch_seed`** — rewrites two lines of a freshly copied template.

- `agent:` — behavior moves verbatim from `cli.py:1138-1146`. Resolved agent
  when there is one; `# agent: claude   # per-developer; ...` when there is not.
- `window_prefix` — matches `^\s*#?\s*window_prefix:` and replaces the line with
  `window_prefix: '<project>__'`, uncommented (D1). The leading `\s*` covers an
  indented or commented variant; the template's own line is at column 0. The
  explanatory comment on the preceding line is left intact; only the key line is
  rewritten.

Project names are directory names and may contain an apostrophe, so the value is
YAML single-quote escaped (`project.replace("'", "''")`).

If either key is absent from the template, that line is left alone — no append,
no crash.

**`pre_remove_wired`** — the doctor lint predicate.

```python
return any("archive-story" in ln and not ln.lstrip().startswith("#")
           for ln in text.splitlines())
```

The comment test is what stops a repo that *documents* archive-story (or
deliberately explains not using it) from reading as wired.

**`wire_pre_remove`** — the retrofit transform. Patches exactly one shape,
matching `^pre_remove:\s*\[\]\s*$`, into:

```yaml
pre_remove:
  - command -v wfctl >/dev/null && wfctl archive-story "$WM_WORKTREE_PATH" "$WM_HANDLE" || true
```

Any other shape returns `None`, and the caller prints a manual instruction.

This is deliberate. `pre_remove: []` is the only shape that exists in the wild —
it is what the template seeded and what `pfms:224` holds. A repo with real
`pre_remove` entries has hooks whose ordering and intent we would be guessing at,
and appending a top-level key to an EOF we have not parsed is how a config file
gets mangled. Refusing is cheaper than being clever.

The retrofit is the *only* consumer of this function. Newly seeded repos get the
hook from the fixed template, so the wiring is not duplicated.

### Template change (wf-skills)

`.agents/configs/workmux/.workmux.yaml:54` becomes:

```yaml
# specs/ and .agent/ are gitignored, so removing the worktree destroys the spec,
# plan, tasks, and analysis with it. `wfctl archive-story` copies them into
# wfctl's per-branch state dir — flattened, numbered in pipeline order, with a
# generated index.
#
# `command -v` guards a checkout without wfctl on PATH: a teardown hook must
# never be the thing that strands a worktree. The subcommand exits 0 on every
# internal failure for the same reason.
pre_remove:
  - command -v wfctl >/dev/null && wfctl archive-story "$WM_WORKTREE_PATH" "$WM_HANDLE" || true
```

The arguments are passed explicitly even though `archive-story` already defaults
both from those same environment variables (`cli.py:298,305`). The bare form is
equivalent and shorter, but explicit keeps the template byte-identical to
`wfctl/.workmux.yaml:84` — and template/reference divergence is the bug this
issue exists to fix.

The retrofit inserts the two-line form without this comment block: a starter
template is meant to be read, but injecting six lines of prose into a file the
repo already owns is presumptuous.

### Doctor lint + retrofit

Follows the tracker prompt at `cli.py:734` — detect gap, explain, `_interactive()`
guard, `typer.confirm`, apply.

```
✓ wfctl 0.12.0 — latest
✓ base: skills up to date (565f8bc)
⚠ .workmux.yaml: pre_remove does not call `wfctl archive-story` — removing a
  worktree will discard its specs, plan, and tasks.
Wire it now? [Y/n]
```

- No `.workmux.yaml` at repo root → skip silently. Not every repo uses workmux.
- Not a TTY → warn only, never prompt. `/start-session` runs `wfctl doctor`
  through a non-TTY shell, so it reports the warning and nothing else.
- Declining does **not** persist. The tracker case records a decline because
  choosing no tracker is a genuine one-time decision; an unwired teardown hook is
  ongoing drift, and re-reporting drift is what a doctor is for.
- **Exit code unchanged.** Matches the `⚠ no pinned commit` precedent
  (`cli.py:1253`), which `continue`s without touching `exit_code`.

### Error handling

| Case | Behavior |
|---|---|
| Template missing `agent:` or `window_prefix` | Line left as-is; seed succeeds |
| Project name contains `'` | Escaped to `''`; valid YAML |
| Project name contains `.` or `:` | Rewritten to `_`; one-line notice printed (D3) |
| `.workmux.yaml` absent | Doctor skips, silent |
| `pre_remove` customized (not `[]`) | Warn + manual instruction; file untouched |
| Retrofit write fails (`OSError`) | Warn; doctor continues |
| Doctor non-interactive | Warn only; no prompt, no write |

No path here can strand a worktree: the retrofit runs inside `doctor`, never
inside a teardown hook.

## Testing

### Pure unit tests — no fixtures

Enabled by the injection above.

- `patch_seed` writes `window_prefix: 'proj__'`, live and uncommented
- `patch_seed` leaves `# agent: claude` when `agent is None` — assertions move
  from `tests/test_install_config.py:148`
- `patch_seed` escapes an apostrophe in the project name
- `patch_seed` leaves a template alone when a key is absent
- `tmux_safe` rewrites `.` and `:`; leaves spaces, `$`, `-`, `_` untouched
- `install-config` prints the sanitize notice only when the name changed
- `pre_remove_wired`: wired → `True`; `[]` → `False`; comment-only mention → `False`
- `wire_pre_remove`: patches `[]`; returns `None` on a custom list

### Real git — acceptance criterion 4

```python
def test_project_name_from_a_worktree(repo_root):
    wt = repo_root / "wt" / "9-x"
    subprocess.run(["git", "-C", str(repo_root), "worktree", "add", str(wt), "-b", "9-x"],
                   check=True, capture_output=True)
    assert project_name(wt) == repo_root.name
    assert project_name(wt) != "9-x"   # the trap #17 names
```

`project_name` has no test today. This is the regression guard for the
`--show-toplevel` trap.

### Integration — existing style

- `install-config` end-to-end asserts the real project name lands in `window_prefix`
- doctor, `_interactive()` → `False`: warns; file is byte-identical afterwards
- doctor, `_interactive()` → `True` + confirm: `pre_remove: []` becomes wired

## Sequencing

1. `wfctl` changes (`_workmux.py`, `project_name`, `cli.py`, tests) — self-contained
2. wf-skills template edit — separate repo, must reach `main`
3. Manual verification, which depends on 2

wfctl's tests build their own fake template, so step 1 does not block on step 2.
Manual verification does.

## Acceptance Criteria

- [ ] A freshly seeded repo has `pre_remove` invoking `archive-story` without hand-editing
- [ ] A failing or missing `archive-story` never strands a worktree during teardown
- [ ] `window_prefix` is written with the real project name, derived correctly
      from a worktree as well as a root checkout
- [ ] `project_name` is public, does not use `--show-toplevel`, and has a test
      asserting the worktree case
- [ ] The `<project>` placeholder no longer ships as a literal
- [ ] `wfctl doctor` reports a `.workmux.yaml` whose `pre_remove` does not call
      `archive-story`, and offers to wire it when interactive
- [ ] Doctor never prompts without a TTY and never changes its exit code for this warning

## Verification

- **Automated:** the unit and integration tests above; `project_name` worktree test
- **Manual:** `wfctl install-config workmux` in a scratch repo → both keys land with
  real values. Then `wm remove` a worktree holding a spec dir and confirm the
  archive appears under `$(wfctl state-dir)/archive`.
- **Evidence:** the archive README index lists the spec artifacts
- **Retrofit:** run `wfctl doctor` in `pfms`, accept the prompt, confirm
  `pfms/.workmux.yaml:224` is wired and the rest of the file is unchanged
  (`git diff` shows two lines)

## Out of Scope

**A pluggable worktree-management adapter.** Raised in #17 and deliberately
rejected there: the tracker adapter earned itself because GitHub, Jira, and
Gerrit all exist and constrained the verb set. Worktree management has one
implementation with no second candidate, and an interface with one
implementation is cost with no realized benefit. `_workmux.py` is an internal
seam, not a plugin boundary — if a second backend ever arrives it would be the
natural place for an adapter to grow, but nothing here anticipates one.

**Wiring `post_create` in the template.** The template's `post_create` ships
entirely commented out, so a seeded repo does not run `install-skills` on
worktree creation the way `wfctl/.workmux.yaml:72` does. Noticed while reading
the template; unrelated to #17. File separately if wanted.

**Migrating `.workmux.yaml` editing to a YAML library.** `ruamel.yaml` would
kill the line-scan smell outright, but it is a new runtime dependency (deps are
`typer` + `rich` today) for a 62-line config, and comment-preserving round-trips
carry their own maintenance burden. Line-scanning stays the house style.

## Notes

`.agent/` is gitignored in this repo, so this spec is not committed. It is the
handoff artifact `/speckit.specify` reads, and `wfctl archive-story` copies it
into the state dir at teardown.
