# Doctor reports drift from the default branch, not just from release tags

## Problem Statement

How might we make `wfctl doctor` tell the truth about a build installed from the
default branch, when the version string it reports cannot distinguish that build
from the tagged release it shares a number with?

Concretely: `_check_wfctl_version` (`wfctl/cli.py:1626`) resolves the newest
`refs/tags/vX.Y.Z` and compares it against `importlib.metadata.version("wfctl")`.
The branch tip is never consulted. README:30 tells users to install from the
default branch, so the ordinary install *is* a branch build — one whose
`pyproject.toml` version equals the latest tag while the code is N commits ahead
of, or behind, it. Doctor prints `✓ latest` either way.

Observed twice. First on 2026-08-05: PR #20 merged 7 commits changing pipeline
inference, no bump, and a build predating the merge reported `✓ wfctl 0.13.0 —
latest` while running the replaced `_infer_steps`. Again during this session's
own start: installed `d8688f6`, master at `271bb2c`, doctor said `✓ wfctl 0.14.0
— latest`.

**The stakes changed on 2026-08-17.** #47 and #49 vendored the wf-skills tree
into the wfctl package. `install-skills` now reads `wfctl/agents` and
`wfctl/specify` out of the installed package, and doctor's skills check is a
content-hash comparison against that same bundle. A bundle always matches
itself, so a stale build ships stale skills that the skills check reports as
`✓ current`. The tool-freshness line is now the only signal for either kind of
staleness. This also retires the argument in issue #21 that the skills check
"compares a commit SHA, which is exactly the granularity the tool check lacks" —
that mechanism no longer exists.

## Recommended Direction

Compare the installed build's commit against the tip of the branch it was
installed from, and report that separately from the release-tag comparison.

The build's commit is already on disk and needs no packaging work. PEP 610 has
pip and uv write `direct_url.json` into `.dist-info` for every VCS install, and
`importlib.metadata` reads it locally:

```
distribution("wfctl").read_text("direct_url.json")
→ {"url":"https://github.com/aamarin/wfctl.git",
   "vcs_info":{"vcs":"git","commit_id":"d8688f6…"}}
```

This is what makes the direction cheap. Issue #21 estimated it as a packaging
change — `setuptools-scm`, or a `_commit.py` written by the build backend — and
therefore entangled with #2 (PyPI distribution name). It is neither. Nothing in
`pyproject.toml` changes and #2 stays independent.

The remote half costs no extra round trip. The existing `ls-remote` call takes
`--symref HEAD` alongside the tag glob and returns the default branch's name and
tip in the same response, so the check needs no hardcoded `"master"` and
survives a rename to `main`:

```
$ git ls-remote --symref --refs <url> HEAD 'refs/tags/v*'
ref: refs/heads/master   HEAD
271bb2c…                 HEAD
822d282…                 refs/tags/v0.1.0
…
```

The comparison target is the URL recorded in `direct_url.json`, not the
`_WFCTL_REPO` constant. A build from a fork has a commit that does not exist in
upstream's history, so comparing it upstream reports drift that no reinstall
ever clears — a permanently wrong line is worse than no line. Following the
recorded URL costs one variable and gives a fork developer, who is the likeliest
person to be running an unreleased build, a comparison that means something.

## Output Contract

Five states. The drift line names the skills consequence, because doctor's
skills row will print `✓` while being wrong, so this line has to carry that
meaning on its own.

| State | Output | Exit |
|---|---|---|
| Newer tag exists | `⬆ wfctl 0.14.0 → 0.15.0 available` + upgrade command | 1 |
| Tag current, commit == tip | `✓ wfctl 0.14.0 — latest` (string unchanged) | 0 |
| Tag current, commit ≠ tip | drift block below | 1 |
| Not a VCS install, or pinned | tag line alone | as tag |
| `ls-remote` fails | existing `⚠ couldn't check latest (offline?)` | 0 |

```
✓ wfctl 0.14.0 — latest release
⬆ build behind master — d8688f6 → 271bb2c
    bundled skills are from this build too
    reinstall: uv tool install --force --reinstall git+https://github.com/aamarin/wfctl.git
```

The `✓` line reads `— latest` on its own and `— latest release` when the drift
line follows it: alone it needs no qualifier, and paired it has to contrast with
the line beneath. Keeping the unqualified string identical to today's output
also keeps the existing assertions and README:247 honest for the common case.

