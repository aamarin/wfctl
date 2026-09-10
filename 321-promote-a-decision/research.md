# Phase 0 research — #321

No `NEEDS CLARIFICATION` reached this phase; the four the clarify step raised are
answered in `spec.md § Clarifications`. What follows is the codebase reading the
plan rests on, with what was read.

## The transition has no existing surface

- `wfctl/_arch.py:404` — `supersede(record, date, reason)` is the module's only
  status mutation.
- `grep -rn "supersede(" wfctl/ tests/` — every caller is in
  `tests/test_arch_records.py`. It has never been reachable from the CLI, so this
  feature adds the first status-writing command rather than a second.
- `wfctl/cli.py:1042` — `arch_app` carries `context`, `none` and `check`. None
  writes a status.

## What the mutation has to get right

Read out of `supersede`'s body and its comments, and carried into `_set_status`
unchanged:

- `record.path.open(newline="")` — `read_text` translates CRLF to LF, which would
  rewrite every line of a CRLF record from a function contracted to change one.
- The `status` key is found by scanning **backwards** from the frontmatter end,
  because `_frontmatter` takes the last of a repeated key. Editing the first would
  log a transition the record does not carry.
- `_log_bounds` returns the end of the `## Log` *section*, not end of file, and
  trailing blank lines stay below the inserted entry.
- A file not ending in a newline gets one before the insert, or the new entry
  welds onto the previous line.
- `write_atomic` — a torn write loses a hand-authored decision no later run can
  reconstruct.

Both raises are also inherited: no `status:` key, and no `## Log` section, each
writing nothing.

## The `Log` column is 12 characters

Every line in `docs/architecture/*.md` pads the status word to 12:

```
- 2026-08-29  accepted    — #96 shipped it; …
- 2026-09-07  proposed    — #100's level-2 pass. …
```

`accepted` + 4, `proposed` + 4, and `supersede` writes `superseded` + 2. The
current code spells those two spaces literally and names no width, so
parameterizing the word means naming the column. `f"{status:<12}"` reproduces
`supersede`'s existing output exactly.

## The consumer that is already waiting

- `wfctl/_predicates.py:40` — `Source = Literal["repo-declared", "accepted-record",
  "human", "ambient"]`.
- `wfctl/_predicates.py:45` — `_PROMISED` contains `"accepted-record"`, so a gate
  reading it blocks when it is silent.
- `grep` finds one use of the string outside those two lines:
  `tests/test_pipeline_commands.py:1143`, asserting the rule. **No gate produces
  it.** #299 is the gate that would, and it is marked blocked on this transition.

This is why FR-008's prohibition matters more than it looks: the evidence class
exists and is unproduced, so whatever this feature makes produce it becomes what
`accepted-record` *means* for every later gate.

## The two precedents, and why they disagree

```
wfctl-runs-the-verification   accepted — #96 shipped it; the code enforced a
                                         rule the contract still called open
required-sections-are-wfctls  accepted — agreed by the maintainer on #318
```

`git log` for the first (`a49387c`) says in its own body: *"It makes the contract
match code that has been enforcing it since 24beb3e."* That is the honest
description of promoting on implementation, and it is the reason the level-2
record rejects it as the rule.

The second (`1e9197b`) is three commits after the one that wrote the record, on a
record that had already merged as `proposed`. That is what falsifies "merge is the
promotion": under that rule the separate agreement was ceremony and the commit
recording it would not exist.

## What the date should be

Checked, because the `Log` line carries one and nothing said which clock:

- `wfctl/_session.py:38`, `wfctl/_verify.py:174`, `wfctl/_io.py:40`,
  `wfctl/_archive.py:104` — every timestamp wfctl writes is UTC.

Answered UTC in `spec.md § Clarifications`, with the cost named.

## Alternatives that were live and are not

Settled in the two records rather than here, and listed so this phase does not
look like it found nothing:

- Merge is the promotion — falsified by the repository's own history, above.
- A gate at a pipeline step — rejected on what the evidence proves, and it would
  couple `_arch` to `_pipeline`.
- A repo-configurable policy — reversible later, and no second project has asked.
- A `Transition` table — two rows do not pay for it.
