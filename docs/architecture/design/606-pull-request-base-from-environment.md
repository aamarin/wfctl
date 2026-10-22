---
status: proposed
---

# The release note check reads the pull request's base branch from the environment

## Context

The release note check works out what a branch added by comparing it with
`main`. In a pull request run it reads the branch name from `GITHUB_HEAD_REF`,
and when that name is `main` it prints "on main, nothing to check" and passes.
A pull request from a fork whose branch is also named `main` therefore passes
with no release note at all.

The fix is for a pull request run to compare against the branch the pull
request targets, and never to take the "on main" shortcut. That leaves one
structural question, which is how the script learns the target branch.

The script runs in two places, `wfctl verify` and the `release-note` CI job,
and both have to reach the same verdict. Its docstring says it takes no
arguments for that reason. `change-carries-release-note` describes the local
run comparing against `main`, and that stays true.

## Verified

- `check_release_note.py` `branch_name()` reads `GITHUB_HEAD_REF` and falls
  back to `git rev-parse --abbrev-ref HEAD`. `main()` returns 0 with "on main,
  nothing to check" when that name is `main`, before comparing anything.
- `merge_base()` tries `origin/main`, then `main`, with `git merge-base <ref>
  HEAD`. No other branch name appears in it.
- GitHub's variables reference says `GITHUB_BASE_REF` is "the name of the base
  ref or target branch of the pull request in a workflow run", and is "only set
  when the event that triggers a workflow run is either `pull_request` or
  `pull_request_target`". `GITHUB_HEAD_REF` is described the same way.
- `ci.yml` runs the `release-note` job only on `pull_request` events, with
  `fetch-depth: 0`, so every branch on `origin` is fetched, a stacked pull
  request's base included.
- `wfctl.json` runs the script in `verify` with no arguments.

## Assumed

- GitHub keeps setting `GITHUB_BASE_REF` to the branch name, not a full ref
  such as `refs/heads/main`. If it changed, `origin/<name>` would not resolve,
  and the check would fail with "can't find" rather than pass, which is the
  safe direction.

## Direct baseline

The script reads `GITHUB_BASE_REF` the same way it already reads
`GITHUB_HEAD_REF`. When it is set, the script compares against
`origin/<base>`, and it skips the "on main" shortcut, since a pull request is
never `main` itself. When it is unset or empty, as in `wfctl verify` and on
push runs, the script compares against `main` exactly as it does today. Nothing
new is passed in from `ci.yml`.

## Decision

The baseline is chosen. The check reads the pull request's base branch from
`GITHUB_BASE_REF`, compares against `origin/<base>` when it is set, and takes
the "on main" shortcut only when it is unset. The script still takes no
arguments, so `wfctl verify` and CI still run the same command.

## Diagram

```
        baseline (chosen)                      --base flag

        ┌───────────────────┐                  ┌───────────────────┐
        │ GitHub runner env │                  │ GitHub runner env │
        └─────────▲─────────┘                  └──▲─────────────▲──┘
                  │ script reads                  │ script      │ ci.yml reads
                  │ head and base                 │ reads head  │ base (new)
        ┌─────────┴─────────┐                  ┌──┴─────────┐   │
        │ check script      │                  │ check      │   │
        │ (no arguments)    │                  │ script     │   │
        └───▲───────────▲───┘                  └─▲────────▲─┘   │
            │ runs      │ runs                   │ runs   │ runs│
            │           │                        │ no     │ with│
            │           │                        │ flag   │ --base (new)
   ┌────────┴─────┐ ┌───┴──────────┐   ┌─────────┴────┐ ┌─┴────┴───────┐
   │ wfctl verify │ │ ci.yml job   │   │ wfctl verify │ │ ci.yml job   │
   └──────────────┘ └──────────────┘   └──────────────┘ └──────────────┘
```

No boundary in force runs between these components, so neither graph draws a
divider. The change this is built to absorb is a second CI system or a second
local caller. In the baseline, the script has one input, the environment, and
both callers run the same command. With the flag, the script has two inputs,
the environment for the head branch and an argument for the base. The callers
also stop running the same command, since only CI passes the flag. The flag
graph has one dependency more, and it is the one that lets the two callers
disagree.

## Considered

- A `--base` flag that `ci.yml` fills from `${{ github.base_ref }}`. It is
  explicit, and a reader of `ci.yml` sees what is compared. We didn't choose it
  because the script would read the head branch from the environment and the
  base branch from an argument. In addition, `wfctl verify` and CI would no
  longer run the same command, which is the property the script's docstring
  relies on.
- Compare against the first parent of the pull request's merge commit,
  `HEAD^1`. `actions/checkout` checks out that merge commit, so this needs no
  branch name at all. We didn't choose it because it only works on GitHub's
  merge ref. The local run would need a second way to find its base, which puts
  two code paths where there is one today.
- Read the base commit from the event payload at `GITHUB_EVENT_PATH`. It gives
  an exact commit instead of a name. We didn't choose it because it means
  parsing a JSON file for a value GitHub already exports as a variable.

## Consequences

A stacked pull request is now judged on what it adds to its base branch, not
on its diff from `main`. A file the parent branch added under `changes/` no
longer produces a finding on the child. The child still needs a note for its
own issue, so the stacked case in `change-carries-release-note` still holds.

The "can't find" message now names the branch it looked for, since it is no
longer always `main`.

Outside a pull request, `GITHUB_BASE_REF` set in a developer's shell would
change what the local check compares against. Nothing sets it outside GitHub,
and the test suite clears it for every test, as it already does for
`GITHUB_HEAD_REF`.

## Verification

The check script has tests for these cases:

1. A pull request whose head branch is named `main`, with no note, fails.
2. A stacked pull request whose base is its parent's branch is judged only on
   what it adds to that branch.
3. A pull request whose base branch can't be found fails, naming that branch.
4. An empty `GITHUB_BASE_REF` counts as unset, so the local run still compares
   against `main`.

The fork case only happens on GitHub, so the pull request description says how
it was checked and does not claim a CI run proved it.

## Log

- 2026-10-22  proposed  — #606. A fork's pull request from a branch named
  `main` passed the check with no note, and this records how the check learns
  what to compare against.
