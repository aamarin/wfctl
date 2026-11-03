# Implementation Plan: Check imports against the Context Map

**Branch**: `544-package-per-context` | **Date**: 2026-11-02 | **Spec**: `spec.md` in this feature folder
**Input**: `spec.md`, `design.md`, and the level-2 record `docs/architecture/contexts-are-packages.md`

## Summary

Currently, nothing checks wfctl's imports against the Context Map, and the code
already breaks it in 8 places. After this change, one script,
`.github/scripts/check_imports.py`, reads the map and the package names from the
domain page, builds the import graph from the source, and fails any import the
map doesn't allow. No module moves on this branch.

A baseline file says which context each unmoved module belongs to and lists the
8 imports that break the map today. The check fails on a baseline line that
matches nothing.

The script has two modes, because the two halves need different trust:

1. The rule check reads only the working tree. `wfctl verify`, CI's `lint` job,
   and the test suite run it with the branch's copy of the script, so the
   author sees a rule change working before it merges. The `review` job still
   runs `main`'s copy, so a fix to the rules lands in its own PR first, and
   that PR waits for a person's approval like any other addition.
2. The approval check compares the branch's baseline, map arrows, shared
   packages, context-to-package pairs, and the two files CI runs the check
   with, against its merge
   base on the default branch, and fails on any addition a person hasn't
   approved. CI's `review`
   job runs it, together with the rule check, using the default branch's copy
   of the script. That job runs under `pull_request_target`, so a branch can't
   change which script runs or drop the step, and it reads the branch's files
   as data without running them.

A person approves an addition with a new command, `wfctl arch approve-imports`,
which the worktree guard refuses when an agent runs it. The command runs
`main`'s copy of the script to list the additions, and stores the approval as a
git note, the same way a review sign-off is stored.

The work has five phases:

1. Phase A updates the domain page, so the check has everything it reads.
2. Phase B writes the rule check and its baseline.
3. Phase C adds the approval check and the approval command.
4. Phase D wires both modes into `wfctl verify`, CI, and the suite.
5. Phase E covers docs and the release note.

## Technical Context

