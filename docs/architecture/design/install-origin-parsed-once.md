---
status: proposed
---

# The install record is parsed once, and each question reads its own answer from the parse

## Context

Someone who installs wfctl's skills from their own checkout and someone who
installs them from a release are told the same thing today: `Installed from
wfctl 0.21.0`. The version cannot tell them apart, since a checkout reports the
version in its own `pyproject.toml` until the next bump. The same gap shows in
the remedy `wfctl start` prints for a worktree with no install. It prints a bare
`wfctl install-skills`, and in a repository that develops wfctl, following it
installs the release over the checkout being tested.

The answer is already on disk. pip and uv write a PEP 610 `direct_url.json`
for every install that did not come from an index, and it says which of three
places the files came from; a repository at a commit, a directory, or an
archive. `_installed_build()` reads that file for `doctor` and answers a
different question, "can this build drift from its origin?" A checkout cannot
drift, so it answers None for one, and that is still right for `doctor` after
this change.

So three callers now ask about one file.

1. `doctor` asks whether the build can drift, and a checkout is not an answer.
2. `install-skills` asks where the files it just wrote came from, and a
   checkout is the answer that matters most.
3. `wfctl start` asks what command would reinstall the same bundle, and needs
   the checkout's directory to name.

The structural choice is where the file's shapes are enumerated. No
architecture record constrains it; all three questions are wfctl's before and
after.

## Verified

- `cli.py:6078` reads `distribution("wfctl").read_text("direct_url.json")` and
  returns None for a missing distribution, an OSError, an empty file, bad JSON,
  and any payload without `vcs_info`. Those are five causes behind one None.
- The editable install in this worktree records
  `{"url":"file:///…/wt/76-install-provenance","dir_info":{"editable":true}}`.
- The `uv tool install` on PATH records
  `{"url":"https://github.com/aamarin/wfctl.git","vcs_info":{"vcs":"git","commit_id":"44bb2ed…"}}`.
- `uv pip install .` into a scratch venv records `"dir_info":{}`, and installing
  the built wheel records `"archive_info":{}`. Both were run, not read from the
  specification.
- `cli.py:272` imports `_issue_check` inside `start_cmd`, and `_issue_check`
  imports only `_manifest`, `_paths`, and `_tracker`. It cannot import from
  `cli` without loading typer and rich into a module whose `decide` is pure
  (`497-issue-check-is-a-pure-verdict`).
- `tests/test_doctor_version.py:59` stubs `importlib.metadata.distribution`
  rather than `_installed_build`, so a parse that still calls `distribution`
  at call time keeps every existing drift test meaningful.

## Assumed

- Five shapes are the whole set; a repository, a directory, an archive, no file
  (an index), and a file that cannot be read. A new PEP 610 key, or a tool that
  writes `dir_info` beside `vcs_info`, would falsify it. Either is one branch in
  the parse and no change to a reader that does not answer for it.
- The directory in a `dir_info` URL is the source the running bundle came from.
  For an editable install it is the live tree; for a plain directory install it
  is where a snapshot was copied from, which can have moved on since. The line
  names it as a working copy in both cases, since both were copied from a tree
  someone can edit.

## Direct baseline

`_installed_build()` stays exactly as it is. Beside it in `cli.py`, a second
function `_bundle_origin()` reads `direct_url.json` again with its own `try`,
its own `json.loads`, and its own checks for `vcs_info`, `dir_info`, and
`archive_info`, and returns the clause the success line appends. `start_cmd`
calls a third small helper that returns the `dir_info` path, and passes it into
`_issue_check.gather` as an argument, since `_issue_check` cannot import `cli`.
That is roughly twenty lines per reader and no new module.

## Decision

A new module, `_provenance`, holds the parse. `parse(raw)` is pure and turns
the file's text into an `Origin`, a frozen record carrying its kind (repository,
directory, archive, index, or unreadable), its URL, its commit, and whether the
revision was pinned. `read()` fetches the text from the installed distribution
and calls `parse`. Two thin readers sit on top of it.

1. `_installed_build()` in `cli.py` keeps its signature and its docstring. It
   returns a `_Build` for a repository origin and None for every other kind.
2. `describe(origin)` in `_provenance` returns the clause for the success line;
   `aamarin/wfctl @ 4ca1604` for a repository, `working copy
   wt/76-install-provenance` for a directory, and a named clause for the other
   three kinds, so no install prints the bare version alone.

`_issue_check.gather` calls `read()` itself and records the directory, when
there is one, as a fact beside `base_source`. The remedy names it with
`--from`.

