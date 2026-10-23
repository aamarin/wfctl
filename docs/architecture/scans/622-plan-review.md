# Plan review scan for #622

## Review 2026-10-23T10:19Z

- Verdict: unsatisfied
- Reviewed: plan.md 96270dd4a271be76eb72d06b2d298484768a6a58, spec.md 1c0295476e1be3e76a9c2aa58e098602d6c41fbd, .specify/memory/constitution.md absent, design.md d40e0b4516c828c4cbe8fd0640829c5222ddebc3, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 0b649f0a435241ffd1007d8b4b7a845cebde164b, docs/architecture/design/622-blocked-reviewer-relays-report.md 29357caf33b2837de6f39a779afa8ec1ff034455, docs/architecture/design/622-review-check-in-worktree-guard.md 34648561c62fc6280d75df7b436cd41d2f296f3a, research.md cb3f2229f4e15641e3c14458cfca915a45c949df, data-model.md c13adbc782701c1527f845dfef6de4c98633970b, contracts/cli.md e32da44ed0a574afb86b4c7c4ecca6d83e775d46, contracts/config.md e36510dafc37222df3080d496bbc0da794cff51e, quickstart.md feb1ec0adbe61a05f4f034dbdd290eccd5a8ba38, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4
- Review type: full (no plan copy from the earlier review)
- Open: BLOCKER 1 · MAJOR 5 · MINOR 9 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-012) |
| Requirements and traceability | Outstanding (PR-010, PR-013) |
| Architecture and boundaries | Outstanding (PR-001, PR-008, PR-009, PR-011, PR-014) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-015) |
| Security and reliability | Outstanding (PR-002, PR-003, PR-004, PR-006) |

### Findings

- **PR-001, BLOCKER, open.** The plan keeps the vendored `/security-review` file byte-identical to upstream, and `vendor-upstream-skills.md` requires an attribution line inside every derived file. The test in `tests/test_skill_attribution.py` only reads `*/SKILL.md` and the specify scripts, so it can't see a file at `reviewing-security/references/security-review.md`. The finding stands because the plan has no place for the attribution line. Part of the cause is in `spec.md`, where FR-024 asks for the line and FR-025 says the file stays unedited.
- **PR-002, MAJOR, open.** Once a command matches, the review check only says how it fails for an unreadable record and a failed `gh` lookup. Every other error is unassigned. The `gh pr view` call has no timeout, so the host can kill the guard on its own hook timeout without an exit 2, and the merge goes ahead.
- **PR-003, MAJOR, open.** The sign-off refusal is the pattern `\breview\s+sign-off\b`. An agent gets past it with `wfctl review 'sign-off'`, `wfctl review sign\-off`, a shell variable, or by writing `sign-off.json` directly, and FR-013 requires a refusal every time.
- **PR-004, MAJOR, open.** Other `gh` commands open or merge a PR without matching, so SC-001's "zero exceptions" can't hold. Examples are `gh pr -R o/r merge`, `gh api` calls on the pulls endpoints, the GraphQL mutations, and `gh pr merge` while checks are pending, which turns on auto-merge and merges a later head. Part of the cause is in `spec.md`, since FR-012 lists only three commands.
- **PR-005, MAJOR, open.** R4 doesn't say how the check reads the PR argument or `--head` out of a command it only matches as text. When the extraction misses the argument, the check falls back to the current branch and judges the wrong one. The plan judges `--head` locally instead of looking it up on GitHub as FR-012a says, and it doesn't handle `-R`.
- **PR-006, MAJOR, open.** A run with zero expected reviewers completes with no review at all. This happens when a group's `reviewers` list is empty or missing, which `wfctl check config` doesn't catch, or when every listed model is unavailable. That can skip the security group, which FR-001 forbids.
- **PR-007, MINOR, open.** The `shutil.which` lookup runs on the agent's `PATH`, so the plan's claim that the agent can't mark a reviewer unavailable doesn't hold. In the other direction, a model that is on `PATH` but fails, such as Codex without a login, blocks every PR. The plan doesn't say it reads FR-023 this narrowly.
- **PR-008, MINOR, open.** The plan marks the `a-rule-is-expressed-as-a-check.md` gate as passed, while its own text says the three-round cap is checkable and ships as prose until #626. That belongs in Complexity Tracking as a deviation.
- **PR-009, MINOR, open.** The Safety section of `AGENTS.md` still says wfctl doesn't gate outward actions, and the plan lists no edit to it.
- **PR-010, MINOR, open.** The trunk refs are underspecified. The `trunk_branch` function usually returns `origin/main`, so the plan's "`origin/` counterpart" has nothing to add. The plan doesn't say what happens when `trunk_branch` returns None, and it uses discovery where FR-006 sets the default to `main`.
- **PR-011, MINOR, open.** The config contract puts no limit on a group's name. A name such as `../x` writes outside `reviews/`, case isn't normalised (`Security` and `security`), and a name can start with a character that isn't a letter.
- **PR-012, MINOR, open.** The spec's Validation Strategy and the design record both name a `wfctl store specs` test for SC-004, and the plan's test list leaves it out. The plan also doesn't say what happens to an old `$FEATURE_DIR/reviews/` folder.
- **PR-013, MINOR, open.** FR-003, the security group committing its fixes before the code group reviews, and FR-004, one findings table in chat, have no place in the plan. The plan names the skills it rewrites but not what they say.
- **PR-014, MINOR, open.** The upstream `security-and-hardening` skill points at `../../references/security-checklist.md`, a path outside its own folder, and R10 doesn't vendor that file.
- **PR-015, MINOR, open.** When reviewed commits aren't pushed yet, the pushed head is behind the last reviewed commit, and R3's ancestor rule then lists every commit on the branch as unreviewed. The check still refuses, which is safe, but the list it prints is wrong.
