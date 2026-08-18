# Review: 36-sweep-migration-checks (working tree vs HEAD)

Reviewed by a fresh-context agent given only the diff, the spec, and the project
rules — no session history. Two findings, both fixed.

```
BLOCKER  wfctl/cli.py:435 — rescue count inferred from destination prefix, which
                            unmapped spec files also match → count it in `_plan`,
                            where the rescue actually happens
WARNING  wfctl/cli.py:362 — retired command name hardcoded twice in one file
                            → module constant used by decorator and check
```

net: −1 line (the fix removed the `sum(...)` comprehension)
Verdict: **Approve** after fixes — both applied and verified.

## BLOCKER — false rescue notice (fixed)

`cli.py` counted rescues with
`sum(1 for dst, _ in mapped if dst.startswith("extra/legacy-agent"))`. Unmapped
spec-dir files land under `extra/` too (`_archive.py:247`,
`f"extra/{src.relative_to(spec_dir)}"`), so an ordinary spec artifact named
`legacy-agent-notes.md` produced destination `extra/legacy-agent-notes.md` and
was counted as a rescued file.

**Impact.** A repository with no `.agent/` directory at all reported
`⚠ rescued 1 file(s) from legacy '.agent/'`. That violates FR-008 and the CLI
contract's suppression guarantee, but the real damage is to SC-004/SC-005: the
notice is the *end condition* for the retained shims, and a repo holding such a
file could never go silent. A fully migrated machine would report needing the
shim forever — defeating the one thing this feature exists to deliver.

**Reproduced** before fixing, with `test_an_unmapped_spec_file_is_not_miscounted_as_a_rescue`
in `tests/test_archive_specs.py`. It failed on the old code and passes now.

**Fix.** The count moved to its source of truth. `_plan` now returns
`(plan, rescued)` and increments as it appends each legacy file; `archive`
returns `(archive_dir, mapped, rescued)`; `cli.py` prints what it is handed.
Only one caller existed, so the signature change was contained. The destination
string is no longer load-bearing for anything but naming.

An anchored prefix match (`dst == f"{p}-spec.md" or dst.startswith(f"{p}/")`)
was rejected: it narrows the collision without closing it — a spec dir
containing a `legacy-agent/` subdirectory still miscounts.

## WARNING — duplicated command literal (fixed)

`"archive-story"` appeared as a bare literal in both the `@app.command` decorator
and the `ctx.info_name` check ~60 lines apart. Renaming the alias at one site
would leave it dispatching without its notice, and nothing — not ruff, not the
tests — would catch it.

**Fix.** `_FORMER_ARCHIVE_COMMAND`, used by both.

The reviewer suggested importing `_workmux._FORMER_COMMAND` instead. Declined:
that constant describes what *users' existing `.workmux.yaml` files say*, which
stays true regardless of what this CLI accepts. The two coincide today but are
different facts, and coupling them would make a future divergence impossible to
express.

## Passes with no findings

- **Correctness beyond the blocker** — deletions left nothing dangling; the
  retired-name notice precedes every early `return`; exit-code contract intact;
  `ctx.info_name` verified correct for both invocation forms via `CliRunner` and
  the installed console script.
- **Security** — both new notices print static text plus an integer. No
  untrusted data reaches them, unlike the `escape()`-guarded path messages
  elsewhere in the file.
- **Architecture** — `_archive.py` owns data, `cli.py` owns console; no cycle.
  The blocker fix strengthened this: `cli.py` no longer reverse-engineers
  data-layer semantics from a naming convention.
- **Performance** — the count is now accumulated during a walk that already
  happens, so the separate O(n) pass is gone.
- **Over-engineering** — nothing to cut. `LEGACY_DEST_PREFIX` survives as the
  single spelling of the destination name, which is still worth having.

## Verification after fixes

`uv run pytest -q` → 394 passed. `uv run ruff check .` → clean.
`uv run --extra dev mypy` → clean. Live re-run against the synthetic legacy
worktree confirms both notices unchanged in wording and behaviour.
