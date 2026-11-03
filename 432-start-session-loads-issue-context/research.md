# Research: Session start loads only the branch's own context

The plan's Technical Context has no open unknowns. These are the decisions it made about how to build each part.

## 1. How the GitHub backend reads an issue's parent

- Decision: a script, `github-issue-parent.sh <id>`, calls `gh api repos/{owner}/{repo}/issues/<id>/parent`. On success it prints one line, `#<number> <title>`. A 404 means the issue has no parent, and the script prints nothing and exits 0. Any other failure exits non-zero.
- Checked on 2026-11-02: `#432` returns `#619 Epic: Faster session start`, and `#2` returns HTTP 404 with the message "No parent issue found". GitHub also answers 404 for a repository the token can't read, so the script treats a 404 as no parent only when that message is present, and exits non-zero otherwise.
- Rationale: GitHub's sub-issues REST endpoint returns the parent in one call. gh's `{owner}/{repo}` placeholder can't appear in a `github.json` argv, because wfctl's substitution reads it as its own and rejects it. That's why `github-issue-state.sh` is a script too.
- Alternatives considered: `gh issue view --json parent`. We didn't choose it because `gh` doesn't expose that field in every supported version, and the REST endpoint is stable.

## 2. How the GitHub backend reads a branch's open PR

- Decision: a script, `github-change-branch.sh <branch>`, runs one GraphQL query for the open PR whose head is the branch. It reads the PR's number, title, URL, the last commit's check rollup state, and its review threads' `isResolved` flags. It prints one line, such as `#712 Session report — checks: failing · 2 unresolved review threads`, or nothing when the branch has no open PR.
- GitHub matches a head branch by name, so a PR from a fork whose branch has the same name also matches. The script keeps only PRs whose head repository is this repository. If more than one still matches, such as two PRs from the same branch into different base branches, it prints the most recently updated one.
- Rationale: one query gets everything the line needs. A query is a read, so it's not a mutation the host's permission layer refuses.
- Alternatives considered: `gh pr list --head <branch> --json statusCheckRollup` plus a second call for threads. We didn't choose it because it takes two calls, and `gh pr list` doesn't return review thread state.

## 3. What wfctl does with a tracker verb's output

- Decision: wfctl prints `view`, `parent`, and `branch` output as the backend wrote it, under its own label. `--session --json` carries each one as a string, or `null` when there's no output, and `tracker_status` gives each one `ok` or a reason code.
- Rationale: wfctl reads no tracker's vocabulary (`tracker-reads-report-failure`). Parsing the PR line for a check state would put GitHub's words in wfctl.
- Alternatives considered: a structured contract, where `branch` prints JSON with `checks` and `unresolved` keys. We didn't choose it because nothing in wfctl acts on those values today, and the report only displays them. If something does later, the contract can grow a structured form then.

## 4. How the report decides a commit mentions the branch's issue

- Decision: a commit mentions the issue when its subject or body contains the key as a whole token. For a key that's only digits, that token is `#<key>`, such as `#432`. For any other key, such as `PROJ-123`, it's the key itself. Matching is case-sensitive for letters, as the tracker's `key_pattern` is.
- Rationale: a bare `432` would match "432 tokens" and other numbers in a commit body. A Jira-style key carries its own prefix, so it doesn't need one.
- Alternatives considered: the tracker's closing keywords, such as `Closes #432`. We didn't choose it because most commits on a branch reference the issue without closing it.

## 5. Which commits are the branch's

- Decision: the commits from the merge base with the trunk to `HEAD`. The trunk is the `trunk` that `wfctl.json` declares on the default branch, which `origin/HEAD` names, or the default branch itself when none is declared. `_review.review_trunk` resolves it, the same way reviews and the PR guard do. With no `origin/HEAD`, the report reads `Commits: trunk not found`, lists the last 20 commits, and marks none, since it can't tell which are the branch's. Any error `review_trunk` raises reads the same way. The spec's Edge Cases carry this as the one exception to FR-019.
- Rationale: the report and reviews count the same commits. We didn't choose `review_trunk`'s local fallback for a repo with no `origin/HEAD`, because it reads the working tree's `trunk`, which the agent can edit.

## 6. How the report reads the last stop

- Decision: `_session.last_stop(agent_dir, branch)` reads `events.jsonl` with the same malformed-line skipping the other readers use, and returns `none`, `continued`, or `wrapped`. The most recent `end` event decides it, and a missing `continued` key counts as `wrapped`.
- Rationale: it replaces the skill's `grep … | tail -1` with code that already rejects a torn line, the case the skill's `}$` guard exists for.

## 7. Where the doctor repair guidance goes

- Decision: `wfctl/agents/skills/start-session/references/doctor-repair.md`. Step 1 keeps one paragraph: run `doctor --session`, and when it prints anything other than a ✓, open the reference file and follow it.
- Rationale: the accepted record places it beside the skill. A green session never opens it.
- Alternatives considered: a separate skill. We didn't choose it because the guidance only applies inside session start, and a skill would add an entry to every session's skill listing.
