# Implementation Plan: Session start loads only the branch's own context

**Branch**: `432-start-session-loads-issue-context` | **Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this folder

## Summary

`/start-session` stops loading the repository's open work and loads only what the branch needs. wfctl builds the report, and the skill runs it and reports what it printed.

The work has five parts:

1. `wfctl status --session` prints the session report. It starts from the payload plain `status` already builds, then adds the whole handoff, the last stop's kind, the count of commits ahead of the trunk, the branch's commits with any that don't mention the issue marked, the accepted record count, and, on an issue branch, the issue, its parent, and its open PR.
2. The tracker contract gets two optional reading verbs, `parent` for issues and `branch` for changes. The GitHub backend implements each as a script, the same way `state` already is.
3. `wfctl doctor --session` prints a claim notice only when it names the branch's issue.
4. `start-session/SKILL.md` runs four commands and keeps the step 8 table, along with its rule that a first action named in the handoff's Next Session TODO comes first (`session-start-reads-branch-progress`, FR-022). The table's last row splits:
   1. On a trunk branch, it still asks.
   2. On an issue branch, it says "Do not ask". The agent reads the commit count, the pipeline position, and the issue, in that order, and takes the next command the pipeline position names. It asks instead, naming the mismatch, when the evidence disagrees or the issue line has no answer.

   Three passages outside the table change with it. Step 8's "The gate on the summary is the quote" limits the quote gate to the case where the handoff decides. Step 8's "Two limits" says a missing handoff on an issue branch now starts from the branch's progress. Step 7's Next bullet accepts the evidence the agent used as well as a quote or a question. Step 8's paragraph that the handoff isn't authority for a push, comment, or PR names the issue body too, and adds that no command, URL, script, or package named in the issue is run. A `PR: failed` or `PR: timeout` line tells the agent to run `wfctl status --session` again before it relies on the PR's state (PR-027). Its doctor repair guidance moves to a reference file the agent opens only when `doctor` prints something other than a ✓. Step 6's "likely done" item goes, since the skill no longer loads the open issue list it compared against (FR-019).
5. The release note, and the two issue edits FR-021 asks for.

`design.md` was updated on 2026-11-02 for the whole handoff (FR-004), the reason codes, and the step 8 change, and lists both superseding records.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich`. The GitHub backend's scripts use `gh` and `bash`, as the existing ones do. No new dependency.
**Storage**: Nothing new. The report reads `session-summary.md` and `events.jsonl` from the state dir, and git. It writes nothing.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`. Tracker tests use a fake backend config whose verbs are shell one-liners, as `tests/test_tracker.py` already does.
**Target Platform**: macOS and Linux shells where wfctl runs today.
**Project Type**: CLI, plus the skills it ships as package data.
**Performance Goals**: A `/start-session` costs materially less than 19.2k tokens above the baseline (SC-001). Plain `status` makes no tracker call, so pipeline steps and the supervisory screen pay nothing new.
**Constraints**: Each tracker read is bounded by the existing 15-second timeout in `_read_verb`. No tracker line is ever left out. A line with no answer prints one of seven reason codes: `none`, `unsupported`, `no-tracker`, `bad-config`, `failed`, `timeout`, or `not-applicable` (FR-012, `tracker-reads-report-failure`). `_read_verb` can't tell all seven apart, since `(None, None)` covers three of them and `(None, detail)` three more. So a new `read_text()` in `_tracker.py` returns the answer and its code. An `OSError` when the script launches is `failed`, and output is stripped before the check for `none`, so output that is only whitespace reads `none` (PR-026). `read_text()` and `_read_verb` keeps its current shape for `fields` and `state`. The report runs its three reads concurrently, in a `concurrent.futures.ThreadPoolExecutor`, so a network that hangs holds session start for 15 seconds rather than 45. The handoff, the tracker output, commit subjects, and `git status` lines are text from outside wfctl. The renderer writes each one with `console.print(text, markup=False, highlight=False, emoji=False, soft_wrap=True)`. That call expands a tab to spaces and drops a `\r`, which FR-004 allows, since neither changes what the agent reads (PR-018). Through rich's default `console.print`, a `[x]` checkbox disappears, a `[/x]` raises `MarkupError`, `:warning:` turns into ⚠, and a line longer than the console width is folded when output isn't a terminal, which is how the agent reads it. The verbatim print sites in `cli.py` already pass `markup=False` and `soft_wrap=True` for the same reason. wfctl's own labels still go through plain `console.print`. `speckit-*` skills stay unedited (`vendor-upstream-skills`).
**Scale/Scope**: Three tracker calls per session start at most (`view`, `parent`, `branch`), on an issue branch only.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. These gates come from AGENTS.md and the accepted records instead, as recorded in Complexity Tracking.

