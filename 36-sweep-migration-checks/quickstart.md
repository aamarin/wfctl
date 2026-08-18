# Quickstart: Sweep the one-time migration checks

How to build, verify, and hand-check this feature.

## Validate

```bash
uv run pytest -q          # full suite
uv run ruff check .       # E4, E7, E9, F
uv run mypy               # disallow_untyped_defs over wfctl/
```

The bundled-template edit additionally rides the wheel checks that CI runs:

```bash
.github/scripts/check_wheel_contents.py     # template ships in the wheel
.github/scripts/check_installed_tree.py     # template lands on install
```

Run these before assuming the template edit is free — they arrived with the
vendoring change and assert on the bundle's contents.

## Verify the deletions by hand

Both removed reports should be unreachable, not merely quiet:

```bash
grep -rn "_check_legacy_agent_dir\|_check_stale_archive_hook" wfctl/ tests/
grep -rn "pre_remove_uses_former_name" wfctl/ tests/
```

All three should return nothing. `ruff` will not catch an orphaned module-level
function, so this grep is the check.

Confirm the retained reports still exist and still fire:

```bash
grep -n "_check_workmux_hook\|_check_spec_root_migration" wfctl/cli.py
```

## Verify the two new notices

### Retired-name notice

```bash
uv run wfctl archive-story /path/to/some/worktree handle    # expect the notice
uv run wfctl archive-specs /path/to/some/worktree handle    # expect silence
```

### Legacy rescue notice

Construct a worktree holding a superseded directory:

```bash
mkdir -p /tmp/probe-wt/.agent
echo "# design" > /tmp/probe-wt/.agent/spec.md
git -C /tmp/probe-wt init -q 2>/dev/null || true
uv run wfctl archive-specs /tmp/probe-wt probe
```

Expect one rescue line naming a count of 1, and the rescued file present under
`extra/legacy-agent-spec.md` in the archive. Then remove the directory and re-run:
expect no rescue line.

A live instance exists on this machine at
`~/Development/pfms/wt/440-editable-table-row/.agent/spec.md` — a single file. It
is the last unswept worktree here, so it is worth exercising the notice against
it before migrating it.

## Verify the template correction

```bash
grep -n "archive-story" wfctl/agents/configs/workmux/.workmux.yaml
```

Expect nothing. Both the hook line and its explanatory comment must name
`archive-specs`; a corrected hook beside a stale comment is a contradiction.

Then confirm a fresh seed is clean:

```bash
cd "$(mktemp -d)" && git init -q .
uv run wfctl install-config
grep -c "archive-story" .workmux.yaml     # expect 0
```

## Verify the health check end to end

```bash
uv run wfctl doctor
```

In this repository, expect no mention of `.agent/` and no mention of
`archive-story`. The teardown-hook and spec-root reports must still appear
whenever their conditions hold.

## The follow-up trigger

This change does not remove the two retained compatibility paths. It makes their
removal decidable. The condition is:

> Neither notice has appeared during a teardown on any machine.

When that holds, delete the legacy read in `wfctl/_archive.py` and the retired
alias in `wfctl/cli.py` together. Both carry a `ponytail:` comment stating this
condition in terms of the output above.
