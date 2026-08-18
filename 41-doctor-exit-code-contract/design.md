# doctor: one exit-code contract, and the checks that belong in it

Issue: [#41](https://github.com/aamarin/wfctl/issues/41) · Children: #36, #31, #38
Base: `origin/master` at `271bb2c` (post-vendoring)

## Problem Statement

How might we make `wfctl doctor`'s exit code mean one thing, so it can be trusted
in CI, without turning every advisory warning into a build failure?

## The defect

`doctor` has no exit-code contract. Three different conventions coexist:

| Site | Returns | Effect on exit code |
| --- | --- | --- |
| `_check_wfctl_version` (`cli.py:1626`) | `int` | folded at `:1872` |
| the four `_check_*(repo_root)` calls (`cli.py:1884-1887`) | `None` | never touches it |
| the manifest loop (`cli.py:1906-1934`) | — | sets `exit_code = 1` inline |

So `doctor` prints `⚠` and exits 0. Fine for a human reading output, wrong the
moment it runs in CI.

Each of the four `None`-returning checks documents the omission as deliberate —
*"Never touches doctor's exit code — drift, reported like the checks around it"* —
and `test_doctor_exit_code_is_unchanged_by_the_spec_root_warning` locks it in.
That convention is what this work reverses, so the reversal has to be explicit
rather than incidental.

## Recommended Direction

**One rule, stated once: a check returns `bool` meaning "found drift", OR'd into
`exit_code`. A check that could not determine an answer returns `False`.**

The second half is what makes the first half safe. Two sites already behave this
way and argue for it in their own comments — `_check_wfctl_version`'s offline
branch returns 0, and the no-recorded-hash warning at `cli.py:1913` says
*"Unmeasurable, not stale... leave the exit code alone."* Without the rule
written down, "any drift fails" would sweep both in and fail builds on a flaky
network rather than a real problem.

With it, `exit 1` means *doctor found something wrong with this repo* and
`exit 0` means *doctor found nothing wrong*, where "couldn't look" counts as
nothing found. That is the weaker of the two possible guarantees, and the honest
one: a check that cannot reach the network has no finding to report.

The four checks that flip to exit 1 all key on positive evidence of real drift —
an unwired teardown hook, a stranded `specs/` directory, a surviving `.agent/`.
None fires on a clean repo. `_check_workmux_hook` in particular returns early
when there is no `.workmux.yaml` at all, so a repo that never adopted workmux is
untouched.

## What the vendoring changed

`#43` (merged as `271bb2c`) vendored the wf-skills tree into the wfctl package
and retired the install-time clone. Two consequences for this work, both
verified against the merged tree:

**#31 stops being a doctor check.** Its stated obstacle was that the assertion
crosses a repository boundary and CI installs nothing. The command files now sit
at `wfctl/agents/commands/*.md`, in the same package as `_STEP_COMMAND`
(`_pipeline.py:14-23`). A plain test asserts the pairing offline, at CI time,
with no install and no network — strictly earlier than a runtime report. The
bundle `content_hash` check already covers an installed tree that drifted from
the bundle, which was the only thing a doctor-side check would have added.

**#36's deletion was blocked by a bug the vendoring introduced.**
`wfctl/agents/configs/workmux/.workmux.yaml` shipped calling `wfctl
archive-story`, the pre-rename name. A freshly seeded repo therefore failed
wfctl's own `doctor`, and the report's remedy — *"re-seed it with `wfctl
install-config`"* — wrote the same name back. #41 verified the removal condition
against `241b245`, before the vendoring imported the name.

Fixed ahead of the rest of this work, with a regression test at
`tests/test_bundle.py` asserting through `_workmux.pre_remove_uses_former_name`
— the function `doctor` itself calls, so the two cannot disagree about what
counts as stale. The existing `install-config` tests all seed a *fake* bundle,
which is what let the real template ship unread.

With that landed, `_check_stale_archive_hook`'s removal condition holds again.

## Key Assumptions to Validate

- [ ] **No repo trips the four flipped checks incidentally.** Test: run `doctor`
      against this repo and a freshly seeded one, confirm exit 0 in both. Already
      true for this repo — no orphans in any recorded parent dir, all eight
      `_STEP_COMMAND` entries resolve.
- [ ] **`.agents/` and `.specify/` hold no hand-authored files.** The orphan check
      treats any unrecorded file there as wfctl's abandoned output. If people do
      hand-author into those trees, the check produces false failures. Test: the
      scan against this repo and the pfms consumer.
- [ ] **`_check_stale_archive_hook` has no remaining consumer.** pfms was checked
      and does not name `archive-story`; the shipped template no longer does. Test:
      grep both repos before deleting.
- [ ] **PR A and PR B stay non-conflicting.** PR A must not touch
      `_check_wfctl_version` (`cli.py:1626`), the one function PR B rewrites end
      to end. Test: `git diff --stat` on the branch names it nowhere.

## Scope

One PR. Five items, in this order — items 1–3 each depend on the state the
previous one leaves.

1. **The workmux template fix.** *(done)* Unblocks item 2.
2. **Delete `_check_stale_archive_hook`** (`cli.py:1783`) and its call site
   (`:1885`). Settles the set of checks before anything is written against it.
3. **The contract.** Convert the remaining three `_check_*(repo_root)` functions
   to `-> bool`, OR their results into `exit_code`, and state the
   couldn't-check-is-not-drift rule where the convention is defined. Rewrite
   `test_doctor_exit_code_is_unchanged_by_the_spec_root_warning`, which asserts
   the old convention.
4. **#38's orphan check**, adopting the contract. Walks the parent directories of
   recorded manifest items, restricted to `.agents/` and `.specify/`, and reports
   files the manifest does not list.
5. **#31 as a test.** Every `_STEP_COMMAND` value has a matching
   `wfctl/agents/commands/<name>.md`. No `cli.py` change.

Bundled here rather than split because items 2–4 all edit `doctor_cmd` and each
either defines or adopts the return contract. Item 5 shares no files with the
rest and could stand alone; kept in for reviewability as one decision.

## Not Doing (and Why)

- **No check registry.** Four calls in a row in `doctor_cmd` is the right amount
  of structure. A table, a `Protocol`, or a decorator buys nothing until there is
  a reason to iterate over them, and there is not one.
- **Not touching `_check_wfctl_version`.** It already returns an exit code and is
  not part of the defect. It is also the one function PR B (#21 + #35 B1) rewrites
  end to end — converting its signature here means resolving the same conflict
  twice. It becomes `bool` as the last step of PR B, on code that PR has already
  rewritten.
- **The orphan scan skips `.claude/commands/`, `.bob/`, `.github/skills/`.** wfctl
  copies into those, but they are the user's directories. A hand-written slash
  command there would be reported as an orphan and, under this contract, fail the
  build. The `.agents/` copy of the same rename orphans identically, so the real
  case from #38 is still caught.
- **No removal for orphans, only reporting.** Removal is correct for a true rename
  and destructive if the file was edited, or if a layer was deselected rather than
  dropped upstream. Reporting is the safe default; a flag can come later if the
  reports go unactioned.
- **Not annotating each check's removal condition** (#36 items 1–2). Docstring
  work that changes no behaviour and gates nothing here. The one deletion it would
  have gated is already justified above.
- **Not the install-time halves of #35 and #38.** #35 A1–A3 are `install-config`
  and `install-skills` defaults; #38's install-time diff of `prior_items`
  (`cli.py:1040`) against the paths just written is where prevention lives. Only
  the reporting surface belongs here.

## Open Questions

- **Is `_check_spec_root_migration` transitional or permanent?** #41 lists it
  undecided. The case for permanent: anyone can run `wfctl spec-root` tomorrow on
  a repo with an existing `specs/` directory and strand it, so no release window
  makes deletion safe. Deferred — it changes a docstring, not behaviour, and the
  contract does not depend on the answer.
- **Does the orphan check need to run when the manifest is empty?** `doctor`
  returns early at `cli.py:1891` when no layers are recorded. A repo that
  uninstalled skills but kept files on disk would have orphans and no manifest to
  diff against. Likely out of scope — with nothing recorded, every file is
  unrecorded, and the report would be noise.
