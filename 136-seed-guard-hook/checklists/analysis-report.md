# Analysis Report: seed-guard-hook

**Date**: 2026-09-09 · **Artifacts**: spec.md, plan.md, tasks.md, data-model.md,
research.md, contracts/, quickstart.md

Nine findings. All nine remediated in the same session; the two HIGHs were
unanswered questions rather than wording, and both are recorded below with the
reasoning, not just the edit.

## Findings and disposition

| ID | Category | Severity | Finding | Disposition |
|---|---|---|---|---|
| C1 | Conflict | HIGH | FR-014 (warn and continue on an unparseable file) and FR-017 (refuse on drift) both fire on a file wfctl cannot fully process, and nothing said which wins | Fixed. FR-014 now outranks FR-017 explicitly; T014a carries it into the code |
| U1 | Underspecification | HIGH | The receipt's state table had no row for `added: false` with the rule absent — the project had the rule, wfctl recorded it as theirs, they later deleted it | Fixed. Unified: any receipt plus a non-exact rule refuses |
| I1 | Inconsistency | MEDIUM | SC-002 required a byte-for-byte round trip; quickstart.md's own steps admit the first install reflows whitespace | Fixed. SC-002 and US2's Independent Test now say parsed content, which is what is true |
| G1 | Coverage | MEDIUM | SC-003 was measurable only against the eight-state table in `design.md`, which is gitignored and never reaches a reviewer | Fixed. The table is now in spec.md |
| G2 | Coverage | MEDIUM | FR-018 ("refusal covers only the rule") held by omission — nothing failed if a later change extended it | Fixed. T009a pins it |
| G3 | Coverage | MEDIUM | FR-016 (Claude layer only) inherited from existing target selection, unasserted | Fixed. T009a pins it |
| G4 | Coverage | MEDIUM | A declined removal was reported; a successful permission removal was not — the summary names hooks only | Fixed. New FR-021, T017a |
| T1 | Terminology | LOW | "directory-change rule", "the `cd` rule", `DENY_RULE`, `Bash(cd:*)` all naming one thing across four files | Fixed. One name per surface, mapping stated once in spec Key Entities and once in tasks |
| D1 | Duplication | LOW | `--force` means "overwrite files" on `install-config` and "accept a divergence" here | Accepted with mitigation. The flag name is right on both; T013 makes the help text part of the task rather than a follow-up |

## The two decisions this pass made

**C1 — an unparseable file does not refuse.** Drift cannot be established in a
file wfctl cannot read, so refusing there is refusing on a guess. It would also
hold the whole skills tree hostage to a stray comma, which is the trade
`cli.py:2952` already refused for the hooks: *"refusing here would trade a working
install for an unparseable settings file the user has to fix before they can have
either."* This is the clarify session's own distinction applied one level down —
an unparseable file is an accident, a drifted rule is a decision.

**U1 — a receipt is a receipt, whichever way `added` reads.** The alternative was
to let `added: false` plus an absent rule pass silently, on the grounds that
wfctl never owned that entry. Rejected: it splits one question into two answers
for no gain, and the project is equally entitled to delete a rule wfctl installed
and one it merely noticed. The unified rule is *a receipt exists and the file does
not carry that rule exactly* — which is also one sentence rather than a table with
an exception in it.

## Coverage after remediation

| | Count |
|---|---|
| Requirements | 21 |
| With at least one task | 21 |
| Without a verification path | 0 |
| Success criteria | 5 |
| Unverifiable as written | 0 |
| Tasks | 28 |
| Unmapped to a requirement | 4 — T005 (docstring), T023–T025 (process gates) |

The four unmapped tasks are deliberate: one is hygiene the docstring change
forces, three are the gates that run before the PR opens.

## Constitution alignment

No `.specify/memory/constitution.md` in this repo. The plan substitutes gates
from the accepted architecture records and `AGENTS.md`, and records the
substitution in its Complexity Tracking table as the template requires. No
conflicts found against the substituted set.

## Note on where this report lives

`specs/` is gitignored and `spec_root` resolves outside the working tree, so this
file reaches no reviewer. That is the defect #307 was filed for during this
session, and this report is an instance of it: the two HIGH findings above were
real design holes, and the only durable trace of them closing is the spec text
they changed.
