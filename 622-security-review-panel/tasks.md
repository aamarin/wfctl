---
description: 'Task list for #622, a security review panel that runs before every change opens'
---

# Tasks: A security review panel runs before every change opens

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/622-security-review-panel/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/cli.md, contracts/config.md

**Design records that bind these tasks**: a task that reverses one of these is a defect.

- `docs/architecture/design/622-review-records-in-state-dir.md`: records live in `<state dir>/reviews/`, and wfctl reads that one location only.
- `docs/architecture/design/622-review-groups-list.md`: `review` holds `commands` and a `groups` list, and security and code always run first.
- `docs/architecture/design/622-blocked-reviewer-relays-report.md`: `wfctl relay` reads the report from a file, never stdin or the command's text, and refuses a relay with no reason.
- `docs/architecture/design/622-review-check-in-worktree-guard.md`: the review check runs inside `wfctl hook worktree-guard`, before the worktree check, with no new `MANAGED_HOOKS` row.

**Scope boundary**: On 2026-10-24 Andre decided the review check stops adding rules. The disguised commands listed as known limits in spec.md's Edge Cases (the backtick glued to `pr`, `gh extension exec`, a two-word alias, a `pulls#x` fragment or grouped `-ifhead=x`, `xargs gh`, `repositories/<id>/…`, a GraphQL mutation in a variable, wrappers such as `uv run --directory` and `direnv exec`, a quoted or variable program name, `gh` inside a script or alias, and `--hostname` or a URL `-R`) are not implemented here. #627 closes them. No task below adds a rule for one of them.

**Tests**: Tests assert on console output, so every test that reads output pins `NO_COLOR` (see `tests/conftest.py`). Test names are sentences, and each docstring says why the test exists, usually naming the failure it catches. Run everything through `uv run`.

**Prose**: Load the `writing-style` skill before writing any skill text, `AGENTS.md` text, record amendment, docstring, comment, or commit message.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: The user story from spec.md (US1 to US6)
- Every implementation task names its verification, or sits next to the test task that verifies it

## Path Conventions

One CLI project. Source is under `wfctl/`, tests under `tests/`, and shipped skills under `wfctl/agents/skills/`. Never edit `.agents/` or `.claude/` by hand, since `install-skills` rewrites them.

## Story order

The phases don't follow spec.md's priority order exactly. US1 is P1, but its skill rewrites drive `wfctl review start`, `wfctl review check`, `wfctl relay`, the `reviewing-security` skill, and the gate's shape rules. Its independent test can't pass until US2, US3, US4, and US6 exist, so US1 is built last. The other stories run in priority order: US2, US3, US4, US5, US6, then US1.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The release note, and a baseline timing taken before any code changes.

- [X] T001 Create the release note `changes/622.addition.md` with `uv run towncrier create 622.addition.md --content "…"`. Write it for an existing wfctl user. Say that every change now gets a security review group and a code review group before its PR opens, that wfctl records which commits each group reviewed, and that the worktree guard refuses `gh pr create` and `gh pr merge` until every group has reviewed the newest commit or a person runs `wfctl review sign-off`. Verify with `uv run python .github/scripts/check_release_note.py`.
- [X] T002 Measure the worktree guard's cost on an `ls` payload before any code changes, for SC-003. Time `wfctl._hook.worktree_guard(b'{"tool_input":{"command":"ls"},"cwd":"<this worktree>"}')` in process with `uv run python -c` and `timeit.repeat` (1000 calls, 5 repeats, take the minimum). Write the number, the commit sha, and the exact command to `/Users/andremarin/Development/wfctl-specs/622-security-review-panel/guard-timing.md`, so T040 can repeat it. Verify by running the command twice and checking that the two minimums agree within 10%.
- [X] T003 Validate Phase 1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Two things every story reads. The `_paths` helpers gain a timeout, since the review check calls them and every `git` call there runs with a 5-second bound (research.md R4, Timeouts and errors item 1). `_review_config` reads the `review` key, since `review start`, `review groups`, `check config`, and the guard all need the groups in run order.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Write failing tests in `tests/test_paths.py` for an optional `timeout` keyword on eight helpers: `trunk_branch`, `_resolve_declared`, `_bare_head`, `is_bare_layout`, `resolve_branch`, `resolve_agent_dir`, `project_state_dir`, and `project_name`. Monkeypatch `subprocess.run` to record its keyword arguments. Check that each helper passes the timeout to every `subprocess.run` it makes, and that the default is `None`, so existing callers are unchanged. Check the pass-down chain: `trunk_branch` passes it to `_resolve_declared` and `_bare_head`, `_bare_head` passes it to `is_bare_layout`, and `resolve_agent_dir` passes it through `project_state_dir` to `project_name`. Check that a `subprocess.TimeoutExpired` from `resolve_branch` propagates rather than falling back to `"detached"`, because a fallback would let the review check judge the wrong branch.
- [X] T005 Add the `timeout: float | None = None` keyword to the eight helpers in `wfctl/_paths.py`, passing it to every subprocess call and down the chain T004 names. Don't change any existing caller. Verify with `uv run pytest tests/test_paths.py -q`.
- [X] T006 [P] Write failing tests in `tests/test_review_config.py` for a `load(repo_root)` function in `wfctl/_review_config.py` that returns the groups in run order and a list of problems. Cover these cases:
  1. No `wfctl.json`, or no `review` key, gives `security` (`s1` to `s3`, all Claude, skill `reviewing-security`) and `code` (`c1` to `c3`, all Claude, skill `code-review`), and no other model is mentioned (FR-022, SC-005).
  2. The config.md example gives `security` `s1` to `s4` (two Claude, then two Codex with the command `codex exec --sandbox read-only`), `code` `c1` to `c3` by default, then `money-rules` `m1` and `m2` with skill `money-rules-review`. Ids are numbered across the group's whole reviewer list in order (data-model.md).
  3. A custom group listed before `code` still runs after `security` and `code`, and other groups keep list order (FR-019).
  4. A built-in group listed without a `reviewers` key gets three Claude reviewers.
  5. A custom group with no `skill` defaults to `code-review`.
  6. Every finding in contracts/config.md, with its exact wording: `review` not an object, `groups` not a list, an entry with no `group` string, a bad group name such as `../x` (`^[a-z][a-z0-9-]*$`), a custom group with no `reviewers` key, an empty `reviewers` list on a built-in group and on a custom group, two groups sharing a first letter, a model with no `commands` entry, a count below 1 or not an integer, and `commands` not an object of strings.
  7. A `wfctl.json` that isn't valid JSON gives a problem rather than an exception.
- [X] T007 Create `wfctl/_review_config.py` with the group and reviewer dataclasses and `load(repo_root) -> (groups, problems)`, per data-model.md and contracts/config.md. Read `wfctl.json` directly. Import nothing that imports `typer` or `rich`, since the guard imports this module. Verify with `uv run pytest tests/test_review_config.py -q`.
- [X] T008 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: The timeouts and the group loader exist. Story work can begin.

