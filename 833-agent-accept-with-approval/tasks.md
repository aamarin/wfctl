# Tasks: Agent accepts with approval

**Input**: Design documents from `specs/833-agent-accept-with-approval/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md
**Design records**: `docs/architecture/design/prompted-spellings-one-table.md` (level 3, proposed); `docs/architecture/prompt-approves-person-commands.md` (level 2, accepted, carries the threat model)

**Before T001**: #407 (`407-auto-approve-mid-session`) has merged to `main`, and this branch is rebased on it. If it hasn't, stop and tell the user. Don't stack on the unmerged branch.

Every command runs through `uv run`. Shell commands that name the three person-only commands in their text are refused by the current guard, so tests and probes put that text in files rather than in a command line.

## Phase 1: Setup

- [X] T001 Rebase `833-agent-accept-with-approval` on `main` once #407 has merged, and confirm `ASK_RULES` and `_ManagedRule` exist in `wfctl/cli.py`; verify with `uv run pytest -q` green before any change
- [X] T002 Create the release note with `uv run towncrier create 833.change.md --content "…"` in `changes/833.change.md`, describing what a wfctl user notices; verify with `wfctl verify`'s release-note check

## Phase 2: Foundational (blocks every story)

- [X] T003 Create `wfctl/evidence/_prompted.py` with `Prompted(command, words)`, the five-entry `PROMPTED` tuple from `data-model.md`, `prompted_match(text) -> Prompted | None` (raw-text, literal, case-sensitive prefix match on the text with only trailing whitespace stripped, followed by a space or the end, per plan review PR-021), and `prompted_host() -> bool` (true when `CLAUDECODE` is non-blank); verify with T005
- [X] T004 Export `PROMPTED`, `Prompted`, `prompted_match`, and `prompted_host` from `wfctl/evidence/__init__.py` in its lazy re-export style; verify with `uv run python .github/scripts/check_imports.py` and `uv run mypy`
- [X] T005 [P] Write `tests/test_prompted.py`: each entry matches its plain form with and without arguments; a leading space, a quoted word, a backslash, and another case don't match; `prompted_host()` is false with `CLAUDECODE` unset or blank and true when it is `1`; verify with `uv run pytest tests/test_prompted.py -q`
- [X] T006 [P] Add `CLAUDECODE` to the variables the autouse fixture in `tests/conftest.py` removes (plan review PR-006); verify with `uv run pytest -q` passing inside Claude Code

## Phase 3: User Story 4 - The guard keeps refusing what the prompt can't see (P1)

Done first among the stories, since Stories 1 - 3 depend on the guard letting the plain spelling through.

**Goal**: one reader for all three commands, and a pass check that lets through only the plain spelling Claude Code will ask for.

**Independent Test**: every form in both records' lists, run through `read()` with a Claude Code payload and the rule present, is refused or let through as the lists say.

**Verification**: `uv run pytest tests/test_review_gate.py tests/test_accept_check_threat_model.py tests/test_guard_entry.py -q`

- [X] T007 [US4] Generalize `_accepts` in `wfctl/_review_gate.py` into `_runs_person_command(text, words, nested="")`, taking the command's words in every place the reader names `arch` and `accept` today, and keeping the dry-run handling specific to the accept; verify with T011
- [X] T008 [US4] In `wfctl/_review_gate.py`, delete `_SIGN_OFF` and `_APPROVE_IMPORTS`, and have `read()` call `_runs_person_command` once each for `("arch", "accept")`, `("review", "sign-off")`, and `("arch", "approve-imports")`; verify with T011
- [X] T009 [US4] Add `_prompt_will_ask(command, payload, cwd) -> str | None` to `wfctl/_review_gate.py` with the six conditions in `plan.md §The guard`: literal prefix match via `prompted_match`; no `$`, backtick, `\`, `;`, `&`, `|`, `<`, `>`, `(`, `)`, or newline; `shlex.split` succeeds and gives the same words with `comments=True`; `tool_name == "Bash"`; `.claude/settings.json` parses and carries the entry's rule (missing or malformed counts as missing); `auto_approve(agent_dir)` is false, with an unresolvable agent dir counting as on. Give the git calls that resolve the agent dir the module's `TIMEOUT` (plan review PR-008); verify with T012
- [X] T010 [US4] Change `read(command)` to `read(command, cwd=None, payload=None)` and `refusal(command, cwd)` to `refusal(command, cwd, payload=None)` in `wfctl/_review_gate.py`, skip a person-command refusal when `_prompt_will_ask` returns `None`, and otherwise print the first line and reason line from `contracts/cli.md` in its precedence order; have `wfctl/guard/_hook.py` pass the decoded payload. The reason line for a form that isn't plain names every refused character, the newline and an unquoted `#` included (plan review PR-017); verify with T012
- [X] T011 [P] [US4] Rewrite `tests/test_accept_check_threat_model.py` to read the four lists in `docs/architecture/prompt-approves-person-commands.md`, and keep reading items 1 - 20 of `accept-check-threat-model.md`'s "Must keep catching": items 1, 2, 16, and 19 pass under the pass conditions and every other item stays refused. Run each item again with the words swapped for sign-off and approve-imports where it has a meaning for them; verify with `uv run pytest tests/test_accept_check_threat_model.py -q`
- [X] T012 [P] [US4] Add tests in `tests/test_review_gate.py` for "Must keep catching" items 13 - 16 (a `uv run` approve-imports, auto-approve on, a Bob payload, the rule removed), a malformed settings file, a payload with no `tool_name`, a leading-space plain form, a citation holding a quoted `#` that passes, and a `grep` and a commit message naming sign-off that pass; update the existing cases that expected a plain spelling refused; verify with `uv run pytest tests/test_review_gate.py -q`

