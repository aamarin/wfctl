# Task

You have just finished a piece of work for the user. Write the reply that
reports it. Nothing else — no code, no tool calls, just the reply as it would
appear in their terminal.

These are the facts. All of it is done and verified; none of it is in question.

- Three files changed on branch `102-reply-over-explains`:
  `wfctl/agents/skills/conversation-response-shape/SKILL.md` (388 → 456 lines,
  +133/−63), `tests/test_response_shape_invariants.py` (new, 4 assertions),
  `.github/pull_request_template.md` (+6/−6).
- 652 tests pass, ruff clean, mypy clean, `wfctl doctor` green.
- What landed: two new rules appended to the skill's precedence list (rule 4
  "establish the subject", rule 5 the register rule), a deleted sentence that
  contradicted them, a new test for when to draw a diagram, a five-row
  form-selection table, and a two-genre reply composition. Two examples that
  used product-specific vocabulary were rewritten to be generic, which closes a
  separate open issue.
- Along the way you made three calls: you cut a rule called "render the literal
  output" because a control run showed it fires at the same rate when absent;
  you folded a worked example that the new selection table duplicated; and you
  raised a line-count ceiling from 450 to 460 because after both cuts the file
  sat at 456 and the remaining 6 lines would have come out of working content.
  The first two were pre-approved in the plan. The third was not.
- Two things the plan did not anticipate: one of the file's "failure modes"
  entries referenced the sentence you deleted and had to go too, and you had to
  defer two test assertions to later tasks because writing them up front would
  have held the suite red across four checkpoints.
- Four validation tasks are not done — they need a fresh agent because you wrote
  both the rules and the scoring rubric, so a self-scored pass proves nothing.
- Nothing is committed.

The user's next decision is whether to spawn a fresh agent for the four
validation tasks, or to commit what exists first.