---

## Phase 3: User Story 2 - wfctl, not the coordinating agent, records whether a review ran (Priority: P1) 🎯 MVP

**Goal**: `wfctl review start` writes a run record with the expected reviewers and the commits to review. `wfctl review check` judges the reports, prints the roster, and moves the group's last reviewed commit only when the run completes. Everything lives under `<state dir>/reviews/`.

**Independent Test**: Start a group run, write two accepted reports and one that names an older commit, and run `wfctl review check`. The roster shows two ✓ and one ✗, and `last-reviewed.json` hasn't moved.

**Verification**:

- Automated: `tests/test_review.py`, `tests/test_review_cli.py`, `tests/test_review_store.py`
- Manual: quickstart.md steps 3 and 5 in this worktree, writing the reports by hand
- Evidence: `run.json` and `last-reviewed.json` under `<state dir>/reviews/<group>/`, and a `wfctl store specs` commit with no `reviews/` path in it

### Tests for User Story 2 ⚠️

> Write these tests first, and check that they fail before implementing.

- [X] T009 [P] [US2] Write failing range tests in `tests/test_review.py` (research.md R3). Build a temporary repository with a bare `origin`, `origin/HEAD` pointing at `main`, and a feature branch. Cover these cases:
  1. The first run starts at the merge base of the head and the trunk branch (FR-007).
  2. A later run starts after the group's last reviewed commit when it is an ancestor of the head.
  3. After a rebase, a last reviewed commit that is no longer an ancestor falls back to the merge base.
  4. A branch that merged in `main` since its last review lists only its own commits, with no merge commit, from `git rev-list --no-merges <base>..<head> --not <trunk refs>` (US2 scenario 4).
  5. The trunk refs are the remote ref from `_paths.trunk_branch` and the local branch of the same name with `origin/` stripped, when it exists. A stale local `main` doesn't make merged commits look like branch work.
  6. A head equal to the last reviewed commit, or behind it, has no unreviewed commits (R3 item 3).
  7. No trunk branch raises an error that names the `trunk` key in `wfctl.json`.
  8. With `WFCTL_STATE_DIR` pointed at an empty directory on a branch with an earlier review, the next run starts at the merge base (`622-review-records-in-state-dir.md`, Verification).
  9. Every `git` call takes the timeout the caller passes.
- [X] T010 [US2] Write failing report tests in `tests/test_review.py` (research.md R2, FR-008):
  1. A `Reviewed: <sha>` line counts when the sha is 7 or more hex digits and a prefix of the run's head. A shorter prefix doesn't count.
  2. A report naming another commit gives the reason `names <sha>, not <head>`.
  3. A report with no `Reviewed:` line gives `no Reviewed: line`.
  4. The verdict counts when the last non-blank line holds `Approve` or `Request changes` and the verdict anchor `^[^A-Za-z]*Verdict` is on that line or the non-blank line before it. Cover `Verdict: Approve`, `**Verdict: Approve**`, `## Verdict` followed by `Approve`, and `Verdict: Request changes`. These are the spellings `test_the_verdict_anchor_accepts_every_spelling_reviewers_use` in `tests/test_review_fanout_skill.py` pins today, so copy its cases.
  5. A report cut off after an early `Verdict` mention gives `no verdict at the end`.
  6. wfctl reads the whole report, so a `Reviewed:` line after 200 lines of findings still counts.
- [X] T011 [US2] Write failing run tests in `tests/test_review.py` (data-model.md, FR-005, FR-009, SC-002):
  1. `start` writes `reviews/<group>/runs/001/run.json` with `group`, `run`, `base`, `head`, `commits` (newest first), `reviewers` (`id`, `model`, `state: expected`, and `command` for a model other than Claude), `started_at`, and `completed_at: null`.
  2. Runs are numbered `001`, `002`, and so on in start order.
  3. A group with no unreviewed commits writes nothing.
  4. `check` completes the run only when every expected reviewer has a counted report. It then sets `completed_at`, changes nothing else in `run.json`, and writes `last-reviewed.json` as `{"sha", "run", "at"}` with the run's head.
  5. A missing report, a report with no verdict, and a report about another commit each leave the run incomplete and `last-reviewed.json` unchanged.
  6. A config change after `start` doesn't change the expected reviewers, since `run.json` already lists them.
  7. A new `start` after an incomplete run opens run N+1 from the same base, and the earlier run's reports don't count toward it.
  8. A commit added while reviewers read leaves their reports naming the older head, so the run stays incomplete.
  9. `start` appends `review-start` (`group`, `run`, `head`, `reviewers` as the expected count) and `check` appends `review-complete` (`group`, `run`, `head`) to `events.jsonl`.
- [X] T012 [P] [US2] Write failing CLI tests in `tests/test_review_cli.py` for `wfctl review start <group>` and `wfctl review check <group>`, using `typer.testing.CliRunner` with `NO_COLOR` pinned. Assert each output line and exit code in contracts/cli.md: the start block (`security run 003 · 2 commits since a1b2c3d · head 9f8e7d6`, the `reports:` path, one line per reviewer), `security is up to date at <sha>`, the no-trunk line, the unknown-group line followed by the group list, and invalid config printing the findings with exit 1. For `check`, assert the roster lines, `complete: security reviewed through <sha>` with exit 0, `incomplete: N of M expected reports missing` with exit 1, `✗ security has no run; run wfctl review start security` with exit 1, and each ✗ reason (`no report`, `names <sha>, not <head>`, `no Reviewed: line`, `no verdict at the end`).
- [X] T013 [P] [US2] Write a failing test in `tests/test_review_store.py` for SC-004 and US2 scenario 5. Run a review group to completion, run `wfctl store specs`, and check that no path under `reviews/` is in the commit it made on the spec store. Reuse the spec store fixtures from `tests/test_spec_store.py`. The autouse `_spec_store_reaches_only_the_tests_own_remote` fixture in `tests/conftest.py` keeps the push local.

### Implementation for User Story 2

- [X] T014 [US2] Create `wfctl/_review.py` with the range functions from R3: the base (last reviewed commit if it is an ancestor of the head, else the merge base), the trunk refs, and the commit list. Every `git` call takes a `timeout` argument, since the guard calls these with 5 seconds. `git merge-base --is-ancestor` exiting 1 and `git show-ref --verify` exiting 1 are answers, not errors. Import nothing that imports `typer` or `rich`. Verify with `uv run pytest tests/test_review.py -q -k range`.
- [X] T015 [US2] Add the records to `wfctl/_review.py`: the `reviews/` path under `_paths.resolve_agent_dir`, run record writing with `_io.write_atomic`, report judging (R2), the roster, completion, `last-reviewed.json`, and the two events through `_io.append_event`. Verify with `uv run pytest tests/test_review.py -q`.
- [X] T016 [US2] Add a `review` Typer group to `wfctl/cli.py` with `start <group>` and `check <group>`, printing exactly what contracts/cli.md shows. `start` prints the reports path, which is how the panel skill learns it (FR-011). Verify with `uv run pytest tests/test_review_cli.py -q`.
- [X] T017 [US2] Confirm the store test passes with no change to `wfctl store specs`, since the records already sit outside the spec directory. Verify with `uv run pytest tests/test_review_store.py -q`.
- [X] T018 [US2] Run quickstart.md steps 3 and 5 by hand in this worktree, writing three reports with `Reviewed: <head>` and a verdict, and one naming an older commit. Check the roster and that `last-reviewed.json` moves only after the bad report is fixed. Verify by reading `uv run wfctl review check security` output and the files under the path `review start` printed.
- [X] T019 [US2] Validate Phase 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: wfctl records which commits each group reviewed, and the roster comes from wfctl rather than the coordinator.

