# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 8ae93cbeb83f687d21b77b9d6536af1abf944a78 | technical strategy |
| spec.md | 24be2267182d5aa3b1e8cbe3556f701ffe8da888 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | adba5c0028c3f61f4b7200f1a2f140d0268f5169 | design-record index |
| docs/architecture/design-exceptions-live-with-specs.md | b76607ed4af18b7ec7b7678c33ac6ebbf8e4e5c5 | design record (level 2) |
| docs/architecture/design/design-exceptions-module.md | 8a09f5f0100ece4b9f9162b69168f98e6beb6cf2 | design record (level 3) |
| research.md | 666038c954094c11ba76fb573adcfbe687e6d72d | planning evidence |
| data-model.md | 89535cf49f9b64c391f7cdcd9e93dee053e03f80 | planning evidence |
| contracts/cli.md | dd2c1c43ae17379248f7572c0257f79cce3e4475 | planning evidence |
| quickstart.md | c2e5eb290bb8cfb6a5ce06374365602228f9017f | planning evidence |
| docs/architecture/an-absent-artifact-is-claimed-not-inferred.md | 340ef7668c317ad98347a271a25be2b616784ea5 | related record, cited by the level-2 record and edited by this branch |
| plan-review.plan.md | adfd05636fe410e3582bcf495a841812a495fb53 | base of this re-review |

## Review scope

- Re-review: the earlier report exists, the plan copy exists, and the copy's
  identity equals the earlier report's `plan.md` row
  (`adfd05636fe410e3582bcf495a841812a495fb53`).
