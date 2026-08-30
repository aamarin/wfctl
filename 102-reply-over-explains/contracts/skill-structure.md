# Contract: the skill's structure

`conversation-response-shape` has no API. Its contract is the set of structural
properties other files depend on — and each item below is stated as something a
test in `tests/` could assert, because "the skill reads well" is not checkable
and everything here is.

## Consumers

| Consumer | Depends on |
| --- | --- |
| `start-session/SKILL.md` step 1 | the skill being reachable at `.agents/skills/conversation-response-shape` |
| `wfctl/agents/commands/conversation-response-shape.md` | the same path, for mid-session re-invocation |
| `tests/test_skill_cross_references.py` | both of the above, already asserted |
| `.github/pull_request_template.md` | the draw test and form selection living here, and only here (FR-007) |
| `speckit-delivery-plan`, `finishing-a-development-branch` | the same, once #556 lands |

## Invariants

### C-1 — Frontmatter keys stay as they are

`name` and `description` present; no `deployment` key, therefore no
`.claude/skills/` mirror; no `disable-model-invocation`, which would be inert
without the mirror.

FR-009 forbids changing this. #99 owns the question of whether it *should*
change — this feature must not pre-empt it.

*Assertable*: frontmatter key set is exactly `{name, description}`.

### C-2 — The precedence list is numbered, contiguous, and complete

Five rules after this change, numbered 1-5, each with a `## N. <name>` section
body in the same order.

*Assertable*: the numbered headings parse to `1..N` with no gaps, and the count
matches the list in the Precedence section.

### C-3 — Existing rule numbers do not move

Rules 1, 2 and 3 keep their numbers. Three in-file references (`SKILL.md:100`
twice, `:176`) resolve by number and no test covers them.

*Assertable*: headings `## 1.`, `## 2.`, `## 3.` still carry their current
titles.

### C-4 — `i-have-adhd` is referenced, never restated

The skill layers over the vendored file (`vendor-upstream-skills`). It may cite
`i-have-adhd`'s rules by number; it must not copy their text.

*Assertable, weakly*: no sentence from `i-have-adhd/SKILL.md` appears verbatim
in this file.

### C-5 — One owner for the draw test and form selection

The draw test and the form-selection table appear in this file and nowhere else
in `wfctl/agents/`. Other surfaces state the obligation and point here.

*Assertable*: the selection table's header row appears exactly once across
`wfctl/agents/**/*.md`.

This is the invariant most likely to rot, because #556 adds two more pointers
after this feature ships.

### C-6 — No example requires wfctl knowledge

FR-006, closing #80. No example uses a `wfctl` command, a pipeline step name, or
a wfctl-only path as the thing being illustrated.

*Assertable*: no fenced example block in this file contains `wfctl`.

Note the asymmetry — the skill may *mention* wfctl in prose about its own
installation; the constraint is on examples, which are what a downstream reader
has to decode.

### C-7 — The file stays under the line ceiling

450 lines, per `plan.md`'s budget. Not a correctness property; a decay-risk one.

*Assertable*: `wc -l` on the file.

## What is deliberately not a contract

- **Section order below the precedence list.** `Show`, `Judgment rules`,
  `Untangling`, `Three surfaces` may be reordered; nothing references them by
  position.
- **Wording of any rule.** The whole feature is a rewording; pinning phrasing in
  a test would make every future edit a test edit.
- **The examples themselves.** Constrained by C-6 only. Which example teaches a
  rule is editorial.
