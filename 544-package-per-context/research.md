# Research: Check imports against the Context Map

## R1: where the import walk lives

- Decision: The script holds its own copy of the walk in
  `tests/test_architecture_view.py`, extended to resolve dotted names under
  subpackages. The test keeps its copy, as the spec's Assumptions say.
- Rationale: The script has to run with the runner's Python before `uv sync`,
  so it can't import from `tests/`. The test can't import from the script
  without changing what it checks, and the spec leaves that test alone.
- Alternatives considered: Moving the walk into `wfctl/` and importing it from
  both. We didn't choose it because the script would then need wfctl installed,
  and CI's `lint` job runs it before `uv sync`. Replacing the test is a later
  cleanup once the first move rewrites it anyway.

## R2: how strictly the mermaid block is read

- Decision: Every non-blank line inside the `### Context Map` block must be the
  `flowchart` header, a node, or an edge. Anything else fails with its line
  number.
- Rationale: A lenient parser drops a line it doesn't recognize, and a dropped
  arrow is an import the check refuses with no visible cause. A dropped
  outside-party node is worse, because the check would then read its arrows as
  arrows between contexts. Failing on the unknown line puts the cause on screen.
- Alternatives considered: A full mermaid parser. We didn't choose it because the
  page uses three line forms, and the strict reader is the one that fails
  loudly when a fourth appears.

## R3: the baseline's format and grain

- Decision: One plain-text file with two kinds of lines, a placement line
  `_session.py session` and a violation line `_pipeline.py -> _session.py`.
  Comments start with `#`. A violation line names two modules, not a line
  number.
- Rationale: A line number moves with every edit above it, so a line-number
  baseline goes stale on unrelated changes. Two modules is the grain at which a
  move resolves a violation, which is when the line is deleted.
- Alternatives considered: TOML or JSON. We didn't choose either because each
  line must diff as one line, so a reviewer sees one added line as one addition.

## R4: how a person approves an addition

- Decision: `wfctl arch approve-imports` writes the note line `imports approved
  <digest>` on HEAD under `refs/notes/wfctl-review`. The digest is the first 12
  hex characters of the SHA-256 of the sorted added lines. The command refuses
  unless it's run in a terminal, and the guard refuses it from an agent. It
  runs `main`'s copy of the script with `--approvals --json`, which prints the
  additions and the digest, so the digest is computed only by the copy CI runs.
- Rationale: It reuses three protections that already exist. The guard refuses
  `review sign-off` from an agent by pattern, `review sign-off` checks for a
  terminal, and the guard refuses every hand-written `git notes` write and every
  push to a notes ref. CI already fetches that ref for the `review` job. The
  digest ties an approval to the exact additions the person saw, so adding one
  more line after the approval fails again. Those protections refuse an agent
  that runs the command, not one that calls the approval code from its own
  Python. R11 and plan item 6.3.5 state that limit.
- Alternatives considered:
  - The human reviewer reads the diff. We didn't choose it because one added
    line in a long baseline is easy to miss, and nothing records that anyone
    looked.
  - A CODEOWNERS rule on the baseline and the domain page. We didn't choose it
    because GitHub won't let a PR's author approve their own PR, and wfctl has
    one maintainer.
  - A separate notes ref. We didn't choose it because every protection above
    names `refs/notes/wfctl-review`, and a second ref would need each one
    widened.
- Limit: The command ships in every wfctl install, but only a repo whose trunk
  has `.github/scripts/check_imports.py` has anything for it to approve.
  Elsewhere it prints that and exits 1, so the command never reads as an
  approval it didn't write. That includes this branch, whose
  additions the person approves by merging the PR. Making the check available
  to other repos is out of scope.

## R5: what counts as `main`

- Decision: The merge base of `HEAD` and a base ref the caller passes with
  `--base`. `approve-imports` fetches the default branch `origin/HEAD` names
  and passes it, and never uses a `trunk` declared in `wfctl.json`. The
  `review` job passes the repository's default branch, whatever the PR's base,
  and runs in a checkout of the PR's head commit. So a stacked PR gets the
  same merge base, and the same digest, from both. Both print the merge base
  they used, so a mismatch shows on screen.
