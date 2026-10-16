# Research: release automation

Every decision below was settled by reading this repository or by running
towncrier 26.9.0 in a scratch folder on 2026-10-15. Nothing in Technical Context
was left open.

## 1. Where the two scripts live, and what runs them

- Decision: both scripts are standalone Python files under `.github/scripts/`,
  `check_release_note.py` and `release.py`, next to `check_wheel_contents.py`
  and `check_installed_tree.py`. The check uses the standard library only.
- Rationale: the record says release automation is this repository's process
  and not something wfctl ships, so nothing goes under `wfctl/`. `layer-model`
  keeps `wfctl/agents/` for what ships, and `.github/scripts/` is already where
  this repository keeps scripts that only its CI and its maintainer run.
- Alternatives considered: a `wfctl release` subcommand, which would ship the
  process to every project that installs wfctl and break SC-005. A shell script,
  which can't read `pyproject.toml` without a TOML parser and would grep for the
  version, the exact bug the tag job's comment warns about.

## 2. How `verify` and CI run the check

- Decision: `wfctl.json` gains
  `["uv", "run", "--frozen", "--extra", "dev", "python", ".github/scripts/check_release_note.py"]`.
  CI gains a `release-note` job, on pull requests only, that checks out with
  `fetch-depth: 0` and runs `python3 .github/scripts/check_release_note.py`
  with no `uv sync`.
- Rationale: the `verify` entry matches the three already there, and `uv run`
  guarantees Python 3.11 or later, where `tomllib` exists. A bare `python3` on a
  Mac can be the system 3.9. In CI, the runner's own Python is new enough, which
  the tag job already relies on for `tomllib`, and the check needs no
  dependency. The full history is needed because the default checkout has no
  `origin/main` to compare against.
- Alternatives considered: a step inside the `lint` job, which would make that
  job fetch the whole history for one step. Running the job on pushes to `main`
  too, where it can only pass.

## 3. How the check finds the branch and what it added

- Decision: the branch name is `GITHUB_HEAD_REF` when set and not empty (a pull
  request in CI), then `git rev-parse --abbrev-ref HEAD`, then `GITHUB_REF_NAME`
  when HEAD is detached. The base is `git merge-base origin/main HEAD`, falling
  back to `main`, and failing with a message when neither exists. The added
  notes are
  `git diff --name-only --no-renames --diff-filter=A <base> HEAD -- changes/`.
  A branch named `release/v<X.Y.Z>` passes with no note when `pyproject.toml`
  at `HEAD`, read with `tomllib`, carries version `X.Y.Z`, and fails naming
  both versions when it doesn't.
- Rationale: in a pull request run, `actions/checkout` checks out a detached
  merge commit, so only `GITHUB_HEAD_REF` carries the branch name. Diffing from
  the merge base means a branch that merged `main` in is judged on its own
  changes only. A stacked branch's diff from `main` includes its parent's note,
  so it still needs one for its own issue, as User Story 1 scenario 4 requires.
  `--no-renames` makes a renamed note count as added. A release branch deletes
  every note and adds none, so it needs its own rule, and tying the name to the
  version keeps `release/` from being a prefix any branch can use to skip the
  note. An empty `GITHUB_HEAD_REF` counts as unset, because GitHub sets it to
  the empty string on push runs.
- Alternatives considered: diffing against the pull request's base branch,
  which for a stacked pull request is the parent and would let the check differ
  between CI and `wfctl verify`.

## 4. Where the category list lives

- Decision: the four categories are the four `[[tool.towncrier.type]]` tables
  in `pyproject.toml`, `none` included, in the order the draft prints them. The
  check reads them with `tomllib`. The release script builds the draft from a
  temporary copy of `changes/` that leaves out the `none` notes.
- Rationale: one list, read by both the check and towncrier, which is what the
  level 3 record decided. Leaving `none` out of towncrier's list was measured
  as an alternative: `towncrier build` silently skips a note whose category
  isn't configured, so it would also work for the draft. It would put `none` in
  a second list inside the check, and `towncrier create 571.none.md` would
  refuse an unknown category.
- Alternatives considered: deleting the `none` notes before the build, as the
  record words it. That changes the working tree before Andre confirms, which
  FR-015 forbids, so the copy is how the record's step is carried out.

## 5. What towncrier renders, and what the script keeps