**Language/Version**: Python 3.11+. The script uses the standard library only,
since CI runs it before `uv sync`, as it does the release note check, and the
`review` job runs it with the runner's Python.
**Primary Dependencies**: none new. `ast` for imports, `re` for the domain page.
**Storage**: Two files. `.github/scripts/check_imports.baseline` in the repo,
and one note line per approval under `refs/notes/wfctl-review`, which wfctl
already pushes and fetches.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run
mypy`, then `uv run wfctl verify`, `uv run wfctl check config`, and `uv run
wfctl doctor`
**Target Platform**: macOS and Linux, and the GitHub Actions Ubuntu runner
**Project Type**: CLI, plus one CI script
**Performance Goals**: SC-003, under 5 seconds on wfctl's code. The rule check
parses 42 files once and calls no git. The approval check makes about eight
git calls: the merge base, two `git show` reads and one `git ls-tree` per side,
and one notes read. `approve-imports` adds one fetch before them.
**Constraints**: No module moves. No new runtime dependency. The guard's
start-up cost doesn't change, since the guard gains one regex and no import.
**Scale/Scope**: 42 files under `wfctl/`, 7 contexts, 2 shared packages, 18
arrows on the map of which 6 join two contexts.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. The gates below come from
`AGENTS.md` and the accepted records, and Complexity Tracking records the
substitution.

- [x] Validation plan exists: the spec's Validation Strategy, plus the test
      files named under Project Structure.
- [x] Complexity is justified: one script with two modes, one data file, one
      CLI command, one guard pattern, and one CI step. Research R4 argues the
      approval against two simpler options, and R11 argues the split.
- [x] Ownership is stated: see "Who computes what" below.
- [x] `contexts-are-packages`: the check enforces its five rules, reads the map
      from the domain page, and fails on any import that breaks a rule and isn't
      on the baseline.
- [x] `a-rule-is-expressed-as-a-check`: the Context Map was prose only, and this
      ships it as a check.
- [x] `wfctl-runs-the-verification`: the rule check joins the `verify` list, so
      wfctl records its verdict, and the agent can't certify it passed.
- [x] `review-record-in-git-notes`: the approval is a note line under the same
      ref, so the guard's existing refusal of hand-written notes covers it,
      within the limit item 6.3.5 states.
- [x] `domain-page-names-contexts`: the check takes the context and package
      names from the domain page, as the design checks do.
- [x] `knowledge-placement`: the map stays on the domain page, and the check
      holds no copy of it.

### Who computes what

| Value | Computed by | Why not the other side |
| --- | --- | --- |
| Which contexts may import which | The user, on the Context Map | An import records only that one module needed another, not whether the dependency was meant |
| Which context a moved module belongs to | Its path | A path can't drift from the code it holds |
| Which context an unmoved module belongs to | A placement line the user approved | The flat path says nothing, so a person decides it once |
| Whether an import breaks a rule | The script, from the source and the map | The agent that wrote the import would be grading its own work |
| What counts as an addition, and its digest | `main`'s copy of the script, and only that copy | A branch's copy is code the agent may have edited, so it could list fewer additions than CI checks |
| Whether an addition was approved | `wfctl arch approve-imports`, run by a person | An agent that could approve its own addition could turn any failure green |

## Implementation

### Phase A: the domain page carries what the check reads

1. **`docs/architecture/domain/wfctl.md`** gets a `### Shared packages` list
   under the Bounded Contexts table. It names `core` as a Shared Kernel holding
   the repo, branch, and trunk lookups, and `tracker` as an Anticorruption
   Layer translating between wfctl and the trackers. The list is a
   three-column table, `| Package | Pattern | Holds |`, so the check parses it
   the same way it parses the contexts table.
2. The vocabulary row for Record says "a context's package outside `arch`
   exports no bare `Record`, `record`, `records`, or `load_record`", replacing
   "public module", to match the amended record and FR-012.
3. The page's `Amended` line notes both changes for #544. The record
   **`docs/architecture/contexts-are-packages.md`** is already amended on this
   branch, and this item creates no task. Its rule 5 defines wiring and names
   both files (25786f7). Its approval paragraph lists every kind of addition,
   including a change to the script, and its title names re-exports instead of
   one public module (the plan re-review commit). Its Log notes both
   amendments and the one exception to the approval rule, this branch's own
   baseline.

### Phase B: the rule check and its baseline