What the extra function buys over the baseline is that the five shapes are
written down once. The baseline enumerates them in two functions, and the part
that drifts is the unhappy path; the baseline's second reader would have to
repeat the four ways of failing to read the file that `_installed_build`
already handles, and nothing keeps the two lists level. `parse` also takes a
string, so each shape is tested as one call on a literal, where the baseline
tests each shape through a stubbed `importlib.metadata`.

## Diagram

Baseline:

```
stable    (nothing)

════ process edge: installed metadata ══════════════════════════════

volatile  ┌──────────────────┐  reads  ┌──────────────────┐
          │ _installed_build │───────► │                  │
          │ (doctor)         │         │ direct_url.json  │
          └──────────────────┘         │                  │
          ┌──────────────────┐  reads  │                  │
          │ _bundle_origin   │───────► │                  │
          │ (install-skills) │         └──────────────────┘
          └──────────────────┘
                  ▲ calls
          ┌───────┴──────────┐ passes path ┌──────────┐
          │ start_cmd        │───────────► │ gather   │
          └──────────────────┘             └──────────┘
```

Decision:

```
stable              ┌──────────────────────────────┐
                    │ _provenance.parse (new)      │
                    │ five kinds, pure             │
                    └──────────────────────────────┘
                       ▲          ▲           ▲
                       │ reads Origin (one arrow per reader)
════ process edge: installed metadata ══════════════════════════════
                       │          │           │
volatile  ┌────────────┴─┐ ┌──────┴───┐ ┌─────┴────┐
          │ _installed   │ │ describe │ │ gather   │
          │ _build       │ │ (install │ │ (start)  │
          │ (doctor)     │ │ -skills) │ │          │
          └──────────────┘ └──────────┘ └──────────┘
          ┌──────────────────────────┐  reads  ┌─────────────────┐
          │ _provenance.read (new)   │───────► │ direct_url.json │
          └──────────────────────────┘         └─────────────────┘
```

The two graphs differ by one arrow into the file and one component above the
process edge. In the baseline, two functions read `direct_url.json` and each
carries its own list of shapes and failures, and `gather` reaches the answer
only because `start_cmd` passes it in. In the decision, one function reads the
file, and the three readers depend on the parsed `Origin` rather than on the
file. The change this is built
to absorb is a new shape or a new way of failing to read one; the baseline
touches two functions for it and the decision touches one. No divider is new.
The process edge is the one `497-issue-check-is-a-pure-verdict` already draws
between `gather` and `decide`, and `parse` sits above it for the same reason
`decide` does.

## Considered

- **`_installed_build()` grows a third state.** One function answers both
  questions. It loses because every caller then handles a state that only one
  of them wants. `doctor` is correct to treat a checkout as having no origin to
  compare against, and teaching it to receive and discard a working-copy answer
  makes a correct helper worse for its original caller.
- **The baseline, two readers over one file.** Equally correct today, and
  shorter by a module. It loses on the failure paths; the two readers must
  agree on five shapes and four ways of failing to read one, and nothing checks
  that they do. It also needs `start_cmd` to carry a fact into `gather` that
  `gather` otherwise asks for itself.
- **Inferring the origin from the version string.** Ruled out before any shape
  was drawn. A checkout reports the released version until the next bump, so
  the version cannot separate two installs with different files.
- **Stamping the origin at build time.** It would add a packaging step to
  answer a question PEP 610 already answers, and give up the property
  `_installed_build`'s docstring names; no build-time stamping, no packaging
  change, and no network.

## Consequences

The success line always carries a clause, so no run reads as a release when it
was not one. The remedy `wfctl start` prints names the running wfctl's own
directory when that wfctl is a working copy, so following it installs the same
bundle the refusing wfctl carries.

The cost is one more module, and a reader of `_installed_build` now follows one
call to see what the file can hold. The failure mode is a reader that switches
on `Origin.kind` and misses a kind added later. `describe` handles every kind
explicitly and its tests cover each, which is where that would show.

## Verification

1. `parse` has one test per kind, each on the literal payload recorded in
   Verified.
2. The drift tests in `tests/test_doctor_version.py` pass unchanged, which is
   the evidence that `doctor`'s answer did not move.
3. `uv run wfctl install-skills` in this worktree prints `working copy
   wt/76-install-provenance`, and the released `wfctl install-skills` in a
   scratch directory prints `aamarin/wfctl @` and a commit.
4. A worktree made with `git worktree add`, refused by `uv run wfctl start`,
   ends up holding its own skills after the printed remedy is run exactly as
   printed.

## Log

- 2026-09-29  proposed  — install-skills and the start remedy needed to tell a working copy from a release, and doctor's reader answers a different question about the same file
