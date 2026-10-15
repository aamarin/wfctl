# Plan review scan for #571

## Review 2026-10-15T10:57Z

- Verdict: unsatisfied
- Reviewed: plan.md 04c371897d76d396f8629034934bffa6a11c0044, spec.md 2fcc707a83127f774eb36d5bcb5967b983e8b4f7, .specify/memory/constitution.md absent, design.md 81d685521e5d2e2850f281921cb920c1dbd391a0, docs/architecture/change-carries-release-note.md 871d5119e12faba1d6c659b3134a86c6ae9fdeee, docs/architecture/design/571-towncrier-builds-release-notes.md 95807a531a9fda579d0bd27199c98ce60de20737, research.md ebcc5e2fe8bbc3e9df0f9c1ff7a860c2fc40dadb, data-model.md 48c0f4f81736638d17312571d8342300e74d237b, quickstart.md 46842929b0222aedd7852c09b40451ed189295a0, contracts/check-release-note.md f6dabad5bac917ad8409f8aa55c710639d981072, contracts/release-script.md b815819701f3122a78f04ef205fae90c37e4f034, contracts/tag-job.md ebedc771d1f89a05d710888d2085550ffb5c8b5b, checklists/requirements.md 37a6a5ce0798ad3e653a03b8fa785d1ce5f4ead5, tests/test_install_config.py 0281ffaa4b3ef803a73f1524c9a0271b26aac47d, tests/test_shape.py 03b350995d6ec85773b0ae5cac37290b571011dd, tests/conftest.py ab0a68e5a72288cdf034f54a415fbbc547c8d725, .github/workflows/ci.yml 51235f6139dda5761a8e3926b459e68b8ac4e205, .github/pull_request_template.md 3ee00e4a2b3a566b3a13b0de2e3f7c36e87851da, pyproject.toml 0529147d3b9406b2c56277e4570a6556440d949f, wfctl.json cd10684006bd8b3c52967743cd4e6e5a63a1a00e, wfctl/_verify.py de7930cbba4cc9d9056a21009d5d0c2f70b8f270
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 1 · MAJOR 1 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/571-release-automation/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-002) |
| Requirements and traceability | Outstanding (PR-003, PR-008) |
| Architecture and boundaries | Outstanding (PR-001) |
| Adversarial implementation and verification | Outstanding (PR-004, PR-005, PR-006) |
| Security and reliability | Outstanding (PR-007, PR-009) |

### Findings

- **PR-001, BLOCKER, open.** `tests/test_install_config.py`
  `test_shipped_github_config_matches_this_repos_own_copy` asserts that this
  repository's `.github/pull_request_template.md` is identical to the shipped
  copy, and `spec.md §FR-018` now requires the two to differ. `plan.md` never
  names the test. Stands because the plan has to decide what that drift guard
  still protects: delete it, exempt the file, or compare with the "Type of
  Change" section taken out.
- **PR-002, MAJOR, open.** `contracts/tag-job.md` falls back to
  `--generate-notes` on an empty body, while `spec.md` User Story 3 says the
  generated list is no longer used and `change-carries-release-note` crosses
  that path out. `plan.md §Design records` says it follows both records and
  doesn't list this difference. Stands because v0.19.0 to v0.23.0 already have
  published releases, so the reason given for the fallback never arises.
- **PR-003, MINOR, open.** `contracts/check-release-note.md` gives no create
  command in the message for a branch with no issue, which `spec.md §FR-007`
  requires of every failure message.
- **PR-004, MINOR, open.** towncrier 26.9.0 renders "No significant changes."
  for an empty copy, so the draft in User Story 2 scenario 8 is never empty and
  that line could be published unnoticed. `git rm` over `changes/` also fails
  once a past release has removed the directory.
- **PR-005, MINOR, open.** The title line the script drops depends on the
  invocation: `# wfctl 0.23.1 (…)` when `--dir` holds this repository's
  `pyproject.toml`, `# 0.24.0 (…)` with `--config` and `--dir` on the copy.
  `plan.md` and `research.md` name neither invocation.
- **PR-006, MINOR, open.** The check reads `GITHUB_HEAD_REF` first, CI sets it
  while `pytest` runs on a pull request, and `tests/conftest.py` doesn't clear
  it, so the check's tests behave differently in CI. A pass on this branch's
  own pull request also doesn't show the branch lookup works.
- **PR-007, MINOR, open.** `contracts/tag-job.md` finds the release commit with
  `-G '^version = '`, the text match the job's own comment warns against, and
  nothing checks that the commit found carries `$v`.
- **PR-008, MINOR, open.** The repository allows squash and rebase merges. A
  pull request merged that way without a note is never listed, and can lead to
  "Nothing to release", which `spec.md §FR-014` forbids. `plan.md` doesn't state
  the merge-commit assumption.
- **PR-009, MINOR, open.** `contracts/release-script.md` puts the version prompt
  before the editor, the reverse of `spec.md` and `design.md`, without listing
  it under Changes from the spec. A non-zero editor exit is unspecified, and a
  re-run after an unpushed release commit prints "pull first", which doesn't
  help.
