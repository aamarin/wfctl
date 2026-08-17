# GitHub Issue Template for `/speckit.decompose`

Use this template when converting `tasks.md` items into GitHub issues.

## Native GitHub Metadata First

Prefer native GitHub fields over repeating the same data in the Markdown body.

- `title`: Required. This is the ticket title. Do not add a `Ticket Title` field
  to the body.
- `assignees`: Use only when explicitly provided or confidently derivable. Do
  not use placeholder values such as "Team member's name".
- `labels`: Apply only labels that already exist in the repository or are part
  of a repo-local standard. Do not fail issue creation because a guessed label
  does not exist.
- `milestone`: Use when the feature or release target is explicit. Prefer this
  over a free-text deadline in the body.
- `issue type`, `project`, `priority`, `target date`, `dependencies`,
  `sub-issues`: If the current client supports them, set them natively instead
  of duplicating them in Markdown.

## Fields To Remove From The Body By Default

These fields are usually redundant or drift-prone when GitHub metadata exists:

- `Ticket Title`
- `Assigned To`
- `Status`
- `Deadline`

Only include one of these in the body when the user explicitly asks for it and
there is no reliable native field available in the current toolchain.

## Fields To Include In The Body

These improve issue quality and make the task actionable without forcing a full
spec reread:

- Summary sentence
- `Context`
- `Entry Points`
- `Acceptance Criteria`
- `Verification`
- `Dependencies`
- `References`
- `Estimate`
- `Additional Notes` (optional)
- `Out of Scope` (optional, for scope-control or debt issues)

## Body Template

```md
{summary sentence}

## Context

- Feature: `{feature_id}`
- Source Task: `{task_id}`
- Phase: `{phase_title}`
- Story: `{story_id_or_none}`
- Priority: `{priority_or_none}`
- Why: {1-3 concise bullets or sentences describing why this task matters now}

## Entry Points

- `{relative/file/path.ts}`
- `{relative/other-file.ts}`

## Acceptance Criteria

- [ ] {criterion derived from the task description, spec, or validation step}
- [ ] {criterion derived from tests, commands, or observable behavior}

## Verification

- Automated: `{test file, test name, or command}`
- Manual: `{manual validation step}`
- Evidence: `{expected artifact, output, or observable result}`

## Dependencies

- Depends on: `{task ids, issue numbers, or "None"}`
- Blocks: `{task ids, issue numbers, or "None"}`

## References

- Spec: `{feature_dir}/spec.md`
- Plan: `{feature_dir}/plan.md`
- Tasks: `{feature_dir}/tasks.md`
- Related: `{contract, quickstart, research, decision record, or issue references as needed}`

## Estimate

{X-Y hours or Small/Medium/Large if the source material does not support an hour estimate}

## Additional Notes

- Validation: `{command or manual verification}`
- Constraint: `{important non-obvious limitation}`
```

## Quality Rules

- Keep the first sentence human-scannable.
- `Context` should explain why, not restate the task verbatim.
- `Entry Points` must be specific files, not directories or vague concepts.
- `Acceptance Criteria` must be measurable and testable.
- `Verification` should map each acceptance criterion to an automated test,
  validation command, or explicit manual check.
- `Dependencies` should reference exact task IDs or issue numbers when known.
- `Estimate` should be omitted only when the available artifacts cannot support
  even a rough estimate.
