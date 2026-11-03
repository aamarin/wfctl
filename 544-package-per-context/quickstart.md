# Quickstart: checking the import check

Run it on the real tree. It passes with the shipped baseline:

```bash
uv run python .github/scripts/check_imports.py
uv run pytest -q tests/test_import_check.py
```

See it refuse a new import against the map. Add `from wfctl._session import
record_blocked` to the top of `wfctl/_verify.py`, then run the check. It fails
with the boundary drawn, naming Evidence and derivation and Session continuity.
Revert the line.

See it refuse a stale baseline line. Remove the import of `_spec_copy` from
`wfctl/_spec_store.py`, run the check, and confirm it names the
`_spec_store.py -> _spec_copy.py` line to delete. Revert.

See it refuse an unapproved addition. This needs the script on `main`, so it
runs on the first branch after this one merges. Add a placement line to the
baseline, commit it, and run the check with `--approvals --base origin/main`.
It fails and names `wfctl arch approve-imports`. Run that command from an
agent's shell and confirm the guard refuses it. Run it in your own terminal
and confirm the check passes. Then drop the commit.

The whole definition of done:

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy
uv run wfctl verify
uv run wfctl check config
uv run wfctl doctor
```