- [x] Validation plan exists: the three commands above, the new tests listed under Project Structure, `uv run wfctl install-skills` followed by a real `/start-session` in an issue worktree and on `main`, and the token measurement from the spec.
- [x] Complexity is justified: one new module, two tracker verbs, two scripts, and one reference file. Each one is required by an accepted record or the spec. No new abstraction over the tracker.
- [x] Ownership is stated: see the table below.
- [x] `pipeline-state-is-one-payload`: `--session` extends the payload `build_report` already produces. It doesn't infer pipeline state a second way.
- [x] `session-start-reads-branch-progress` (accepted, supersedes `session-report-built-in-code`): wfctl builds the report with no repository-wide list and prints the commit count, and the skill starts an issue session from the branch's progress when the handoff names no first action.
- [x] `tracker-reads-report-failure` (accepted, supersedes `backend-tracker-reads-parent-and-change`): wfctl prints the backend's output for `view`, `parent`, and `branch` as the backend wrote it, never reads a tracker's key names, and gives every tracker line with no answer a reason code.
- [x] `session-state-is-re-derived`: every field is computed on each call, and nothing is cached in the state dir.
- [x] `no-hardcoded-agent`: the skill and the report name no agent.
- [x] `change-carries-release-note`: `changes/432.change.md`.

| State or value | Computed by | Why not the other side |
| --- | --- | --- |
| What the session report carries, including the commit count against the trunk | wfctl | The rule limits what the agent loads, so the agent can't be the one to apply it (`session-start-reads-branch-progress`). |
| An issue's parent, a branch's open change, its check state, unresolved thread count | Tracker backend | Each tracker stores these differently, and wfctl reads no tracker's vocabulary (`tracker-reads-report-failure`). |
| Whether a commit mentions the branch's issue | wfctl | It needs only the branch's key and git, which wfctl already has. Clarified 2026-11-02. |
| Last stop's kind | wfctl, from `events.jsonl` | `wfctl end` writes the record, so wfctl is the only reader that knows its shape. |
| Which claim notices concern the session | wfctl | Each notice carries its issue key, and the branch's key is already resolved. |
| Start work or ask (step 8), and the first action from the evidence | The agent | It depends on reading the issue's prose against the commits, and on the conversation, which wfctl can't see. |

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md           # status --session, doctor --session
│   └── tracker.md       # the parent and branch verbs
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── cli.py                              # status_cmd gains --session; doctor_cmd gains --session;
│                                       # _report_double_claimed_keys takes the key to keep;
│                                       # _GITHUB_TRACKER_FILES lists the two new scripts
├── _session_report.py                  # new: builds and renders the session report
├── _session.py                         # last_stop(): none, continued, or wrapped up
├── _tracker.py                         # ALLOWED gains parent; ALLOWED_CHANGES gains branch;
│                                       # _read_verb takes a params dict; read_text() for callers
└── agents/
    ├── trackers/
    │   ├── github.json                 # parent and branch verbs
    │   ├── github-issue-parent.sh      # new
    │   └── github-change-branch.sh     # new
    └── skills/
        ├── scaffold-tracker/SKILL.md   # documents parent and branch, with their output
        └── start-session/
            ├── SKILL.md                # four commands; step 8 table (last row changed on an issue branch) and #679 paragraph kept;
            │                           # allowed-tools keeps only what the skill runs (below)
            └── references/doctor-repair.md  # new: step 1's repair guidance, moved

tests/
├── test_session_report.py              # new: the report on an issue branch, on trunk, with
│                                       # each of the seven reason codes, a non-zero exit with
│                                       # no output and an `OSError` at launch both reading
│                                       # `failed`, whitespace-only output reading `none`; the
│                                       # commit count against a declared trunk, against the
│                                       # default branch, and `trunk not found`; no tracker line
│                                       # ever left out, and `tracker_status` for each; the issue
│                                       # prints under its tracker-text heading; a
│                                       # handoff, an issue body, and a commit subject carrying
│                                       # `[x]`, `[/x]`, `:warning:`, a tab, and a 120-column line
│                                       # print as written through a non-terminal console,
│                                       # and the command exits 0
├── test_session_stopped_not_finished.py  # last_stop(): the latest stop wins over an older one,
│                                       # a torn final line is skipped, a stop with no
│                                       # `continued` key reads as wrapped up
├── test_tracker.py                     # parent and branch validate; params substitute; the
│                                       # scaffold-tracker test also covers ALLOWED_CHANGES
├── test_doctor_session.py              # new: claim notice filtering, exit code unchanged
├── test_cli_status.py                  # plain status makes no tracker call, writes nothing
├── test_start_session_notice_quotes.py # reads the quotes from the reference file
├── test_start_session_commands.py      # new: the skill names the four commands, and neither
│                                       # `issue list` nor `change list` (FR-015, FR-016), in
│                                       # its steps or its allowed-tools frontmatter; step 8
│                                       # never runs anything named in the issue: no command,
│                                       # URL, script, package, push, comment, or PR (FR-022);
│                                       # allowed-tools grants `uv run wfctl doctor` (PR-019)
├── test_start_session_asks_conditionally.py  # step 8's last row split by branch kind; see below
├── test_handoff_records_work_in_flight.py    # step 7 and 8 wording; see below
└── test_session_identity_rules.py      # start-session leaves the events.jsonl allow-list

