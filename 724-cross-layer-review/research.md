# Research: Reviewers check that each layer accepts the same input

## R1. Where the passes go in the rubric

- Decision: passes 7 and 8 in Step 4, after Over-engineering, with headings `**7. Input trace**` and `**8. Sibling paths**`.
- Rationale: `tests/test_review_fanout_skill.py` finds the passes by the pattern `^\*\*\d\. ([A-Za-z][A-Za-z &-]*)\*\*`, so both headings have to match it. Appending keeps the six existing numbers, which other text cites by name rather than number.
- Alternatives considered: folding the trace into Correctness and the sibling check into Architecture. We didn't choose this because the experiment's baselines had those passes and missed both bugs, and each procedure needs its own trail.

## R2. Where the trail and the severity floor go

- Decision: Step 5. The floor is one line under the severity table. The trail follows the findings and comes before `net:` and the verdict, with the report example extended to show it.
- Rationale: Step 5 already owns severity and the report format, and the coordinator reads the report in that order.
- Alternatives considered: the floor inside pass 7. We didn't choose it because severity is set in Step 5 for every pass, and a second place would drift.

## R3. Whether `requesting-code-review` is derived from upstream

- Decision: edit it in place, one phrase.
- Rationale: the change is the count in "(the six-pass rubric)". If the file is upstream-derived, a pull reverting that phrase reintroduces a wrong count, which the count search in quickstart.md finds. Tasks checks the file's attribution line before editing.
- Alternatives considered: dropping the count from the phrase. That's equally good and removes the next drift, so tasks may take it instead.

## R4. Whether to check report contents mechanically

- Decision: no check in this branch.
- Rationale: a reviewer's report is written in a scratch folder and relayed through `wfctl relay`, which counts reports and doesn't parse them. A check that the trail exists would need `_review*.py` changes, which #725 owns.
- Alternatives considered: a test that the rubric text names the trail. The pass-count test already ties the rubric's structure to the panel skill, and a test that a phrase exists is the kind `AGENTS.md` says doesn't carry its weight.

## R5. Neutral examples

- Decision: pass 7 uses a signup form that allows a 40-character username where the server caps it at 32. Pass 8 uses a commit that escapes HTML in a comment preview, where every other view of the same comment text should be checked.
- Rationale: these came from the experiment's cards, which replaced the PFMS bugs so the reviewers weren't given the answers. Neither is specific to one repository.
