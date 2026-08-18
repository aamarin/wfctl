# Sweep the one-time migration checks

## Problem Statement

How might we retire five transitional checks in `doctor` and `archive-specs`
without deleting the two that are still preventing data loss?

## Recommended Direction

Issue #36 treats the five as one class and proposes deleting them in a single
pass, on the reasoning that reviewing them together makes it obvious none is
load-bearing. Reviewing them together shows the opposite. Their failure modes
differ, and the difference is the whole design.

Three are pure reports. Deleting one produces silence — the reader stops being
told about drift that was already inert. Two sit on the rescue path, where
deleting one destroys a file (`.agent/spec.md` on a worktree torn down after the
move) or produces a silently empty archive (a `pre_remove` still naming
`archive-story`, whose `|| true` swallows the unknown-command exit). A sixth
entry, `_check_workmux_hook`, is on #36's list but is not transitional at all:
it is the only path by which an already-seeded repo becomes protected, and it
stays.

So the sweep splits. The reports go now. The two rescue-path shims stay and gain
the thing #36 was actually filed about — an observable end condition. Each prints
one line when it fires, which happens only on a machine that still predates the
move. When neither line has appeared anywhere, they are deletable on evidence
rather than on a comment that nothing reads. This costs two print statements and
no new state, flag, or command.

One prerequisite came free: since `wf-skills` was vendored into the wheel
(#43/#47), the `.workmux.yaml` template that still seeds `archive-story` lives at
`wfctl/agents/configs/workmux/.workmux.yaml` in this repo. Before that merge the
alias regenerated itself from another repo and its removal condition was
unreachable. It is now a one-line fix in the same PR.

## Key Assumptions to Validate

- [ ] **Legacy output is noticed when it fires.** Both new lines print from a
      `pre_remove` hook during teardown. Test by tearing down
      `pfms/wt/440-editable-table-row` and confirming the rescue line appears.
- [ ] **`ctx.info_name` reports the invoked alias under Typer's two-decorator
      form.** The alias line depends on it. Test directly: invoke both
      `archive-specs` and `archive-story` and assert only the latter warns.
- [ ] **The vendored template is asserted on by CI.** `check_wheel_contents.py`
      and `check_installed_tree.py` arrived with the vendoring merge. Run CI on
      the template change before assuming it is a free edit.
- [ ] **No machine holds an unswept worktree beyond the known one.** Verified on
      this machine (`pfms/wt/440-editable-table-row`). Not verifiable from here
      for other checkouts — which is why the shims stay.

## MVP Scope

**In — one PR:**

| Action | Site |
|---|---|
| Delete `_check_legacy_agent_dir` | `cli.py:1673` + call `:1887` |
| Delete `_check_spec_root_migration` | `cli.py:1819` + call `:1886` |
| Delete `_check_stale_archive_hook` | `cli.py:1783` + call `:1885` |
| Delete `pre_remove_uses_former_name` | `_workmux.py:159` — sole caller was the check above |
| Retarget the bundled hook | `wfctl/agents/configs/workmux/.workmux.yaml:55,65` → `archive-specs` |
| Announce the legacy rescue | `cli.py`, from `mapped`'s `extra/legacy-agent*` entries |
| Announce the alias invocation | `cli.py:299` — add `ctx: typer.Context`, read `ctx.info_name` |

The rescue line prints from `cli.py`, not `_archive.py`: `mapped` already carries
the destinations, and `_archive.py` returns data and owns no console.

**Tests:** drop the deleted checks' assertions (`test_workmux.py:225-249`, the
doctor cases in `test_remaining_commands.py`); add two — alias invocation warns, legacy
rescue reports its count. `test_archive_specs.py`'s legacy coverage stays; that
path is unchanged.

**Machine migration**, outside the PR: move
`pfms/wt/440-editable-table-row/.agent/spec.md` into its spec dir, and delete
`pfms/specs/` — 51 directories, byte-identical to `pfms-specs` and committed
there, with nothing unique.

**Out — the follow-up PR.** Delete the legacy `.agent/` read (`_archive.py:188`)
and the `archive-story` alias (`cli.py:299`) once neither announcement has
appeared on any machine.

## Not Doing (and Why)

- **Deleting all five at once** — two are on the rescue path. Their failure mode
  is a destroyed file, not a missing warning.
- **Removing `_check_workmux_hook`** — listed in #36, but it reports ongoing
  drift, not a transition. A repo can lose its hook at any time.
- **A self-clearing gate in `doctor`** (recorded "migration complete" flag, a
  `--migrations` mode) — permanent machinery for a temporary problem, and the
  announcements observe the same condition for two lines.
- **A deprecation window for third parties** — the install base is one person on
  several machines, and wfctl is not on PyPI (#2 open). The gate is "every one of
  my machines", not a release count.
- **Touching `doctor`'s exit code** — that is #41. This sweep shrinks the check
  set #41 reasons about and should land first, but changes no exit behavior.

## Open Questions

- Sweep the other machines before or after this PR merges? Before keeps `doctor`
  as the detector; after means finding stale `.agent/` dirs with `find` instead.
  Does not change the design.
- What closes the loop on the follow-up PR — a dated reminder, or simply the next
  time an announcement fails to appear during a teardown?