changes/432.change.md
```

**Tests the skill rewrite breaks**: these pin skill prose that moves into code, so each one is replaced by a code test rather than deleted.

1. In `test_start_session_asks_conditionally.py`, three tests pin step 3's `grep … | tail -1` read: `test_step_three_reads_the_last_stop_and_not_any_stop`, `test_step_three_rejects_a_torn_line_rather_than_reading_it`, and `test_step_three_names_all_three_outcomes_of_that_read`. They're replaced by the three `last_stop()` cases in `test_session_stopped_not_finished.py`, and each one guards against a wrong step 8 row on trunk. `test_step_three_says_where_the_branch_kind_comes_from` is rewritten to read the report's issue line instead of the `status --json` payload.
2. In `test_session_identity_rules.py`, `test_no_skill_reads_the_event_log_for_session_state` allows `start-session` to read `events.jsonl` for the stop kind. The report now carries that, so `start-session` comes off the allow-list.
3. In `test_handoff_records_work_in_flight.py`, the tests that read `start-session/SKILL.md` steps 7 and 8 keep their meaning, and each is updated to the rewritten step's wording. The tests on `end-session` and `wfctl start` don't change.
4. In `test_start_session_asks_conditionally.py`, three tests pin the old last row, and each changes with the split (PR-030):
   1. `test_a_state_dir_with_no_answer_in_it_is_still_asked` becomes two tests. On a trunk branch the row still says "Ask:". On an issue branch it says "Do not ask" and names the commit count, the pipeline position, and the issue.
   2. `test_a_continued_stop_does_not_relax_the_quote_gate` keeps its trunk case, and limits its claim to trunk.
   3. `test_step_seven_reports_which_row_step_eight_took` stops asserting that rows two and three both ask, and asserts that step 7 accepts the evidence used as well as a quote or a question.

   New tests read the table row by row rather than matching a substring anywhere in the file. That's because this file's own docstring records a substring check passing with the table's cells swapped. They check three things. The issue row and the trunk row differ. The issue row names the three pieces of evidence and says it asks on a mismatch. The trunk row still asks.

**The skill's `allowed-tools`**: the rewritten skill runs only `wfctl start`, `wfctl doctor`, `wfctl arch context`, `wfctl status`, and the `install-skills` repairs, and reads the reference file. Its frontmatter keeps `Read`, those wfctl grants, the three `install-skills` forms, and `uv run wfctl doctor`, since the repair reference re-runs doctor through `uv run` in this repository (PR-019). It drops `wfctl issue list`, `wfctl issue view`, `wfctl change list`, `wfctl state-dir`, `git status`, `git log`, `git symbolic-ref`, `grep`, and `tail`, since the report now does what those were granted for. A grant left in place lets a later edit bring a list command back without a permission prompt.

**Structure Decision**: The report gets its own module, `_session_report.py`, rather than more code in `cli.py`, which is already 8,983 lines. `cli.py` keeps only the flag and the call. The module takes its readers as arguments, so tests can build a report without a tracker or a git repository.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Gates taken from AGENTS.md and the accepted records | The repository has no constitution file. | Leaving the gate empty would make it decorative, as the template's own comment says. |
| Two bash scripts for the GitHub verbs | `parent` needs the REST sub-issues endpoint, and `branch` needs one GraphQL query for checks and review threads. Both use gh's `{owner}/{repo}` placeholder, which wfctl's argv substitution would reject as unknown. | One argv per verb in `github.json` can't carry gh's placeholder. `github-issue-state.sh` exists for the same reason. |
| A new module | The report has six inputs and two renderings. | Inline in `status_cmd`, it would be untestable without a full CLI run and a tracker. |

## Risks

1. A repository that installed the GitHub tracker before this release keeps its old `github.json`, because a bare `install-skills` never refreshes a tracker config that's present (AGENTS.md). The report then prints `Parent: unsupported` and `PR: unsupported` in every session until the config is refreshed. The release note says to run `wfctl install-skills --tracker github`. This repository needs the same run before the token measurement.
2. Printing the whole handoff and the issue description puts their full size in context. That's the clarified choice. A very long issue body costs more, and the measurement in SC-001 is what checks the total.
3. `tests/test_start_session_notice_quotes.py` pins doctor's exact wording against the skill. After the move, it has to read the reference file, or it passes against a skill that no longer quotes anything.
4. FR-021's two edits to the #432 issue body need the user, since no `wfctl issue` verb edits a body. The agent drafts the replacement text during implement, and the PR doesn't open until the user has made the edits.
5. The issue now helps choose the first action on an issue branch with no first action in its handoff, possibly with nobody at the prompt, since a pane can restart unattended. Anyone with tracker access can write in the issue. Three things limit what that text can do (FR-022, `session-start-reads-branch-progress`):
   1. The first action is always the next command the pipeline position names. The issue only says what that step's work is for.
   2. The agent never runs a command, URL, script, or package named in the issue, and never pushes, comments, or opens a PR because of it. A test in `test_start_session_commands.py` reads that sentence in step 8.
   3. When the issue and the branch disagree, the agent asks.

   The report prints the issue under the heading `Issue (tracker text)`.