Drift exits 1, matching the stale-release branch and the skills check: a build
missing merged pipeline logic is the exact failure PR #20 produced, and CI can
gate on it.

When a newer release exists, the drift line is suppressed. The reinstall that
the upgrade line already prescribes fixes both, and two upgrade lines in one
report is one more than anyone acts on.

`ls-remote` returns a tip SHA, never a distance, so the output says which commit
to which commit and claims no count. The issue's sketch of `7 commits on master
since this build` would need a second call to the GitHub compare API — a new
network dependency to decorate a line that is already actionable.

## Key Assumptions to Validate

All three were tested during `/speckit.plan`. **`research.md` supersedes this
section** — the conclusions below are the outcomes, kept so a later reader does
not re-litigate them or implement an option that evidence removed.

- [x] **`uv tool install --force` actually re-resolves the branch ref.** Proven
      (research R4): a sandboxed clone whose tip was moved re-resolved
      `271bb2c → 2d23045` under `--force` alone. **`--reinstall` is dropped from
      the printed command** — this reverses the "until proven, print both flags"
      instruction that stood here. Confirmation against the real HTTPS origin is
      task T021; the caveat about uv's per-URL ref cache is recorded in R4.
- [x] **pip writes `direct_url.json` for VCS installs too.** Proven (research
      R2): pip 25.3 recorded `vcs_info` plus `requested_revision` for a pinned
      install. No installer-specific handling is needed.
- [x] **`requested_revision` reliably marks a deliberate pin.** Proven (research
      R3): present for a pinned install, absent for a branch install. **The
      tag-SHA fallback described here is dropped, not implemented** — beyond being
      unnecessary, it would misread a branch install whose tip sits on a release
      commit as pinned, and stop checking it forever.

## MVP Scope

**In:**

- `_installed_build() -> tuple[str, str] | None` in `wfctl/cli.py` — `(url,
  commit)` from `direct_url.json`, `None` for PyPI, sdist, editable, or pinned
  installs.
- `_check_wfctl_version` (`cli.py:1626`) extends its `ls-remote` invocation to
  `--symref HEAD 'refs/tags/v*'`, parses the symref line for the default branch
  tip, and emits the drift block per the contract above.
- Tests under the existing `real_version_check` marker
  (`tests/test_install_skills.py:531`; conftest's autouse stub at
  `tests/conftest.py:50` keeps the check off every other test). Four cases, all
  offline, each stubbing the `ls-remote` output and the metadata read:
  behind-tip, at-tip, pinned-revision skip, no-`direct_url` skip.
- README:247, which describes doctor as comparing "installed version vs latest
  release tag" — no longer the whole truth.

**Out:** everything in Not Doing.

Roughly 25 lines in `cli.py` and 60 in tests. The stale `d8688f6` build on this
machine is a live end-to-end fixture: install it, run `wfctl doctor`, confirm the
drift block appears where `✓ latest` used to.

## Not Doing (and Why)

- **Embedding a build commit via `setuptools-scm` or a generated `_commit.py`** —
  PEP 610 already records it. Packaging changes would also drag in #2.
- **Reporting a commit count** — `ls-remote` cannot produce one. A GitHub API
  call for a nicer number is a new network dependency and a new failure mode.
- **Comparing fork builds against upstream** — reports drift no reinstall clears.
- **Release-hygiene-only (direction 2 in issue #21)** — "always bump and tag on
  merge" leaves the failure possible and merely forbidden by policy, and the
  vendored skills make an unnoticed stale build cost more than it used to. Worth
  writing down separately; it is not a substitute for the check.
- **Touching the skills check** — its hash comparison is correct for what it can
  see. Its blind spot is the build itself, which is precisely what this closes.
- **Making doctor fetch or clone** — `ls-remote` on the existing call is the
  whole network budget.

## Open Questions

Both are deferred to `/speckit.specify` deliberately — each is a requirement to
write down, not a design fork.

- Does `wfctl doctor` run anywhere that treats a non-zero exit as a hard failure?
  Drift now exits 1; if some wrapper gates on that, a branch build starts failing
  it. Session start calls doctor for reporting only, which is fine.
- Should the drift line appear when the recorded commit is *ahead* of the tip —
  a local build, or a merge not yet pushed? SHA equality cannot distinguish ahead
  from behind. Current answer: report the same line, since "your build is not
  what the branch says" is true either way, and the wording states two commits
  rather than a direction.