## Phase 4: User Story 1 - Accept a record from the agent's session (P1)

**Goal**: the accept runs with no terminal under Claude Code, with an optional citation.

**Independent Test**: with `_at_terminal` false and `CLAUDECODE` set, the accept writes the record and the prompt Log line; with neither, it refuses; at a terminal, `--agreed` is still required.

**Verification**: `uv run pytest tests/test_arch_accept.py tests/test_arch_accept_dry_run.py tests/test_arch_drawing_fingerprint.py -q`, then quickstart steps 2 - 5

- [X] T013 [US1] In the accept command in `wfctl/cli.py`, change the terminal check to `not _at_terminal() and not prompted_host()`, make `--agreed` optional with a blank value counting as absent, write "approved at the permission prompt" as the citation with no terminal and no citation, keep refusing a terminal run with no citation naming `--agreed`, and apply the same rule to a redraw's "drawing signed off" line; verify with T015
- [X] T014 [US1] Add `wfctl arch check-accept <slug>` in `wfctl/cli.py`, running exactly what the accept's dry run runs; verify with T015
- [X] T015 [P] [US1] Add tests to `tests/test_arch_accept.py` and `tests/test_arch_accept_dry_run.py` for each row of `data-model.md §Accept Log line`, a blank `--agreed ""`, a redraw with no terminal, `WFCTL_AGENT=claude` alone still refusing (plan review PR-013), and `check-accept` matching the dry run's output and exit code on a passing and a refused record; verify with `uv run pytest tests/test_arch_accept.py tests/test_arch_accept_dry_run.py -q`
- [X] T016 [US1] Add the blank-citation and redraw rows to `specs/833-agent-accept-with-approval/data-model.md §Accept Log line` (plan review PR-016); verify by reading the table against T015's cases

## Phase 5: User Story 2 - Sign off a review from the agent's session (P1)

**Goal**: sign-off runs with no terminal under Claude Code, with no typed sha.

**Independent Test**: with `_at_terminal` false and `CLAUDECODE` set, sign-off records through HEAD without calling `input()`; at a terminal it still asks.

**Verification**: `uv run pytest tests/test_review_cli.py -q`, then quickstart step 6 on a throwaway branch

- [X] T017 [US2] In the sign-off command in `wfctl/cli.py`, change the terminal check to `not _at_terminal() and not prompted_host()`, and with no terminal skip `input()` after printing the pending commits; verify with T018
- [X] T018 [P] [US2] Add tests to `tests/test_review_cli.py`: no terminal with `CLAUDECODE` signs off without reading stdin; no terminal without it refuses; `WFCTL_AGENT=claude` alone refuses; a terminal run still asks for the short sha; verify with `uv run pytest tests/test_review_cli.py -q`

## Phase 6: User Story 3 - Approve imports from the agent's session (P2)

**Goal**: the installed approve-imports runs with no terminal under Claude Code, with no typed digest.

**Independent Test**: with `_at_terminal` false and `CLAUDECODE` set, it approves without reading stdin; the worktree refusal still fires.

**Verification**: `uv run pytest tests/test_review_notes.py -q`, then quickstart step 7 on a throwaway branch

- [X] T019 [US3] In `wfctl/cli.py`'s approve-imports command and in `approve_imports` and `run_approve_imports` in `wfctl/_review_notes.py`, change each terminal check to `not _at_terminal() and not prompted_host()`, and with no terminal approve without asking for the digest after printing the additions; keep `_inside_a_worktree`; verify with T020
- [X] T020 [P] [US3] Add tests to `tests/test_review_notes.py` for the no-terminal path with and without `CLAUDECODE`, `WFCTL_AGENT=claude` alone, a terminal run still asking for the digest, and the worktree refusal; verify with `uv run pytest tests/test_review_notes.py -q`

## Phase 7: User Story 5 - Doctor reports a missing rule (P2)

**Goal**: `install-skills` writes the five rules from the table, and `doctor` reports any that's missing.

**Independent Test**: remove each rule in turn and see `doctor` exit 1 naming it.

**Verification**: `uv run pytest tests/test_prompted_rules.py -q`, then quickstart steps 1 and 9