4. **`.github/scripts/check_imports.py`** is a standard-library script. With no
   arguments it runs the rule check, in this order, and each step is a function
   a test can call on a fixture:
   1. `read_domain(page)` returns the context-to-package table, the shared
      packages, and the arrows between two contexts. It fails, naming the
      section, when the table, the list, or the `### Context Map` mermaid block
      is missing. Inside the block, every line must match one of three forms: the
      `flowchart` header, a node `ID["Label"]`, or an edge `A -->|"text"| B` or
      `A --> B`. A blank line is skipped, since it holds no node or edge, and
      the real page has one between its nodes and its edges. Any other line
      fails with its line number (FR-010). A Package cell is read with its
      backticks stripped, since the real table writes `` `evidence` ``. A node whose
      label ends in `(outside)` is skipped, and every other label must match a
      context name in the table. A package name may appear only once across the
      contexts table and the shared list.
   2. `read_baseline(path)` returns the placement lines and the violation lines,
      in the format in `contracts/baseline.md`. A malformed line fails with its
      line number.
   3. `module_contexts(root, domain, baseline)` maps every `.py` file under
      `wfctl/` to a context, a shared package, or `wiring`:
      1. A file under `wfctl/<package>/` takes that package's context.
      2. A flat file takes its placement line.
      3. A file on the script's `WIRING` list is `wiring` (research R8,
         FR-006). Wiring is the layer above the contexts that routes a command
         to them and holds no logic of its own. The list is a constant in the
         script, `WIRING = ("cli.py", "_entry.py")`, and no other file is
         wiring. `cli.py` is the full command line. `_entry.py` is the console
         script, which starts the worktree guard and the restart hook without
         loading `cli.py`. The list is part of the script, so adding a name
         changes the script, and that change waits for a person's approval
         (item 6.3.5). That matters because a wiring file may import every
         context. And since the `review` job runs the default branch's copy,
         the list change lands in its own PR before the file it names, like
         any other rule fix.
      4. `wfctl/__init__.py` is skipped while it imports no wfctl module, which
         it doesn't today. Once it does, it fails as unplaced, so a person
         decides where it belongs.
      5. `wfctl/agents/`, `wfctl/specify/`, and `wfctl/contracts/` are package
         data and are skipped. This list is part of the script too, so adding
         a directory to it waits for a person's approval (item 6.3.5).
      6. Any other flat file with no placement line fails (FR-008).
      7. A `.py` file under a directory that is neither a listed package nor
         package data fails as unplaced, the same as a flat file with no
         placement line. So a renamed package or a new `wfctl/util/` can't
         carry modules past the check.
   4. `import_graph(root)` returns one `Import(src, dst, line)` per import of a
      wfctl module, using the walk `tests/test_architecture_view.py` uses:
      function-local imports, `from wfctl import _x`, relative imports, and a
      module bound by an import and then read as an attribute. It resolves
      dotted names, so `wfctl.evidence._status` resolves to that file once the
      package exists (research R1). In `from P import N`, when `P.N` is a
      module, the import targets `P.N`, not `P`. So
      `from wfctl.evidence import _status` is an import of the private module,
      and a fixture test pins it.
   5. `violations(graph, contexts, domain)` applies these rules in order and
      returns each failing import with the rule it broke. The first rule that
      matches decides:
      1. `wiring` importing a module inside a context's package: refused
         (FR-006). A shared package's modules aren't covered by this rule, by
         rule 3 below, or by FR-004, so any module may import them.
      2. Same context, or `wiring` as the importer: allowed.
      3. A shared package as the importer, and a context as the target: refused
         (FR-005).
      4. A shared package as the target: allowed.
      5. No arrow from the target's context to the importer's: refused (FR-003).
      6. An arrow, but the target is a module inside a context's package rather
         than the package itself: refused (FR-004). An unmoved target is
         exempt.
   6. `exported_record_names(root, contexts)` reads each moved package's
      `__init__.py` `__all__` and returns any bare `Record`, `record`,
      `records`, or `load_record` outside `arch` (FR-012). On this branch no
      package exists, so it returns nothing, and its tests run on fixtures.
   7. `stale(baseline, graph, contexts)` returns every placement line whose
      module no longer exists or now sits in a package, and every violation line
      that matches no failing import (FR-009).
   8. `render(failure)` prints each failure in the shapes in
      `contracts/failure-output.md`. That contract governs the output. The
      drawings in `design.md` predate the amended record and name a "public
      module". The process exits 1 on any failure and 0 otherwise.
   9. Both modes take the tree to check from the current directory, never from
      the script's own path, as `check_release_note.py` does. The `review` job
      depends on this, because it runs the trusted copy of the script from
      inside the PR's checkout. A script that found the tree from its own path
      would check the trusted tree and pass every PR.
   10. Every path the script reads from the working tree, the domain page, the
       baseline, and each `.py` file, must be a regular file inside the root.
       A symlink fails, naming the path and never printing its target's
       content. In the `review` job, a PR could otherwise link the baseline to
       `pr/.git/config`, and a failure message that quotes the bad line would
       print that file to the public log.