- Rationale: Comparing against the trunk's tip would count a line `main` deleted
  after the branch was cut as an addition by the branch. The merge base is what
  the branch started from. The caller passes the base because
  `actions/checkout` sets no `origin/HEAD`, and on a `pull_request` run `HEAD`
  is GitHub's merge commit, whose merge base with `main` is `main`'s tip.
- Failure: Any git call that fails ends the run with exit 1. A skipped
  comparison would let a shallow clone or a missing ref turn the approval check
  off with nothing on screen.

## R6: where CI runs it

- Decision: The rule check is a step in the `lint` job. Both modes run again
  in the `review` job, with `main`'s copy of the script (R11).
- Rationale: `lint` runs under `pull_request`, which runs the workflow file as
  the branch has it, so a branch can edit the step to run its own copy or drop
  it. `review` runs under `pull_request_target`, which runs the file as `main`
  has it, for exactly this reason. Both jobs are already required, so the
  ruleset doesn't change.
- Alternatives considered: A new required job under `pull_request_target`. We
  didn't choose it because it needs a ruleset edit and a manual re-apply, as
  `AGENTS.md` describes, and `review` already has the trusted checkout, the full
  history, and the notes fetch this needs.

## R7: the placement of the 39 flat modules

The 2026-11-01 session agreed the placement, but no list was written down. This
one is drafted from each module's docstring, its imports, and the Bounded
Contexts table's Includes column. It needs the user's confirmation at the
walkthrough.

| Context | Modules |
| --- | --- |
| `evidence` | `_evidence`, `_pipeline`, `_declared`, `_stall`, `_completion`, `_verify`, `_plan_review`, `_contract`, `_design_exceptions`, `_spec_store`, `_review`, `_review_config`, `_review_notes`, `_review_gate`, `_record_gate`, `_change`, `_sections`, `_shape` |
| `arch` | `_arch`, `_contexts` |
| `install` | `_bundle`, `_settings`, `_bob_settings`, `_workmux`, `_provenance` |
| `session` | `_session`, `_restart`, `_restart_send`, `_issue_check`, `_archive`, `_spec_copy`, `_copy_out` |
| `guard` | `_guard`, `_hook` |
| `core` | `_paths`, `_io`, `_md`, `_manifest` |
| `tracker` | `_tracker` |
| `design`, `attention` | none, since both are skills and a screen not built yet |

Four calls are judgments rather than readings, and R8 covers a fifth:

1. `_review_gate` and `_record_gate` go in `evidence`, not `guard`. The table
   says the guard runs "the checks a PR must pass" from Evidence and derivation.
2. `_io` goes in `core`. It holds atomic writes, which every context uses, and
   the event log, which belongs to Evidence. It splits when Evidence moves.
3. `_manifest` goes in `core`, though its language is Install's. `_paths`
   imports it, and `core` may not import a context.
4. `_spec_copy`, `_copy_out`, and `_archive` go in `session`. The table puts
   "saving specs before a worktree is removed" there.
5. `_entry.py` is wiring beside `cli.py` (R8).

Under this placement, 8 module pairs break the map, in 11 import statements:

| Importer | Imported | Why it breaks the map |
| --- | --- | --- |
| `_pipeline` (evidence) | `_session` (session) | No arrow from Session to Evidence. This is the R6 reversal. |
| `_contract` (evidence) | `_session` (session) | Same, `record_blocked` |
| `_review_notes` (evidence) | `_session` (session) | Same, `record_outward_action` |
| `_tracker` (tracker) | `_session` (session) | A shared package may not import a context |
| `_spec_store` (evidence) | `_spec_copy` (session) | No arrow from Session to Evidence |
| `_review_gate` (evidence) | `_guard` (guard) | No arrow from the guard to Evidence |
| `_contexts` (arch) | `_design_exceptions` (evidence) | The arrow runs from Architecture records to Evidence, not back |
| `_issue_check` (session) | `_provenance` (install) | No arrow between Install and Session |

