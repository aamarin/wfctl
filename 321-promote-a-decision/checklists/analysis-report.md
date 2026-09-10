# Analysis report — #321

**Scanned**: `spec.md`, `plan.md`, `tasks.md` — all three present and read.
**Also loaded**: `data-model.md`, `contracts/arch-accept.md`, `research.md`,
`quickstart.md`, and both committed records.

## Findings

| ID | Pass | Severity | Summary | Disposition |
| --- | --- | --- | --- | --- |
| F1 | F · Inconsistency | HIGH | The contract exited 0 when nothing was promotable; FR-007 requires the request to report as unsuccessful | Acted on |
| F2 | F · Inconsistency | MEDIUM | User Story 2 scenario 1 requires the already-accepted message to say *when*; the contract allowed the date to be dropped | Acted on |
| F3 | E · Coverage gaps | LOW | FR-008 — "MUST NOT infer acceptance" — is carried by no task | Accepted |
| F4 | A · Duplication | LOW | The command's output strings exist in both `design.md` § Level 1 and `contracts/arch-accept.md` | Accepted |
| F5 | E · Coverage gaps | LOW | FR-010 — acceptance survives the branch — is carried by no task | Accepted |

### F1 — the no-op that reported success

`contracts/arch-accept.md` gave `wfctl arch accept` with nothing promotable exit
0, reasoning that "nothing was asked for that could not be given". FR-007 says the
request MUST report as unsuccessful and draws no exception for an empty backlog.

The spec is authoritative and the contract is derived from it, so the contract was
corrected: exit 1 in both no-slug cases, with the empty-backlog reason on its own
line. Decided against amending FR-007 to carve out the empty case — a caller that
asked to accept and accepted nothing reading 0 is green over a no-op, which is the
reading this repository refuses in `doctor`, in `verify` and in `arch none`.

Caught here rather than in implementation because it is only visible with both
documents open: each is internally consistent.

### F2 — a scenario the contract could not always satisfy

The scenario requires the already-accepted refusal to name when. The contract
allowed the date to be omitted for a record carrying no `accepted` `Log` line.

An earlier draft of this finding claimed that was seven of the ten accepted
records. It is none of them — every record accepted by hand carries the line, and
the claim was written from memory rather than from a count. The finding stands on
the narrower ground: `_set_status` requires a `## Log` section and not an
`accepted` entry within it, so a status edited by hand without one reaches this
branch, and a scenario that cannot always be satisfied is still a defect at any
frequency.

Corrected in the contract by answering the question instead of dropping it:
`(no acceptance logged)`. Decided against inventing a date from git history — the
record's `Log` is the durable answer this whole feature exists to create, and
reading one from elsewhere would make the message assert something the file does
not say. Decided against relaxing the scenario, for the reason F1 gives: the spec
outranks the contract.

### F3 — a prohibition with no test

FR-008 forbids inferring acceptance from a merge, a passing step, shipped code or
a risk assessment. No task verifies it, because it is a prohibition on code that
does not exist, and a test cannot assert the absence of an inference nobody wrote.

Accepted rather than fixed. What would make it checkable is a test that `_arch`
imports nothing from `_pipeline` — the module boundary is the form the prohibition
actually takes, and it is the thing a later change would break. Recorded here as a
review question rather than added as a task: `tasks.md` is not this step's to
edit, and the check is worth one line in review whether or not it becomes a test.

### F4 — two copies of the output strings

`design.md` § Level 1 renders each state's literal string as the level-1 gate's
answer; `contracts/arch-accept.md` renders the same strings as the surface to
build. Both are in `FEATURE_DIR` and neither reaches a reviewer.

Accepted. T009 names the contract as the one to follow, so a drift between them
has a stated winner, and the level-1 answer is a record of what the gate concluded
rather than a second specification. Deleting it would remove the gate's evidence.

### F5 — a property with no task

FR-010 says acceptance survives the branch that wrote it. Nothing tests it,
because it is a consequence of where the fact is stored: the record file is
committed and the state dir is not. The task that would test it would be asserting
that no state-dir write happens, which is F3's shape again.

Accepted, and named in review: a later change that caches acceptance in the state
dir would violate it silently, and that is what a reviewer should look for.

## Requirement-to-task coverage

Nine of eleven functional requirements are carried by a named task — **82%**.

| Requirement | Tasks |
| --- | --- |
| FR-001 | T004, T009 |
| FR-002 | T009, T015 |
| FR-003 | T002, T004, T005 |
| FR-004 | T005, T006, T007 |
| FR-005 | T004, T011, T012, T013, T014 |
| FR-006 | T008 |
| FR-007 | T016, T018 |
| FR-008 | — (F3) |
| FR-009 | T010, T020 |
| FR-010 | — (F5) |
| FR-011 | T002, and the existing supersede tests |

Both uncovered requirements are prohibitions rather than behaviours, and both are
recorded above as review questions. NFR-001 is untestable by its own statement and
NFR-002 is an accepted risk; neither is counted.

## Next actions

1. Implement from `tasks.md` — the contract corrections above are already in
   `contracts/arch-accept.md`, so T009 reads the corrected strings.
2. Carry F3 and F5 into the review as questions: does `_arch` still import nothing
   from `_pipeline`, and does acceptance still touch no state directory.
