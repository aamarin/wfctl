---
name: 'speckit-orchestrate'
description: 'Read pipeline state after a speckit step completes, then auto-advance or surface the next command based on the step auto flag.'
---

## Steps

0. **Epic-inherited spec check** — run before trusting wfctl's own inference.
   A sub-issue worktree has no spec dir under its own branch name, so
   `wfctl status`/`resume` can report "no spec dir found" and default to
   `brainstorm` even when the epic's spec/plan/tasks/decompose are done and this
   sub-issue is mid- or post-implementation.

   `wfctl` closes part of this gap itself: `resolve_spec_dir` tries the exact
   branch dir, then a key glob, then the same lookup against each ancestor branch
   nearest-first. **Do not delete this step on the strength of that.** The
   ancestor leg needs the sub-issue branch to be a git descendant of the epic's
   branch, which nothing arranges — worktrees branch off the target branch — and
   the glob legs miss whenever the sub-issue's key differs from the epic's, which
   is the normal case. The check below resolves both, because it matches on the
   issue key recorded in `delivery.md` rather than on branch ancestry or
   directory name.

   Check: run `wfctl feature-paths` and read `FEATURE_DIR` from that output —
   the plain command, not `eval "$(…)"`, which the command's pre-approval would
   not match, costing an approval prompt on every run.
   Substitute the real path everywhere below. It resolves through this repo's
   recorded spec root, which may be outside the working tree — never assume the
   spec dir is inside the repo. If that directory does not exist:
   - Resolve the active tracker's key format: read `key_pattern` from whichever
     `.agents/trackers/*.json` exists (default `\d+` — GitHub's bare-numeric
     default — if no tracker config or no `key_pattern` field). Build a match
     regex `#?{key_pattern}` — optional leading `#`, since GitHub issues are
     conventionally written `#123` in prose while other trackers' keys (e.g.
     `PROJ-123`) never take one.
   - Find every `delivery.md` under the spec root — the parent of `FEATURE_DIR`,
     so the search follows the spec root wherever it points. Use `Glob` with that
     absolute directory as its path; a spec root outside the working tree is a
     normal case here, not an edge one. In each file's "Issue Grouping Map"
     table, search
     every row for that regex. A row whose match equals the current issue's key
     means that `delivery.md`'s directory is the real spec dir, and the row's
     `Tasks` column is this sub-issue's task range. (Older delivery.md files may
     predate the standardized `{issue-key}`-leads-the-cell format — the regex
     search-anywhere-in-row approach still finds them.)
   - If found, ignore wfctl's brainstorm default:
     - For a GitHub-backed repo, `gh pr list --head {current-branch}` is a cheap
       non-blocking nicety — an open/merged PR means the sub-issue is past
       `implement`; report that instead ("PR #N open, awaiting review" / "PR #N
       merged — story complete"). Skip this check for other trackers; the six
       standard verbs don't include a by-branch change lookup.
     - No PR found (or non-GitHub tracker) → sub-issue is at `implement`
       (spec/plan/tasks/decompose are already done at the epic level); next
       command is `/speckit.implement` scoped to the resolved task range, not
       `/speckit.brainstorm`.

1. Run `wfctl status` and display the output so the user can see the updated pipeline position.

2. Run `wfctl resume`. It re-infers the step, records the advance, and refuses
   here if the boundary question went unanswered — none of which the read below
   does.

3. Run `wfctl status --json` and read `next_command` and `auto` off the payload.
   Not `$(wfctl state-dir)/next-step.md`: that file is written once per
   `resume`/`next` and holds whatever was true then, observed 2.5 hours stale
   during #114. `--json` re-derives from the artifacts on disk at the moment
   you ask.

4. Branch on the result:

   **Story complete** (`next_command` is `null`):
   - Display: "Story complete — open PR or run `/end-session`."
   - Stop.

   **`auto` is `true`**:
   - Strip the leading `/` from `next_command` (e.g. `/speckit.plan` → `speckit.plan`)
   - Output on its own line: `EXECUTE_COMMAND: {command-without-slash}`

   **`auto` is `false`**:
   - Display: "Next: run `{next_command}` when ready."
   - Stop.
