Marker comment — `# wfctl: bootstrap-handled` anywhere in the `post_create` block turns the warning off.

The check today is one substring search: does any live line under `post_create:` contain `install-skills`. That answers "does this config name our command", not "will a fresh worktree come up with skills". The marker lets the repo answer the second question itself, in the file the reader is already looking at.

The thing that bites: `_live_lines` drops comment lines, so a marker comment is invisible to the very function that would consume it. Read the marker from `_block` instead — the raw block, comments included.

```python
_BOOTSTRAP_OPT_OUT = "# wfctl: bootstrap-handled"


def post_create_wired(text: str) -> bool:
    if any(_BOOTSTRAP_OPT_OUT in ln for ln in _block(text, "post_create:")):
        return True
    return any("install-skills" in ln for ln in _live_lines(text, "post_create:"))
```

Reading the raw block for the marker and live lines for the command keeps a commented-out `install-skills` reading as unwired — the opt-out is a declaration, the command is a hook, and only the hook has to be live.

An empty `post_create` still warns, with no extra code: no lines means no marker, and that is the case the check was written for.

Two tests in `tests/test_workmux.py`, beside the five already there: marker present suppresses, marker under a different key (`pre_remove:`) does not. `_warn_missing_bootstrap` in `cli.py` needs no change — it reads the boolean.

Want the warning text to name the opt-out too, so a repo that needs it learns from the warning rather than the source?