---

## Phase 4: User Story 3 - A pull request can't open or merge with unreviewed commits (Priority: P2)

**Goal**: The worktree guard runs a review check first. It refuses `gh pr create`, `gh pr new`, `gh pr merge`, and the `gh api` merge calls while any group has unreviewed commits that no sign-off covers. It refuses every time the commands it can't read for sure. `wfctl review sign-off` lets a person sign off at an interactive terminal, and the guard refuses it from an agent.

**Independent Test**: On a branch with one unreviewed commit, pipe a `gh pr create` payload into `uv run wfctl hook worktree-guard`. It exits 2 and names the commit. After a complete run of every group, the same payload exits 0 and prints nothing.

**Verification**:

- Automated: `tests/test_review_gate.py`, `tests/test_guard_entry.py`, `tests/test_review.py` (sign-off coverage), `tests/test_review_cli.py` (sign-off command), and the existing `tests/test_worktree_guard.py`
- Manual: quickstart.md steps 2 and 7, and the SC-003 timing in T040
- Evidence: exit codes and stderr text matching contracts/cli.md's guard table, and an added cost under 1 ms on an `ls` payload

### Tests for User Story 3 ⚠️

> Every case below is in plan.md's `test_review_gate.py` list or contracts/cli.md's guard table. All of `tests/test_review_gate.py` is one file, so its tasks run in order.

- [ ] T020 [US3] Build the fixtures for `tests/test_review_gate.py`:
  1. A temporary repository with a bare `origin`, `origin/HEAD` pointing at `main`, a `main` checkout, a feature worktree on `604-x`, and a second worktree on `630-x`.
  2. A stub `gh` script on `PATH` that answers `gh repo view --json nameWithOwner` and `gh pr view [<arg>] [-R <repo>] --json headRefName,headRefOid` from a table the test sets, can fail, and can hang.
  3. The review check's timeout as a module constant in `wfctl/_review_gate.py` that the hang test lowers with `monkeypatch`, so a timeout test doesn't wait 5 seconds.
  4. `XDG_STATE_HOME` pointed at the test's own directory.
  5. A helper that completes a group's run with `_review`, and one that calls `_hook.worktree_guard` with a payload holding `command` and `cwd` and returns the exit code and stderr.
  6. Every gate test clears `WFCTL_BRANCH` with `monkeypatch.delenv`, or sets it to the `cwd`'s branch. The `agent_dir` and `storyctl_dir` fixtures in `tests/conftest.py` set `WFCTL_BRANCH` and `WFCTL_STATE_DIR`, and a test would otherwise refuse for the wrong reason. A test that judges another branch also clears `WFCTL_STATE_DIR`, for the same reason (R5).
  7. The independent-test cases also run the real `uv run wfctl hook worktree-guard` process, so the `_entry.py` path is covered.
- [ ] T021 [US3] Write failing judging tests in `tests/test_review_gate.py`:
  1. A reviewed branch: `gh pr create --fill` exits 0 and prints nothing.
  2. An unreviewed branch: exit 2, and stderr matches contracts/cli.md's refusal block, listing each commit under its group, every group included, a custom group too.
  3. The code group commits a fix after the security group's run, and the fix commit is listed under `security` (US3 scenario 7).
  4. A sign-off covering the head allows `gh pr create` (scenario 4), and a commit added after it is refused again (scenario 5).
  5. An ancestor test answering "no" is read as an answer, not an error.
  6. A half-written `last-reviewed.json` gives the error refusal naming the file (scenario 6), and so does an unreadable `wfctl.json`.
  7. No trunk branch gives the error refusal with `can't find the trunk branch; set trunk in wfctl.json`.
  8. Any other exception after a match gives the error refusal naming it.
  9. The error refusal ends with the sentences saying a sign-off won't get past it and a person can run the command in their own terminal. A judged refusal, such as unreviewed commits, doesn't carry that last sentence.
  10. `echo "gh pr create"` on an unreviewed branch is refused with the commit list.
  11. `gh pr create --fill && echo done` is judged as `gh pr create --fill`.
  12. `gh pr new --fill` is judged as `gh pr create`.
  13. `gh pr merge` with no argument looks up the current branch's PR with `gh pr view` and judges it at `headRefOid`.
- [ ] T022 [US3] Write failing matching tests in `tests/test_review_gate.py` for research.md R6 patterns 1 to 7:
  1. `-R` before `pr` and before the verb, spaced, with `=`, and attached as `-R<repo>`, and `--repo` before `pr` and before the verb, spaced and with `=` (FR-012).
  2. `GH pr merge 630`, `Gh pr create`, `/opt/homebrew/bin/Gh pr create --fill`, and `GH api …/pulls` with a body are matched.
  3. `gh api …/pulls/630/merge` and `…/pulls/630/merge-async` are judged as PR 630.
  4. A `gh api` create is refused every time with `open the pull request with gh pr create so the review check can judge its branch`, in each spelling: `-f head=…`, `-fhead=x`, `--field=head=x`, `-XPOST`, a path ending `/pulls/`, and `"…/pulls?x=1"`.
  5. `gh api graphql` naming `createPullRequest`, `mergePullRequest`, `enablePullRequestAutoMerge`, or `enqueuePullRequest` is refused every time, naming `gh pr create` or `gh pr merge`.
  6. `gh api "$URL" --input body.json` and `gh api "repos/{owner}/{repo}/pulls/$N/merge" -X PUT` are refused with `write the gh api path out plainly; the check can't read where it writes`. `gh api "repos/{owner}/{repo}/pulls/$N/comments"` is not matched.
  7. `gh api graphql -F query=@mutation.graphql` and `gh api graphql --input q.json` are refused with `put the GraphQL query in the command; the check doesn't read files`.
  8. `gh api …/pulls/630/comments` and a plain `gh api …/pulls` read are not matched.
  9. `gh version` and `gh help pr` are not matched.
  10. `rg 'gh pr' wfctl/` and `` git commit -m "run `gh pr` first" `` are not matched.
  11. Sign-off spellings are refused every time with `✗ wfctl review sign-off is for a person to run in their own terminal, not an agent.`: `wfctl review sign-off`, `uv run wfctl review signoff`, `wfctl review sign_off`, and text with other words between `review` and `sign-off`.
  12. `ls`, and any command holding none of `gh`, `merge`, or `sign`, makes no `subprocess` call and reads no file in the review check (FR-016).
