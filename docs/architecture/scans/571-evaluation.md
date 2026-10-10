# Evaluation scan — #571

An `evaluation`, the kind of scan file with no pipeline step behind it. This
branch ran none, and what needs to reach a reviewer is the comparison and the
count behind it. `writing-a-scan-file` governs what a section carries. The
coverage rows are this evaluation's own, taken from the issue's Scope list and
its three costs before the tools were compared. The subject count in row A was
run before this file was written.

## Session 2026-10-10

- Verdict: **satisfied**
- Scope: the three candidates the issue names (release-please,
  python-semantic-release, and a script owned by this repo), measured against
  the releases 0.22.0 and 0.23.0. No candidate was installed or run. The tool
  rows rest on each tool's documentation, cited per finding.
- Ran against: 120 commits in `v0.22.0..v0.23.0` (102 non-merge, 18 merge),
  the 17 pull requests merged in that window, and the release commit bodies of
  0.22.0 and 0.23.0.
- Versions: release-please 17.11.2 and release-please-action 5.0.0,
  python-semantic-release 10.7.0, wfctl 0.23.0.
- Detail: no `FEATURE_DIR` artifact. This branch ran no pipeline step, so
  everything the evaluation established is here.

**The recommendation is a release script owned by this repo, with the person
cutting the release still making the version call.** Neither generator can
produce the part of the notes that matters most, the list of what changes for an
existing consumer without them doing anything. That list is not recorded
anywhere at merge time today: none of the five items 0.23.0 led with was marked
as a feature or a breaking change in its commit subjects, and one of the five
was marked breaking in its pull request. A generator reading either source
would have published notes without the list, and would have computed the right
version for 0.23.0 only because four unrelated feature commits happened to be
in the window.

What the script automates is the rest of the job, which is where the dropped
steps came from: reading every merged pull request, bumping the version,
relocking, and writing the notes once. The CI tag job keeps its gate, and
publishes the release commit's body as the GitHub release instead of a
generated pull request list.

### Coverage

| Pass | Status |
| --- | --- |
| A · A strict Conventional Commits parse of every subject since v0.22.0 | Clear (0 of 102 misread; finding 1) |
| B · Whether subjects carry the changes a consumer sees without acting | Clear (they do not; finding 2) |
| C · Whether the pull request template carries them instead | Clear (1 of 5; finding 3) |
| D · release-please against the four requirements | Clear (finding 4) |
| E · python-semantic-release against the four requirements | Clear (finding 5) |
| F · A script owned by this repo against the four requirements | Clear (finding 6) |
| G · The tag job's gate under each candidate | Clear (findings 4, 5, 6) |
| H · Merged work sitting unreleased | Deferred (finding 7) |
| I · Whether the choice rules out publishing to PyPI | Clear (none of the three does; finding 8) |

The four requirements in rows D to F are the issue's Scope list:

1. The version is right, including the minor-versus-patch call.
2. The notes lead with what changes for an existing consumer without them doing
   anything.
3. `uv.lock` is relocked in the release commit, since CI's `uv lock --check`
   fails a release that leaves it behind.
4. Nothing is tagged until test, wheel, and lint pass on that commit.

## Finding 1 — Every non-merge subject since v0.22.0 parses

A strict parser reads a subject as `type(scope)!: description` and ignores any
subject that does not match. All 102 non-merge subjects match, with a type from
the standard set:

| Type | Count | What a parser releases for it |
| --- | --- | --- |
| docs | 47 | nothing |
| fix | 42 | a patch |
| test | 7 | nothing |
| feat | 4 | a minor |
| chore | 2 | nothing |

The 18 merge commits ("Merge pull request #568 from ...") do not match, and
both tools skip them by default, which is the correct reading. None of the 120
commits carries a `!` or a `BREAKING CHANGE` footer. Since v0.17.0, one commit
has: `feat!: remove the outward-action grant`, which shipped in 0.21.0.

So the "conventional-ish" description in AGENTS.md is out of date for this
window. Syntax is not where a parser goes wrong here.

## Finding 2 — The changes a consumer sees without acting are typed as fixes

The 0.23.0 release commit opens with five changes that reach an existing
consumer without that consumer doing anything. Every commit behind each of them
is typed `fix`, and none is marked breaking:

