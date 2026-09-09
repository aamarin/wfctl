# Research: one predicate signature

Phase 0. Two questions the plan rests on, both answerable by reading the code
rather than by trying it. No `NEEDS CLARIFICATION` reached this phase — the
Technical Context is a repo this feature lives inside, not a stack being chosen.

## Q1 — Do six evidence values cover all eight predicates?

**Decision**: Yes. `Evidence` carries `spec_dir`, `repo_root`, `spec_text`,
`has_markers`, `tasks_text`, `tasks_open`, and nothing else.

**Rationale**: Read off the eight arms of `_infer_steps`
(`wfctl/_pipeline.py:474-589`). Every value they read is already computed at
`:443-461`, before the loop begins:

| Step | Reads |
|---|---|
| brainstorm | `spec_dir`, `repo_root` |
| specify | `spec_dir` (for `spec.md`), `has_markers` |
| clarify | `spec_text`, `has_markers`, `spec_dir` (for `plan.md`) |
| plan | `spec_dir` |
| tasks | `tasks_text` |
| analyze | `spec_dir` |
| decompose | `spec_dir`, `repo_root`, `tasks_text`, `tasks_open` |
| implement | `tasks_text`, `spec_dir`, `repo_root` |

`spec_md` and `tasks_md` are paths derived from `spec_dir`, not separate reads.
The four steps that only test for a file's presence need `spec_dir` alone.

**Alternatives considered**: Passing each predicate only what it reads, which
is what the code does today and is why no two share a shape. Rejected — that is
the problem, not a design. A per-step argument list cannot be dispatched from a
table.

## Q2 — Can `decompose` route through `blocks` without changing its verdict?

**Decision**: Yes, with `source="ambient"`, and the `tasks_open` test stays
outside `blocks`.

**Rationale**: `_unkeyed_issues` (`:262`) returns `int | None`. Mapping its
three outcomes onto `Verdict`:

```
_unkeyed_issues → verdict          blocks(verdict, "ambient")   today
─────────────────────────────────────────────────────────────────────
None  (no map, or map with     →   inconclusive → False         proceeds
       no rows; or no tracker
       configured at all)
0     (every row keyed)        →   satisfied    → False         proceeds
n > 0 (n rows unkeyed)         →   unsatisfied  → True          reason set
```

Today's `if unkeyed:` treats `None` and `0` alike — both fall through to `done`
— which is `blocks` returning `False` for both, by two different routes. The
docstring at `:271-273` states the inconclusive policy in its own words: "None
means there is nothing here to judge… A delivery plan predating the table is not
evidence that issues are missing, so it goes on reading `done`."

`ambient` is the honest source, not a convenience. `_PROMISED` is
`{repo-declared, accepted-record, human}` — somebody undertook to produce it.
Neither inconclusive case has such an owner: a delivery plan written before the
Issue Grouping Map existed never promised one, and a repo that declared
`"tracker": null` promised no keys and can never gain any. Reading either as a
missing answer would strand the pipeline with no action that unblocks it, which
is the exact case `promised-evidence-blocks-on-silence` sends to `ambient`.

**The `tasks_open` test is a separate question and stays where it is.** Today
the reason is recorded whenever a row is unkeyed, and only *stands in the way*
while work is open (`:568-581`). `blocks` answers "is this a finding"; the
`tasks_open` test answers "does the finding stop the step". Folding the second
into `blocks` would change behaviour and is out of scope.

**Alternatives considered**: `source="repo-declared"`, on the reading that the
tracker config is a repo declaration. Rejected on consequence and on meaning:
`repo-declared` is in `_PROMISED`, so inconclusive would block, and a repo with
no tracker would sit at `decompose` for the life of the repo — the outcome
`:557-560` was written to prevent. It also misreads what was declared: the repo
declared a tracker's *absence*, which is the opposite of undertaking to produce
keys.

## Consequence for the plan

Both assumptions in `spec.md` are now checked rather than assumed, so the
implementation carries no open research. The two remaining open items — where
`implement`'s task tally is composed, and which module holds the step table —
are decided by whichever result is shorter and by import order respectively.
Neither changes observable behaviour, so both are settled in code review rather
than here.
