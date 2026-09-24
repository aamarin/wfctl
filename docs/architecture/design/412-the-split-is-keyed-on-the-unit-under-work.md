---
status: proposed
---

# The references split on the unit of code under work, not on the source's chapters

## Context

`clean-code` is a router plus references loaded on demand, so an agent pays for
naming guidance when it is naming something. That only holds if the router can
address a topic. Two of the draft's seven references bundle unrelated topics
behind one entry, and the router's own line shows it: *"For objects and data,
errors, external dependencies, tests, classes or modules, system assembly, and
simple design, read `references/design-boundaries-tests.md`"* — seven subjects,
one destination. Ask that skill about a class and the agent also loads error
models and test design, which is the opposite of what the structure is for.

The split has to be keyed on something. `level-3-owns-structural-heuristics`
routes four of these references at level 3 and three at level 4, so the key also
decides whether that routing table can be written at all.

## Verified

The first three bullets describe the pre-split draft, which was never committed —
it existed only in the working tree this change replaced. They are the baseline
the split is measured against and nothing else in the repository carries it, so
they stand as testimony rather than as something a later reader can re-run.

- `references/design-boundaries-tests.md` was 157 lines carrying eight `##`
  sections: Objects/Data/Responsibility, Errors and Absence, External and
  Uncertain Boundaries, Tests as Design and Safety Net, Classes/Modules/Change,
  System Assembly, A Simple-Design Check, Design Review Prompts.
- `references/functions-comments-formatting.md` was 94 lines carrying four:
  Functions and Procedures, Comments, Formatting and Locality, Local Review
  Prompts.
- `references/source-map.md`'s "Distilled location" column named the seven draft
  filenames, four of its rows pointing at
  `references/design-boundaries-tests.md` and three at
  `references/functions-comments-formatting.md`.
- `wfctl/agents/skills/speckit-delivery-plan/references/` holds three files and
  `wfctl/agents/skills/using-superpowers/references/` holds three — a
  `references/` subdirectory is already a shipped shape, not a new one.
- `MANIFEST.in` reads `graft wfctl/agents`, and its own comment says `graft`
  "walks with `os.walk` and filters nothing" — so a new subdirectory ships
  without a packaging change.
- `install_skills_cmd`'s copy loop in `wfctl/cli.py` reaches each item with
  `shutil.copytree(item, dest, dirs_exist_ok=True)` — so `install-skills` copies
  a skill's subdirectories rather than its top level. Cited by name rather than
  by line: this change moved that call twelve lines, and the next one will move
  it again.
- `tests/test_skill_cross_references.py:22` —
  `_REFERENCE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)")` — the check
  sees a skill name and nothing below it, so no test reads a `references/` path.

## Assumed

- That an agent at the moment it needs guidance knows which *unit* it is working
  on — an identifier, a function, a module, an error path, a test. Falsified if
  routing an actual task through the finished router reaches for a reference the
  router did not name; #412's definition of done exercises exactly that, with a
  function in `wfctl/cli.py`.
- That eleven references is not itself a cost worth avoiding. Falsified if the
  router's routing table grows past what an agent reads before choosing —
  measured by the table, not the file count.

## Direct baseline

Carry the seven draft files across unchanged and write the router's table
against them. Two entries name several subjects each; the agent loads a file and
skips most of it.

## Decision

Eleven references, each named for the unit of code the agent is holding when it
needs them. `design-boundaries-tests.md` becomes `classes-and-modules.md`,
`errors.md`, `boundaries.md` and `tests.md`; `functions-comments-formatting.md`
becomes `functions.md` and `comments-and-formatting.md`. `naming.md`,
`concurrency.md`, `refactoring-workflow.md`, `review-catalog.md` and
`source-map.md` carry across as they are.

`source-map.md` is rewritten rather than carried: its "Distilled location"
column is the one thing in the tree whose whole job is telling a later reader
which chapter landed where, and left alone it names four files that no longer
exist. The book's chapters keep their view — in that file, where a maintainer
checking coverage looks — and they are not the key the router uses.

## Diagram

