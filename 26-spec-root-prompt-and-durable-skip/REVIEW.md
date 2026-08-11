# Review: planning artifacts, `wfctl-specs` 4b1fa8b..d364c31

**Target**: design.md, spec.md, plan.md, tasks.md, data-model.md, contracts/cli.md, quickstart.md, delivery.md
**Reviewed as**: a work product to be implemented, not as prose. Every claim about `wfctl`'s behaviour was re-verified against the working tree rather than against the reasoning that produced it.
**No implementation exists** (implement 0/48), so passes 2 (security) and 5 (performance) have no surface: no user input, no secrets, no queries, no hot paths. Both recorded as N/A rather than silently skipped.

---

BLOCKER  contracts/cli.md, plan.md, tasks.md T022 — the `pre_remove` hook is specified across two YAML lines with no `;` before `else`. YAML folds the break to a space, so `else` becomes an **argument**, not a keyword → fix: put `; else` on one logical line, or use a YAML block scalar (`- |`).

BLOCKER  tasks.md T019 vs T018 — the narrow exit rule is not implementable as specified. `cli.py:345` catches everything from one `try`, and `archive()` raises a bare `OSError` carrying no indication of whether the plan was non-empty. T018 additionally forbids changing the returned tuple shape → fix: specify the channel — a typed `ArchiveFailed(at_risk: int)` raised by `_archive`, or an explicit status in the return — in data-model.md before implementation starts.

WARNING  tasks.md Phase 3 header — "Write these first and confirm they FAIL before implementing" is wrong for two of the ten tests. T008 is a **regression guard** asserting today's behaviour, and T014 asserts exit 0 when nothing is at risk, which the command already always does. Both must **pass** before implementation; a failing T008 means the fixture is wrong, not that work is needed → fix: split the block into "must fail first" (T009–T013, T015–T017) and "must pass first" (T008, T014).

WARNING  tasks.md T013 — the named injection method ("unwritable state dir") fails at `resolve_agent_dir`/`mkdir`, **before** the copy loop, so it cannot produce the partial state T016 and T017 exist to detect → fix: name the method that actually works — patch `shutil.copy2` to raise on the Nth call, as the A2 reproduction did.

WARNING  tasks.md T020 — promote-on-success does not say what happens to a staging directory left by a **killed** process (SIGKILL, no exception to catch). `_copy` uses `exist_ok=True`, so stale files would be merged into the next run and promoted into `archive/` as phantom entries → fix: `shutil.rmtree(staging, ignore_errors=True)` before the copy loop, or make the staging name unique per run.

NIT  spec.md FR-020 — a fifth transitional check is added while #36 exists to remove all five. Deliberate and recorded (it gives FR-019's alias an end condition), and the alternative was an alias with no removal criterion. Flagged only so the trade stays visible.

NIT  working tree — 82 uncommitted lines in `.gitignore` from `wfctl install-skills`, unrelated to this feature and already covered by PR #34 on another branch → fix: do not commit here; `git checkout .gitignore` before the first implementation commit.

---

## What held up under scrutiny

Verified against the working tree, not assumed:

- **Every source line number** in tasks.md still resolves to the intended construct: `cli.py:276, 300, 424, 604, 803, 1338`, `_archive.py:98, 113, 114, 158-176, 173`, `_paths.py:222`.
- **The `_NON_LAYER_KEYS` crash claim is real.** `_layer_keys` returns every key not in the set and callers do `manifest[key].get("items", [])`; `True.get` raises `AttributeError` on sight. T033's "same commit" constraint is justified.
- **The containment predicate fits `_plan`'s existing shape.** It filters a list that function already assembles; no signature change needed, and T018's "do not change the tuple shape" is right for that task in isolation.
- **The A2 atomicity finding reproduces** against the real module, and the naming contract in data-model.md matches observed behaviour (three successful runs → `archive/` plus two timestamped directories).
- **R-001 and R-002** were established by experiment, and `--force` genuinely does not bypass the hook.

## Passes with no surface

- **Security**: no user input, no credentials, no queries, no rendered output. The one adjacent concern — copying possibly-secret untracked files into a long-lived state directory — was deliberately scoped out to #37.
- **Performance**: the predicate is a path comparison over a list already built; no new filesystem calls or subprocesses. `feature-paths` runs on every speckit invocation and is untouched.

## Over-engineering

The artifacts specify a change that is net-negative in the hook and net-positive in
`archive()`. Nothing here is speculative flexibility: no interface with one
implementation, no configuration nobody sets, no abstraction added for a second
caller that does not exist. FR-020 is the only candidate and it buys the alias a
removal criterion.

`net: −1 line in .workmux.yaml, +~6 in archive(). Lean already.`

## Verdict

**Request changes** — 2 blockers.

Both are in the executable specification rather than in code, which is the cheapest
possible place to catch them. The hook bug in particular would have shipped: it
passes `bash -n`, and its failure mode when `wfctl` is present is a non-zero exit,
which after this feature means **every teardown in every repo is refused**.

Fix both, plus the three warnings, before starting T001.

---

# Resolution

All 2 blockers and 3 warnings fixed. Both NITs left open by decision.

| Finding | Outcome |
|---|---|
| BLOCKER hook YAML fold | **Fixed** — block scalar (`- \|`) in all three copies (contracts/cli.md, design.md, quickstart.md; plan.md had none). Verified by parsing the YAML and executing the result with `wfctl` present and absent. Contract now carries the failure table so the form is not "tidied" back. |
| BLOCKER exit-status channel | **Fixed** — `ArchiveIncomplete(at_risk, cause)` specified in data-model.md with the two rejected alternatives; T019 rewritten to name it; T018 amended so "do not change the tuple shape" reads as a consequence of that choice rather than a constraint fighting it. |
| WARNING must-fail vs must-pass | **Fixed** — Phase 3 test block split explicitly. T008 and T014 marked "Must pass now"; delivery.md's Wave 2 gate and verification table updated to match. |
| WARNING T013 injection method | **Fixed** — now specifies monkeypatching `shutil.copy2` to raise mid-loop, and states why the unwritable-state-dir method fails at `mkdir` before any copy. |
| WARNING T020 stale staging | **Fixed** — `shutil.rmtree(staging, ignore_errors=True)` required before the copy loop, with the SIGKILL path spelled out. |
| NIT FR-020 fifth lint | **Open by decision** — deliberately included so FR-019's alias has an end condition; #36 tracks removing all five. |
| NIT uncommitted `.gitignore` | **Open** — 82 lines from `install-skills`, belongs to PR #34. Do not commit here; `git checkout .gitignore` before the first implementation commit. |

## Verification

- The block-scalar hook was parsed with PyYAML and executed both ways: `wfctl`
  present → invoked with exactly two arguments; absent → warning printed, exit 0.
  The folded form was executed too, and reproduced both failure modes.
- No copy of the folded form remains in any artifact.
- Task IDs still T001–T048, sequential, no gaps.
- Every task still names a verification path.

**Revised verdict: Approve.** No blockers outstanding. The artifacts are ready for
T001.

Two findings were only reachable by executing what the documents specified rather
than re-reading them — the hook bug passes every static check, and the exit-status
gap only shows when you trace `cli.py:345` back into `archive()`. Worth repeating
that method on the implementation diff.
