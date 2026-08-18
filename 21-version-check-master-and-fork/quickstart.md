# Quickstart: verifying the branch-drift check

## The live fixture

This machine is already in the failing state, so no setup is needed to reproduce
the bug:

```
installed build : 0.14.0 @ d8688f6
branch tip      : 0.15.0 @ 271bb2c   (three commits ahead, untagged)
newest tag      : v0.14.0
```

`wfctl doctor` reports `✓ wfctl 0.14.0 — latest` — the defect, live.

## Verify the fix

```bash
wfctl doctor                 # expect: ✓ latest release, then the drift block
echo $?                      # expect: 1

uv tool install --force git+https://github.com/aamarin/wfctl.git
wfctl doctor                 # expect: ✓ wfctl 0.15.0 — latest, no drift block
echo $?                      # expect: 0
```

**The second command gates FR-005.** If the recorded origin does not advance —
check `direct_url.json` in the installed `.dist-info` — then `--force` did not
re-resolve against an HTTPS remote and `--reinstall` must be added to the printed
command. Research R4 proved `--force` sufficient against a `file://` remote; this
run is the confirmation against the real one.

## Sandbox for the states this machine cannot show

A local clone whose branch tip can be moved, with an isolated tool dir, exercises
drift without touching the real install:

```bash
git clone <repo> /tmp/sandbox/srcrepo
export UV_TOOL_DIR=/tmp/sandbox/uvtools UV_TOOL_BIN_DIR=/tmp/sandbox/uvbin
uv tool install "git+file:///tmp/sandbox/srcrepo"
git -C /tmp/sandbox/srcrepo commit --allow-empty -m "drift"
uv tool install --force "git+file:///tmp/sandbox/srcrepo"
cat $UV_TOOL_DIR/wfctl/lib/python*/site-packages/wfctl-*.dist-info/direct_url.json
```

Install shapes and what each proves:

| Install command | Records | Branch check |
| --- | --- | --- |
| `uv tool install git+<url>` | `vcs_info`, no `requested_revision` | runs |
| `pip install "git+<url>@v0.13.0"` | `requested_revision: v0.13.0` | skipped (pin) |
| `pip install -e .` | `dir_info`, no `vcs_info` | skipped (checkout) |
| index install (future) | no `direct_url.json` | skipped |

## Automated

```bash
pytest                       # whole suite, offline
pytest -m real_version_check # this feature's cases only
ruff check
mypy
```

The suite's autouse fixture stubs this check out for every test that is not
marked `real_version_check`, so new cases must carry that marker or they will
silently test the stub instead of the code.