5. **`.github/scripts/check_imports.baseline`** holds one placement line for each
   of the 39 flat modules research R7 places, and one violation line for each
   of the 8 imports that break the map today. A violation line names a pair of
   modules, not a line number, so an edit elsewhere in a file doesn't make it
   stale.

### Phase C: additions wait for a person

6. **`check_imports.py --approvals --base <ref> [--json]`** runs the approval
   check against the repository in the current directory. `--base` is required,
   so the script never guesses the trunk. It runs these steps, and any git call
   that fails ends the run with exit 1 and git's message. A shallow clone, a
   missing base ref, or no merge base is a failure, never a reason to skip.
   1. Find `git merge-base <base> HEAD`, and print it as the first line of
      output, or as the `merge_base` field with `--json`. When a person's
      approval doesn't turn CI green, they can compare the two merge bases.
      Then read the domain page and the baseline at that commit and at `HEAD`
      with `git show`, and the blob hash of each file on the script's
      `TRUSTED` list (item 6.3.5) at each with one `git ls-tree <commit> --
      <paths>`. `git ls-tree` prints nothing for a missing path and exits
      non-zero only when the call fails, so a missing file and a failed read
      can't be confused.
   2. Read the merge base's page with the same strict map reader. Its contexts
      table needs only the name column, and a missing `### Shared packages`
      list counts as empty, as a missing baseline does. A page that fails to
      parse ends the run with exit 1, naming the commit. Each of these
      allowances can only add to the list of additions, so none of them can
      hide one.
   3. List the additions. Each is something `HEAD` has and the merge base
      doesn't:
      1. A baseline line.
      2. An arrow between two contexts. Arrows compare as pairs of context
         names, so renaming a context adds each of its arrows.
      3. A shared package.
      4. A context-to-package pair. When a context's Package cell changes, the
         new pair is an addition. Otherwise a branch could swap two contexts'
         package names and move every module in both, with no file moving and
         nothing listed. A context whose merge-base row has no Package column
         counts as having no pair, so its first pair is an addition too.
      5. A change to a file CI runs the check with. The script lists these
         as a constant, `TRUSTED`, of two files:
         1. `.github/scripts/check_imports.py`, which holds `WIRING`, the
            package-data list, `TRUSTED` itself, and every rule.
         2. `.github/workflows/review.yml`, which runs the check in CI.

         When a file's blob at `HEAD` differs from its blob at the merge
         base, the addition is `changed <path> <HEAD's full blob hash>`. That
         includes a file absent at the merge base and present at `HEAD`. A
         file present at the merge base and absent at `HEAD` is `deleted
         <path>`. Otherwise an agent could open a separate PR that only
         loosens the script or drops the step from `review.yml`, merge it
         once the review panel has run, and then pass its original branch,
         or every later one, against the weakened copy. The script's
         contents are never read as data, so a `WIRING` written as something
         other than a literal can't hide a name either. Both paths sit under
         `.github/`, so the context moves under #671 don't relocate them.

         These two are the files CI takes from the default branch, so gating
         them is enforced by CI. The local side is not. The worktree guard,
         the hook that installs it, and the approval command are wfctl code
         an agent can edit, and every PR changes some of it. They stop an
         agent from taking a shortcut, such as running `approve-imports` or
         writing a note by hand. They don't stop an agent set on getting
         around them, for example by calling the approval function from its
         own Python, or by merging a PR that weakens the guard. That's the
         protection `review sign-off` gives today, and the record and FR-015
         state it as a limit.
   4. Hash the sorted additions into a 12-character digest, and look for the
      note line `imports approved <digest>` on any commit in
      `<merge-base>..HEAD`, under `refs/notes/wfctl-review`. No match fails, and
      the message lists each addition and the command to approve it. The
      message also says that a person decides whether to keep an addition, and
      that an agent may instead revert it and make the change some other way,
      such as moving code into the importing context
      (`contracts/failure-output.md`). Any later
      edit to the additions changes the digest, so an approval covers exactly
      what the person saw (research R4).
   5. With `--json`, print the additions and the digest instead of checking for
      a note. This is the interface `approve-imports` reads, so the digest is
      computed in one place.
