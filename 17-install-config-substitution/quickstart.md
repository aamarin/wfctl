# Quickstart: install-config substitution

**Feature**: #17 · **Branch**: `17-install-config-substitution`

How to build it, and how to prove it works.

---

## Build order

Bottom-up. Each step is green before the next begins.

1. **`wfctl/_workmux.py` + `tests/test_workmux.py`** — pure transforms, no
   dependencies on anything else in the feature. Fully testable in isolation.
2. **`project_name` in `_paths.py` + worktree test** — a rename plus the missing
   regression guard. Independent of step 1.
3. **`install-config` call site** (`cli.py`) — wires steps 1 and 2 into seeding.
   Delivers User Story 3.
4. **`doctor` lint + retrofit** (`cli.py`) — uses `pre_remove_wired` and
   `wire_pre_remove` from step 1. Delivers User Story 2.
5. **Integration tests** — end-to-end seeding, both health-check TTY paths.

Steps 3 and 4 are independent and may land in either order.

---

## Verify

```bash
uv run pytest -q          # 269: 227 baseline + 42 for this feature
uv run ruff check .
uv run mypy
```

### Unit checks worth writing first

```python
# no fixtures — this is the payoff for injecting `project`
assert "window_prefix: 'proj__'" in patch_seed(TEMPLATE, agent=None, project="proj")
assert "# agent: claude"        in patch_seed(TEMPLATE, agent=None, project="p")
assert "agent: bob"             in patch_seed(TEMPLATE, agent="bob", project="p")

assert tmux_safe("my.proj") == "my_proj"
assert tmux_safe("a:b.c")   == "a_b_c"
assert tmux_safe("my proj") == "my proj"      # spaces survive

assert pre_remove_wired("pre_remove:\n  - wfctl archive-story x\n") is True
assert pre_remove_wired("# skip archive-story on purpose")          is False
# scoped to the block — a mention elsewhere must not report "protected"
assert pre_remove_wired("  - command: archive-story\npre_remove: []\n") is False

assert wire_pre_remove("pre_remove: []\n")        is not None
assert wire_pre_remove("pre_remove:\n  - echo\n") is None    # refuses
```

### The regression guard that did not exist before

```python
def test_project_name_from_a_worktree(repo_root):
    wt = repo_root / "wt" / "9-x"
    subprocess.run(["git", "-C", str(repo_root), "worktree", "add", str(wt), "-b", "9-x"],
                   check=True, capture_output=True)
    assert project_name(wt) == repo_root.name
    assert project_name(wt) != "9-x"      # what --show-toplevel would have returned
```

---

## Manual verification

### Seeding (User Story 3)

```bash
mkdir /tmp/scratch && cd /tmp/scratch && git init
wfctl install-config workmux
grep window_prefix .workmux.yaml
# expect:  window_prefix: 'scratch'    — active, no '<project>' anywhere
```

Then repeat from inside a worktree of a real repo and confirm the prefix is still
the **project** name, not the branch handle.

### Retrofit (User Story 2)

```bash
cd ~/Development/pfms
wfctl doctor
# expect the warning, the archive destination, and a [Y/n] prompt
# answer y, then:
git diff --stat .workmux.yaml     # expect 1 file changed, 2 insertions(+), 1 deletion(-)
git diff .workmux.yaml            # expect ONLY the pre_remove line
```

Confirm untouched: `window_prefix: 'pfms__'`, the `post_create` port arithmetic,
the `deploy` window, and the commented `pre_remove:` example below the patch.

Run `wfctl doctor` a second time — the warning must be gone.

### End-to-end archive (User Story 1 — delivered by wf-skills#12, merged)

```bash
cd ~/Development/pfms
wm add 999-probe -b
mkdir -p wt/999-probe/specs/999-probe && echo probe > wt/999-probe/specs/999-probe/spec.md
wm remove 999-probe
ls ~/.local/state/wfctl/pfms/999-probe/archive/
# expect the artifacts plus a generated README index
```

Baseline for comparison, today:

```
~/.local/state/wfctl/wfctl/005-update-install-skills-default/archive   1 archive
~/.local/state/wfctl/pfms/                     22 branches, 0 archives
```

---

## Gotchas

- **`patch_seed` must receive an already-sanitized project name.** Sanitizing
  inside it would hide the substitution from the caller that has to report it.
- **`<agent>` is not a placeholder to substitute.** It is workmux's own runtime
  token, resolved by workmux. Only `<project>` is ours.
- **Never let the retrofit touch a customized `pre_remove`.** `wire_pre_remove`
  returns `None` and the caller prints manual instructions.
- **`doctor`'s exit code must not change.** Follow the `⚠ no pinned commit`
  precedent at `cli.py:1253`, which warns and continues.
- **The prefix is written active, not commented** — unlike `agent:`, which stays
  commented when it cannot be resolved.
