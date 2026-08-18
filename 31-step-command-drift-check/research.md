# Research: step-command drift check

**Date**: 2026-08-17
**Phase**: 0 — resolve unknowns before design

## R1: Can a similarity heuristic attribute the drift?

`design.md` left one item unvalidated: whether `difflib.get_close_matches` at its
default cutoff separates "the command was renamed" from "the table entry is
wrong". FR-004 was written assuming it does.

**Decision**: No. Drop the heuristic; print both sides instead.

**Rationale**: Measured against five drift cases, three renames and two wrong
entries. Every command shares the `speckit.` prefix — 8 of ~15 characters — so
the ratio is dominated by the part that never varies.

At the default cutoff of 0.6, on raw names:

| Case | Table names | Reality | Suggested | Correct? |
| --- | --- | --- | --- | --- |
| Rename, prefix added (the #23 case) | `speckit.brainstorm` | `brainstorm` | `brainstorm` | yes |
| Rename, truncated | `speckit.decompose` | `speckit.decomp` | `speckit.decomp` | yes |
| Rename, prefix dropped | `speckit.plan` | `plan` | `speckit.implement` | **no** |
| Wrong entry | `speckit.deploy` | (nothing) | `speckit.plan` | **no** |
| Wrong entry | `speckit.review` | (nothing) | `speckit.brief` | **no** |

Two of the three failures are false attributions on cases where nothing was
renamed at all — the check would confidently name an innocent file. Raising the
cutoff does not fix it: at 0.75 through 0.85 the prefix-add and prefix-drop
renames fall out first, and those are precisely the #23 shape this feature
exists to catch.

Comparing on the stem after the last dot, at cutoff 0.8, does get all five right.
It was rejected anyway: the 0.8 is fitted to five cases invented for this
document, and a check whose purpose is catching silent drift should not carry a
tuned constant that can silently stop fitting. The failure mode of a bad guess is
worse than no guess — a named innocent file sends the reader to the wrong fix.

**Alternatives considered**:

- *Default cutoff, raw names* — what FR-004 assumed. Wrong on 3 of 5 cases.
- *Higher cutoff, raw names* — wrong on 3 of 5 at 0.8; loses the renames first.
- *Stem-normalized, cutoff 0.8* — correct on all 5, but the constant is fitted to
  those 5. Recorded here so a future reader knows it was measured, not overlooked.
- *Print both sides* — chosen. The missing entries, then the sorted list of
  shipped commands. No constant to tune and no false attribution: the reader sees
  `speckit.plan` missing with `plan` sitting in the list two lines below. 23 names
  is a readable block.

**Consequence**: FR-004 is amended — the report distinguishes the two causes by
showing both sides, not by nominating a candidate. SC-003 ("a reader can tell
which side moved without opening either file") is unchanged and still met.

## R2: How does the check reach the shipped commands?

**Decision**: `Path(wfctl.__file__).parent / "agents" / "commands"`.

**Rationale**: The obvious route, `_bundle.BUNDLE_ROOT`, does not work under the
suite. `tests/conftest.py` installs an **autouse** fixture repointing that
constant at a temporary tree holding one fake command, so a check reading it
reports all eight commands missing. Verified by probe: reading `BUNDLE_ROOT`
under the fixture yields `{"test-cmd"}`; reading the package path yields the real
23 commands with zero missing.

The fixture's own docstring argues tests should not read the real tree, because
they would pass "for the wrong reason". This check is the deliberate exception —
reading the real tree *is* its purpose — so the code says so at the point of use.

**Alternatives considered**:

- *`_bundle.BUNDLE_ROOT`* — defeated by the autouse fixture, as above.
- *`importlib.resources.files("wfctl")`* — how `_bundle` computes the path, and
  also immune to the monkeypatch since the fixture replaces the module attribute
  rather than the function. Equivalent; `__file__` was chosen as the shorter of
  two equal options.
- *Opting out of the fixture* — possible, but it would make the check depend on
  fixture-override ordering rather than on a path it names itself.

## R3: Does the merged step table change any observable behaviour?

**Decision**: No, and that is the acceptance bar.

**Rationale**: The three tables are read from seven lines, all in
`_pipeline.py` — two loops over the step-name list, and two `.get()` calls in
`next_step_content`. No test and no other module references them. Merging them
into one `dict[str, tuple[str, bool]]` with the name list derived via `list(...)`
preserves insertion order (guaranteed since Python 3.7; the CI matrix is 3.11 and
3.13) and preserves the `("", False)` fallback for an unknown step.

That fallback matters: `cli.py:170` treats an empty command as "pipeline
finished" and prints "story complete". The merge must keep an *absent* step
returning empty rather than raising, or a genuinely complete pipeline becomes an
error. Pinned by an acceptance scenario rather than left to review.

**Alternatives considered**:

- *`NamedTuple` per step* — self-documenting field access, at the cost of a
  construct and a name for two values read in one place. The tuple plus a header
  comment carries the same information at eight definition sites.
- *`dataclass` per step* — same trade, heavier.
- *Keep three tables, assert they agree* — the answer this supersedes. Detects
  what the merge makes impossible.
