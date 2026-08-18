# Phase 0 Research: Sweep the one-time migration checks

Three unknowns blocked the design. All three were resolved by measurement rather
than by reasoning from documentation, and the evidence is recorded here because
two of them contradicted the assumption the issue was filed under.

## R-001: Can a command tell which of its two registered names invoked it?

**Decision**: Yes — `typer.Context.info_name` carries the invoked name. Add
`ctx: typer.Context` as the first parameter of the archive command and read it.

**Rationale**: Verified directly against the installed typer version rather than
assumed, since the command carries two stacked `@app.command` decorators and the
behavior under that form is not obvious. A probe registering one function under
both names and printing `ctx.info_name`:

```
archive-specs: exit=0 out="info_name='archive-specs' worktree='/tmp/wt'"
archive-story: exit=0 out="info_name='archive-story' worktree='/tmp/wt'"
```

Argument parsing is unaffected — the positional argument still binds correctly
under both names.

**Alternatives considered**:
- `sys.argv[1]`: works, but breaks under `CliRunner`, which is how the archive
  command's existing tests drive it.
- A separate wrapper function for the retired name: duplicates the body or adds
  an indirection, and the two names would drift.
- Not reporting the invocation at all, relying on the health check to detect the
  stale hook instead: rejected because that health check is the one being deleted
  (FR-003), and it only reports repositories the developer happens to run it in.

## R-002: Is the stranded-spec-directory condition still reachable?

**Decision**: Yes. The report is recurring drift and is retained (FR-002). It is
removed from the sweep.

**Rationale**: The condition requires a recorded external spec root plus in-repo
spec directories. Both are still produced today: `install-skills` prompts every
new project for its spec location (`cli.py:868-891`, `_spec_root_question_answered`
and the three-option panel), and `wfctl spec-root` can switch an existing project
at any time. A project that accumulated `specs/` under the in-repo default and
later adopts an external root lands in exactly this state.

This is not hypothetical. It was the live state of the `pfms` project during this
session: 51 in-repo spec directories against a recorded external root. The report
is what surfaced it, and acting on it is what made the duplicates safe to delete —
after confirming they were byte-identical to, and committed on, the external
root's `specs-trunk` branch.

**Alternatives considered**:
- Deleting it with the rest: rejected. It fails the test that governs the whole
  sweep — "nothing can create this condition any more" — and a future spec-root
  adoption would strand directories silently.
- Narrowing it to fire only on probable duplicates: rejected as more logic to
  maintain, and it would have stayed silent on the `pfms` case until the two
  copies diverged, which is precisely when the warning is least useful.

## R-003: Does anything still create the superseded artifact directory?

**Decision**: No. `_check_legacy_agent_dir` is genuinely transitional and is
deleted (FR-001).

**Rationale**: The singular `.agent` path appears in exactly two places in the
package — the rescue read at `_archive.py:189` and the health check reporting it
at `cli.py:1673-1710`. No code writes it, and the skills that once did are
vendored at their current versions (#43/#47), so a reinstall cannot reintroduce
one. Every other match in the source is the plural `.agents/` directory, which is
the current, unrelated layout.

The same test applied to `_check_stale_archive_hook`: once the bundled template
stops seeding the retired name (FR-013), nothing creates that condition either,
and existing hooks are covered by the archive command's own report (FR-010). Both
therefore pass the deletion test that FR-002's subject failed.

**Alternatives considered**:
- Retaining the health check as a convenience detector for other machines:
  rejected. It only fires where the developer happens to run the health check,
  whereas the rescue path fires wherever the directory actually matters — during
  the teardown that would otherwise destroy it.

## Resulting scope change

Issue #36 lists five checks and proposes deleting all five in one pass. Measured
against "can anything still create this condition, and what breaks if it is
gone", three of the five turn out to be load-bearing:

| Check | Verdict | Evidence |
|---|---|---|
| `_check_legacy_agent_dir` | Delete | R-003 — no writer remains |
| `_check_stale_archive_hook` | Delete | R-003 — no seeder remains after FR-013 |
| `_check_workmux_hook` | Keep | Reports ongoing drift; a hook can be lost at any time |
| `_check_spec_root_migration` | Keep | R-002 — condition reachable by any new adoption |
| Legacy `.agent/` read (`_archive.py`) | Keep, with an end condition | Deleting it destroys a rescued file |
| Retired command alias (`cli.py`) | Keep, with an end condition | Deleting it produces a silently empty archive |
