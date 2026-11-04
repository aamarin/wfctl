# Research: Read review.commands from the trunk

## R1: Where the commands get swapped

- Decision: `review start` in `cli.py` replaces each reviewer's command with the trunk's through `_review_config.with_commands`, before `_review.start`.
- Rationale: The groups keep coming from `_review_groups_or_exit` unchanged (FR-006), and only the command field changes. `start` keeps working on whatever `Group` it is given, so its other callers in tests are untouched.
- Alternatives considered: A required `commands` keyword on `_review.start`, like `cap`. We didn't choose it because `start` would then resolve commands it is also handed inside the group, and eight test call sites would change for no behavior.

## R2: One trunk read or two

- Decision: `trunk_commands` reads `wfctl.json` on the trunk on its own, beside `trunk_rounds`.
- Rationale: The read is two git calls on a small file, and `trunk_rounds` is already called from two places (`review start` and `_capped`). Sharing the read means changing `trunk_rounds`' signature, which `_capped` also uses.
- Alternatives considered: One helper returning the parsed `review` dict for both. Left to the refactor pass if the duplication reads badly.

## R3: A non-Claude reviewer with no command

- Decision: `_availability` treats it as unavailable, with a reason naming the trunk ref.
- Rationale: The roster and the `⚠` line already explain a reviewer that can't run, and the run completes on the rest (record Decision).
- Alternatives considered: Falling back to the branch's command for a model the trunk lacks. We didn't choose it because it reopens the hole for any new model.

## R4: A trunk whose commands can't be used

- Decision: No fallback in `review start`. A broken trunk `wfctl.json` stays refused by the group check, which runs first.
- Rationale: `required_at` parses the trunk with `_parse_at(rounds=False)`, and that parse still validates `review.commands`. So `review start` exits 1 on an unreadable file or invalid commands before it could read them (plan review PR-001). `test_start_refuses_when_the_trunks_file_cannot_be_read` already pins that refusal, and its docstring says why: CI can't read the group list from a broken file either.
- Alternatives considered: Validate the trunk's commands leniently in `required_at`, as it treats `review.rounds`. We didn't choose it because `required_at` is the reader the worktree guard and CI share, which this change stays out of, and a run started from a file CI can't read ends in a PR CI refuses.
