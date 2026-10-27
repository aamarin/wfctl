# Research: The design checks match records to the contexts a branch changes

The Technical Context has no open unknowns. These are the decisions the plan makes beyond the two records, each with what it beat.

## R1. Read only the header of `design.md` and the domain page

- Decision: `listed` and `names` read the lines before the first `## ` heading, using `_arch._key_value`.
- Rationale: A `design.md` quotes `Contexts: …` in code blocks further down, as this feature's own does in its Behavior section. A full-file scan would read the first quoted line as the branch's list. The header is also where the domain page already keeps its `State` line, and `_key_value` already skips the `# title` line and indented lines.
- Alternatives considered: Scanning the whole file and skipping fenced code blocks. We didn't choose it because it adds a fence parser to catch a case the header rule never meets. Requiring `Contexts` on line 3 exactly. We didn't choose it because a title that wraps or a blank line would break the check with no visible cause.

## R2. One `pause` function with two `Level` constants

- Decision: `_contexts.pause(names, spec_dir, records, level)` returns the reason and remedy for both checks. `ARCHITECTURE` and `SOFTWARE_DESIGN` are `NamedTuple` constants carrying the record noun ("architecture record" or "software design record"), the pass name (`None` or `"brainstorm.software-design"`), and the "no" command.
- Rationale: The spec added three outcomes after the level-3 record was written: no `Contexts` line, a name not on the list, and a remedy naming the context. Each check would otherwise format all three itself, which repeats the rule the record moved into one module.
- Alternatives considered: Each check calling `unanswered` and formatting its own messages. We didn't choose it for the reason above. A `Protocol` per level. We didn't choose it because the two levels differ only in three strings, and a constant is enough.

## R3. Refuse a branch-wide "no" when the repo has a name list

- Decision: With a name list, `wfctl arch none`, `wfctl step none brainstorm.architecture`, and `wfctl step none brainstorm.software-design` without `--context` refuse and name the option. The pipeline's claim lookup also drops a whole-pass claim on either pass, so one written before the list existed doesn't answer the check.
- Rationale: FR-011 says a branch-wide "no" doesn't answer a listed context. If wfctl accepted it, the command would succeed and brainstorm would still pause, and the agent would learn why only from the pause. The refusal says so when the command runs. For `step none`, it also keeps #648's pipeline from reading the whole-pass claim and hiding the row.
- Alternatives considered: Accepting the bare form and ignoring it in the check. We didn't choose it because the command would report success for an answer nothing reads, and a bare `step none` claim would hide the software design row, which FR-010a rules out.

## R4. `--context` on `step none` only for `brainstorm.software-design`

- Decision: `step none` refuses `--context` on any other pass.
- Rationale: The software design pass is the only pass the contexts check reads. A per-context "no" on a repo-declared pass such as `brainstorm.ui-design` would be written and never read.
- Alternatives considered: Accepting it on every pass. We didn't choose it because nothing reads those files, so the command would record an answer to a question nobody asked.

## R5. `governs` names are split by one function in `_arch`

- Decision: `_arch.split_names(value)` splits on commas, trims each entry, and drops empty ones. `parse_record` and `_contexts` both call it.
- Rationale: The domain page's header lines, the `Contexts` line, and the `governs` field are all comma-separated lists of the same names, so one split rule keeps them comparable. It sits in `_arch` because `_contexts` imports `_arch`, and the reverse import would create a cycle.
- Alternatives considered: YAML list syntax for `governs`. We didn't choose it because frontmatter is scanned line by line, not parsed, and a multi-line list would need a parser for one field.

## R6. The done display lists each per-context "no"

- Decision: When a check passes and at least one context was answered with a "no", its done `Assessment` carries a `display` of `<context>: no — <reason>` lines.
- Rationale: FR-010a asks `wfctl status --all` to show each per-context "no". A done `Assessment` with `display` already renders beside the row, as `DRAWINGS_UNCHECKED` does, so this needs no change to the renderer.
- Alternatives considered: A new `claims` list on the pass in the status payload. We didn't choose it because it changes the payload's shape for one display, which `pipeline-state-is-one-payload` would require every view to handle. Tasks verify how the display renders under `--all` before committing to it.

## R7. The Boundary line asks the same function as the architecture check

- Decision: With a name list and a `design.md`, `_observe` reads the Boundary line from `_evidence.context_gap`, the function the architecture reader calls. Otherwise it reads the line as #635 leaves it.
- Rationale: A restarted session reads the Boundary line before anything else. Under #635, the line sees only a branch-wide "no" or a touched record. A branch that answered every context with a "no" would read "unanswered" while `wfctl status` shows the pass done, and a branch whose only record governs the wrong context would read "answered". The next session would then redo finished work or skip unfinished work. Calling one function from both places keeps them in agreement.
- Alternatives considered: Calling `_architecture_answered` from `_observe`. We didn't choose it for the reason #635's R6 gives: that function returns `None` past `spec.md`, so the line would read "answered" on every branch past specify. Leaving the line as #635 has it. We didn't choose it because of the disagreement above. The user chose this in the plan walkthrough on 2026-10-26.

## R8. The guard's contradiction check reads per-context "no" answers

- Decision: The worktree guard refuses `gh pr create` and `gh pr merge` when the branch's own `exceptions/<context>/boundary.md` exists and a level-2 record the branch touches governs that same context.
- Rationale: #635 added the check because an agent can write a "no" early and add a record later, and both the gate and the PR body then carry a wrong answer to the reviewer. With a name list, every "no" is per context, so a guard that reads only the branch-wide file never fires. The check runs only when something changed after the "no", which is a record for the same context showing up later. A record for a different context doesn't make the "no" wrong.
- Alternatives considered: Checking the "no" right after `arch none` writes it. We didn't choose it because the contradicting record usually comes later, sometimes during implementation, which is why #635 put the check at PR open. Treating any touched record as a contradiction, as #635 does for the branch-wide file. We didn't choose it because a "no" for session continuity stays true when the branch adds a record about install and drift. The user chose this in the plan walkthrough on 2026-10-26.
