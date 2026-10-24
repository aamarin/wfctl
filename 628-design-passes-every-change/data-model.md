# Data model: design passes on every change

This feature adds no stored state. It adds one config key and two finding
shapes. The spec answer itself lives in the PR body, in the "Needs a spec?"
section.

## `change_sections` in `wfctl.json`

The list of PR section headings every PR body in this repo has to answer.

```json
{ "verify": [ … ], "change_check": [ … ], "change_sections": ["Needs a spec?"] }
```

- **Owner**: the repo. wfctl ships no section names, so only the repo can say
  which of its own template's sections need a real answer.
- **Absent or `[]`**: nothing is required, and `check-body` behaves as it does
  today.
- **Valid value**: a list of non-empty strings. A duplicate is kept once.
- **Invalid value**: anything else. `load_required` returns no names and one
  problem per fault, in the same wording as `_change.load_required`:
  - `wfctl.json: 'change_sections' must be a list of section headings`
  - `wfctl.json: 'change_sections' entry 2 must be a section heading, got int`
  - `wfctl.json: 'change_sections' entry 2 is empty`

## Section finding

One line `check-body` prints for one listed section. It's computed by
`_sections.body_findings(body, required)`, a pure function of the body text and
the list.

| State | When | Line, without the `⚠` marker |
| --- | --- | --- |
| missing | no ATX heading outside a fence matches the name | `"<name>" is missing. This repository asks every pull request to answer it.` |
| empty | the section holds nothing once HTML comments and whitespace are stripped | `"<name>" is empty. The template's comment under that heading says what to write.` |
| N/A | what's left matches `n/?a\.?`, case-insensitive | `"<name>" holds N/A. The template's comment under that heading says what to write.` |
| no reason | what's left matches `(yes\|no)[.!]?`, case-insensitive | `"<name>" answers yes or no with no reason. The template's comment under that heading says what to write.` |
| answered | anything else | no line |

The heading match is case-insensitive and trimmed. A section runs to the next
ATX heading of the same or a higher level.

## Template finding

One line `check config` prints for one gap between `change_sections` and the
repo's PR templates. Computed by `_sections.template_problems(repo_root,
required)`.

| State | Line |
| --- | --- |
| no template found | `wfctl.json: 'change_sections' lists sections, but no PR template was found` |
| template lacks a section | `wfctl.json: 'change_sections' lists "<name>", which <template path> doesn't have` |