- [ ] T023 [US3] Write failing tests in `tests/test_review_gate.py` for `gh` command words the check can't read (R6 pattern 8, FR-012b). Each is refused on a reviewed branch:
  1. A substitution, quote, glob, or variable in the verb after `pr`: `gh pr $(git push -q) create`, `gh pr 'merge' 630`, and `gh pr m* 630`, with `write gh's command words out plainly; the check can't read them`.
  2. A word off the list of `gh`'s own commands: `gh stack merge`, `gh stack submit`, `gh co 630`, `gh copilot`, `gh agent-task`, `gh "$X" merge 630`, `rg 'gh (pr|api)' wfctl/`, and `git commit -m "the gh CLI"`, with `run gh <word> in your own terminal; the check knows only gh's own commands`.
  3. A flag before the verb: `gh pr --squash=true merge 630`, two `-R` before `pr`, `gh -R $(git push -q; echo a/b) pr merge 630`, `gh -R 'owner/repo' pr merge 630`, `gh --version`, and `gh --help`, with `move flags after the verb, and write -R as OWNER/REPO; the check reads only one plain -R before pr or the verb`.
  4. `gh -R=<this repo> pr merge 630` is judged as `gh pr merge 630`, with the value read without the `=`.
  5. One `-R` before `pr` and one after the verb count as two, refused with `name the repository once; the check can't tell which -R gh uses`.
- [ ] T024 [US3] Write failing tests in `tests/test_review_gate.py` for the command shape rules (R4, FR-012b):
  1. A match after a commit, a push, a `cd`, a `git switch`, or a second match is refused with `run gh pr create on its own; the check judges the branch before anything earlier in the command runs`. Cover `git commit -am fix && git push && gh pr create --fill`, `cd ../x && gh pr create`, and `gh pr create --fill && gh pr merge 630`.
  2. A quoted separator counts: `bash -c "git push && gh pr create"` is refused.
  3. `$(`, a backtick, `<(`, and `>(` in the matched command are refused with `run gh pr create without a substitution; the shell runs it after the check has judged the branch`.
  4. `GIT_DIR=../630-x/.git`, `GIT_WORK_TREE=`, `GH_REPO=owner/other`, `NO_COLOR=1`, and `env -C ../630-x` before the match are refused with `run gh pr create without an environment prefix or env; the check can't see where it points gh`.
- [ ] T025 [US3] Write failing argument tests in `tests/test_review_gate.py` (R4, How the check reads the arguments):
  1. `gh pr merge -s 630`, `--subject=fix 630`, `-tfix 630`, `-sd 630`, and `-st fix 630` are judged as PR 630.
  2. `gh pr merge -sx 630` is refused with `can't read the pull request this command names`, and so are two pull request arguments, an unknown flag, and a `shlex.split` failure.
  3. `gh pr merge --help` and `-h` exit 0.
  4. `gh pr merge --auto` is refused with `auto-merge would merge a head this check never judged`.
- [ ] T026 [US3] Write failing tests in `tests/test_review_gate.py` for another repository, another branch, and where the check reads from (R4, R5, FR-012a, FR-012c):
  1. `gh pr -R owner/other merge 630`, `gh -R owner/other pr merge 630`, `gh pr -Rowner/other merge 630`, `-R github.com/owner/other`, and `-R ghe.example.com/<this repo>` are refused with `-R names another repository; its reviews aren't here`.
  2. `gh pr -R github.com/<this repo> merge 630` is judged, with the host dropped before comparing.
  3. `gh api -X PUT repos/owner/other/pulls/630/merge` is refused with `the path names another repository; its reviews aren't here`, and `gh api -X PUT repos/{owner}/{repo}/pulls/630/merge` is judged as PR 630.
  4. `gh pr create --head forkowner:630-x` is refused with `--head names another owner's branch; its reviews aren't here`. `--head <this owner>:630-x` is judged as `630-x` at the commit `git ls-remote origin refs/heads/630-x` returns.
  5. From the `604-x` worktree, `gh pr merge 630` and `gh pr create --head 630-x` are refused with `run this from the checkout on main; a worktree opens and merges only its own branch's pull request`, whether `630-x` is reviewed or not (scenario 10).
  6. From the `main` checkout, `gh pr merge 630` judges `630-x` by its own records, reviewed and unreviewed (scenario 8). `trunk_branch` returns `origin/main` there, and the check strips `origin/` before comparing.
  7. A lookup that fails, times out, or names a commit missing from the local repository gives the error refusal (scenario 9).
  8. Judging another branch creates no state directory for it (`resolve_agent_dir(..., create=False)`).
  9. `WFCTL_STATE_DIR` set while another branch is judged is refused, saying the override names one branch.
  10. `WFCTL_BRANCH` naming a branch other than the one checked out in `cwd` is refused, saying the override names a different branch from the session's directory.
  11. A payload `cwd` in the `630-x` worktree, while the hook process runs in the `main` checkout, is judged by `630-x`'s records.
  12. A matched command with no `cwd`, or a `cwd` outside any git repository, gives the error refusal naming the missing working directory.
