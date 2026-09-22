---
status: proposed
---

# The placement check reads the two record tiers by name, and never asks the record loader what a record is

## Context

`doctor-owns-the-placement-verdict` decides that `doctor` reports a record filed
at the wrong level, and that the verdict turns on which of two headings the file
carries. It does not say how the check reaches the files or how it recognises a
heading, and both have a wrong answer already present in the tree.

The pressure is that every existing reader of the arch root was built around
`load_records`, which is the function whose one-level glob *is* the bug. A check
written from that habit inherits the blind spot it was called to remove. The
second pressure is that the two heading names would now be written in wfctl's
code as well as in the two templates wfctl ships, and nothing would hold the two
copies together.

Constrained by `required-sections-are-wfctls` (accepted), which already decided
how wfctl pins a section list it does not author, and by the `#113` boundary
that `_check_arch_records` states: wfctl reads the arch root and never writes it.

## Verified

- `_arch.py:150` — `load_records` returns
  `[parse_record(p) for p in sorted(root.glob("*.md"), ...)]`. One level, root
  only; `design/` is unreachable through it.
- `_arch.py:25` — `STATUSES = frozenset({"proposed", IN_FORCE, "superseded",
  "rejected", "retired"})`, and `parse_record` sets `status` to `""` for
  anything outside it.
- `software-design-decisions/design-record-template.md:17` — a level-3 record's
  status runs `proposed -> approved -> superseded | rejected`. `approved` is not
  in `STATUSES`, so every approved design record parses to `status=""`.
- `_paths.py:306` — `non_record_subtrees(arch)` returns
  `[arch / "scans", arch / "implementation"]`. `design/` is not in it, and is
  excluded separately by `_predicates.py:599`.
- `_predicates.py:284` — `_missing_sections(text, required)` matches
  `^##[ \t]+<name>(?!\w)` under MULTILINE, and its docstring records why the
  lookahead is `(?!\w)` and not `\b`.
- `_predicates.py:322` at the time this was written — `_quoted_out(text)` blanks
  fenced blocks and inline spans, over `_md.walk`, so a document illustrating a
  heading does not carry one. It is public `quoted_out` at `:413` now, and it
  blanks HTML comments too, both by decisions later on this branch — the rename
  by this record's own Decision, the third shape by
  `419-the-template-check-reads-its-own-projection`.
- `_md.py:15` — "This yields per-line state and projects nothing." The fence
  walker holds no projection, by its own statement; `_quoted_out` is one of the
  three shapes it names as the callers'.
- `cli.py:5652` — `_check_arch_records` reaches `_arch` through a function-local
  `from wfctl import _arch`. `doctor`'s checks compose their dependencies at the
  call rather than at module import.
- `architecture-decisions/record-template.md:24` carries `## Owns truth`;
  `software-design-decisions/design-record-template.md:53` carries `## Diagram`.
  Both templates are wfctl's own, not derived.
- Run over the corpus, 2026-09-21: 58 records, 39 with `Owns truth` at the root,
  19 with `Diagram` under `design/`, none with both, none with neither. The 19
  counts this record.

## Assumed

- That the two templates stay the only way records get written. A record
  hand-written without either heading is the `⚠` row, so the bet is not that
  this never happens — it is that it stays rare enough for a nag to be the right
  response rather than a failure.
- Falsified by: a run over the corpus producing `⚠` rows for records their
  authors consider complete. The check prints the path, so the evidence arrives
  with the complaint.

## Direct baseline

Call `load_records` twice — once on the arch root and once on `<root>/design/` —
and read each returned `Record`'s path and `body`. No new enumeration, no new
parser, and `Record` already carries the file text for exactly this kind of
reader.

## Decision

The check globs the two tiers by name, `<root>/*.md` and `<root>/design/*.md`,
and does not call `load_records`. It reads each file's text and asks
`missing_sections` for the tier headings, over `quoted_out` output. It lives
in `cli.py` beside `_check_arch_records`, as `_check_record_placement`, and
composes its dependencies at the call the way the check beside it already does.

The two heading names are constants in `_arch.py`, and a test compares them
against `record-template.md` and `design-record-template.md` in the same wheel —
`required-sections-are-wfctls` applied to a second pair of documents.

`_missing_sections` and `_quoted_out` are renamed without the leading underscore.
A second module reaching for them makes the privacy marker wrong, and a copy
made to avoid renaming is the fourth heading matcher this package already paid
for once.

## Diagram

