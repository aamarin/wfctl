# Quickstart: step-command drift check

**Date**: 2026-08-17
**Phase**: 1

## What changes

Two files:

- `wfctl/_pipeline.py` — three step-keyed tables become one.
- `tests/test_pipeline_commands.py` — new; asserts every step's command ships.

## The restructure

Replace lines 9–35 of `wfctl/_pipeline.py`:

```python
# step → (slash command that advances it, whether orchestrate may proceed unattended)
_STEPS: dict[str, tuple[str, bool]] = {
    "brainstorm": ("/speckit.brainstorm", False),
    "specify":    ("/speckit.specify",    True),
    "clarify":    ("/speckit.clarify",    False),
    "plan":       ("/speckit.plan",       True),
    "tasks":      ("/speckit.tasks",      True),
    "analyze":    ("/speckit.analyze",    False),
    "decompose":  ("/speckit.decompose",  False),
    "implement":  ("/speckit.implement",  False),
}

_STEP_NAMES = list(_STEPS)
```

and `next_step_content` (line 203):

```python
def next_step_content(step: str) -> tuple[str, bool]:
    """Return (slash_command, auto_flag) for the given pipeline step.

    An unknown step yields ("", False) — the caller reads the empty command as a
    finished pipeline and prints "story complete", so this must not raise.
    """
    return _STEPS.get(step, ("", False))
```

`_STEP_NAMES` keeps its name and its two readers (lines 62 and 86) unchanged.

## The check

```python
# tests/test_pipeline_commands.py
_COMMANDS = Path(wfctl.__file__).parent / "agents" / "commands"
```

Read through the package rather than `_bundle.BUNDLE_ROOT`: `conftest.py`
installs an autouse fixture repointing that constant at a fake tree, and a check
subject to it reports every command missing. Say so in a comment at the point of
use — the next reader will otherwise "fix" it back.

Put the comparison in a pure helper taking the shipped names as an argument:

```python
def _unresolved(shipped: set[str]) -> dict[str, str]:
    return {s: c for s, (c, _) in _STEPS.items() if c.lstrip("/") not in shipped}
```

The real test passes the glob; the negative cases pass a constructed set. That is
what keeps them from renaming tracked files or pointing at scratch directories.

On failure, print the unresolved entries **and** the sorted shipped names. Do not
nominate a likely rename: measured, similarity scoring names an innocent file
more often than the right one (`research.md` R1).

## Verify

```bash
uv run pytest -q                      # full suite
uv run ruff check .                   # lint gate
uv run mypy                           # type gate — exactly as CI invokes it
wfctl status                          # pipeline output unchanged
```

The issue's Verification section asks for a renamed command to be caught. Do it
as a test, not as a filesystem edit:

```python
_unresolved((real - {"speckit.plan"}) | {"plan"})   # -> {"plan": "/speckit.plan"}
_unresolved(set())                                  # -> all eight entries
```

Renaming `wfctl/agents/commands/*.md` by hand and restoring it was rejected: an
interrupted run leaves the repository broken and the bundle content hash wrong.

## Watch for

- The restructure is behaviour-preserving or it is a regression. All eight
  commands and flags must match the table in `data-model.md` exactly, **in
  order** — `_STEP_NAMES` derives from the literal and is the pipeline sequence,
  so assert the ordered list rather than each step separately.
- An unknown step must still return `("", False)`, not raise.
- The check must fail, not pass, when the commands directory is absent — an empty
  set makes every entry unresolved, which is the correct outcome.