7. **`wfctl/_review_notes.py`** gets `IMPORTS_APPROVED_PREFIX = "imports
   approved "`, `approve_imports(repo_root, digest)`, and
   `run_approve_imports(repo_root)`, which carries every step in item 8,
   the terminal check included. `approve_imports` itself repeats the terminal
   check, so an agent calling it from a one-line script with no terminal is
   refused. That narrows the gap item 6.3.5 states, and doesn't close it.
   `approve_imports` appends the line to HEAD's note, sends the ref to
   `origin` the way a sign-off does, and then calls the existing `rerun`,
   since pushing a notes ref starts no CI run and the approval check runs in
   the `review` job. A test pins the script's copy of the prefix against this
   constant, since the script can't import wfctl.
8. **`wfctl/cli.py`** gets `wfctl arch approve-imports`, which calls
   `run_approve_imports` and holds no logic of its own. The command refuses
   unless stdin and stdout are both a terminal, as `review sign-off` does. It
   then:
   1. Refuses when wfctl's own source is inside any worktree of the
      repository it runs in. It compares the package's `__file__` against
      each path in `git worktree list --porcelain`, both resolved, since
      macOS reports `/tmp` and `/private/tmp` for the same folder. Under `uv
      run wfctl` in the branch's worktree, the command would be the branch's
      own code, which an agent may have edited to show fewer additions than
      the digest it writes. This refusal catches an honest mistake only,
      since a tampered branch can delete it. What protects the person is
      running the installed `wfctl`, which the refusal and `AGENTS.md` both
      say. An installed `wfctl` has the command once a release ships it, or
      once the user reinstalls from `main` with `uv tool install --force`
      after this branch merges.
   2. Refuses on a detached `HEAD`, since it names no branch to compare
      against, and says to check out the PR's branch first. Then it fetches
      `origin/<current branch>` and refuses unless `HEAD` equals it,
      so the approval is written on the commit CI checks. Otherwise the check
      stays red with a matching merge base and nothing on screen saying why.
      It compares against the branch of the same name rather than the
      configured upstream, since a branch created from `origin/main` often
      tracks `origin/main`. When `origin/<current branch>` doesn't exist, it
      refuses and says to push first. Otherwise the refusal says whether to
      push or pull.
   3. Finds the default branch from `origin/HEAD` and fetches it with `git
      fetch origin <branch>`, so a stale local copy, such as after a stacked
      parent merged, doesn't give a different merge base from CI's. It exits 1
      when `origin/HEAD` is unset or the fetch fails. It never uses a `trunk`
      declared in `wfctl.json`, because the `review` job uses the default
      branch too, and two bases would give two digests.
   4. Reads `main`'s copy of the script with `git show
      origin/<branch>:.github/scripts/check_imports.py` into a file under
      `tempfile.mkdtemp()`, outside the repository, and runs it with
      `sys.executable -I` and `--approvals --base origin/<branch> --json`.
      `-I` keeps Python from putting the file's directory or the working
      directory first on the import path, so a branch's own `ast.py` or
      `json.py` can't load in place of the standard library. It never runs
      the branch's copy, because the person runs this command outside the
      guard, and the branch's copy is code an agent may have edited.
   5. Prints the merge base it used and each addition. For each changed file
      on the `TRUSTED` list, it also prints `git diff --no-ext-diff
      --no-textconv <merge-base> HEAD -- <path>`, so the person reads what
      changed rather than a hash. Then it asks the person to confirm, and
      calls `approve_imports` with the digest the script printed.
   6. When the trunk has no copy of the script, it prints that there's nothing
      on the trunk to check additions against, and that the first baseline is
      approved by merging its PR by hand (item 12). It exits 1, so the command
      never reads as an approval it didn't write.
9. **`wfctl/_review_gate.py`** gets `_APPROVE_IMPORTS =
   re.compile(r"\barch\b.*\bapprove.?imports\b", re.S)` beside `_SIGN_OFF`, with
   a matching refusal line. The guard refuses it the same way it refuses
   `review sign-off`. The guard's existing refusal of any `git notes` write
   stops an agent from writing the line with a `git notes` command. Neither
   refusal sees an agent that calls the approval function from its own
   Python. Item 7's terminal check narrows that, and item 6.3.5 states what's
   left as a limit.

### Phase D: where each mode runs

10. **`wfctl.json`** adds `["uv", "run", "--frozen", "--extra", "dev", "python",
    ".github/scripts/check_imports.py"]` to `verify`. This is the rule check, so
    `wfctl verify` passes on this branch before anyone approves the baseline.
11. **`.github/workflows/ci.yml`** adds a step to the `lint` job that runs the
    branch's copy of the rule check. It needs no history and no notes.
12. **`.github/workflows/review.yml`** adds a step to the `review` job, after
    the notes fetch. The job already checks out the PR's head commit as `pr`,
    with full history. The step works against the repository's default branch,
    whatever the PR's base is, taking its name from
    `github.event.repository.default_branch` through `env` as the existing step
    takes `BASE_REF`:
    1. It checks that `origin/$DEFAULT` resolves, with `git -C pr rev-parse
       --verify "origin/$DEFAULT^{commit}"`, and fails if it doesn't.
    2. It writes the default branch's copy of the script to a file under
       `$RUNNER_TEMP`, outside both checkouts, with `git -C pr show
       "origin/$DEFAULT:.github/scripts/check_imports.py"`. When that fails,
       the step fails.
    3. It runs that file with `python3 -I` in `pr`, first with no arguments and
       then with `--approvals --base "origin/$DEFAULT"`. `HEAD` there is the
       PR's head commit, not GitHub's merge commit, so the merge base is where
       the branch left the default branch.

    Using the default branch rather than the PR's base keeps CI and
    `approve-imports` on the same merge base, so a stacked PR gets the same
    digest from both, and the script that runs is the default branch's even
    when the base is a parent feature branch. The workflow file itself still
    comes from the PR's base, as for the existing review check, so a stacked
    PR's step is only as trusted as its parent's `review.yml`.

    The script only reads `pr`'s files and git objects as data, and `ast.parse`
    runs nothing. `-I` and the file's location outside `pr` keep a PR's own
    `ast.py` or `json.py` from loading in place of the standard library. So
    the job keeps its rule that it never runs code from `pr/`.

    The step has no pass for a default branch without the script. It never
    runs on this branch's own PR, because that PR targets `main`, and
    `pull_request_target` runs `main`'s `review.yml`, which doesn't have the
    step yet. The step and the script reach `main` in the same merge, so from
    then on a missing copy means someone deleted or renamed it, and failing
    is right. The only PRs that meet a default branch without the script are
    ones stacked on this branch before it merges. They fail the step until it
    merges, and pass once their `review` check runs again. The ruleset
    already requires `review`, so it doesn't change.
13. **`tests/test_import_check.py`** loads the script the way
    `tests/test_release_note_check.py` does. It runs the rule check over the
    real tree with the shipped baseline (SC-001), then runs one test per
    acceptance scenario in the spec against fixture trees and a fixture domain
    page under `tmp_path`. The fixtures build real subpackages, so the
    moved-package rules are tested before any context moves. One test runs the
    script from a directory other than the tree it checks, the way the
    `review` job does, and one gives it a symlinked baseline. The approval
    check is tested on fixture git repositories with their own notes, never on
    this repository's history, so the suite passes in CI's shallow `test`
    checkout. `tests/test_review_notes.py` covers `run_approve_imports` on the
    same kind of fixture: it refuses from a worktree's own source, refuses
    when `HEAD` differs from the upstream, and prints a diff for a changed
    trusted file. `tests/test_review_workflow.py` already checks that the
    `review` job runs nothing from `pr/`, and it gains tests that the new
    step takes the default branch through `env`, writes the script under
    `$RUNNER_TEMP`, and runs it with `python3 -I`, and that the `lint` job
    runs the branch's copy.

On this branch, `wfctl verify` and CI's `lint` pass once Phase B lands. The
`review` job's new step doesn't run on this PR, since `main`'s `review.yml`
doesn't have it yet, and the existing review check runs as before.

This branch's additions can't go through `approve-imports`, since there's no
copy on `main` to compute a digest with. So the user approves them by merging
this PR by hand, from their own terminal, and the agent doesn't merge it.
Before merging, the user checks the 39 placement lines against research R7,
which the walkthrough confirmed. The 8 violation lines need no such check,
because `stale()` fails any violation line that matches no failing import.
This branch also adds the script and changes `review.yml`, the two trusted
files, so the user reads both diffs before merging too. The merge records that
the user signed off on the baseline and both files. It doesn't prove they
read every line, and the plan doesn't claim it does. FR-015 and the record's
Log name this one exception. Every later branch goes through
`approve-imports`.

### Phase E: docs and the release note

14. **`AGENTS.md`** gets a short section. It says what the check enforces, how
    to read a failure, and that a new arrow, baseline line, shared package,
    context-to-package pair, or any change to a file on the script's `TRUSTED`
    list waits for `wfctl arch approve-imports`. It says the person runs the
    installed `wfctl`, never `uv run wfctl` in a worktree, and reinstalls it
    from `main` once this branch merges. It also says how to recover when
    `main`'s copy of the script blocks a branch:
    1. Land the script fix in its own PR first. That PR changes the script, so
       it waits for a person to run `approve-imports`. Once it merges, the
       branch that needed the fix passes.
    2. When the approval check itself is what's broken, recover as for a broken
       `review` key. The maintainer removes `review` from the ruleset's required
       checks, merges the fix, and applies the ruleset again.
15. **`changes/544.addition.md`** says that every install gains `wfctl arch
    approve-imports` and a guard refusal for it, and that wfctl's own CI now
    checks its imports against the Context Map. Research R9 explains the
    category.

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── baseline.md
│   └── failure-output.md
└── tasks.md             # /speckit.tasks, not this step
```