- [ ] T027 [US3] Write failing tests in `tests/test_review_gate.py` for the wrong refusals spec.md's Edge Cases documents. Each test asserts exit 2, asserts the refusal message, and checks that the rewording the spec names isn't refused:
  1. `gh api -f merge_method=merge repos/{owner}/{repo}/pulls/630/merge -X PUT` is refused as an environment prefix. Writing the path first is judged as PR 630.
  2. `gh api -X PUT repos/:owner/:repo/pulls/630/merge` is refused as another repository. The `{owner}/{repo}` form is judged.
  3. A review-comment reply through a variable path, such as `gh api "repos/{owner}/{repo}/pulls/comments/$ID/replies" -f body=x`, is refused with the `write the gh api path out plainly` message. The path written out isn't matched.
  4. `grep "gh pr create\|gh pr merge" wfctl/` is refused on a reviewed branch. Pattern 8's plain-verb rule fires, since the verb after the first `gh pr` is `create\|gh` and holds a backslash, so assert the `write gh's command words out plainly` message. The separator rule also fires on the second match, because a quoted `|` precedes it, so assert that the plain-verb line is present rather than that it is the only line. Name both rules in the docstring. `rg 'gh pr.*merge'` is refused with the unlisted-word message, since the word after `gh` is `pr.*merge`. `grep "pr create" wfctl/` isn't matched.
  5. `which gh && gh pr view` is refused with the unlisted-word message. `which gh` on its own isn't matched.
  6. A commit message quoting `gh "$X" merge 630` is refused with the unlisted-word message. `git commit -F <file>` isn't matched.
- [ ] T028 [P] [US3] Write failing sign-off coverage tests in `tests/test_review.py` (R9, FR-014): a sign-off covers a group's unreviewed commits when each is the signed-off commit or one of its ancestors. A commit added after it isn't covered. Each sign-off overwrites `sign-off.json` (`{"sha", "at"}`).
- [ ] T029 [P] [US3] Write failing CLI tests in `tests/test_review_cli.py` for `wfctl review sign-off` (FR-013, FR-014, R9). Monkeypatch `isatty` on stdin and stdout:
  1. Without a terminal on either one, it prints `✗ wfctl review sign-off needs a person at an interactive terminal` and exits 1.
  2. It lists the covered commits per group, then asks `Type <sha> to sign off on these commits:`. The seven-character head sha writes `sign-off.json`, prints `✓ signed off through <sha>`, appends `review-sign-off` (`sha`), and exits 0.
  3. Anything else typed prints `✗ not signed off; nothing written`, writes nothing, and exits 1.
  4. With nothing unreviewed, it prints `nothing unreviewed; no sign-off needed` and exits 0.
  5. It works with no completed run at all, since a sign-off doesn't wait for three rounds.
- [ ] T030 [P] [US3] Extend `tests/test_guard_entry.py`: a payload that matches the review check, run through the real entry point, imports neither `typer` nor `rich`. An `ls` payload doesn't import `wfctl._review_gate`. Keep `test_a_command_with_no_path_asks_git_nothing` passing for a payload with none of `gh`, `merge`, or `sign`.

### Implementation for User Story 3

- [ ] T031 [US3] Create `wfctl/_review_gate.py` with the prefilter and patterns 1 to 7 from R6. The guard tests for `gh` in any case, `merge`, and `sign` before importing this module. The program word `gh` matches in any case, and everything after it stays case-sensitive. Import nothing that imports `typer` or `rich`. Verify with `uv run pytest tests/test_review_gate.py -q -k "match or sign"` and T022.
- [ ] T032 [US3] Add pattern 8 to `wfctl/_review_gate.py`: the fixed list of `gh`'s own commands from R4 (`alias`, `api`, `attestation`, `auth`, `browse`, `cache`, `codespace`, `completion`, `config`, `extension`, `gist`, `gpg-key`, `help`, `issue`, `label`, `licenses`, `org`, `pr`, `preview`, `project`, `release`, `repo`, `ruleset`, `run`, `search`, `secret`, `skill`, `ssh-key`, `status`, `variable`, `version`, `workflow`, without `copilot` and `agent-task`), the one plain `-R` allowed before a command word, and the plain-verb rule. Drop one quote or backtick at the end of a word before reading it. Verify with T023.
- [ ] T033 [US3] Add the shape rules to `wfctl/_review_gate.py`: a separator (`;`, `&`, `|`, newline, quoted or not) before a match, a substitution from the start of the text to the end of the matched command, and a `NAME=value` word or `env` before the match. Judge every match, and refuse the whole text on one refusal. Verify with T024.
- [ ] T034 [US3] Add argument reading to `wfctl/_review_gate.py`: split from the matched verb to the next unquoted `;`, `&&`, `||`, `|`, or newline with `shlex.split`, using the `merge` and `create` flag tables in R4, grouped short flags read letter by letter, `--flag=value`, `-h`/`--help`, `--auto`, and `-R` counted across all three places. Verify with T025.
- [ ] T035 [US3] Add judged-branch resolution to `wfctl/_review_gate.py`: `git -C <cwd> rev-parse --show-toplevel`, `resolve_branch` and `resolve_agent_dir(..., create=False)` with `repo_root` and `timeout`, `gh repo view` only when an `-R`, a `repos/` path, or an `owner:` prefix is present, `gh pr view` for a merge, `git ls-remote origin refs/heads/<branch>` for `--head`, the trunk-checkout rule with `origin/` stripped, and the `WFCTL_STATE_DIR` and `WFCTL_BRANCH` refusals. Every `gh` and `git` call runs in `cwd` with the module's 5-second timeout. Verify with T026.
- [ ] T036 [US3] Add judging and refusal text to `wfctl/_review_gate.py`: unreviewed commits per group from `_review`'s range at the judged head, the sign-off ancestor test, the refusal block grouped by group in run order, and the error refusal. Wrap everything after a match in one `try` that turns a timeout, a non-zero exit that isn't an answer, or any exception into the error refusal. Verify with T021 and T027.
- [ ] T037 [US3] Call the review check from `worktree_guard` in `wfctl/_hook.py` before the `"/" not in command` fast path, in its own `try`, passing the payload's `cwd`. A refusal prints to stderr and returns 2. An allow goes on to the worktree check unchanged. Update the function's docstring to say it runs both checks. Verify with `uv run pytest tests/test_review_gate.py tests/test_guard_entry.py tests/test_worktree_guard.py -q`.
- [ ] T038 [US3] Add sign-off coverage and writing to `wfctl/_review.py`. Verify with T028.
- [ ] T039 [US3] Add `wfctl review sign-off` to the `review` group in `wfctl/cli.py`, with the terminal check, the commit list, and the typed sha. Verify with T029.
- [ ] T040 [US3] Repeat the T002 timing with the same command and record the after number beside the baseline in `/Users/andremarin/Development/wfctl-specs/622-security-review-panel/guard-timing.md`. Verify that the difference is under 1 ms (SC-003), and compare both numbers with the per-call figures in the `_hook.py` module docstring, as spec.md's Validation Strategy asks. Put both numbers in the commit message of the change that wires the check into `_hook.py`.
- [ ] T041 [US3] Run quickstart.md step 2 by hand in this worktree. Verify that `uv run wfctl hook worktree-guard` exits 2 and lists this branch's commits under `security` and `code`.
- [ ] T042 [US3] Validate Phase 4 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: An agent can't open or merge a PR with unreviewed commits through any command the plan specifies, and only a person can sign off.

---

## Phase 5: User Story 4 - A reviewer blocked from writing still gets its report counted (Priority: P2)

**Goal**: `wfctl relay <id> --reason TEXT --from PATH` saves a blocked reviewer's report as that reviewer's, marked as relayed with the reason, and the roster shows it.

**Independent Test**: Relay a report with a block reason and run `wfctl review check`. The line reads `✓ relayed:` with that reason, and the run completes.

**Verification**:

- Automated: `tests/test_review.py`, `tests/test_review_cli.py`, `tests/test_review_gate.py`
- Manual: quickstart.md step 4
- Evidence: `<id>.md` in the run folder starting with the `Relayed:` and `Relayed-at:` header

### Tests for User Story 4 ⚠️

- [X] T043 [P] [US4] Write failing relay tests in `tests/test_review.py` (FR-017, US4 scenarios 1 to 3, `622-blocked-reviewer-relays-report.md` Verification):
  1. A relayed report naming the head counts, and the roster line reads `s2 claude ✓ relayed: write denied`.
  2. The saved file starts with `Relayed: <reason>`, `Relayed-at: <UTC time>`, a blank line, then the report verbatim.
  3. A relay with no reason, or a blank one, is refused, and the run stays incomplete.
  4. A relayed report naming an older commit doesn't count.
  5. A relay appends `review-relay` (`group`, `run`, `id`, `reason`).
- [X] T044 [P] [US4] Write failing CLI tests in `tests/test_review_cli.py` for every row of the `wfctl relay` table in contracts/cli.md: saved, `--reason` missing or blank, `--from` missing, a file that doesn't exist or can't be read, an empty file, an id not in the latest run, and an id that already has a report. Check that the command never reads stdin, by passing stdin text and asserting it isn't saved.
- [ ] T045 [US4] Write a failing test in `tests/test_review_gate.py`: on an unreviewed branch, `wfctl relay s2 --reason "write denied" --from <file>` is allowed when the file quotes `gh pr create`, `pulls/630/merge`, and "review sign-off", since the report's text isn't in the command (R8).

### Implementation for User Story 4

- [X] T046 [US4] Add the relay to `wfctl/_review.py`: find the group by the id's letter, check the id is in that group's latest run with no report yet, write the header and the report with `_io.write_atomic`, and append the event. Show the reason on the roster line. Verify with T043.
- [X] T047 [US4] Add the top-level `wfctl relay` command to `wfctl/cli.py`, reading the report only from `--from`. Verify with T044 and T045.
- [X] T048 [US4] Run quickstart.md step 4 by hand. Verify that `uv run wfctl review check security` shows `✓ relayed: write denied` on `s3`.
- [X] T049 [US4] Validate Phase 5 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: A blocked reviewer's findings count, and the roster says they were relayed and why.

---

## Phase 6: User Story 5 - A repository chooses its reviewers and adds its own groups (Priority: P3)

**Goal**: `wfctl check config` reports every `review` finding. `review start` warns about a model whose command isn't on `PATH`, leaves its reviewers out, and never completes a run where no reviewer can run. `AGENTS.md` documents the key.

**Independent Test**: With the config.md example in `wfctl.json`, `wfctl review start security` lists `s1` to `s4`, two Claude and two Codex, and `wfctl review start code` lists `c1` to `c3`, all Claude.

**Verification**:

- Automated: `tests/test_review_config.py`, `tests/test_review.py`, `tests/test_review_cli.py`
- Manual: `uv run wfctl check config` on this repository
- Evidence: the `⚠` line and `✗ unavailable` roster lines for a model not on `PATH`

### Tests for User Story 5 ⚠️

- [X] T050 [P] [US5] Write failing tests in `tests/test_review_config.py` that run `wfctl check config` through `CliRunner` with `NO_COLOR` pinned. Each finding from T006 prints as one `- ` line under `✗ wfctl.json:` and exits 1, alongside the existing `steps` and `trunk` findings. A valid `review` key passes (US5 scenarios 2 to 4, FR-021).
- [X] T051 [P] [US5] Write failing availability tests in `tests/test_review.py` (R7, FR-023, US5 scenario 5):
  1. A model whose command's first word `shutil.which` can't find is written to `run.json` as `"state": "unavailable"` with a reason such as `` `codex` not found on PATH ``.
  2. `check` doesn't expect a report from it, and the run completes on the other reviewers' reports.
  3. When every reviewer is unavailable, `start` still writes the run record and `check` never completes it.
  4. A model on `PATH` that writes no report reads as `no report`, and the run stays incomplete.
  5. Claude has no command and is always available.
- [X] T052 [P] [US5] Write failing CLI tests in `tests/test_review_cli.py` for contracts/cli.md's availability output: the command printed after each Codex reviewer, `s3 codex  ✗ unavailable`, the `⚠ codex: …; s3 and s4 left out of this run` line, the every-reviewer-unavailable `⚠` line with exit 0, the roster reason `unavailable: <reason>`, and `incomplete: no reviewer in security could run` with exit 1.

### Implementation for User Story 5

- [X] T053 [US5] Add `_review_config.load`'s problems to `check_config_cmd` in `wfctl/cli.py`, and update its docstring to name the `review` key. Verify with T050.
- [X] T054 [US5] Add the availability lookup to `review start` in `wfctl/_review.py` and its output in `wfctl/cli.py`. Verify with T051 and T052.
- [X] T055 [US5] Add a "Declaring reviewers" section to `AGENTS.md` beside "Declaring what a change must carry" and "Declaring a stage of your own". Cover what `commands` and `groups` hold, the default of three Claude reviewers, that security and code always run first, how ids are formed, that `check config` reports problems and `review start` warns about a missing command, and why the key lives in `wfctl.json`. Load `writing-style` first. Verify by copying the section's example into a scratch `wfctl.json` and checking that `_review_config.load` returns no problems for it, and that `uv run wfctl check config` passes on this repository.
- [X] T056 [US5] Validate Phase 6 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl check config` — merge gate