- Decision: `[tool.towncrier]` sets `directory = "changes"`,
  `filename = "CHANGELOG.md"` (never written, it only selects the markdown
  template), and `issue_format = "#{issue}"`. The script runs
  `sys.executable -m towncrier build --draft --version <v> --config
  <repo>/pyproject.toml --dir <temporary copy>`, keeps the text after
  towncrier's "What is seen below is what would be written." line, drops the
  first line that starts with `# ` whatever follows it, and drops a line that
  reads exactly `No significant changes.`.
- Rationale: measured output is a `# 0.24.0 (2026-10-15)` title, then a
  `## Behaviour changes` heading per category with `- <text> (#542)` lines, and
  a `+` note renders with no number. GitHub links `#542` in a release body on
  its own, so the plain format reads correctly on the release page and in
  `git log`. The release page already shows the version, so the title is
  dropped, and the draft no longer depends on which version Andre confirms.
  The title's text depends on the invocation: with `--dir` pointed at a folder
  whose `pyproject.toml` names the project, it reads `# wfctl 0.23.1 (…)`, and
  with `--config` and `--dir` as above it reads `# 0.24.0 (…)`. Matching on the
  leading `# ` rather than the whole shape drops either. towncrier prints `No
  significant changes.` when there are no fragments, which is User Story 2
  scenario 8. Dropping it leaves the draft empty, so Andre has to write the
  release notes before saving, and the line can't reach a release page.
- Alternatives considered: `title_format = false`, which moves the category
  headings up to `#`. A full markdown link per issue, which reads badly in
  `git log`.

## 6. Editing the draft without losing its headings

- Decision: the script writes the draft to a temporary file, opens it with
  `git var GIT_EDITOR`, and commits with `git commit --cleanup=verbatim -F
  <file>`. An empty file after editing aborts.
- Rationale: every section heading starts with `#`. Git's default cleanup when
  it opens its own editor strips lines starting with `#` as comments, so
  editing the draft through `git commit -e` would delete every heading without
  a word.
- Alternatives considered: `git commit -e` with `--cleanup=whitespace`, which
  keeps the headings but also keeps git's own comment block in the body.

## 7. Finding the merges that came with no note

- Decision: the script reads
  `git log --merges --format='%H %s' <last tag>..HEAD`, keeps subjects matching
  `Merge pull request #<n> from <owner>/<branch>`, and lists a merge when
  `git diff --name-only --no-renames --diff-filter=A <merge>^1 <merge> -- changes/`
  is empty.
- Rationale: the clarified FR-009. Every merge since v0.23.0 has that subject,
  and the merges of `origin/main` into a branch don't, so they drop out. A child
  merged into its parent is its own merge commit in the range, so it is judged
  on its own note. A squash or rebase merge leaves no merge commit and would be
  missed, which is why the repository allows merge commits only (section 11).
  The last release's merge is never in range, because its tag sits on that
  merge and the range starts after it.
- Alternatives considered: matching the issue in the branch name, rejected in
  clarify.

## 8. Reading the release body in the tag job

- Decision: when the tag or the release for `v$v` is missing, the tag job first
  finds the release commit with
  `git log -1 --no-merges --format=%H --fixed-strings --grep "chore(release): cut $v" HEAD`,
  confirms the subject is exactly that, reads `pyproject.toml` at that commit
  with `tomllib` and confirms its version is `$v`, and writes its body with
  `git log -1 --format=%b`. Any of the three failing, or an empty body, fails
  the job with a message saying which, before anything is tagged. Only then does
  it tag and run `gh release create "v$v" --notes-file`. There is no fallback
  to `--generate-notes`. The tag stays on the commit the job ran on, as today.
- Rationale: the release commit isn't the commit the job runs on, since the
  release now merges as a merge commit. Finding it by subject and confirming
  the version with `tomllib` is the tag job's own rule against grepping for
  `^version =`, which would match any later commit that adds or removes such a
  line. `--no-merges` is needed because this repository's merge commits carry
  the pull request title in their body (`merge_commit_message=PR_TITLE`), so
  the release pull request's merge also matches the grep and would be found
  first. Checking before tagging matters because the tag is what `doctor` and
  `uv tool install` upgrade to, so a tag with no release is a half-published
  release. The fallback was there for a release cut before this feature, and
  v0.19.0 to v0.23.0 are already published, so it would never run for them.
  A failed job is visible, and is fixed by publishing that one release by hand.
  The gate on test, wheel, and lint is unchanged.