```
              baseline                           decision

stable   ┌──────────────────┐              ┌──────────────────┐
         │ _arch            │              │ _predicates      │
         │  .load_records   │              │  .missing_       │
         │  .parse_record   │              │   sections       │
         │  STATUSES        │              │  .quoted_out     │
         └──────────────────┘              └──────────────────┘
                   ▲                                 ▲
                   │ calls twice                     │ calls
         ┌─────────┴────────┐              ┌─────────┴────────┐
         │ _check_record_   │              │ _check_record_   │
         │  placement       │              │  placement       │
         └──────────────────┘              └──────────────────┘
                   │                            │        │
                   │ reads Record.body          │ globs  │ globs
                   │ and Record.status          │ <root> │ design/
══ wfctl reads the arch root and never writes it (#113) ═══════════
                   ▼                            ▼        ▼
volatile ┌──────────────────┐              ┌────────┐ ┌──────────┐
         │ arch root        │              │ *.md   │ │ design/  │
         │  (one loader's   │              │        │ │  *.md    │
         │   idea of it)    │              └────────┘ └──────────┘
         └──────────────────┘
```

The graphs differ by what decides which files the check sees. In the baseline
that is `parse_record`, which has already classified every file against the
level-2 status vocabulary before the placement question is asked — so a design
record arrives carrying `status=""`, and the check's input is shaped by the same
tier assumption it exists to test. In the decision the tiers are two names the
check writes down itself, and the only thing it asks another module is whether a
line is a heading.

## Considered

- **The baseline, `load_records` twice** — smallest, and it reuses a parser that
  already reads every record. It loses on fault: `parse_record` applies
  `STATUSES` to both tiers, so every `approved` design record comes back with an
  empty status. The placement check would ignore that field, and the next reader
  of the function would not.
- **`rglob("*.md")` under the arch root, minus `non_record_subtrees`** — one
  walk, and it picks up a tier added later for free. Rejected because the
  correct verdict for a subdirectory nobody has declared a record tier is
  silence, and this shape makes it a finding. The exclusion list answers "not a
  record"; the check needs "which tier", which is the inverse and is not
  derivable from it.
- **A local heading regex in `_arch.py`** — no rename, no cross-module reach,
  three lines. Rejected for the reason `_md` exists: three modules each carrying
  their own fence walker answered differently, and a fourth matcher for the
  question one level up repeats it with the subtleties already paid for
  (`(?!\w)` over `\b`, fenced illustrations blanked) left to be rediscovered.
- **Moving `quoted_out` into `_md`** — puts the projection beside the walk both
  callers share. Rejected on the module's own statement: `_md` yields per-line
  state and projects nothing, and it names the blanked-text shape as a caller's.
  Contradicting that in passing costs more than a rename.
- **Function-local imports between `_arch` and `_predicates`** — avoids the
  rename and any import-time cycle, mirroring what `_predicates` already does
  toward `_arch`. Rejected because two peers importing each other lazily means
  neither reads alone; putting the check at the top of the stack, in `cli.py`,
  needs no edge between them at all.

## Consequences

`_missing_sections` and `_quoted_out` become public, and the tests importing
them by the private name change with them. A grep for either name is the whole
of that migration.

A new record tier is two edits and not one: the glob list and the constants. The
`rglob` shape would have made it zero, and that is the cost this decision
accepts in exchange for silence over undeclared subdirectories.

The heading constants can drift from the templates only by failing wfctl's
build, which is the obligation `required-sections-are-wfctls` already named and
accepted for the spec and plan templates. It is now carried for two more
documents, both wfctl's own — so the rename that would trip it is this
repository's to make, not an upstream pull's, which makes the obligation
cheaper here than where it was first taken on.

## Verification

- A test per row of the level-2 record's finding table, over a `tmp_path` arch
  root: a file under `design/` carrying `Owns truth`, a file at the root
  carrying only `Diagram`, a file carrying neither.
- A test that a file carrying both headings is read as level-2 and produces no
  finding at the root — the case the level-2 record settled by asking
  `Owns truth` first.
- A test that a `## Owns truth` heading illustrated inside a fenced block does
  not satisfy the check, which is what `quoted_out` is in the path for.
- A test comparing the two constants against the headings in the two shipped
  templates, failing on divergence.
- The corpus run itself: `doctor` over this repository prints no placement
  finding. A check that fires on a correctly-placed record gets ignored and then
  removed, so this is the one that matters most and the one a fixture cannot
  give.

## Log

- 2026-09-21  proposed  — the level-3 gate for #419. `doctor-owns-the-placement-verdict`
  settled which command owns the verdict; this settles how it reaches the files
  and recognises a heading, and both had a wrong answer already in the tree.
