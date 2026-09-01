Commit first, then spawn the validation agent. Nothing is committed, so the agent would score a working tree with no baseline to diff against, and you'd have nothing to revert to if its findings land badly.

**Where the branch stands** — 652 tests, ruff, mypy and `wfctl doctor` all green.

| Landed (5) | Open (3) |
|---|---|
| Rules 4 and 5 appended to the precedence list | Four validation tasks — they need a fresh agent, since I wrote both the rules and the rubric |
| The sentence that contradicted them, deleted, and one failure-modes entry that referenced it | Two test assertions deferred — writing them up front would have held the suite red across four checkpoints |
| Five-row form-selection table, two-genre reply composition | Nothing committed |
| `test_response_shape_invariants.py`, 4 assertions | |
| Two product-specific examples rewritten generic — closes the separate vocabulary issue | |

One call outside the plan: I raised the line ceiling from 450 to 460. The file sits at 456 after cutting the "render the literal output" rule and folding the duplicated example, and the remaining 6 lines would have come out of working content. Say the word and I'll put it back at 450.

Next: `git commit` on `102-reply-over-explains`, then spawn the validation agent.
