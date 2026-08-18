# Phase 0 Research: doctor exit-code contract

No `NEEDS CLARIFICATION` markers survived into Technical Context — the language,
dependencies, test runner, and platform are all fixed by the existing repository.
What follows is the evidence gathered while designing this feature, recorded so
the next session does not re-derive it. Each item was verified against
`origin/master` at `271bb2c` on 2026-08-17.

## Decision: one `bool` outcome, with "could not determine" returning `False`

**Decision**: Every check returns `bool` meaning "found drift", OR'd into the exit
code. A check that cannot reach the network, or finds no recorded value to compare
against, returns `False` and says so in its output.

**Rationale**: Two sites already behave this way and argue for it in their own
comments. `_check_wfctl_version`'s offline branch returns 0, and the
no-recorded-hash warning states *"Unmeasurable, not stale... leave the exit code
alone."* Without the rule written down, "any drift fails" sweeps both in and fails
builds on a flaky network rather than a real problem. With it, `exit 1` means
*doctor found something wrong* and `exit 0` means *doctor found nothing wrong*,
where "could not look" counts as nothing found — the weaker of the two possible
guarantees and the honest one.

**Alternatives considered**:
- *Severity tiers* (`⚠` exits 0, `✗` exits 1) — preserves the defect the feature
  exists to fix, and declares "prints a warning and exits 0" to be correct.
- *Land the signature but leave existing checks returning `False`* — ships a
  contract three of five callers opt out of, which is the ambiguity being removed.
- *Could-not-determine exits 1* — strictest reading, and a build genuinely cannot
  distinguish a passing check from a skipped one otherwise. Rejected because it
  fails the build when GitHub is briefly unreachable, which is not a repository
  problem.

## Finding: the vendoring reintroduced the superseded command name

**Observed**: `wfctl/agents/configs/workmux/.workmux.yaml` shipped calling
`wfctl archive-story`, the pre-rename name. Confirmed end to end in a scratch
repository:

```
$ wfctl install-config workmux
✓ Seeded workmux config (1 file(s)) from wfctl 0.15.0
$ wfctl doctor
⚠ .workmux.yaml: pre_remove calls `wfctl archive-story`, renamed to
  `archive-specs`. The old name still works, so teardown is protected.
  Update the hook, or re-seed it with `wfctl install-config`.
```

The printed remedy re-seeds the same name — a loop with no exit. Under the new
contract it would also fail the build of every freshly configured repository.

**Why it was not caught**: every `install-config` test seeds a substitute bundle
and writes its own YAML, so no test ever read the shipped file.

**Consequence for #36**: issue #41 verified the removal condition for
`_check_stale_archive_hook` ("no `.workmux.yaml` names `archive-story`") against
`241b245`, before the vendoring imported the name. The condition was false again
by `271bb2c`. Fixing the template restores it, which is why the fix is item 1 of
the implementation order rather than a loose end.

## Finding: #31's stated obstacle no longer exists

**Recorded in the issue**: *"The assertion crosses a repository boundary. wfctl's
tests cannot see wf-skills' command files unless skills are installed in the
checkout, and CI installs nothing."* Three options were listed, and issue #41
chose a runtime `doctor` check on that basis.

**Now**: `#43` vendored the command files to `wfctl/agents/commands/*.md`, in the
same package as `_STEP_COMMAND` (`_pipeline.py:14-23`). A plain test asserts the
pairing offline, with nothing installed — strictly earlier than a runtime report.
Verified: all eight table entries resolve against the shipped set today.

**Alternatives reconsidered after the vendoring**:
- *Doctor check only* — catches a hand-mangled install, but only after someone
  installs and runs `doctor`, never in CI. The bundle `content_hash` check already
  covers an installed tree that drifted from the bundle, which was the only thing
  the runtime check added.
- *Both* — two mechanisms for one invariant, the runtime half largely duplicating
  `content_hash`.

## Decision: `difflib.get_close_matches` for the nearest-name suggestion

**Decision**: FR-012's nearest shipped name comes from `difflib.get_close_matches`.

**Rationale**: The standard library already does this in one call, so no matching
code is written or owned, and no dependency is added. It names the likely rename
directly, which is the #23 case that motivated the check: the table said one name
while the shipped command said another.

**Alternatives considered**: listing all ~23 shipped names (readable, but leaves
the reader to spot the rename); naming only the missing entry (minimal, leaves the
reader to list the directory).

## Finding: the install record stores directories, not only files

**Observed**: manifest `items` mix both. `.agents/commands/speckit.plan.md` is a
file; `.agents/skills/brainstorming` and `.specify/scripts/bash` are directories
installed and recorded as single paths.

**Consequence**: an upstream rename of a skill abandons a *directory*. Reporting
per-file would produce one finding per file inside it — dozens for one rename.
FR-008a fixes reporting at the granularity the record uses, matching how
`uninstall-skills` already removes them.

## Finding: the reference repository is currently clean under both new checks

Diffed every recorded parent directory against the manifest, and every
`_STEP_COMMAND` value against the shipped command set:

| Check | Result |
| --- | --- |
| Recorded parent dirs | `.agents/commands`, `.agents/skills`, `.specify/scripts`, `.specify/templates` |
| Abandoned entries found | none |
| `.claude/commands/` present | no |
| `_STEP_COMMAND` entries resolving | 8 of 8 |

So "quiet when they agree" (FR-011, SC-005) is demonstrable here, and the contract
flip introduces no new findings in this repository. The one known consuming
repository carries two worktrees predating the `.agent/` move, which is genuine
drift and expected to report.

## Decision: scan `.agents/` and `.specify/` only

**Decision**: The abandoned-entry report walks the parent directories of recorded
items, restricted to the tool's own installation trees.

**Rationale**: `.claude/commands/`, `.bob/`, and `.github/skills/` are the user's
own agent directories. wfctl copies into them, but a hand-written slash command
there would be reported as abandoned and, under FR-002, fail the build. The
`.agents/` copy of the same rename abandons identically, so the case from #38 is
still caught — the base layer installs `.agents/commands/speckit.brainstorm.md`,
so a stale `.agents/commands/brainstorm.md` is found there.

**Alternative considered**: scanning every recorded parent directory, which
reports the literal file #38's evidence names but produces false findings on
user-authored commands.

## Constraint: PR boundary against the version-check rewrite

`_check_wfctl_version` (`cli.py:1626`) must not be modified here. It is the one
function separate work (#21 + #35 B1) rewrites end to end, and converting its
signature means editing the exact lines that work replaces. It already returns an
exit code and is not part of the defect; it becomes `bool` as the last step of
that rewrite, on code already rewritten. Recorded as FR-013 so a contract sweep
does not reach it by tidiness.

## Note on line references

Every `cli.py` line number in issue #41 predates the vendoring and has shifted by
27 to 34 lines. Current positions: `_check_wfctl_version` :1626,
`_check_legacy_agent_dir` :1673, `_check_workmux_hook` :1714,
`_check_stale_archive_hook` :1783, `_check_spec_root_migration` :1819,
`doctor_cmd` :1867, the four call sites :1884-1887, the early return on an empty
manifest :1891, the manifest loop :1906-1934.