```
          baseline                          decision

stable   ┌──────────┐                     ┌──────────┐
         │ SKILL.md │                     │ SKILL.md │
         │  router  │                     │  router  │
         └──────────┘                     └──────────┘
            │    │                     ┌───┬──┴─┬───┬───┐
            │    │                     │   │    │   │   │
═══ loaded on demand ═════════════════════════════════════════
            │    │                     │   │    │   │   │
volatile    ▼    ▼ reads               ▼   ▼    ▼   ▼   ▼ reads
   ┌──────────────┐ ┌────────┐    ┌───────┐ ┌──────┐ ┌──────┐ …
   │ design-      │ │functions-│  │classes│ │errors│ │tests │
   │ boundaries-  │ │comments- │  │-and-  │ └──────┘ └──────┘
   │ tests   157L │ │formatting│  │modules│ ┌──────────┐
   └──────────────┘ └────────┘    └───────┘ │boundaries│
    objects·errors   functions·               └──────────┘
    ·boundaries·     comments·
    tests·classes·   formatting
    assembly·simple
```

The divider is the boundary already in force in every skill that has a
`references/` directory: the router is always loaded, a reference is loaded
because the router named it. The two graphs differ by how many arrows cross it
for one question. In the baseline, asking about a class crosses once and brings
back seven subjects; in the decision it crosses once and brings back one. The
file count is not the argument — the ratio of what is read to what was asked is.

## Considered

- **Leave the two files whole; 157 lines is not large.** True and beside the
  point. The cost is not the file's size, it is that a router cannot address a
  topic inside a file, so the routing table
  `level-3-owns-structural-heuristics` requires — four references at level 3,
  three at level 4 — cannot be written at all. `design-boundaries-tests.md`
  would have to be named at both levels and its level-4 half read at level 3.
- **One file per chapter of the source.** This is the traceability view and it
  is genuinely useful — it is what a maintainer checking coverage wants.
  Rejected as the *router's* key rather than as a view: the agent knows it is
  naming a variable; it does not know that is chapter 2. It keeps its home in
  `source-map.md`, which is why that file is rewritten rather than dropped.
- **Split further — a file per `##` section, nineteen of them.** Symmetrical
  with the decision and worse: `errors.md` and `tests.md` are each one coherent
  unit an agent holds, while "Design Review Prompts" is not a unit anyone works
  on. Splitting past the unit produces files the router has no honest trigger
  for.
- **Fold `review-catalog.md` into the per-unit files.** Rejected: the catalog is
  ordered by consequence, across units, and that ordering is what `code-review`
  reads it for. Distributing it destroys the one property it has.

## Consequences

Eleven reference files ship where there were seven, and none of them is seen by
`test_skill_cross_references.py` — its regex captures a skill name and stops.
That is #218's exact shape, at twice the count, so the tree is verified by
listing `.agents/skills/clean-code/references/` after `install-skills` rather
than by a green suite. #218 remains the issue that would make this checkable;
this change does not close it.

`source-map.md` becomes the only file that must be edited whenever a reference
is renamed, because it is the only one holding the chapter-to-file mapping. That
is the cost of keeping the traceability view separate from the routing key, and
it is paid in one place rather than in the router.

## Verification

- Follow the finished router from a real task — a function in `wfctl/cli.py` —
  to a reference, and check that the reference it names is the one the task
  needed. Reaching for one the router did not name falsifies the first
  assumption above.
- `ls .agents/skills/clean-code/references/` after `uv run wfctl install-skills`
  returns the eleven files this split produced, plus any reference added since —
  twelve after #463's `after-implementation.md`. What falsifies the split is a
  missing one of the eleven, not a higher count.
- Every row of the rewritten `source-map.md` names a file that exists.

## Log

- 2026-09-17  proposed  — #412, written while the split was being chosen. The
  deciding evidence is the router's own single-entry line naming seven subjects,
  not the 157-line count the issue leads with.
- 2026-09-24  amended   — the Verification count made re-runnable after #463
  added a twelfth reference. The "eleven" elsewhere in this record describes
  what the split produced and stays as written.
