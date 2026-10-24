# CLI contract: `check-body` and `check config`

## `wfctl check-body <path>`

The argument and the existing drawing and verification findings are unchanged.
The change adds section findings between them:

```
found = _shape.body_findings(body)
      + _sections.load_required(repo_root) problems
      + _sections.body_findings(body, required)
      + _verification_finding()
```

| Repo state | Body | Output | Exit |
| --- | --- | --- | --- |
| no `change_sections` | any | same as before this change | same as before |
| lists "Needs a spec?" | section answered | `✓ <path>: the drawings look right` | 0 |
| lists "Needs a spec?" | heading deleted | `⚠ "Needs a spec?" is missing. This repository asks every pull request to answer it.` | 1 |
| lists "Needs a spec?" | only the HTML comment | `⚠ "Needs a spec?" is empty. The template's comment under that heading says what to write.` | 1 |
| lists "Needs a spec?" | `N/A` | `⚠ "Needs a spec?" holds N/A. The template's comment under that heading says what to write.` | 1 |
| lists "Needs a spec?" | `No.` | `⚠ "Needs a spec?" answers yes or no with no reason. The template's comment under that heading says what to write.` | 1 |
| `change_sections` is `"x"` | any | `⚠ wfctl.json: 'change_sections' must be a list of section headings` | 1 |
| outside a git repo | any | same as before (no section findings) | same as before |

Outside a git repo there's no `wfctl.json` to read, so `check-body` reads no
sections, the same way `_verification_finding` already returns nothing there.

## The template comment the messages point at

The empty, N/A, and no-reason messages say "The template's comment under that
heading says what to write" (research R1). So the comment is the only place the
agent learns what a real answer looks like, and SC-005 depends on its text. This repo's
`.github/pull_request_template.md` gains this section after Issue Links:

```markdown
## Needs a spec?
<!--
Did this change need a full spec? Answer yes or no, then give the reason in one
sentence. For example: "No. It fixes an off-by-one in check-body and moves no
boundary." A yes or no with no reason fails the check. N/A and None aren't
answers here, since every change either needed a spec or didn't.
-->
```

The comment names "None" as well as N/A because `opening-a-change` Step 4
offers both for an empty section. `check-body` reports only N/A (research R5).

## `wfctl check config`

Adds `_sections.load_required` problems and `_sections.template_problems` to
the problems it already collects, printed under the existing
`✗ wfctl.json:` header and exiting 1.

```
$ wfctl check config
✗ wfctl.json:
  - wfctl.json: 'change_sections' lists "Needs a spec?", which .github/pull_request_template.md doesn't have
```

A `wfctl.json` whose `change_sections` is valid and fully covered adds no line
to the success output. The docstring's list of keys it validates gains
`change_sections`.
