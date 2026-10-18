# Data model: release automation

There is no database. Every entity is a file or a git object, and each one is
read from disk or from git at the moment a script runs.

## Release note

A file under `changes/`, committed on the branch that makes the change.

| Field | Where it comes from | Rule |
| --- | --- | --- |
| issue | the file name before the first dot | digits, or `+<name>` for work with no issue |
| category | the file name's second part | one of the `[[tool.towncrier.type]]` directories |
| counter | an optional third part, such as `.2` | written by `towncrier create` when the name is taken |
| text | the file's content | not empty, not whitespace only, not "Add your info here" |

Accepted names: `<issue>.<category>.md`, `<issue>.<category>.<n>.md`, and
`+<name>.<category>.md`. Any other file the branch adds under `changes/` fails
the check.

Lifecycle: added on a branch, merged to `main`, read by the release script, and
deleted by the release commit. A note never changes after its branch merges.

## Category

One `[[tool.towncrier.type]]` table in `pyproject.toml`. The order of the
tables is the order of the draft's sections.

| directory | name | In the draft | Version it proposes |
| --- | --- | --- | --- |
| `change` | Behaviour changes | first section | minor |
| `addition` | Additions | second section | minor |
| `fix` | Fixes | third section | patch |
| `none` | Nothing to notice | left out | none on its own |

Both the check and towncrier read this table. The release script reads it too,
for which categories propose a minor. That mapping is the one fact it holds
itself, as a constant naming `change` and `addition`.

## Merge

A merge commit on `main` since the last tag, whose subject reads
`Merge pull request #<n> from <owner>/<branch>`.

| Field | Where it comes from |
| --- | --- |
| pull request | `#<n>` in the subject |
| notes added | files under `changes/` in `git diff --diff-filter=A <merge>^1 <merge>` |

A merge with no notes added is listed under "Merged with no release note".

## Version proposal

Computed by the release script and confirmed by Andre.

| Field | Where it comes from |
| --- | --- |
| current | `[project].version` in `pyproject.toml` |
| proposed | minor if any note is `change` or `addition`, patch otherwise |
| reason | counts per category, such as "minor: 2 behaviour changes, 1 addition" |
| confirmed | what Andre types, or the proposal when he presses Enter |

A confirmed version must parse as `X.Y.Z` and be greater than the current one.

## Release commit

One commit on a `release/v<version>` branch, made and pushed by the release
script, and merged into `main` by Andre through the release pull request.

| Part | Content |
| --- | --- |
| subject | `chore(release): cut <version>`, as releases 0.16.0 to 0.23.0 read |
| body | the draft as Andre left it in his editor |
| `pyproject.toml` | the confirmed version |
| `uv.lock` | relocked to match |
| `changes/` | every note deleted |

The tag job finds it by its subject, confirms that `pyproject.toml` at that
commit carries the version being released, and publishes its body. An empty
body fails the job before anything is tagged.

## Release pull request

| Part | Content |
| --- | --- |
| branch | `release/v<version>`, into `main` |
| title | the release commit's subject |
| description | the release commit's body |
| checks | the five the ruleset requires; `release-note` passes because the branch's name matches its version and that version is higher than `main`'s |

It is merged as a merge commit, and the tag lands on that merge.