**Checkpoint**: A repository can add models and groups, and a bad declaration is a finding rather than a silent drop.

---

## Phase 7: User Story 6 - The security reviews ship with wfctl (Priority: P3)

**Goal**: `security-and-hardening` and the `/security-review` file ship under `wfctl/agents/skills/`, credited the way `vendor-upstream-skills.md` requires. A wfctl-owned `reviewing-security` skill tells each security reviewer how to run both over wfctl's commit range.

**Independent Test**: Run `uv run wfctl install-skills --agent claude` and find both security reviews in the installed tree, credited as research.md R10 says.

**Verification**:

- Automated: `tests/test_skill_attribution.py`, `tests/test_skill_frontmatter.py`, `tests/test_skill_cross_references.py`, `tests/test_packaging.py`, `tests/test_bundle.py`
- Manual: the installed tree under `.agents/skills/` and `.claude/skills/` after `install-skills`, and `uv run wfctl doctor`
- Evidence: `cmp` showing the `/security-review` file is byte-identical to upstream, and a diff showing `security-and-hardening/SKILL.md` differs from upstream only by its last line

### Tests for User Story 6 ⚠️

- [X] T057 [US6] Extend `tests/test_skill_attribution.py` (R10 item 6). Keep `_TEMPLATE_ROW` as `specify/templates/`, so `_listed_templates()` and the template tests don't change. Add `_NOTICED_ROWS` holding `specify/templates/` and `agents/skills/reviewing-security/references/`, and have `_listed()` drop rows under either one. Add a test that each row under the second prefix names a file that exists under `wfctl/`, that no line of that file matches `_LINE`, and that the file's path is named under its upstream's section in `wfctl/agents/skills/NOTICES.md`. Add that test's reader of path claims to `_declaration_sources`, so a path named twice in the notice fails. Write the docstrings to say why. Verify that the new test fails before T060 and T061.

### Implementation for User Story 6

