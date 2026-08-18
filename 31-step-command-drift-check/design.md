# Step-command drift check

Issue: [aamarin/wfctl#31](https://github.com/aamarin/wfctl/issues/31)

## Problem Statement

How might we make a mismatch between `_STEP_COMMAND` and the commands wfctl
actually ships fail loudly, instead of surfacing as a session being told to run
a command that answers to nothing?

## Recommended Direction

One test, asserting `_STEP_COMMAND` against the bundled command files.

```python
# tests/test_pipeline_commands.py
_COMMANDS = Path(wfctl.__file__).parent / "agents" / "commands"

def test_every_step_command_ships_in_the_bundle() -> None:
    have = {p.stem for p in _COMMANDS.glob("*.md")}
    missing = {s: c for s, c in _STEP_COMMAND.items() if c.lstrip("/") not in have}
    assert not missing, _which_side_moved(missing, have)
```

`_which_side_moved` builds the message with `difflib.get_close_matches`: a near
hit means the command was renamed under the table, no hit means the table entry
is wrong. Different fixes, so the message distinguishes them.

#31 argued for a `doctor` lint over a test, because the assertion crossed a
repository boundary — wfctl's tests could not see wf-skills' command files, and
CI installed nothing. **That premise died in 271bb2c.** wf-skills is vendored
into the package at `wfctl/agents/commands/`, and upstream is archived. Both
sides now live in one repo at one commit, so CI sees them and the check runs
before merge rather than at whatever moment someone next runs `doctor`.

The runtime half is already covered: `doctor` hashes the installed tree against
the bundled tree (`cli.py:1899-1927`) and reports `skills stale → run
install-skills`. A repo whose installed commands disagree with the bundle is
already told so. A second lint would re-report it.

## Key Assumptions to Validate

- [x] The bundled command set satisfies the table today — verified: 23 commands
      found, 0 missing
- [x] Reading `_bundle.BUNDLE_ROOT` would *not* work. `tests/conftest.py:55-78`
      installs an **autouse** `bundle` fixture repointing it at a fake tree
      holding only `test-cmd.md`; the naive version reports all 8 commands
      missing. Verified by probe. The test reads `Path(wfctl.__file__).parent`
      instead, and says why in a comment — the fixture's docstring argues tests
      should not read the real tree, and this is the deliberate exception.
- [ ] `difflib.get_close_matches` default cutoff (0.6) separates a rename from a
      wrong entry on realistic names. Check against the #23 case:
      `speckit.brainstorm` vs `brainstorm`.

## MVP Scope

**In:** one new file, `tests/test_pipeline_commands.py` — the assertion plus the
close-match message. No production code.

**Out:** everything else.

## Not Doing (and Why)

- **A `doctor` lint** — the content-hash check already reports installed-vs-bundle
  drift. Adding a second report of the same fact trains the reader to skim past
  both.
- **A checked-in list of expected command names** (#31 option 1) — the bundle is
  checked in. A second list to keep in sync is the drift this issue is about.
- **A check in wf-skills' CI** (#31 option 3) — the repo is archived.
- **Reporting bundled `speckit.*` commands no step names** — `speckit.checklist`,
  `speckit.brief`, `speckit.orchestrate` are legitimately not step commands, so
  this direction reports noise permanently.
- **Deciding whether `doctor` exits non-zero** — out of scope per #31; that is
  [#41](https://github.com/aamarin/wfctl/issues/41)'s call.

## Open Questions

- #31's "The awkward part" section is now factually wrong. Comment on the issue
  saying the vendoring dissolved it, so the next reader does not re-derive the
  cross-repo constraint?