- Alternatives considered: tagging the release commit rather than the commit
  the job ran on. Test, wheel, and lint ran on the second one, so moving the tag
  would publish a commit the gate never saw.

## 9. The towncrier pin

- Decision: `towncrier>=26.9,<27` in the `dev` extra, locked in `uv.lock`.
- Rationale: towncrier uses calendar versions, so a minor pin like ruff's would
  expire within a month. The assumption the record names is that the file name
  format holds across the versions the pin allows. A year's range is short
  enough for that to be checked at the next `uv lock --upgrade`.
- Alternatives considered: no upper bound, which lets an upgrade change the
  file name format under notes already on `main`.

## 10. Testing the scripts

- Decision: `tests/test_release_note_check.py` and `tests/test_release_script.py`
  load the scripts with `importlib` and run them against git repositories made
  in `tmp_path` with `git init -b main`, each with a bare repository in
  `tmp_path` as its `origin`. The release script takes the lock command, the
  editor, and the pull request command as parameters, so tests replace `uv
  lock` and `gh pr create` with stubs that record their arguments, and set the
  editor to a command that leaves or rewrites the draft. The pull request stub
  can only see arguments, so the tests assert `--fill` and a branch holding one
  commit whose body is the draft. That gh fills the description from a lone
  commit's body was read in gh 2.91.0's source rather than tested here. The
  check's tests
  clear `GITHUB_HEAD_REF` and `GITHUB_REF_NAME` in an autouse fixture, and one
  test sets them on purpose.
- Rationale: CI sets `init.defaultBranch master`, so a test that relies on the
  default branch name breaks there. `uv lock` resolves over the network and
  costs seconds. towncrier is in the `dev` extra, so the tests run the real
  build. A bare `origin` lets the push run for real. GitHub sets
  `GITHUB_HEAD_REF` for every step of a pull request run, the test suite's
  included, so without the fixture every check test would read the pull
  request's branch name instead of its scratch repository's.
- Alternatives considered: shelling out to the scripts as subprocesses for
  every case, which hides which function failed.

## 11. Cutting the release through a pull request, and protecting `main`

- Decision: after both prompts, the release script creates
  `release/v<version>` from `main`, makes the release commit there, pushes the
  branch with `git push -u origin release/v<version>`, opens the pull request
  with `gh pr create --base main --head release/v<version> --fill`, which takes
  the title and description from the branch's one commit, prints its URL, and
  switches back to `main`. Protection is a ruleset committed as
  `.github/rulesets/main.json` and applied with `gh api -X POST
  repos/{owner}/{repo}/rulesets --input .github/rulesets/main.json`. It targets
  `refs/heads/main`, has no bypass actors, and carries four rules: `deletion`,
  `non_fast_forward`, `pull_request` with zero required approvals, and
  `required_status_checks` with `test (3.11)`, `test (3.13)`, `wheel`, `lint`,
  and `release-note`. Merge commits only is a repository setting, applied with
  `gh api -X PATCH repos/{owner}/{repo} -F allow_squash_merge=false -F
  allow_rebase_merge=false`. AGENTS.md gives both commands, and Andre runs them
  once this feature has merged.
- Rationale: with no bypass, a push straight to `main` is refused for Andre
  too, so the release has to arrive as a pull request. Zero approvals, because
  Andre is the only reviewer and GitHub doesn't let an author approve their
  own pull request. A ruleset rather than classic branch protection, because a
  ruleset's JSON is the same document the API takes, so the file in the
  repository is what is applied and can be reviewed like any other change. The
  repository had no ruleset on 2026-10-15. The script opens the pull request as
  Andre, from his machine, so CI runs on it. A pull request opened by a
  workflow with the default `GITHUB_TOKEN` would start no CI run, which is the
  catch the evaluation found in release-please. The status check names are the
  job names GitHub reports, with the matrix value for `test`. Applying it waits
  until this feature has merged, because `release-note` doesn't report on any
  pull request before then, and a required check that never reports blocks
  every merge.
- Alternatives considered: a bypass for Andre, which with one person merging
  would also let every red merge through. Having the tag job or a workflow open
  the release pull request, which needs a personal access token or a GitHub
  App to get CI to run on it. Requiring branches to be up to date before
  merging, which would make every open pull request into `main` re-run CI after
  each merge, for the rare case in the spec's edge cases where a change merges
  while a release pull request is open.
