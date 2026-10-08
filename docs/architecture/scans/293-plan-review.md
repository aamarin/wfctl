# Plan review scan for #293

## Review 2026-10-08T02:01Z

- Verdict: satisfied
- Reviewed: plan.md cf53f835537e3406c244454340cbff24544f607e, spec.md 59ad635caae7fa7b34da475cbb224fde004990ad, .specify/memory/constitution.md absent, design.md f2960fe2d5d4f671711bf684fc3f66bf82806e27, research.md 02989e5be9ffc3f3cc110c408654ef2a150d56ba, data-model.md 2dee00f7d4fb5e7e484652f7630145064936e37b, quickstart.md fdeafb100cd743ffdff0b942bcb4a0b4476d697a, docs/architecture/deletion-follows-recorded-files.md 0e4f7e4a9917e80d151697919161da411cd9e73f, docs/architecture/install-modes.md 4233b4dbe4343f4c734e175db91417108db59428, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 4 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/293-mirror-below-recorded-dir/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-005, PR-006) |
| Architecture and boundaries | Outstanding (PR-003) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-004) |
| Security and reliability | Outstanding (PR-001, PR-002) |

### Findings

- **PR-001, MAJOR, open.** `spec.md §Edge Cases` calls the upgrade's one-time
  backup harmless, and it is not. A later `uninstall-skills` restores wfctl's
  own earlier copies of the three scripts instead of removing them, so US3
  scenario 3 fails in an upgraded repository. Where the old folder entry had a
  backup of its own, the per-file copy overwrites the developer's original
  scripts under `.wf-skills-backup/.specify/scripts/bash/`. It stands because
  neither the plan nor the record accounts for the restore loop in
  `uninstall_skills_cmd`. It was graded MAJOR rather than BLOCKER because the
  overwrite needs a folder entry with its own backup, and the record already
  accepts losing that entry's pointer.
- **PR-002, MAJOR, open.** An older wfctl running `install-skills --prune` over
  the new per-file record deletes the three scripts right after copying the
  folder, and crashes in `shutil.copytree` when per-file backups already exist.
  It stands because the plan and the record cover the upgrade direction only,
  and this repository runs two wfctls side by side.
- **PR-003, MINOR, open.** `research.md §1` says the stale `none`-layer cleanup
  reads only `.agents/` paths, and it compares every path. A `none` entry from
  before the layer split holds `.specify/scripts/bash` and is never dropped
  after the change. It stands because the research claim is wrong as written.
- **PR-004, MINOR, open.** The plan does not say the guard's prefix test
  compares path components. A plain string prefix would guard a dropped
  `brainstorm` skill because `brainstorming` exists, which breaks the claim
  that skill behaviour is unchanged. It stands because the plan leaves the
  comparison unstated.
- **PR-005, MINOR, open.** The plan names three test themes against eleven
  scenarios and SC-004. US1 scenario 3, US2 scenarios 2 - 4, US3 scenarios 1
  and 4, and SC-004 map to no test. It stands because `plan.md §Project
  Structure` carries no mapping.
- **PR-006, MINOR, open.** A fresh install now writes three `.gitignore` lines,
  one per script, instead of `.specify/scripts/bash`, so a developer's own
  script there shows in `git status`. It stands because the plan says the
  change adds nothing a developer can see.

## Review 2026-10-08T10:33Z

- Verdict: satisfied
- Reviewed: plan.md f23f4bbc6634ac512c550b178822f3ec35e28d22, spec.md 124c2d23ebe59177ecefe30d9707df75ca3dfccb, .specify/memory/constitution.md absent, design.md c32081dc9e19f32a52a40b72d957e872874ddf87, research.md 02989e5be9ffc3f3cc110c408654ef2a150d56ba, data-model.md 2dee00f7d4fb5e7e484652f7630145064936e37b, quickstart.md fdeafb100cd743ffdff0b942bcb4a0b4476d697a, docs/architecture/deletion-follows-recorded-files.md 0b68dc4d882006850550d851b60578533ccab080, docs/architecture/install-modes.md 4233b4dbe4343f4c734e175db91417108db59428, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, plan-review.plan.md cf53f835537e3406c244454340cbff24544f607e (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 7 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/293-mirror-below-recorded-dir/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-007, PR-009) |
| Requirements and traceability | Outstanding (PR-005, PR-006, PR-007, PR-009) |
| Architecture and boundaries | Outstanding (PR-003) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-008) |
| Security and reliability | Resolved (PR-001 and PR-002 fixed) |

### Findings

- **PR-001, MAJOR, fixed.** Fixed by `plan.md §Summary` part 3, `spec.md
  §FR-008`, User Story 2 scenarios 4 and 5, and the record's amended
  Consequences. A path below a recorded folder now counts as on record, so the
  upgrade takes no backup and a later uninstall restores nothing.