### Source code

```text
.github/scripts/check_imports.py         # new
.github/scripts/check_imports.baseline   # new
.github/workflows/ci.yml                 # rule check step in `lint`
.github/workflows/review.yml             # both modes, `main`'s copy, in `review`
docs/architecture/domain/wfctl.md        # shared packages list, vocabulary row
docs/architecture/contexts-are-packages.md  # rule 5 defines wiring; Log
wfctl/_review_notes.py                   # approval line, writer, rerun
wfctl/_review_gate.py                    # guard refusal
wfctl/cli.py                             # `arch approve-imports`
wfctl.json                               # `verify` entry
tests/test_import_check.py               # new
tests/test_review_gate.py                # refusal cases for the new command
tests/test_review_notes.py               # `run_approve_imports` refusals and diff
tests/test_review_workflow.py            # the new `lint` and `review` steps
AGENTS.md
changes/544.addition.md
```

**Structure Decision**: The flat layout stays. The script lives beside
`check_release_note.py`, since both are repo checks that CI runs before
`uv sync`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution, so the gates come from `AGENTS.md` and the records | The repo has no `.specify/memory/constitution.md` | A gate with no source is decorative |
| A person-only command and a guard pattern, not just a script | FR-015 requires that only the user approves an addition. The command and the guard refuse an agent that runs the command, within the limit item 6.3.5 states | Research R4: a reviewer reading the diff misses an added baseline line, and a CODEOWNERS rule needs a second GitHub account |
| The check runs in two jobs with two copies of the script | The `lint` job runs the workflow as the branch has it, so a branch could change which script runs there | Research R11: running only in `lint` leaves the approval one `ci.yml` edit away. Running only in `review` would give the author no early sight of a rule change, which the branch's copy in `lint` and `verify` provides. Either way, a rule fix lands in its own PR first |

