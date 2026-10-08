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