- **PR-002, MAJOR, fixed.** Fixed by the record's Consequences and `spec.md
  §Edge Cases`, which accept the cost while Andre is the only user of wfctl.
  The reviewer traced the recovery, a run of the current wfctl, and it holds.
- **PR-004, MINOR, fixed.** Fixed by the `plan.md §Summary` paragraph requiring
  `Path.parents`, which `spec.md §FR-008` repeats.
- **PR-003, MINOR, open.** `research.md §1` says the stale `none`-layer cleanup
  reads only `.agents/` paths, and it compares every path. It stands because
  the research claim is still wrong as written.
- **PR-005, MINOR, open.** The plan names three test themes against twelve
  scenarios that name a command, SC-004, and FR-008. US1 scenario 3, US2
  scenarios 2 - 5, the FR-008 sibling-name case, US3 scenarios 1 and 4, and
  SC-004 map to no named test. It stands because the plan carries no mapping.
- **PR-006, MINOR, open.** A fresh install writes three `.gitignore` lines
  instead of one folder line, and the plan says no visible string changes. It
  stands because the plan has not been corrected.
- **PR-007, MINOR, open.** `quickstart.md §1` still says the install backs the
  scripts up once, which contradicts plan part 3, FR-008, and US2 scenario 4. It
  stands because the quickstart was not updated with the plan.
- **PR-008, MINOR, open.** Swapping the helper into the backup branch alone
  raises `KeyError` on `prior_items[rel_dest]` for a path on record only through
  a parent. It stands because the plan does not say that branch needs two cases,
  an exact match that carries its backup forward and a parent match that
  records none.
- **PR-009, MINOR, open.** `plan.md §Constitution Check`, `§Project Structure`,
  and `§Source Code`, and `design.md §Structure`, still describe the
  two-change plan without the helper. It stands because those sections were not
  updated with Summary.

## Review 2026-10-08T22:32Z

- Verdict: satisfied
- Reviewed: plan.md d7a81cbc1e3ceafdaa2185a6d6573857a65aace6, spec.md 124c2d23ebe59177ecefe30d9707df75ca3dfccb, .specify/memory/constitution.md absent, design.md 01d0f724e1ec585823dc28dbd821dd563b90d353, research.md c26248e4fafb1720c1a001211fabfcc660285499, data-model.md 2dee00f7d4fb5e7e484652f7630145064936e37b, quickstart.md 6ae3b68a119462ac7c9f065b5f48acea428da431, docs/architecture/deletion-follows-recorded-files.md 0b68dc4d882006850550d851b60578533ccab080, docs/architecture/install-modes.md 4233b4dbe4343f4c734e175db91417108db59428, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, plan-review.plan.md f23f4bbc6634ac512c550b178822f3ec35e28d22 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 3 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/293-mirror-below-recorded-dir/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-009, PR-011) |
| Architecture and boundaries | Resolved (PR-003 fixed) |
| Adversarial implementation and verification | Outstanding (PR-010) |
| Security and reliability | Resolved (PR-001 and PR-002 remain fixed) |

### Findings

- **PR-003, MINOR, fixed.** Fixed by `research.md §1`, which now says the
  stale `none`-layer cleanup compares every path, and why no entry naming the
  scripts folder survives an install since the layer split.
- **PR-005, MINOR, fixed.** Fixed by `plan.md §Test Plan`, which maps all 12
  scenarios that name a command, FR-006, FR-008, and SC-004 to a test.
- **PR-006, MINOR, fixed.** Fixed by `plan.md §Summary`, which states the
  per-script `.gitignore` lines and when none are written.
- **PR-007, MINOR, fixed.** Fixed by `quickstart.md §1`, which now expects no
  backup and checks for one.
- **PR-008, MINOR, fixed.** Fixed by `plan.md §Summary` part 3, which gives the
  backup branch its two cases.
- **PR-001, PR-002, and PR-004** remain fixed, as the earlier review recorded.
- **PR-009, MINOR, open.** `design.md §Software design decisions` and `§MVP
  Scope` still describe the change without the helper. It stands because only
  `design.md §Structure` was updated.
- **PR-010, MINOR, open.** The FR-008 test row checks the helper only, and the
  plan does not say the orphan guard shares that comparison. A string-prefix
  guard would pass every row. It stands because no test covers the guard's
  comparison.
- **PR-011, MINOR, open.** The US2 scenario 1 test row does not run `doctor`
  after the upgrade, and `spec.md §FR-007` and `§SC-002` require a clean
  `doctor`. It stands because the row omits that step.