## What the walkthrough settled

The user walked through this plan on 2026-11-02, and these items came out of it:

- The placement of the 39 flat modules in research R7 stands. `_manifest` and
  the event log stay in `core` for now. `_manifest` can move to `install` once
  `_paths` stops reading `spec_root` and `arch_root` from it, and the event log
  moves when Evidence does.
- Wiring is its own layer above the contexts, with a closed list of two files,
  `cli.py` and `_entry.py` (Phase B item 4.3.3). The record's rule 5 is amended
  to define it, and FR-006 already names both files.
- This branch's own additions are approved by the user merging the PR by hand
  (Phase D, closing paragraphs). FR-015 names the exception.
- The `unapproved-addition` failure says a person decides, and what an agent
  may do instead (Phase C item 6.4).

Spec and contract edits made with this revision: FR-015 names the bootstrap
exception and lists context-to-package pairs and wiring names as additions,
FR-006 says what wiring is, FR-008 covers a file under an unlisted directory,
and `contracts/failure-output.md` updates the unapproved-addition block.

The plan re-review that followed found PR-024 to PR-029, and this revision
answers them:

1. Any change to the script is one addition, which replaces the `WIRING`
   addition and also covers the package-data list and the rules (PR-024).
   FR-015, research R8 and R11, the data model, the failure contract, and the
   record now say so.