| 0.23.0 lead item | Subjects behind it | What a parser reads |
| --- | --- | --- |
| A feature with tasks and no plan review now holds at `plan` (#542) | 3 × `fix(pipeline)`, 1 × `fix(contract)` | patch |
| `doctor` can now exit 1 on a project that read as current (#494) | 4 × `fix(doctor)` | patch |
| The next prune deletes the speckit scripts unless the project reinstalls once (#293) | 2 × `fix(install)` | patch |
| The worktree guard now refuses a `..` path into a peer worktree (#365) | 14 × `fix(guard)` | patch |
| `check config` now rejects a `trunk` it accepted before (#509) | 2 × `fix(paths)` | patch |

The third row is a breaking change in the ordinary sense: an installed project
loses files on its next routine command unless someone acts first. A parser
sees a bug fix.

A parser would still have cut 0.23.0 as a minor, because four `feat` commits
were in the window (#568, #509's `trunk` key, #76, and #532). All four are
additive and appear in the notes under "the rest of the surface", not in the
lead list. Without them, the same five behaviour changes would have shipped as
0.22.1.

0.22.0 shows the other way this goes wrong. Its fourth lead item removes two
skills from the bundle, so `--prune` deletes them from a consuming repo (#485).
The commit that removed them is `refactor(skills)`, which a parser releases
nothing for. The version came out right because three of the other lead items
had `feat` commits behind them.

**Measured:** in the last two releases, 0 of 9 lead items carried a breaking
marker, and 6 of 9 carried no `feat` either. **Concluded:** the version a
parser computes from these subjects is right only when an unrelated feature
lands in the same window, and the subjects cannot supply the lead list at all.
Deriving the version from subjects would need a change to how subjects are
written, and finding 3 suggests a per-change field would not hold either.

## Finding 3 — The template's "Breaking change" box was ticked once in five

The pull request template asks for a Type of Change, including "Breaking change
(fix or feature that would cause existing functionality to change)". For the
five 0.23.0 lead items:

| Lead item | Pull request | Ticked |
| --- | --- | --- |
| Plan review hold | #560 | Bug fix, Breaking change |
| `doctor` exit 1 | #555 | Bug fix, New feature, Testing improvements |
| Scripts recorded per file | #566 | Bug fix |
| Guard refuses `..` | #557 | Bug fix |
| `trunk` declarations refused | #548 | Bug fix |

So the judgment is not made at merge time in any form a tool could read. It is
made once, at release time, by someone reading every merged pull request. That
is how 0.22.0 and 0.23.0 got their lead lists, and the 0.23.0 reading took a
subagent over 17 pull requests.

A fourth candidate was considered on this evidence: a release-note fragment per
pull request, in the style of towncrier, where the author files the consumer
impact with the change. It is not recommended. The template already asks the
same question at the same moment and was answered correctly once in five, so a
fragment would need its own enforcement before it was any better, and the
release-time reading it replaces is the step that already works.

## Finding 4 — release-please does not fit how releases are cut here

release-please keeps a release pull request open, updates it on every push to
`main`, and tags and publishes when it is merged
([README](https://github.com/googleapis/release-please/blob/main/README.md)).

1. **Version:** derived from subjects, so finding 2 applies. A `Release-As:`
   footer or the `release-as` setting overrides it
   ([manifest docs](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)).
   At 0.x, a breaking change bumps the major unless `bump-minor-pre-major` is
   set.
2. **Notes:** generated from subjects. The release pull request body becomes the
   release body, but a hand edit to it is overwritten the next time
   release-please updates the pull request. That is open upstream as
   [#877](https://github.com/googleapis/release-please/issues/877), "stop
   release-please from blowing away manual edits". The
   supported override, `BEGIN_COMMIT_OVERRIDE` in a merged pull request's body,
   does not work with merge commits, which this repo uses for stacked pull
   requests.
3. **Relock:** not supported natively. The request is open as
   [#2561](https://github.com/googleapis/release-please/issues/2561). The
   generic `extra-files` updater can rewrite the package's version line in
   `uv.lock`, which is a text edit rather than a relock.
4. **Gate:** a pull request opened with the default `GITHUB_TOKEN` starts no
   workflow run
   ([GitHub docs](https://docs.github.com/en/actions/concepts/security/github_token)),
   so the release pull request gets no CI without a personal access token or a
   GitHub App. `skip-github-release` can leave the release to the existing tag
   job. Whether it also skips the tag was not checked.

Its one advantage is real: the open release pull request is a standing reminder
that merged work is unreleased, which is the issue's first cost. It also
changes the process from a direct commit to a pull request, which the issue
allows but would have to say.

## Finding 5 — python-semantic-release fits the process and not the notes

python-semantic-release commits the bump to `main` and tags it, which matches
how releases are cut today
([commands](https://python-semantic-release.readthedocs.io/en/latest/api/commands.html)).

1. **Version:** derived from subjects, so finding 2 applies. `--minor` and
   `--major` force the level. Two defaults would have to change for a 0.x
   project: `allow_zero_version` (false since 10.0.0, which starts at 1.0.0)
   and `major_on_zero` (true, which sends a breaking change to 1.0.0)
   ([configuration](https://python-semantic-release.readthedocs.io/en/latest/configuration/configuration.html)).
2. **Notes:** Jinja templates over the parsed commits. A template can read a
   file into the notes, so a hand-written list could be pulled in, but nothing
   documents a human edit between computing the version and publishing it.
3. **Relock:** documented. The uv guide runs
   `uv lock --upgrade-package "$PACKAGE_NAME"` and `git add uv.lock` as the
   `build_command`, so the lock lands in the release commit
   ([uv guide](https://python-semantic-release.readthedocs.io/en/latest/configuration/configuration-guides/uv_integration.html)).
   The tool's own GitHub Action image has no uv, so it would run as a plain
   step.
4. **Gate:** by default it tags its own release commit, which no CI run has
   tested, and that is the guarantee the tag job exists for. `--no-tag
   --no-vcs-release` leaves tagging to the existing job, but a push made with
   the default `GITHUB_TOKEN` starts no workflow run, so the release commit is
   never tested and never tagged without a personal access token.

## Finding 6 — A script owned by this repo meets all four

The script does the four steps of the issue's "How a release is cut today" and
leaves the version call with the person running it:

1. **Version:** the script lists every pull request merged since the last tag,
   with its ticked types and its Impact line, and proposes a minor when any is
   anything other than docs or tests. The person confirms or changes it. Every
   release from 0.17.0 to 0.23.0 was a minor, so the proposal is the common
   case.
2. **Notes:** the script drafts the release commit body in the 0.22.0 and
   0.23.0 shape, with the lead list left for the person or an agent to write
   from that listing. The tag job then publishes that body as the GitHub
   release (`gh release create --notes-file`), so the notes are written once.
   That fixes the issue's second cost.
3. **Relock:** the script runs `uv lock` and commits the lock with the bump.
   That is the step 0.18.0, 0.20.0, and 0.21.0 dropped.
4. **Gate:** unchanged. The person pushes the release commit, the push starts
   CI because it was not made by `GITHUB_TOKEN`, and the tag job tags it only
   after test, wheel, and lint pass.

No token, app, or third-party action is added, and the process stays a direct
commit to `main`. The cost is a script to maintain, and the reading in step 1
stays a person's or an agent's judgment. Finding 3 is the evidence that it has
to.

## Finding 7 — The reminder for unreleased work is not settled

Merged work sat untagged for two weeks before 0.16.0 (#153). release-please is
the only candidate that answers this on its own, through its standing pull
request. The script can report how many pull requests are unreleased when it is
run, but that only helps someone who thinks to run it. Whether something should
prompt for a release, and where (a scheduled job, a line in `wfctl status` on
`main`, or nothing), is left to the follow-up that builds the script.

## Finding 8 — None of the three rules out PyPI

Publishing to PyPI would be a job after `tag`, started by the tag. None of the
three candidates changes what that job has to do, so the choice made here
neither helps nor blocks it.

## What this changes in the repo's stated rationale

The comment above the `tag` job says the bump "belongs in the PR that makes the
change, where the major/minor/patch call has context". Finding 3 shows that the
context is not captured in the pull request, and every release from 0.17.0 to
0.23.0 was a standalone commit. The recommended script keeps the call with a
person, so the comment's conclusion stands and only its premise is wrong.

What does move is where the release notes come from: the GitHub release would
carry the release commit's body rather than a list GitHub generates from merged
pull requests. That is the decision a proposed architecture record should carry
before `.github/workflows/ci.yml` changes.