- [X] T058 [P] [US6] Vendor `skills/security-and-hardening/SKILL.md` and `skills/security-and-hardening/references/hardening-patterns.md` from `addyosmani/agent-skills` into `wfctl/agents/skills/security-and-hardening/`, at one upstream commit you record in the commit message. Append the attribution line `Derived from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT, © 2025 Addy Osmani).` as the last line of `SKILL.md`, the same as `idea-refine`, and edit nothing else. Vendor the upstream's top-level `references/security-checklist.md` to `wfctl/agents/skills/security-and-hardening/references/security-checklist.md`. Verify with `diff` against the fetched upstream files, and with `uv run pytest tests/test_skill_frontmatter.py -q`. If the frontmatter test rejects upstream's frontmatter, stop and tell Andre rather than editing the file, since `vendor-upstream-skills.md` allows only the attribution line.
- [X] T059 [P] [US6] Vendor `.claude/commands/security-review.md` from `anthropics/claude-code-security-review` to `wfctl/agents/skills/reviewing-security/references/security-review.md` byte for byte, at one upstream commit you record in the commit message. Read the upstream's `LICENSE` for the MIT terms and the copyright holder. Verify with `cmp` against the fetched file.
- [X] T060 [US6] Edit `wfctl/agents/skills/NOTICES.md`. Add `security-and-hardening` to the `addyosmani/agent-skills` section's list. Add an `anthropics/claude-code-security-review` section in the existing sections' shape, naming `reviewing-security/references/security-review.md` by path and carrying the copyright line from T059. Verify with `uv run pytest tests/test_skill_attribution.py -q`.
- [X] T061 [US6] Amend `docs/architecture/vendor-upstream-skills.md` in place (R10 item 4). Add a `security-and-hardening` | `addyosmani/agent-skills` row to the skills table in alphabetical order. Add an `agents/skills/reviewing-security/references/security-review.md` | `anthropics/claude-code-security-review` row to the file table. Change "The templates are the one case where the notice stands in for the line" to name this file as the second case. Add a sentence giving R10 item 5's reason: the file ends on the instruction that defines the reviewer's whole reply, so a line after it is the last thing the reviewer reads. Add the Log line `amended — anthropics/claude-code-security-review's /security-review file credited by NOTICES.md, as the templates are (#622)` with today's date. Load `writing-style` first. Verify with `uv run pytest tests/test_skill_attribution.py tests/test_arch_records.py -q`.
- [X] T062 [US6] Write `wfctl/agents/skills/reviewing-security/SKILL.md`, a wfctl-owned skill with no attribution line (plan.md, What the skill rewrites say, item 3, and R10 item 7); verify with `uv run pytest tests/test_skill_frontmatter.py tests/test_skill_cross_references.py tests/test_skill_attribution.py -q`. Load `writing-style` first. It tells a security reviewer to do four things:
  1. Run both reviews over the commit range `wfctl review start` printed, reading `../security-and-hardening/SKILL.md` and `references/security-review.md` by path, since Claude Code's built-in `/security-review` would otherwise take its place.
  2. Skip the `/security-review` file's git section.
  3. Read the checklist at `security-and-hardening/references/security-checklist.md`, not the `../../references/` path the vendored skill cites.
  4. Write one report covering both reviews, with a `Reviewed: <sha>` line and a verdict at the end, to the path `wfctl review start` printed. Say that this outranks the vendored file's last line, its "Do not use the bash tool or write to any files" line, and its sub-task steps when the reviewer can't launch sub-tasks, and that its `allowed-tools` frontmatter doesn't apply because the file is read as a reference.