2. The `review` step fails whenever the default branch has no script, and it
   checks the ref before reading the file. The bootstrap pass and its
   `wfctl.json` read are gone, since the step never runs on this branch's own
   PR (PR-025).
3. Both runs of the trusted copy write it outside the repository and run it
   with `-I` (PR-026).
4. `approve-imports` fetches the default branch first, never uses a declared
   `trunk`, and prints its merge base, as the script does in CI (PR-027).
5. Research R4 says `approve-imports` exits 1 with no copy on the trunk
   (PR-028).
6. The record's title and approval paragraph now match FR-015, and Phase A
   item 3 creates no task (PR-029).

The next re-review found PR-030 to PR-033, and the revision after it answers
them:

1. The script's addition widens to a closed `TRUSTED` list of six files: the
   script, `review.yml`, the three guard modules, and `_review_notes.py`.
   `cli.py` stays off the list and is a stated limit (PR-030).
2. `approve-imports` refuses to run from a worktree's own source, and its
   logic moves into `_review_notes.py` (PR-031).
3. `approve-imports` prints a diff for each changed trusted file, and an
   addition carries the full blob hash (PR-032).
4. `approve-imports` refuses unless `HEAD` equals the branch's upstream
   (PR-033).

The third re-review found PR-034 to PR-040. Each widening of the list exposed
more wfctl code the guard depends on, so this revision draws the line at what
CI enforces instead:

1. `TRUSTED` holds only the script and `review.yml`, the two files CI takes
   from the default branch. The guard, its hook, and the approval command are
   stated as a limit in item 6.3.5, FR-015, and the record: they stop an agent
   taking a shortcut, not one set on getting around them, the same as `review
   sign-off` today (PR-034, PR-035).
2. `approve_imports` repeats the terminal check, and item 9 no longer claims
   the hand-written route is closed (PR-036).
3. The worktree-source refusal compares resolved paths and is described as
   catching an honest mistake only (PR-037).
4. The `HEAD` check compares against `origin/<current branch>` and refuses
   when it doesn't exist (PR-038).
5. FR-015, the record's Log, and the bootstrap paragraph cover the two
   trusted files this branch changes (PR-039).
6. A file absent at the merge base counts as changed, and both trusted paths
   sit outside the #671 moves (PR-040).
