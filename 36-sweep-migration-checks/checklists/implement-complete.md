Implementation complete: 2026-08-17

26 of 27 tasks done. T025 remains open by design — it posts the reclassification
comment to issue #36 once the PR is open, and no PR exists yet.

## Result

- 393 tests pass (394 baseline − 9 obsolete + 8 new), ruff clean, mypy clean.
- Source net −44 lines: `cli.py` +50/−86, `_workmux.py` +3/−17, `_archive.py`
  +7/−1 (comment only), bundled template +2/−2.
- Both bundle scripts pass against a built wheel, and a repo seeded from that
  wheel gets `archive-specs` in its teardown hook.

## Deviations from the plan, all recorded in tasks.md

1. **T019 landed in `tests/test_bundle.py`**, not `test_install_config.py`. Every
   test in that file seeds a *fake* bundle, so an assertion there would only
   check what the test itself wrote.
2. **T009 authored nothing.** Both surviving reports were already covered —
   `test_remaining_commands.py:142` and seven assertions in
   `test_install_skills.py:1199-1310`.
3. **T005 deleted without replacing.** Two conversions were written and then
   removed on finding `test_workmux.py` already covered both cases.
4. **`uv run mypy` was wrong** in every artifact — mypy is in the `dev` extra.
   Corrected to `uv run --extra dev mypy` across five files.
5. **Both notices were reworded during T023.** SC-005 failed its own check: the
   original text told the reader the path was "scheduled for removal" but not
   that the *silence* is the removal signal, which left the trigger readable
   only in the source comment. Each notice now ends "retired once this line
   stops appearing", and both tests assert that string.

## Verified against the real world, not only fixtures

`~/Development/pfms/wt/440-editable-table-row` — the last unswept worktree on
this machine — exercised the mixed case: durable spec dir plus legacy rescue,
under the retired command name. All three messages appeared, none suppressed
another, exit code 0, and the source file survived at 5429 bytes with its copy
in the archive.

That run wrote a real archive to
`~/.local/state/wfctl/pfms/440-editable-table-row/archive`.

## Follow-up

The two retained compatibility paths are still in place, now with an observable
end condition. Delete `wfctl/_archive.py`'s legacy read, the `archive-story`
alias in `wfctl/cli.py`, and both notices together once neither line has
appeared during a teardown on any machine.