- [X] T063 [US6] Run `uv run wfctl install-skills --agent claude` in this worktree and check that `security-and-hardening` (with both references) and `reviewing-security` (with `references/security-review.md`) are in the installed tree, along with the updated `NOTICES.md`. Verify with `uv run wfctl doctor` exiting 0 and `uv run pytest tests/test_packaging.py tests/test_bundle.py -q`. A run in a fresh scratch repository needs Andre, since the worktree guard refuses commands in a second checkout.
- [X] T064 [US6] Validate Phase 7 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl doctor` — merge gate

**Checkpoint**: Every repository that installs wfctl's skills has both security reviews, credited.

---

## Phase 8: User Story 1 - Every change gets a security review before the code review (Priority: P1)

**Goal**: `opening-a-change` runs every group `wfctl review groups` lists, security first, and `fanning-out-code-review` drives each group through `wfctl review start`, `wfctl relay`, and `wfctl review check`. The findings reach Andre in chat as one table, and none go in the PR description.

**Independent Test**: In a repository with no `review` key, run `opening-a-change` on a branch with one commit. Three security reviewers report, then three code reviewers report on a commit that includes the security group's fixes. One findings table reaches the chat, and the PR description holds no finding.

**Verification**:

- Automated: `tests/test_review_cli.py`, `tests/test_review_fanout_skill.py`, `tests/test_opening_a_change_panel.py`, `tests/test_skill_commands.py`, `tests/test_panel_stays_out_of_the_body.py`
- Manual: one `opening-a-change` run on a real branch after `uv run wfctl install-skills --agent claude`
- Evidence: the rosters for `security` and `code` in chat, one findings table naming reviewer id and model (such as `s3 codex`), and a PR body with no finding

### Tests for User Story 1 ⚠️

- [ ] T065 [P] [US1] Write failing CLI tests in `tests/test_review_cli.py` for `wfctl review groups`: with no `review` key it prints exactly `security  reviewing-security  s1 s2 s3 claude` and `code      code-review         c1 c2 c3 claude`, a custom group prints after them, and an invalid `review` key prints the `check config` findings and exits 1 (contracts/cli.md).
- [ ] T066 [P] [US1] Update `tests/test_review_fanout_skill.py` for the rewritten skill. Retire the tests that run bash fences the rewrite removes: the roster check, the undispatched check, their zsh variants, and the two-fence comparison. `wfctl review check` replaces those fences, and `tests/test_review.py` now holds the verdict-anchor spellings (T010). Update `test_the_skill_still_names_the_test_that_holds_the_anchor_open` to name the T010 test. Add tests that the skill starts a group with `wfctl review start`, launches one reviewer per printed id with the range and the reports path, tells each reviewer to write `Reviewed: <sha>` and end with a verdict, relays with `wfctl relay <id> --reason "…" --from <file>`, says never to put a report in a command's text, finishes with `wfctl review check`, and no longer writes to `$FEATURE_DIR/reviews/`. Keep the tests that still hold.
- [ ] T067 [P] [US1] Update `tests/test_opening_a_change_panel.py` and `tests/test_skill_commands.py` for the rewritten skill. Check that it runs every group from `wfctl review groups` in order with no condition that skips one, commits the security group's fixes before the code group starts, reports one findings table with reviewer id and model, puts no finding, table, or status line in the PR body, and stops after three complete rounds to ask for a sign-off. Check that Step 5 shows `wfctl check-body` and `gh pr create` as two separate commands, each naming `/tmp/pr-body-<branch>.md` with the branch written out, with no `$(`, no environment prefix, and no chaining. Add a test that pipes Step 5's `gh pr create` line, with this test's branch name in it, into `_hook.worktree_guard` on a reviewed branch and gets exit 0, so the skill's own command passes the shape rules.

### Implementation for User Story 1

- [ ] T068 [US1] Add `wfctl review groups` to the `review` group in `wfctl/cli.py`. Verify with T065.
- [ ] T069 [US1] Rewrite `wfctl/agents/skills/fanning-out-code-review/SKILL.md` per plan.md, What the skill rewrites say, item 2. Take each group's skill from `wfctl review groups`, since `review start` doesn't print it. Keep the instruction that the coordinator checks a relay reason against what it saw and reports a gap to Andre when the reviewer wasn't really blocked. Load `writing-style` first. Verify with `uv run pytest tests/test_review_fanout_skill.py -q`.
- [ ] T070 [US1] Rewrite `wfctl/agents/skills/opening-a-change/SKILL.md` per plan.md, What the skill rewrites say, item 1, sub-items 1 to 6. When the review check refuses with an error, the skill says to stop and tell the person, naming the error, without retrying in another spelling. When it refuses another branch's PR, the skill leaves that PR to the checkout on the trunk branch. Load `writing-style` first. Verify with `uv run pytest tests/test_opening_a_change_panel.py tests/test_skill_commands.py tests/test_panel_stays_out_of_the_body.py -q`.
- [ ] T071 [US1] Run `uv run wfctl install-skills --agent claude`, then `uv run wfctl doctor`. Then run `opening-a-change` (`wfctl/agents/skills/opening-a-change/SKILL.md`) end to end on this branch at PR time, with no `review` key: the security group (`s1` to `s3`) runs, its fixes are committed, the code group (`c1` to `c3`) covers them, one findings table reaches the chat, and the PR body holds no finding (US1 scenarios 1 to 3). Verify by reading both rosters from `uv run wfctl review check security` and `uv run wfctl review check code`, and the body file before `gh pr create`.
- [ ] T072 [US1] Validate Phase 8 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl doctor` — merge gate

**Checkpoint**: Every change gets both groups before its PR opens, and wfctl holds the record.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation that spans stories, and the end-to-end run.

- [ ] T073 Update the Safety section of `AGENTS.md`. It says wfctl doesn't gate outward actions. After this change, the review check is the one refusal wfctl makes. An agent that meets it runs the review groups rather than reporting a host refusal with `wfctl report-block`, and when the check refuses with an error, a person can run the command in their own terminal. Load `writing-style` first. Verify by rereading the section against plan.md's `knowledge-placement` gate, and with `uv run pytest -q`.
- [ ] T074 Run quickstart.md steps 1 to 9 in this worktree. Two checks need Andre, so ask him for both: step 8, since `wfctl review sign-off` runs only at his terminal, and US6's fresh-repository `install-skills` run that T063 leaves to him, since the worktree guard refuses commands in a second checkout. Verify each step's stated result, and that the `wfctl store specs` commit in step 9 has no path under `reviews/`. At step 7, the security group runs again on a branch with an earlier review, so also check that each security reviewer's findings stay inside the fix commit's range and that wfctl counts its report (US6 scenario 2).
- [ ] T075 Reread `changes/622.addition.md` against what shipped and correct it if a behavior changed during the build. Verify with `uv run python .github/scripts/check_release_note.py`.
- [ ] T076 Validate Phase 9 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl check config`, and `uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T002 has to run before any code change.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every story.
- **US2 (Phase 3)**: Depends on Phase 2.
- **US3 (Phase 4)**: Depends on US2, since the gate reads `_review`'s range and records.
- **US4 (Phase 5)**: Depends on US2. T045 adds to `tests/test_review_gate.py`, so it follows T020.
- **US5 (Phase 6)**: Depends on US2. It extends `review start` and `check config`.
- **US6 (Phase 7)**: Depends only on Phase 2, and can run beside US2 to US5.
- **US1 (Phase 8)**: Depends on US2, US3, US4, and US6. Its skill text names their commands and the gate's shape rules, and T067 runs Step 5's command through the gate.
- **Polish (Phase 9)**: Depends on every story.

### Within Each User Story

- Tests come first and fail before the implementation task that names them.
- In US3, the `_review_gate.py` tasks T031 to T036 build on each other in order, and T037 wires them in last.
- The `tests/test_review_gate.py` tasks run in order, since they share one file.

### Parallel Opportunities

- T004 and T006 (different files).
- In US2: T009, T012, and T013.
- In US3: T028, T029, and T030 beside the `test_review_gate.py` sequence.
- In US4: T043 and T044.
- In US5: T050, T051, and T052.
- In US6: T058 and T059, and the whole of US6 beside US2 to US5.
- In US1: T065, T066, and T067.

## Parallel Example: User Story 6 beside User Story 2

```bash
# One agent builds the records:
Task: "Write failing range tests in tests/test_review.py"           # T009
Task: "Write failing CLI tests in tests/test_review_cli.py"          # T012
Task: "Write a failing test in tests/test_review_store.py"           # T013

# Another vendors the security reviews:
Task: "Vendor security-and-hardening into wfctl/agents/skills/"      # T058
Task: "Vendor security-review.md into reviewing-security/references/" # T059
```

## Parallel Example: User Story 3

```bash
# Beside the tests/test_review_gate.py sequence (T020 to T027):
Task: "Write failing sign-off coverage tests in tests/test_review.py"      # T028
Task: "Write failing sign-off CLI tests in tests/test_review_cli.py"       # T029
Task: "Extend tests/test_guard_entry.py for the review check's imports"    # T030
```

---

## Implementation Strategy

### MVP First (User Story 2)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US2). wfctl now records which commits each group reviewed, and the roster comes from wfctl.
3. Stop and validate with the US2 independent test.

US2 alone doesn't stop anything, because nothing reads the record before a PR opens. US2 and US3 together are the first increment that enforces the review.

### Incremental Delivery

1. Setup and Foundational give the timeouts and the group loader.
2. US2 gives the records and the roster.
3. US3 gives the gate and the sign-off. This is the first enforcing increment.
4. US4 gives the relay, so a blocked reviewer doesn't leave a run that can never complete.
5. US5 gives other models, custom groups, and the `check config` findings.
6. US6 ships the security reviews. It can land any time after Phase 2.
7. US1 rewrites the skills that drive the rest, and its end-to-end run is the feature's acceptance.

## Notes

- `_review_config.py`, `_review.py`, and `_review_gate.py` import nothing that imports `typer` or `rich`, since the guard imports all three on a matched command.
- No new row goes in `MANAGED_HOOKS`, and the hook keeps the name `worktree-guard`.
- The three-round cap ships as an instruction in `opening-a-change` only. #626 decides how rounds are counted, so no task counts rounds in wfctl.
- Comments explain why the code has its shape. Anything that only makes sense beside the diff goes in the commit message.