- Changed since the earlier report, from the plan diff: `§The callers` item 7
  (`_record_gate.refusal` now takes `trunk`, and `_judge` passes the value it
  holds before stripping `origin/`), and the last `§Complexity Tracking` row
  (names the two records this PR waits on, and says the level-3 record
  doesn't hold it). Reviewed together with the rest of item 7, `§Summary`
  item 5, `§Design records`, `§Project Structure`, and `§Order of work` steps
  8 and 11.
- Inputs that changed, each re-read in full with the whole of `plan.md`
  reviewed against it: `research.md` (R14's cost paragraph and the paragraph
  after it), `data-model.md` (the **Agreement** bullet), and
  `docs/architecture/an-absent-artifact-is-claimed-not-inferred.md` (the
  plain-language rewrite in commit 767a050). Every other row matches its file
  now.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification, with verification, dependency,
  and scope folded in as the rubric's lenses 4, 7, and 8.
- Conditional lenses: security and reliability applied, since the change adds
  two refusals to the worktree guard, which gates opening and merging a PR.
- Design records: 2 listed in design.md, both resolved and unchanged.
  - `docs/architecture/design-exceptions-live-with-specs.md`
  - `docs/architecture/design/design-exceptions-module.md`
- Existing code and state inspected, to check claims the revision added:
  `wfctl/_review_gate.py` (`_judge` calls `_paths.trunk_branch`, refuses on
  `None`, then strips `origin/`), the diff of commit 767a050, and
  `gh issue view 339` (closed).
- No `[NEEDS CLARIFICATION` marker stands in `spec.md`.
- Reviewers: the lenses above, run in sequence by one agent in a fresh context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 9

No BLOCKER findings identified in this review. Three findings are fixed:
PR-026, PR-027, and PR-028.

1. R14 and the last `§Complexity Tracking` row now name the two records the
   guard holds this PR on, `design-exceptions-live-with-specs.md` and #339's
   `an-absent-artifact-is-claimed-not-inferred.md`, and say the level-3
   record doesn't hold it. R14 also says the edit stays on this branch because
   #339 is closed, which settles the direction R9 item 10 takes (PR-026).
2. The data model's **Agreement** bullet now carries the inherited-exception
   skip, in the same terms as FR-015, R12, and item 6 (PR-027).
3. Item 7 now gives `_record_gate.refusal(session, branch, head, trunk)`, with
   `_judge` passing the unstripped value it already holds (PR-028).

Two new MINOR findings. The record rewrite already made one of the three edits
R9 item 10 plans, so R9 item 10 now quotes a passage that no longer exists
(PR-029). The `§Complexity Tracking` row's "since #339 is closed" can be read as
the reason the PR waits, rather than the reason the edit stays here (PR-030).
PR-014, PR-015, and PR-020 to PR-024 stay open. No reviewed artifact was
changed.

## Findings

### PR-001: A spec folder can belong to more than one branch, so a per-branch exception leaks to siblings

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §Edge Cases` and `§Key Entities`, `plan.md §Epic sub-issues`,
    `research.md R11`, and `research.md R8` item 11.
- Finding: Fixed. The semantics are decided in the spec, the plan and research,
  and pinned by two tests.
- Why it matters: The implementer no longer has to choose among sharing, keying
  by branch, or refusing.
- Suggested response: Fixed by `research.md R11` and `plan.md §Epic sub-issues`.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-002: The claim-before-git order changes a held case, and SC-003 names no exception for it

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §SC-003`, `research.md R3` closing paragraph, `R8` item 9.1, and
    `plan.md §Order of work` step 4.
- Finding: Fixed. The deliberate change is named and a gate test pins it.
- Why it matters: SC-003 matches the gate's behavior.
- Suggested response: Fixed by `spec.md §SC-003` and `research.md R8` item 9.1.
- Corroborated by: requirements and traceability

### PR-003: A test that writes a step claim under the arch root is missing from the test list

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md R8` item 8 and `plan.md §Order of work` step 6.
- Finding: Fixed.
- Why it matters: The fixture writes through the module, as FR-009 asks.
- Suggested response: Fixed by `research.md R8` item 8.
- Corroborated by: adversarial implementation

### PR-004: Several acceptance scenarios and the record's own verification tests are not named

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md R8` item 10, `plan.md §Project Structure`, and
    `plan.md §Order of work` step 4. The record's third verification item, the
    grep, is step 9.
- Finding: Fixed.
- Why it matters: The assumptions both records flag are regression tests.
- Suggested response: Fixed by `research.md R8` item 10.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-005: User-facing help and one skill still say the claim reaches the reviewer through the diff

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md R9` items 8 and 9, `plan.md §Project Structure`, and
    `§Order of work` step 11.
- Finding: Fixed.
- Why it matters: `--help` and the skill will name the spec folder and the PR
  body, as FR-013 asks.
- Suggested response: Fixed by `research.md R9` items 8 and 9.
- Corroborated by: requirements and traceability

### PR-006: The revised related record still says the claim is committed and reaches the reviewer

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `research.md R9` item 10, `plan.md §Project Structure`, and
    `§Order of work` step 11.
- Finding: Fixed. The record is still unchanged, which is expected, since its
  edit is implementation work. R14 now names what that edit costs (PR-026,
  fixed), and PR-029 reports that the record's rewrite already made one of the
  three edits.
- Why it matters: The two records will give one answer about where the claim
  lives.
- Suggested response: Fixed by `research.md R9` item 10.
- Corroborated by: architecture and boundaries

### PR-007: SC-004's "one edit in one module" holds for code only

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §SC-004`, `plan.md §Complexity Tracking`, and the closing
    paragraph of `research.md R9`.
- Finding: Fixed.
- Why it matters: A later move has a list of texts to update.
- Suggested response: Fixed by `spec.md §SC-004` and `research.md R9`.
- Corroborated by: architecture and boundaries

### PR-008: The spec's #382 comment has no step in the plan

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Order of work` step 12.
- Finding: Fixed.
- Why it matters: #382 will not be planned against a file that no longer exists.
- Suggested response: Fixed by `plan.md §Order of work` step 12.
- Corroborated by: requirements and traceability

### PR-009: Removing `STEP_CLAIMS_DIR` breaks a test file and adds a false listing that the plan's lists miss

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md R8` item 8, `research.md R4`, and the `plan.md` test lists.
- Finding: Fixed. Both test sites are on the list, and the `record:` line is a
  stated, accepted cost.
- Why it matters: The suite failure and the listing are both expected now.
- Suggested response: Fixed by `research.md R4` and `R8` item 8.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-010: The plan says it follows both records as written, but the level-2 record still deletes the step claims

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `docs/architecture/design-exceptions-live-with-specs.md §Consequences` and
    its 2026-10-26 `revised` Log entry (commit 024a991).
- Finding: Fixed.
- Why it matters: A reader accepting the level-2 record accepts the consequence
  the feature carries out.
- Suggested response: Fixed by commit 024a991 and `plan.md §Order of work`
  step 9.
- Corroborated by: architecture and boundaries, requirements and traceability

### PR-011: A sub-issue's own spec folder replaces the epic's whole folder for that branch, not only its exceptions

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md R11`, the paragraph on a sub-issue's own folder.
- Finding: Fixed.
- Why it matters: The first user to give a sub-issue its own folder can read
  what it costs before doing it.
- Suggested response: Fixed by `research.md R11`.
- Corroborated by: adversarial implementation

### PR-012: The plan does not say how the 5 moved folders reach `specs-trunk`

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Order of work` step 9 and `research.md R10`.
- Finding: Fixed. PR-014 reports one side effect of the named mechanism.
- Why it matters: The implementer has a command and does not route around
  `store specs`.
- Suggested response: Fixed by `plan.md §Order of work` step 9 and
  `research.md R10`.
- Corroborated by: adversarial implementation

### PR-013: The rename left "a exception" and similar article errors across the artifacts

- Priority: MINOR
- Category: Enhancement Suggestion
- Status: fixed
- Evidence:
  - The revised item 6, item 7, step 7, step 8, R12, R14, and the data-model
    section add no new article error.
- Finding: Fixed.
- Why it matters: The errors no longer travel into task text and PR bodies.
- Suggested response: Fixed by the earlier article edits.
- Corroborated by: requirements and traceability

### PR-014: Storing the 5 folders under `WFCTL_BRANCH` records each push in another branch's state directory

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `plan.md §Order of work` step 9 and `research.md R10` still store each
    folder with `WFCTL_BRANCH=<branch> wfctl store specs`, and say nothing
    about where each push is logged. Neither changed in this revision.
  - `wfctl/cli.py` `store_specs_cmd` logs the push under the state directory
    `resolve_agent_dir` gives for the overridden branch.
  - `AGENTS.md §Safety`: the logged push "is the only trace of one a restarted
    session can read".
- Finding: Each of the 5 runs logs its push in a merged branch's state
  directory, and this session's state directory records none of them.
- Why it matters: A session on this branch restarted after step 9 can't tell
  from its log that the pushes ran. The cost is bounded, since a repeat store
  of a stored folder has nothing to commit.
- Suggested response: Say in step 9 that each run logs to that branch's state
  directory, and record the pushes on this branch with
  `wfctl report-action push` once the 5 runs are done.
- Corroborated by: security and reliability, adversarial implementation

### PR-015: The level-3 grep's pass condition does not fit the hit it is most likely to produce

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Order of work` step 9, unchanged: run
    `grep -rn '"exceptions"\|boundary\.md' wfctl/cli.py wfctl/_pipeline.py wfctl/_evidence.py`
    "and confirm every hit is a call into `_design_exceptions`".
  - A call such as `_design_exceptions.boundary(spec_dir)` matches neither
    pattern. A rewritten `--help` docstring naming `exceptions/boundary.md`
    (`research.md R9` item 8) is a hit that isn't a call.
- Finding: The condition as written can only be met by an empty result, and a
  docstring hit fails it on wording while meeting the record's intent.
- Why it matters: The implementer has to guess whether a docstring hit counts.
- Suggested response: Say the grep prints nothing outside docstrings and
  comments, or that a hit is a finding only when it builds a path or parses a
  file.
- Corroborated by: adversarial implementation

### PR-016: The guard's record list is not the level-2 set the spec asks for

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `data-model.md §The guard's record checks` item 1 now reads the list from
    `git diff --name-only --diff-filter=d <trunk>...<commit>`, with `<trunk>`
    the value `trunk_branch` returns, and counts a path only when its parent is
    the arch root and it ends in `.md`. It leaves out level-3 records, views,
    scans, and deleted files.
  - `plan.md §The callers` item 7 gives the same range, filter, and parent rule.
    The data model leaves out the `-- <arch>` pathspec, which the parent rule
    makes redundant, so the two give the same set.
  - `wfctl/_arch.py` `load_records` globs `*.md` one level deep, and every
    top-level `.md` under `docs/architecture/` carries a `status:` line, so the
    parent rule admits no file without a status.
- Finding: Fixed. The plan and the data model now name one record set.
- Why it matters: `tasks` reads both artifacts and gets the same list from
  each.
- Suggested response: Fixed by the edit to `data-model.md §The guard's record
  checks`.
- Corroborated by: architecture and boundaries, adversarial implementation,
  security and reliability

### PR-017: R14 holds a branch that edits any proposed record, not only one that adds a record

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md R14` now says "A proposed record already on `main` holds a PR
    only when the branch edits it", gives the reason an edit counts, and says
    why the design gate's `added_only` rule doesn't apply. That reason matches
    the `_evidence._branch_records` docstring.
  - R14's cost paragraph says every branch that adds or edits a proposed
    record waits for a person, and that a record held as proposed on purpose
    holds any branch that edits it.
  - `plan.md §Complexity Tracking` last row now reads "adds or edits", and
    names the held-on-purpose cost. `spec.md §FR-017`, `plan.md §Summary`
    item 5, `data-model.md`, and the level-2 record all say "touches", which
    agrees.
  - The wrong sentence about proposed records on `main` is gone.
- Finding: Fixed. The user's decision that edits hold is stated the same way in
  every artifact, with its cost. R14 now applies that cost to this branch
  correctly (PR-026, fixed).
- Why it matters: The equality test in step 8 item 4 now pins a set the
  artifacts say they want.
- Suggested response: Fixed by `research.md R14` and the `§Complexity Tracking`
  row.
- Corroborated by: architecture and boundaries, security and reliability

### PR-018: The plan doesn't say which diff range the guard reads

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The callers` item 7 now gives
    `git diff --name-only --diff-filter=d <trunk>...<head> -- <arch>`, with
    `<trunk>` the value `_paths.trunk_branch` returns before `_judge` strips
    `origin/`, and says why a three-dot range doesn't list records the trunk
    gained after the branch point. `data-model.md` gives the same range.
  - `wfctl/_paths.py` `trunk_branch` returns `origin/HEAD`'s target, or for a
    declared trunk `origin/<name>` when the remote has it
    (`_resolve_declared`). So the claim that a stale local `main` doesn't move
    the base back holds. `records_on_this_branch` diffs `f"{trunk}...HEAD"`
    with that same value.
  - `plan.md §Order of work` step 8 item 3 adds a fixture whose trunk gains a
    proposed record after the branch point.
- Finding: Fixed. How the value reaches the new module is now stated too
  (PR-028, fixed).
- Why it matters: The guard and the fact read the same range, and a test fails
  on the two-dot reading.
- Suggested response: Fixed by `plan.md §The callers` item 7 and step 8 item 3.
- Corroborated by: adversarial implementation

### PR-019: `check-body` would demand an inherited "no new boundary" reason from a sub-issue whose record answers yes

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-015` now says an inherited boundary exception "MUST NOT be
    reported when the branch touches a level-2 record".
  - `research.md R12` adds the skip, defines "inherited" with R13's test, and
    reads the records from `_evidence._branch_records`. `check-body` runs in
    the working tree, and `cli.py` already imports from `_evidence` lazily,
    so that call is available.
  - `plan.md §The callers` item 6 gives the same rule, and `§Order of work`
    step 7 adds a test for both sides of it.
- Finding: Fixed. A sub-issue that answers yes no longer has to quote the
  epic's "no". The inherited test shares PR-020's gap. The data model's
  agreement rule now carries the skip (PR-027, fixed).
- Why it matters: The guard and `check-body` now agree on when an inherited
  exception stops counting.
- Suggested response: Fixed by `spec.md §FR-015`, `research.md R12`, and
  `plan.md §The callers` item 6 and step 7.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-020: The "own spec folder" test misses a folder matched by issue key

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `plan.md §The callers` item 7.1, unchanged: "Own" is
    `resolve_spec_dir(branch, root) == spec_root(root) / branch`.
  - `research.md R12`, `plan.md §The callers` item 6, and now the
    `data-model.md` **Agreement** bullet use the same test for "inherited"
    ("the folder isn't named after the branch").
  - `wfctl/_paths.py` `resolve_spec_dir` tries the exact name, then the first
    folder matching `<key>-*` or `<key>_*`, and only then the `delivery.md`
    fallback.
- Finding: A branch `635-a` whose folder is `635-b` resolves to its own folder
  through the key match, but both tests read it as inherited. R13 never fires
  for that branch, and `check-body` skips its own boundary exception once it
  touches a record. The two fail open the same way, so they don't disagree with
  each other.
- Why it matters: The checks fail open for a renamed branch. It's rare, since
  `feature-paths` names the folder after the branch.
- Suggested response: Define "own" as "not resolved through the `delivery.md`
  fallback", which is what R11 means by an inherited folder, and use it in
  both places.
- Corroborated by: adversarial implementation

### PR-021: The contract's `check-body` lines use a marker `check-body` doesn't print

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `contracts/cli.md §wfctl check-body in any repo`, unchanged, shows each
    finding as `✗ the boundary exception's reason isn't in the body: "…"`.
  - `wfctl/cli.py` `check_body_cmd` prints every finding from every source as
    `⚠ <line>`, and the sources return bare lines.
- Finding: A test written against the contract fails, or `_exception_findings`
  adds its own `✗` and prints `⚠ ✗ …`.
- Why it matters: The contract is what the story 5 tests assert on.
- Suggested response: Change the two contract lines to `⚠`, and say that
  `_exception_findings` returns bare lines like `_section_findings`.
- Corroborated by: adversarial implementation

### PR-022: R15 doesn't say how the skill learns that the branch has a boundary exception

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `research.md R15`, unchanged: the step applies "on a branch that has a
    boundary exception, own or inherited", and reads `auto_approve` from
    `wfctl status --json`.
  - `wfctl/contracts/status-payload.json` carries `auto_approve` and nothing
    about exceptions.
  - `research.md R9` closing paragraph and `spec.md §SC-004`: the texts that
    name the exceptions folder don't include `architecture-decisions`.
- Finding: The skill either names `exceptions/boundary.md` in `FEATURE_DIR`,
  which adds a text that R9's list misses, or relies on the agent remembering
  that it ran `arch none`, which misses an inherited exception.
- Why it matters: A later move of the folder would leave the skill pointing at
  the old path.
- Suggested response: Name how the skill finds the exception in R15, and add
  `architecture-decisions/SKILL.md` to R9's list if it names the path.
- Corroborated by: requirements and traceability

### PR-023: The reason for moving `RULED_ON` overstates the guard's import cost

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `plan.md §The callers` item 7 and `§Complexity Tracking`, both unchanged
    on this point: the guard can't import `_evidence` "without loading five
    more modules on every Bash call", and `_record_gate` "doesn't import
    `typer`, `rich`".
  - `wfctl/_review_gate.py`: `_judge` runs only for a command that opens or
    merges a PR, and the record call sits after the review check inside it.
  - `_record_gate` calls `resolve_spec_dir`, which imports `wfctl/_tracker.py`,
    which imports `rich.console`.
- Finding: The extra modules load only on a command that opens or merges a PR,
  not on every Bash call, and `_record_gate` loads `rich` through
  `resolve_spec_dir` anyway.
- Why it matters: The move is still reasonable, but the stated reason is
  wrong, and the "no `rich`" claim will be false once the module is written.
- Suggested response: Give the cost as "on every command that opens or merges
  a PR", and drop `rich` from the list or say it arrives through `_tracker`.
- Corroborated by: architecture and boundaries

### PR-024: R14 doesn't state that an agent can run `wfctl arch accept` itself

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `research.md R14`, revised in this round but not on this point: without
    the check, an unattended run could open and merge a PR for a boundary no
    person signed off on.
  - `wfctl/cli.py` `arch_accept_cmd` checks that `--agreed` is present and not
    a placeholder, and has no interactive-terminal check.
  - `docs/architecture/a-human-accepts-a-decision.md`: "Nothing stops an agent
    from running `arch accept` with an invented citation", which it accepts as
    tamper-evident.
- Finding: An unattended agent that meets R14's refusal can accept its own
  record and retry. The acceptance record already accepts that ceiling, but
  R14 states its guarantee without it.
- Why it matters: A reader of R14 takes the refusal as a human checkpoint,
  when it's a tamper-evident one.
- Suggested response: Add one sentence to R14 naming the ceiling and pointing
  at `a-human-accepts-a-decision.md`.
- Corroborated by: security and reliability

### PR-025: The plan doesn't say how the guard finds the arch root's subdirectories at `head`

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The callers` item 7 now keeps a path from the diff only when its
    parent is the arch root and it ends in `.md`, and says this needs no list
    of subdirectories, which would have to come from the working tree (R13).
  - `data-model.md §The guard's record checks` item 1 says the same.
- Finding: Fixed. The rule reads only the diff output, so a subdirectory the
  `main` checkout lacks can't leak into the list.
- Why it matters: Two implementers now build the same filter.
- Suggested response: Fixed by `plan.md §The callers` item 7.
- Corroborated by: adversarial implementation

### PR-026: R14 names the wrong records as the ones this PR waits on, and its advice contradicts R9 item 10

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md R14` cost paragraph now says this PR waits on
    `design-exceptions-live-with-specs.md` and on
    `an-absent-artifact-is-claimed-not-inferred.md` from #339, "which this
    branch edits", and that the level-3 record under `design/` doesn't hold
    the PR because the guard reads only level-2 records.
  - The paragraph after it says an edit to a record held as proposed on
    purpose belongs on the branch that validates it, "unless that branch is
    already closed", and that the edit stays here because #339 is closed.
    `gh issue view 339` reports `CLOSED`. That agrees with R9 item 10, which
    edits the record on this branch.
  - `plan.md §Complexity Tracking` last row names the same two records and
    says the level-3 record doesn't hold the PR.
  - `git diff --name-only --diff-filter=d origin/main...HEAD -- docs/architecture`
    still lists exactly those two top-level records, both `status: proposed`.
- Finding: Fixed. The records R14 and the cost row name are the ones the guard
  will hold this PR on, and R14 says which way R9 item 10 goes. PR-030 reports
  a wording point in the cost row.
- Why it matters: The person reading the cost row now expects to accept both
  records before this PR opens, including the #339 record.
- Suggested response: Fixed by `research.md R14` and the `§Complexity Tracking`
  row.
- Corroborated by: architecture and boundaries, security and reliability

### PR-027: The data model's agreement rule still says every exception is compared

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `data-model.md §"Moves a boundary?" PR section`, **Agreement**, now says
    `check-body` skips an inherited boundary exception when the branch changes
    a level-2 record, and defines "inherited" as a spec folder not named after
    the branch, citing R12 and FR-015.
  - `spec.md §FR-015`, `research.md R12`, and `plan.md §The callers` item 6
    give the same rule.
- Finding: Fixed. The data model's definition of "inherited" is the same one
  PR-020 reports, so it now shares that gap in a third place.
- Why it matters: A task generated from the data model alone now builds the
  skip.
- Suggested response: Fixed by the **Agreement** bullet.
- Corroborated by: requirements and traceability

### PR-028: The new module's signature doesn't carry the unstripped trunk the plan says it uses

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The callers` item 7 now gives `_record_gate.refusal(session,
    branch, head, trunk)`, and says `_judge` keeps the value
    `_paths.trunk_branch` returns before stripping `origin/` and passes it in,
    so the new module makes no second git call.
  - `wfctl/_review_gate.py` `_judge` calls `trunk_branch` at line 749, refuses
    when it returns `None`, and strips `origin/` at line 752. So the value
    passed in is never `None`, and keeping it means holding it in a second
    variable before line 752.
- Finding: Fixed.
- Why it matters: Two implementers now write the same signature and the same
  call.
- Suggested response: Fixed by `plan.md §The callers` item 7.
- Corroborated by: adversarial implementation

### PR-029: R9 item 10 still plans an edit the record rewrite already made, and quotes text that is gone

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `research.md R9` item 10, unchanged: three passages are to be rewritten,
    the third being §Considered, quoted as "`specs/` is gitignored ... so the
    claim reaches no reviewer".
  - `docs/architecture/an-absent-artifact-is-claimed-not-inferred.md
    §Considered`, after commit 767a050, now says "the claim reached no
    reviewer" and that "#635 later moved the claims into the spec folder too,
    with the PR body carrying each one to the reviewer". That passage already
    matches `design-exceptions-live-with-specs.md`.
  - The other two passages R9 item 10 names still stand as quoted:
    §Decision ("writes a committed sentence into the change under review") and
    §Owns truth ("a sentence committed to the branch", "that it reached the
    reviewer").
  - `plan.md §Project Structure` still lists the record with "three passages
    (research R9 item 10)".
- Finding: The plan and R9 say three passages are left to rewrite, and only
  two are. The record now also disagrees with itself until step 11 runs:
  §Considered says the claims moved to the spec folder, while §Decision says
  the command writes a committed sentence into the change under review.
- Why it matters: The implementer at step 11 searches for a quotation that
  isn't there, and a reader of the record before step 11 reads two answers
  about where the claim lives. The cost is bounded, since step 11 fixes the
  remaining two either way.
- Suggested response: Change R9 item 10 and the `§Project Structure` comment
  to the two remaining passages, and note that §Considered was rewritten in
  767a050.
- Corroborated by: architecture and boundaries, requirements and traceability

### PR-030: The cost row's "since #339 is closed" reads as the reason the PR waits

- Priority: MINOR
- Category: Enhancement Suggestion
- Status: open
- Evidence:
  - `plan.md §Complexity Tracking` last row: "This PR waits on
    `design-exceptions-live-with-specs.md` and on #339's
    `an-absent-artifact-is-claimed-not-inferred.md`, which it edits, since #339
    is closed."
  - `research.md R14`: the guard holds the PR because the branch edits a
    proposed record. #339 being closed is the reason the edit stays on this
    branch, not the reason the PR waits. R14 also says "unless that branch is
    already closed", where #339 is an issue.
- Finding: Read alone, the row ties the wait to #339's state. A reader could
  take it that a record from an open issue would not hold the PR, which
  contradicts R14's rule.
- Why it matters: The row is the one place a reader of the plan sees the cost,
  and it should state the rule R14 gives. No implementation choice turns on
  it.
- Suggested response: Split the clause, for example "and on #339's
  `an-absent-artifact-is-claimed-not-inferred.md`, which it edits. The edit
  stays here because #339 is closed." Say "issue" in R14's "unless that
  branch is already closed".
- Corroborated by: architecture and boundaries

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §The callers 1; contracts/cli.md | covered |
| FR-002 | plan.md §The callers 2; data-model.md §Pass exception | covered |
| FR-003 | data-model.md §`_design_exceptions` module; research R1 | covered |
| FR-004 | plan.md §The callers 1-2; contracts/cli.md refusals | covered |
| FR-005 | research R5; contracts/cli.md | covered |
| FR-006 | plan.md §The callers 3; research R3, R8 item 9.1 | covered |
| FR-007 | research R4; R8 item 9.2; Order of work 2 and 4 | covered |
| FR-008 | plan.md §The callers 4; research R7, R8 items 10.3 and 11 | covered |
| FR-009 | plan.md §`wfctl/_design_exceptions.py`; Order of work 6 and 9 | covered; PR-015 |
| FR-010 | Order of work 10; contracts/cli.md | covered |
| FR-011 | plan.md §Technical Context constraints; research R12 | covered |
| FR-012 | Order of work 9; research R10; level-2 record §Consequences | covered; PR-014 |
| FR-013 | research R9 items 1-10; Project Structure `opening-a-change` | covered; PR-029 |
| FR-014 | plan.md §The callers 5; research R6; contracts/cli.md §`wfctl end` | covered |
| FR-015 | plan.md §The callers 6; research R12; data-model.md Agreement; Order of work 7 | covered; PR-020, PR-021 |
| FR-016 | plan.md §The callers 7 and 7.1; research R13; Order of work 8 | covered; PR-020 |
| FR-017 | plan.md §The callers 7 and 7.2; research R14; Order of work 8 | covered; PR-024, PR-030 |
| FR-018 | plan.md §The callers 7 (`git show <head>:<path>`, any error refuses, deleted files filtered) | covered |
| FR-019 | research R15; Project Structure `architecture-decisions` | covered; PR-022 |
| SC-001 | Order of work 9 | covered |
| SC-002 | contracts/cli.md; quickstart §1-2 | covered |
| SC-003 | Order of work 4; research R3, R8 items 5 and 9 | covered |
| SC-004 | plan.md §Complexity Tracking; research R9 closing paragraph | covered; PR-022 |

## Assumptions challenged

- #635's PR waits on its level-2 record and on #339's record, and not on its
  level-3 record. Now stated that way in R14 and the cost row, and it matches
  the branch's diff today.
- The edit to #339's record belongs on this branch. Holds, since #339 is
  closed and a follow-up branch would wait on the same record (R14).
- The trunk value passed to `_record_gate` is never `None`. Holds, since
  `_judge` refuses before that point when `trunk_branch` returns `None`.
- An inherited boundary exception stops counting once the branch touches a
  record. Now stated the same way in FR-015, R12, item 6, and the data model.
  All share the "named after the branch" test, and so all share PR-020.
- The guard's refusal stops an unattended run. It's tamper-evident, since an
  agent can run `arch accept` (PR-024).

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- R14 now gives both halves of the cost for this branch: which records hold
  it, and why the #339 edit stays here rather than moving to a follow-up.
- Item 7 passes the trunk `_judge` already resolved, so the guard and
  `records_on_this_branch` read one range from one git call.
- The parent-is-the-arch-root rule reads only the diff output, so the guard
  gets the right set from the `main` checkout without reading any directory
  listing.
- FR-015, R12, item 6, the data model, and step 7 state the
  inherited-exception skip the same way, and step 7 tests both sides of it.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
