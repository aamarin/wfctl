# Plan review scan for #828

## Review 2026-11-20T02:10Z

- Verdict: satisfied
- Reviewed: plan.md 41bca0f8cbecb5f794f60f45de28271de0b58b27, spec.md a1333415e2a8373864a9f2124bc7e581b2296257, .specify/memory/constitution.md absent, design.md ff8eb09c3ce363c583f2b91f18a1a99a048cbb8f, docs/architecture/design/828-verify-measures-each-child.md b302abfb437fa21f1b4cd5cc8e7890c9e3eedc04, docs/architecture/worktree-span-read-from-git.md aaa1c76d3d5e7b415252ae10402f09d0c169a629, docs/architecture/wfctl-runs-the-verification.md 737e16e5908bbf17a961af5a8099e731a9707f8e, research.md a109b3d4e14239534d99c63d83dfab73a3defba8, data-model.md 93909e8a892c72bd691975d36a02dde722f40070, contracts/wfctl-timings.md 621c8218d333c2d070a2372ce1ad6f814d4bd32e, contracts/events.md 55974a62555d632c90af2d4f9b3a66ba2fa590b3, quickstart.md 59dd191bc0096f14da051eaa4786dbf77f959857, scans/clarify.md da9200942e9cbabd3812780cbc0b7f17bc3f6ffd
- Review type: full (no earlier review)
- Open: BLOCKER 0 · MAJOR 0 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/828-session-verify-durations/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-001, PR-003, PR-007) |
| Requirements and traceability | Outstanding (PR-001, PR-003) |
| Architecture and boundaries | Outstanding (PR-007) |
| Adversarial implementation and verification | Outstanding (PR-002, PR-004, PR-005, PR-006) |
| Security and reliability | Outstanding (PR-001, PR-005, PR-006; the security half didn't apply, since no secret, authorization, or new input source is involved) |

### Findings

- **PR-001, MINOR, open.** The removal hook's catch-all lets a removal go ahead without reaching the span call after `_save_unsaved`, so FR-007 misses that path and the no-span line gets a third, unnamed cause.
- **PR-002, MINOR, open.** The existing interrupt test patches `subprocess.run`, which the `Popen` change bypasses. The plan doesn't say how the new test raises the interrupt, checks the child is gone, or why it drops `subprocess.run`'s 0.25-second grace before the kill.
- **PR-003, MINOR, open.** SC-002 names macOS and Linux, but CI runs only on Linux, so the macOS branch of `_peak_bytes` is never tested.
- **PR-004, MINOR, open.** The plan doesn't say how an open worktree is matched to its branch for the no-span exclusion, and a detached worktree reads differently depending on the source.
- **PR-005, MINOR, open.** A valid JSON event with a missing or wrong-typed field, such as `seconds` as a string, would crash `wfctl timings`. The reading rules cover only lines that aren't JSON objects.
- **PR-006, MINOR, open.** The hook runs before the removal, so a removal that fails afterward, or a hook run by hand, writes a span for a worktree that still exists. The next removal adds a duplicate with the same `created`.
- **PR-007, MINOR, open.** The plan's file count says three changed where its listing shows four, and research R5 doesn't say a relative `gitdir` path resolves against the admin folder.

## Review 2026-11-20T02:21Z

- Verdict: satisfied
- Reviewed: plan.md 1865d0233de4ea21c31ad5e3a489ac3dd2ef158c, spec.md b180226476208e6269db317b7ca5afe58fac9fc4, .specify/memory/constitution.md absent, design.md ff8eb09c3ce363c583f2b91f18a1a99a048cbb8f, docs/architecture/design/828-verify-measures-each-child.md b302abfb437fa21f1b4cd5cc8e7890c9e3eedc04, docs/architecture/worktree-span-read-from-git.md aaa1c76d3d5e7b415252ae10402f09d0c169a629, docs/architecture/wfctl-runs-the-verification.md 737e16e5908bbf17a961af5a8099e731a9707f8e, research.md 005ab4c7bbbb8ec122ef72ad737df7d4a6c278ac, data-model.md 32e85081e266edf0ff2ddb8f11f59cbc0cddc1f0, contracts/wfctl-timings.md 459297a95f2131df40ef177c3aaa1f32c83ec104, contracts/events.md dbc1d76ddf0db7f45dda77fda63b225b6a3d8357, quickstart.md 59dd191bc0096f14da051eaa4786dbf77f959857, scans/clarify.md da9200942e9cbabd3812780cbc0b7f17bc3f6ffd, plan-review.plan.md 41bca0f8cbecb5f794f60f45de28271de0b58b27 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 5 · Fixed since the earlier review: 7
- Detail: /Users/andremarin/Development/wfctl-specs/828-session-verify-durations/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-008, PR-010) |
| Requirements and traceability | Outstanding (PR-008, PR-010; PR-001 and PR-003 fixed) |
| Architecture and boundaries | Resolved (PR-007 fixed) |
| Adversarial implementation and verification | Outstanding (PR-009, PR-010, PR-011, PR-012; PR-002, PR-004, PR-005 fixed) |
| Security and reliability | Outstanding (PR-008; PR-001, PR-005, PR-006 fixed; the security half didn't apply, since no trust boundary, secret, or sensitive data is involved) |

### Findings

- **PR-001, MINOR, fixed.** Fixed by plan Part 2 step 2, which writes the span on the catch-all path too.
- **PR-002, MINOR, fixed.** Fixed by the Validation list, which names how the interrupt test raises the interrupt and checks the child is gone, and keeps the 0.25-second grace.
- **PR-003, MINOR, fixed.** Fixed by testing `_peak_bytes` with `sys.platform` patched both ways.
- **PR-004, MINOR, fixed.** Fixed by research R8, which reads an open worktree's branch from its admin folder.
- **PR-005, MINOR, fixed.** Fixed by plan Part 3 step 5 and contract reading rule 6.
- **PR-006, MINOR, fixed.** Fixed by the new spec edge case and research R9.
- **PR-007, MINOR, fixed.** Fixed by the corrected file count and the relative `gitdir` note in R5.
- **PR-008, MINOR, open.** If `branch` didn't resolve, the catch-all path has no state folder and writes nothing, a cause the spec doesn't name. The plan also doesn't say `repo_root` and `branch` start as `None` before the `try`, so the catch-all would hit a `NameError`.
- **PR-009, MINOR, open.** A worktree stopped mid-rebase has a detached `HEAD`, so `resolve_branch` returns a short SHA and the span lands in a folder named for a commit, while R8 maps the same worktree to its real branch.
- **PR-010, MINOR, open.** The spec deduplicates on creation time alone, while the plan uses branch plus creation time. The open-worktree drop ignores the branch, and nothing says `commondir`'s nanosecond modified time is floored to the second before comparing.
- **PR-011, MINOR, open.** The plan and contract disagree on whether a wrong-typed field drops the whole command entry or one figure, and three malformed shapes have no rule. A branch with one valid span and one bad span lands on the no-span line, against FR-014.
- **PR-012, MINOR, open.** The replacement interrupt test drops the check that `verify.json` is unchanged after an interrupt, and two comments in the plan's source tree are stale.
