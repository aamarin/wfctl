# Research: plan-walkthrough

Every decision below was checked against the code on this branch. Line numbers
are as of 82d40ae.

## R1. Where the `needs_person` check sits in the pass reading

- **Decision**: Inside `_pass_states` (`wfctl/_pipeline.py:365`), after the
  pass's reader returns and before the cascade flag is set. If the reading is
  `done`, the pass is `done`. If it is not, and the pass carries
  `needs_person` and `auto_approve` is on, the pass is `skipped` with the
  annotation "needs a person; auto-approve is on". Otherwise the reading
  stands, as it does today.
- **Rationale**: FR-011 orders the checks as claim, then evidence, then
  `needs_person`, then the reader. For a declared pass the reader is the
  evidence check (`build_file_exists_reader`, `_declared.py:202`), so checks 2
  and 4 are one call, and putting the new branch after that call gives the
  required order with a single read. A skip set here does not set `cascade`,
  the same as a claimed skip (`_pipeline.py:400-403` uses `continue` before the
  cascade line), so a pass declared after this one is still read.
- **Alternatives considered**: Checking `needs_person` before calling the
  reader loses on order, since a marker a person wrote would then read
  `skipped` while auto-approve is on, which Story 3 scenario 3 forbids. Reading
  the evidence file a second time, apart from the reader, duplicates the one
  thing the reader already does.

## R2. How `auto_approve` reaches the pass reading

- **Decision**: `build_report` (`_pipeline.py:869`) reads the approval mode
  once, before `_infer_steps`, and passes it down as a keyword argument
  `auto_approve: bool = False` through `_infer_steps` to `_pass_states`. The
  later read at `_pipeline.py:922` uses the same value instead of reading the
  file again.
- **Rationale**: `_pass_states` has no `agent_dir` today, and the value is
  already read in `build_report`, only after inference. One read with two
  consumers is the pattern `build_report` already follows for evidence, since
  two reads can disagree while another process is writing. A default of
  `False` keeps `infer_pipeline` (`_pipeline.py:677`, which has no caller in
  `wfctl/`) and every test that calls `_infer_steps` directly unchanged.
- **Alternatives considered**: Passing `agent_dir` down and reading the mode
  inside `_pass_states` loses because it reads the same file twice per report
  and puts session state inside a function that today reads only artifacts.

## R3. Where `needs_person` lives on a pass

- **Decision**: A new field `needs_person: bool = False` on `SubStep`
  (`_pipeline.py:49`), set only by `_declared._load_step`. `_PipelineSubStep`
  (`_pipeline.py:225`) carries it too, and the payload builder
  (`_pipeline.py:968-977`) emits it beside `manual`.
- **Rationale**: `SubStep` is the declared shape, and `manual` is already folded
  into it as `command is None`. `needs_person` cannot be folded into an
  existing field, since it changes the reading only under one mode. The
  default keeps every built-in pass unchanged.
- **Alternatives considered**: Keeping the flag in `_declared` and passing a set
  of qualified names into `_pass_states` loses because it splits one pass's
  shape across two structures that have to agree on names.

## R4. The `check config` findings

- **Decision**: Two findings in `_declared._load_step`, right after the
  `command` and `manual` block (`_declared.py:153-162`), in the existing
  `f"{qualified} ..."` form:
  1. `{qualified} has a 'needs_person' that is not a boolean`
  2. `{qualified} declares 'manual' and 'needs_person' — a manual pass already stops an autonomous run`
  A pass with a finding is dropped, as every other finding does today.
- **Rationale**: FR-013. The form matches the sibling findings, so
  `check_config_cmd` (`cli.py:5431`) needs no change.
- **Alternatives considered**: None credible. A warning that keeps the pass
  would be the only finding in the file that does not drop it.

## R5. The status payload contract

- **Decision**: Add `"steps[].sub_steps[].needs_person": "boolean"` to
  `wfctl/contracts/status-payload.json` and bump `version` from `1.0` to `1.1`
  with `wfctl contract regenerate`, which also moves `STATUS_PAYLOAD_VERSION`
  (`_pipeline.py:12`).
- **Rationale**: An added key owes a minor bump
  (`tests/test_status_contract.py::test_an_added_key_fails_naming_the_path_and_owing_minor`),
  and `test_the_shipped_file_matches_the_union_in_both_directions` fails until
  the file names the new path. `autonomous-agent-skips-human-checks` already calls
  the key additive.
- **Alternatives considered**: Carrying the reason only in `annotation` and
  adding no key loses on FR-012, since a consumer would have to parse prose to
  tell this skip from an inherited one.

## R6. How the skill knows auto-approve is on

- **Decision**: The skill runs `wfctl status --json` first and reads the
  top-level `auto_approve` key. When it is `true`, the skill refuses as FR-014
  says and stops.
- **Rationale**: The key is already in the payload and in the contract, and
  the skill needs no new command. The skill cannot tell a typed command from
  one orchestrate issued (clarify Q1), so the mode is the whole test.
- **Alternatives considered**: A new `wfctl` verb for the mode loses because
  the payload already carries it.

## R7. The marker's plan hash

- **Decision**: The skill writes the sha256 of `plan.md` with `sha256sum`, or
  `shasum -a 256` where that is missing, and records the hex digest only.
- **Rationale**: macOS ships `shasum` and not `sha256sum`; most Linux systems
  ship both. The feature directory can sit outside the working tree, so a git
  object id is not available in every repository.
- **Alternatives considered**: `git hash-object` loses because the plan may not
  be in a git repository at all. A new `wfctl` command for the hash loses on
  scope, since nothing reads the hash yet (#502 would).

## R8. `_MIRRORED_SKILLS`

- **Decision**: No entry.
- **Rationale**: A name in that set suppresses the command wrapper on the
  mirroring layer (`cli.py:2818-2822`). The declaration names `/plan-walkthrough`,
  and `check config` finds it in `.agents/commands/` either way
  (`_is_installed`, `cli.py:5409`), so mirroring buys only native discovery.
  Native discovery would let an agent start the interview on its own reading of
  a phrase such as "grill me", and FR-006 says the agent never runs the
  interview on the person's behalf. The skill is reached through its command.
- **Alternatives considered**: Mirroring it, as `start-session` is, loses for
  the reason above.

## R9. Where the declaration is documented

- **Decision**: A new section in `docs/reference.md`, right after
  `## The pipeline` (line 25) and before `## What lands in your repo` (line
  67). It covers the `steps` key, `evidence`, `manual`, `before`, `after`, and
  `needs_person`, with the plan-walkthrough declaration as its example.
  `SKILL.md` points to that section in one line.
- **Rationale**: Clarify Q2. `docs/reference.md` is where `wfctl.json` keys are
  documented for a consuming repository (`change_check`, line 645), and it has
  no section on `steps` yet.
- **Alternatives considered**: Recorded in `docs/architecture/scans/500-clarify.md`.
