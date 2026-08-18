# Phase 0 Research: version check — default branch and fork

Every assumption carried over from `design.md` and `spec.md` was tested rather
than reasoned about. Three of the four changed the design.

## R1: Is the installed build's origin readable without packaging changes?

**Decision**: Read PEP 610 `direct_url.json` from the installed distribution via
`importlib.metadata`. No build-backend change, no `setuptools-scm`, no generated
`_commit.py`.

**Evidence**:

```
$ ~/.local/share/uv/tools/wfctl/bin/python -c \
    "import importlib.metadata as m; print(m.distribution('wfctl').read_text('direct_url.json'))"
{"url":"https://github.com/aamarin/wfctl.git",
 "vcs_info":{"vcs":"git","commit_id":"d8688f6eec75c2a8eac3a94f3fc44e25041d22a9"}}
```

**Rationale**: `Distribution.read_text` returns `None` for a missing file rather
than raising, so the absent case needs no exception handling. The file is local;
the check adds no network cost.

**Alternatives considered**: `setuptools-scm` and a build-time `_commit.py` —
both rejected as packaging changes that would entangle this work with issue #2
(distribution name / PyPI). `uv tool list` — rejected: shells out, is
installer-specific, and is unavailable to a pip install.

## R2: Does pip write `direct_url.json`, or only uv?

**Decision**: Both. No installer-specific handling.

**Evidence** — pip 25.3 into a throwaway venv, pinned to a tag:

```
$ pip install "git+https://github.com/aamarin/wfctl.git@v0.13.0"
$ cat …/wfctl-0.13.0.dist-info/direct_url.json
{"url": "https://github.com/aamarin/wfctl.git",
 "vcs_info": {"commit_id": "2232f357…", "requested_revision": "v0.13.0", "vcs": "git"}}
```

**Rationale**: PEP 610 is an interoperability standard; pip has written it since
19.3. The key spacing differs from uv's output, which is irrelevant to a JSON
parser and is the reason the file must be parsed rather than pattern-matched.

## R3: Is a deliberate pin distinguishable from a branch install?

**Decision**: Yes — `vcs_info.requested_revision` is present for a pin and
absent for a branch install. **The fallback proposed in `spec.md` (treat a
commit matching any known release tag as pinned) is unnecessary and will not be
implemented.**

**Evidence**: the R2 install pinned to `v0.13.0` records
`"requested_revision": "v0.13.0"`. The sandbox install from a bare branch URL
(R4) records no `requested_revision` at all.

**Rationale**: This removes a whole speculative code path plus its tests. It also
resolves the item deferred from `/speckit.clarify` — deferred pending exactly
this evidence, which now exists.

**Alternatives considered**: comparing the recorded commit against every tag SHA
in the `ls-remote` response — rejected as unnecessary once `requested_revision`
proved reliable, and wrong in a real case: a branch install whose tip happens to
sit on a release commit would be misread as pinned and never checked again.

## R4: Does the printed reinstall command actually re-resolve the branch?

**Decision**: `uv tool install --force <url>` is sufficient. **`--reinstall` is
not needed** and will not be printed.

This was the assumption flagged as load-bearing: a remedy that silently no-ops
makes the entire report unactionable.

**Evidence** — a sandboxed clone whose branch tip could be moved, with an
isolated `UV_TOOL_DIR` so no real install was touched:

```
1. uv tool install "git+file://…/srcrepo"     → records 271bb2c
2. git -C srcrepo commit --allow-empty        → tip moves to 2d23045
3. uv tool install --force "git+file://…/srcrepo"
   - wfctl==0.15.0 (from …/srcrepo@271bb2c9…)
   + wfctl==0.15.0 (from …/srcrepo@2d23045d…)
```

The recorded commit advanced. uv re-resolved the branch ref without `--refresh`.

**Caveat, stated rather than hidden**: this used a `file://` remote. uv caches
git resolutions per URL and ref, and an HTTPS remote could in principle behave
differently under an unexpired cache. The mitigation is that the manual
verification step in `spec.md`'s Validation Strategy runs against the real HTTPS
origin on this machine, which is currently three commits stale — a live fixture.
If that run fails to advance, `--reinstall` goes back into the printed command
and this section is amended.

**Alternatives considered**: printing `--force --reinstall` unconditionally —
rejected once `--force` proved sufficient; a longer command implies the shorter
one is insufficient, which would be false. `uv tool upgrade wfctl` — rejected:
it does not apply to a pip install, and the README already prescribes
`uv tool install` for upgrades.

## R5: What do the non-VCS install shapes actually record?

**Decision**: Branch on the presence of `vcs_info`, never on the URL scheme.

**Evidence** — editable install into the same venv:

```
{"dir_info": {"editable": true},
 "url": "file:///Users/andremarin/Development/wfctl/wt/21-version-check-master-and-fork"}
```

No `vcs_info`, so the branch comparison is skipped by the FR-004 rule with no
extra logic.

**Rationale**: A `file://` URL is *not* a reliable signal of a working checkout.
The R4 sandbox install was `git+file://` — a genuine git install from a local
clone, carrying a real `vcs_info` and a real branch worth comparing against.
Keying on the scheme would have wrongly skipped it. Presence of `vcs_info` is the
only correct discriminator.

## R6: Which repository answers for tags, and which for the branch?

**Decision**: Settled in `/speckit.clarify` — tags always from the canonical
upstream constant, branch tip from the recorded origin, a second query only when
they differ.

**Supporting evidence**: the current repository state is itself an instance of
the problem. `pyproject.toml` on the branch declares `0.15.0`; the newest tag is
`v0.14.0`. An install from the branch therefore reports a version no tag will
ever match, and the release comparison alone can say nothing useful about it.

## Resulting simplifications

Three code paths were removed from the design by evidence, not by preference:

1. The tag-SHA pin-detection fallback (R3) — the metadata answers directly.
2. The `--reinstall` flag in the printed remedy (R4) — `--force` suffices.
3. URL-scheme special-casing for local installs (R5) — `vcs_info` presence covers it.