- [X] T021 [US5] In `wfctl/cli.py`, build one `_ManagedRule(SETTINGS_PATH, f"Bash({' '.join(p.words)}:*)", "ask", cost)` per `PROMPTED` entry beside #407's `ASK_RULES`, with a `cost` naming the command that stops prompting; verify with T023
- [X] T022 [US5] Add one `prefix_rule(pattern=[…], decision="prompt", …)` per `PROMPTED` entry to `wfctl/agents/codex/rules/wfctl.rules`; verify with T023
- [X] T023 [P] [US5] Write `tests/test_prompted_rules.py`: install writes every rule, `doctor` reports each removed rule and exits 1, `uninstall-skills` removes them, and the Codex file's prompt rules equal the ones built from `PROMPTED`; verify with `uv run pytest tests/test_prompted_rules.py -q`

## Phase 8: Polish & cross-cutting

- [X] T024 In `wfctl/arch/_records.py`, count a superseded record as claimed when its last `superseded` Log line names, as the first word after `by ` with trailing punctuation removed, a record that exists; verify with a test in `tests/test_arch_records.py` and `uv run wfctl doctor` no longer warning about `guard-catches-literal-accept`
- [X] T025 [P] Switch the dry-run references to `wfctl arch check-accept` in `wfctl/_evidence.py`'s fix line, the refusal text in `wfctl/_review_gate.py` and `wfctl/cli.py`, `wfctl/agents/skills/speckit-brainstorm/SKILL.md`, `wfctl/agents/commands/speckit.brainstorm.md` and its `allowed-tools`, and `wfctl/agents/skills/design-levels/references/drawing-style.md`; verify with `uv run pytest -q` and a search for the old dry-run spelling
- [X] T026 [P] Change the skills that call the three commands terminal-only to say the agent runs them only when the user asks and Claude Code asks first: `opening-a-change`, `architecture-decisions` (with `references/threat-model.md` and `references/threat-model-agent-commands.md`), `fanning-out-code-review`, `design-passes`, `reviewing-security`, and `drawing-style.md`, under `wfctl/agents/skills/`. Keep `speckit-brainstorm`'s rule that an agent doesn't accept under auto-approve. Load `writing-style` first; verify with `uv run wfctl install-skills --agent claude` and reading each changed line
- [X] T027 [P] Update `AGENTS.md`'s Safety and Releasing sections the same way; verify by reading the changed lines against `prompt-approves-person-commands.md`
- [X] T028 Run the definition of done: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl doctor`, `uv run wfctl check config`
- [ ] T029 Walk `quickstart.md` with the user, who installs the branch build at step 0 and reinstalls from `main` at step 12; verify each step's stated outcome

## Phase 9: #838 folded in (user scope change, 2026-11-20)

The user folded #838 into this branch as the same change. The PR body closes both #833 and #838. Do T030 - T033 before T028's final run and T029's walk.

- [x] T030 [#838 part 1] Let through a command that only quotes a person-only command: `echo`/`printf` of a quoted string, and `cat > <file> <<'EOF'` with a quoted delimiter and no other command. Today's reader refuses all three (probed after T027: `echo "run wfctl arch accept s next"`, `printf '%s\n' 'wfctl review sign-off'`, and a quoted-delimiter heredoc into `changes/x.md`). This loosens a security control, so the forms go into a threat-model list the user accepts first: `prompt-approves-person-commands.md` is accepted and isn't edited, so this needs an amendment the user accepts or a new record. Ask the user before writing code, since the user sets the lists. Likely shape: extend `_reads_text_only` / `_TEXT_READERS` in `wfctl/_review_gate.py`, and reuse `_PRINTED_HEREDOC` for a heredoc whose only command is `cat > file`. Verify with tests for a heredoc and a quoted string, for all three commands, with every `Must keep catching` item still refused
- [x] T031 [#838 part 2] Accepting an accepted record whose last Log line is `amended` writes a new `accepted` Log line; an accepted record with no later amendment still prints "already accepted" and writes nothing. Start from `_not_promotable` and the redraw path in the accept command in `wfctl/cli.py`, and `accept`/`_set_status`/`redraw_only` in `wfctl/arch/_records.py`. Verify with tests in `tests/test_arch_accept.py` for both cases
- [x] T032 Add #838 to the release note (`changes/838.fix.md`), and add a spec FR and a data-model row for part 2
- [X] T033 Rerun T028's definition of done after T030 - T032

## Dependencies

- T001 before everything. T003 - T004 before every story.
- US4 (T007 - T012) before US1, US2, and US3, since their walks need the guard to let the plain spelling through. Their unit tests don't depend on US4.
- US5 (T021 - T023) is independent of US1 - US4 in code, and the walk needs it.
- T025 depends on T014. T028 after every other code task. T029 last.

## Parallel examples

- After T004: T005, T006 together.
- In US4: T011 and T012 together once T010 is done.
- After US4: US1, US2, US3, and US5 can proceed side by side, since they change different functions.
- In Polish: T025, T026, T027 together.

## Implementation strategy

MVP is Phase 2, US4, and US1: the agent accepts a record behind the prompt, and every wrapped form stays refused. US2 and US3 follow the same pattern in their own commands. US5 is required before the walk, since the guard refuses the plain spelling until the rule is installed.

The PR body names three things for the user to confirm: the reading of old items 16 and 19, the nested-agent gap with `CLAUDECODE`, and the switch from a `supersedes` list to the Log line.