The first four reach the event-log functions in `_session`, which move to
Evidence with the event log (E22 on the domain page), so one move resolves them.

## R8: `_entry.py` is wiring

- Decision: `_entry.py` gets the same rule as `cli.py`, and FR-006 names both.
- Rationale: It's the console script. It imports `_hook` and `_restart` so the
  guard and the restart can run without loading `cli`. Since it starts code in
  two contexts, it can't belong to either one without importing the other. The
  walkthrough confirmed this, and found that wiring was a layer only the
  conversation described. So the record's rule 5 is amended to define wiring
  and name both files, and the script keeps them as a closed `WIRING` list.
  The list is part of the script, so adding a name is a change to the script
  and waits for a person's approval.

## R9: the release note's category

- Decision: `addition`.
- Rationale: Every install gains `wfctl arch approve-imports`, which shows in
  `wfctl arch --help`, and a guard refusal that applies to agents in every
  repo. Both are new things a user can notice, even though the check itself
  runs only in wfctl's own repo.
- Alternatives considered: `none`, since the command does nothing outside this
  repo (R4). We didn't choose it because the release script proposes the
  version from the categories, and `none` would hide a new command from the
  release notes.

## R11: which copy of the script runs where

- Decision: `wfctl verify`, the test suite, and the `lint` job run the branch's
  copy of the rule check. The `review` job runs `main`'s copy of both modes,
  over the PR's files as data. `approve-imports` runs `main`'s copy of the
  approval mode. "`main`'s copy" means the default branch's copy, read from git
  rather than from the `trusted` checkout, which for a stacked PR holds the
  parent branch. When the default branch has no copy, the `review` step fails.
  It never runs on this branch's own PR, whose base `review.yml` doesn't have
  the step yet, and the user approves this branch's baseline by merging the PR
  by hand.
- Rationale: The approval check in R4 stops a branch from widening the
  baseline, the map, or the shared packages. Without `main`'s copy, a branch
  could weaken the script or the `lint` step instead, and CI would run the
  weakened version. The `review` job already reads the trunk's `wfctl.json` for
  the same reason (`review-round-cap`). The branch's copy still runs in
  `verify` and `lint`, so the author sees new behaviour before it merges.
- Security: `pull_request_target` hands the job the base repository's token, so
  the job must never run the branch's code. The script reads the branch's files
  with `ast.parse` and its git objects with `git show`, and neither runs any of
  it. Both callers write the trusted copy outside the repository and run it
  with `python3 -I`, since Python otherwise puts the script's directory first
  on the import path, and a branch's `ast.py` or `json.py` there would run
  with the job's token.
- Limit: A branch whose change needs a fix to the script is checked by
  `main`'s copy until the fix merges. The recovery is to land the fix in its own
  PR first. That PR changes the script, which is an addition, so it waits for
  a person to run `approve-imports`. Without that, an agent could loosen the
  script in a PR that changes no imports, merge it, and pass every later
  branch against the weakened copy. The same holds for `review.yml`, so the
  script gates both files CI takes from the default branch. The guard and the
  approval command are wfctl code an agent can edit, and gating every file
  they depend on would gate nearly every PR, so they're a stated limit: they
  stop a shortcut, not an agent set on getting around them, as `review
  sign-off` does today. The person runs the installed `wfctl`. When the
  approval check itself is broken, the maintainer recovers as `AGENTS.md`
  describes for a broken `review` key.

## R10: lazy re-exports

- Decision: Deferred to the first move under #671, as the spec's Assumptions say.
- Rationale: Nothing on this branch writes an `__init__.py`. Ruff 0.15.22
  parses PEP 810's `lazy` imports, and mypy's support is still open in
  python/mypy#20978.
