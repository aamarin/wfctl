# Tasks: seed-guard-hook

**Input**: Design documents from `specs/136-seed-guard-hook/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: `_settings.py` is pure and gets unit tests; every console line this
adds is asserted on, per `a-rule-is-expressed-as-a-check`. The one thing no test
covers is `quickstart.md`, which is a manual gate before the PR opens.

## Format: `[ID] [P?] [Story] Description`

- **[P]** — different file, no dependency on another unfinished task
- The spec calls it the *directory-change rule*; this file and the code call it
  `Bash(cd:*)` / `DENY_RULE`. Same thing, one name per surface.
- Stories are US1 (guard arrives on), US2 (their settings survive), US3 (drift is
  visible), US4 (hand-wired guard corrected)

## Phase 1: Pure logic — `wfctl/_settings.py`

No I/O, no `wfctl.*` imports. Lands first because it is the only part that stands
up with nothing else in place.

- [ ] **T001** [US4] Give `merge_hook` an optional `matcher` parameter. Its
      in-place branch collects `(group, hook)` pairs rather than flattening to
      hooks, so a replaced entry's group can have `matcher` corrected; a freshly
      appended group carries it. `matcher=None` leaves every group untouched —
      today's behaviour for `UserPromptSubmit` and `Stop`, and the regression to
      watch. `wfctl/_settings.py`
- [ ] **T002** [P] [US1] Add `merge_permission(settings, rule) -> bool`, returning
      whether it added the rule. Defensive about shape the way `_is_managed` is:
      a `permissions` value that is not an object raises `ValueError`, which the
      caller reports as a merge problem. `wfctl/_settings.py`
- [ ] **T003** [P] [US2] Add `remove_permission(settings, rule) -> bool`, pruning
      upward — an emptied `deny` list goes, and a `permissions` map left empty
      goes with it, so uninstall restores a file that never had the key.
      `wfctl/_settings.py`
- [ ] **T004** [P] [US3] Add `permission_present(settings, rule) -> bool` for the
      drift check. `wfctl/_settings.py`
- [ ] **T005** Update the module docstring: it currently says groups exist to
      carry a matcher for tool events and that none of the managed events has
      one. That stops being true at T001. `wfctl/_settings.py`

**Verification**: `tests/test_settings_merge.py` gains cases for each — a
hand-written entry whose matcher is corrected in place *and keeps its array
position*; a matcher-less event whose groups are untouched; permission add,
add-when-present, remove, remove-when-absent; the upward prune; the malformed
`permissions` raise. `uv run pytest -q tests/test_settings_merge.py`

---

## Phase 2: Constants and the third hook — `wfctl/cli.py`

- [ ] **T006** [US1] Add `_PRETOOL_EVENT = "PreToolUse"`, build
      `GUARD_HOOK_COMMAND` from `_settings.MANAGED_PREFIX` and the existing
      `_WORKTREE_GUARD`, and add both to `MANAGED_HOOKS`. `wfctl/cli.py:1478-1509`
- [ ] **T007** [US1] Add `_HOOK_MATCHER = {_PRETOOL_EVENT: "Bash"}` and pass
      `.get(event)` through `_merge_hooks` into `merge_hook`. A separate map
      rather than widening `MANAGED_HOOKS`' values, which three call sites read
      as commands. `wfctl/cli.py`
- [ ] **T008** [US3] Add the `_HOOK_GONE` line for `PreToolUse`. It says what
      *this* hook's absence costs — nothing stops a Bash call reaching into a
      sibling worktree — not what the other two lose. `wfctl/cli.py:1512`
- [ ] **T009** [P] Add `DENY_RULE = "Bash(cd:*)"` beside the hook constants, with
      the comment explaining why it cannot carry `MANAGED_PREFIX`. `wfctl/cli.py`

- [ ] **T009a** [P] Add the two tests that keep FR-016 and FR-018 from holding by
      omission: a base-layer install (no `--agent`) adds no guard entry and no
      rule, and a drifted managed *hook* is still corrected in place without
      refusing. Both currently pass by nothing happening, which is exactly why
      they need pinning. `tests/test_install_skills.py`

**Verification**: an install into an empty settings file produces all three hooks
with the guard's group carrying `"matcher": "Bash"`; `doctor` names the
`PreToolUse` hook when it is deleted; T009a's two assertions hold.
`uv run pytest -q`

---

## Phase 3: The receipt — install (US1, US2)

- [ ] **T010** Add `_merge_permissions(repo_root, agent, prior)` mirroring
      `_merge_hooks`' return shape. `added` comes from the prior record when one
      exists for the same `(path, rule)`; only with no prior record is it observed
      from the file. A run that cannot read or write re-emits the prior record.
      `wfctl/cli.py`
- [ ] **T011** Call it from `install_skills`, build its `prior` map keyed
      `(path, rule)`, and write the result to `manifest[agent]["permissions"]` as
      a sibling of `merged` — never a member of `items`, which uninstall deletes
      outright. `wfctl/cli.py:2733-2785`
- [ ] **T012** Report the permission in the existing merge summary block rather
      than adding a second one. The consumer-owned file is already called out
      there, and a second block would split one file's story in two.
      `wfctl/cli.py:2973`

**Verification**: install into a file with the project's own `deny` entries —
theirs survive, `Bash(cd:*)` joins them, the record says `added: true`; install
into one already carrying the rule — record says `added: false`, file unchanged;
re-install writes nothing. `uv run pytest -q tests/test_install_skills.py`

---

## Phase 4: The refusal (US2)

- [ ] **T013** Add `--force` to `install-skills`, documented as accepting a
      divergence rather than overwriting files — `install-config --force` means
      the second thing, and the two must not read as one flag. The help text is
      what keeps them apart, so it is part of this task and not a follow-up.
      `wfctl/cli.py`
- [ ] **T014** Add the drift check **before any file is copied** and after the
      prior manifest is read. A prior receipt for the rule — `added` either way —
      plus a file that does not carry it exactly is a refusal: print what was
      found, what wfctl installed, and both ways forward — restore it, or
      `--force`. Exit 1. `wfctl/cli.py`
- [ ] **T014a** Make the check require a readable file. A settings file that will
      not parse cannot establish drift, so it falls to the existing warn-and-
      continue arm rather than refusing — spec FR-014 outranks FR-017, and
      refusing there would hold the whole skills tree hostage to a stray comma.
      `wfctl/cli.py`

**Verification**: the placement is the risk, not the logic. A test asserts the
refusal leaves the skills tree untouched — not merely that it printed — because
`_merge_hooks` runs after the copies and a check written there would half-install.
Also: `--force` re-asserts and records `added: true`; a receipt of `added: false`
with the rule deleted refuses the same way `added: true` does; an unparseable file
warns and the install completes; a `post_create`-shaped install into a fresh
`.claude/` never trips the refusal. `uv run pytest -q`

---

## Phase 5: Uninstall (US2)

- [ ] **T015** Add `_unmerge_permissions(repo_root, records)` returning changed
      files, declined entries and problems. Removes only on `added: true` *and* an
      exact text match. `wfctl/cli.py`
- [ ] **T016** Call it from `uninstall_skills` and **union** its changed-file set
      with `_unmerge_hooks`', never add — both passes touch the same file, and
      adding reports `2` for one file. `wfctl/cli.py:3083-3113`
- [ ] **T017** Report each declined entry: the file, the text found, and the rule
      wfctl installed. Today's summary says "Your own entries in them were left
      alone", which reads as reassurance while the thing left is descended from
      wfctl's. `wfctl/cli.py:3111`
- [ ] **T017a** Widen the summary line so a removed rule is accounted for. It says
      "Removed the managed hook from N settings file(s)" today, which under-reports
      a run that also removed a permission from a file the project owns (FR-021).
      `wfctl/cli.py:3111`

**Verification**: uninstall over an untouched install returns the file to its
original parsed content — parsed, not byte-equal, because the first install
reflows it (FR-021, SC-002); over an edited rule it leaves the text and prints all
three parts; over `added: false` it leaves the rule; with the manifest deleted it
removes nothing; a run that removed a rule says so.
`uv run pytest -q tests/test_uninstall_skills.py`

---

## Phase 6: doctor (US3)

- [ ] **T018** Add `_check_managed_permissions(repo_root, manifest)` printing a
      `⚠` line when a rule the receipt claims is gone. It returns nothing the exit
      code reads — deliberately unlike `_check_managed_hooks`. `wfctl/cli.py`
- [ ] **T019** Call it from `doctor` outside the `any([...])` that sets
      `exit_code = 1`. Placing it inside is the whole defect this avoids.
      `wfctl/cli.py:4986`

**Verification**: a deleted rule makes `doctor` print and **exit 0**; a deleted
hook still exits 1; a clean install prints nothing about the settings file.
`uv run pytest -q tests/test_doctor.py`

---

## Phase 7: Documentation

- [ ] **T020** [P] Rewrite the README's guard section: it currently hands the
      reader a JSON block to paste and says the guard is "Not seeded by
      `install-config`". Both stop being true. Say installing seeds it, and keep
      the block only as what the entries look like. `README.md:406-465`
- [ ] **T021** [P] Add the `cd` deny rule to the README's merge-mode section as
      the second managed entry kind, with one line on why it cannot carry the
      marker and where the receipt lives. `README.md`

**Verification**: `uv run wfctl doctor` clean, and no test asserts on the old
README text.

---

## Phase 8: Gates before the PR

- [ ] **T022** Run `quickstart.md` end to end on a scratch repo. Not optional and
      not covered by anything above: the suite is dict literals and has never met
      a real consumer's key order.
- [ ] **T023** `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
      `uv run mypy wfctl/`, `uv run wfctl doctor` — all four, `uv run` every time.
- [ ] **T024** Dispatch the review panel over the full diff, confirm every
      reviewer reported, reconcile the findings. Findings applied are new
      unreviewed code: commit them and re-run T023.
- [ ] **T025** Write the PR body from `.github/pull_request_template.md`, every
      section in its order, with the panel's disposition table. `--body-file`,
      never `--body`. `Closes #136`.

---

## Dependencies

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
                            └──────► Phase 5
                            └──────► Phase 6
Phase 7 is independent of all of them.
Phase 8 waits on everything.
```

T001 blocks T007 (the parameter has to exist). T010 blocks T015 and T018 (both
read the record it defines). T002–T004 are parallel with each other, T020–T021
with everything.

## What is deliberately not here

- A standing preference mechanism. #313 owns it; until then T014's refusal message
  carries the whole burden, which spec FR-019 records.
- Extending refusal to drifted hooks. Clarify settled this as out of scope — it
  would change behaviour for every existing consumer.
