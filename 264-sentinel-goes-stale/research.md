# Research: A new task reopens the `implement` step

The plan's Technical Context carried no open question. Each entry below
records a decision the plan rests on that the spec and the design records did
not already settle, with what was checked in the code.

## R1. The whole fix lands in `_tasks_open`

**Decision**: Change `_tasks_open` in `wfctl/_evidence.py` and nothing else in
the inference.

**Rationale**: `tasks_open` is computed once per read in `build_evidence` and
consumed in three places. The `implement` reader returns `in_progress` with
its tally when it is true, before it reads the definition of done.
`next_step_content` routes an open `implement` to `/speckit.implement` rather
than `wfctl verify`. The `decompose` reader reads `skipped` only when it is
false. All three already behave as the spec asks once `tasks_open` is right,
in both the configured and the unconfigured arm.

That claim holds for a feature with a delivery plan whose rows are all
keyed, or a delivery plan in a repository that declares no tracker. With no
`delivery.md`, the `decompose` reader reads `pending` once `tasks_open` is
true, so it becomes the current step and `implement` waits behind it. A
delivery plan with an unkeyed row under a configured tracker does the same.
`implement` becomes current once a delivery plan exists and either every row
in it is keyed or the repository declares no tracker.

The routing is left as it is and recorded as a spec edge case rather than
changed in the `decompose` reader. Every feature in this repository's spec
store that holds a completion record also holds a `delivery.md` (22 of 22),
so the case reaches new features, other repositories, and any feature whose
delivery plan has an unkeyed row.

**Alternatives considered**: A new reason on the `implement` assessment, such
as "1 new task since completion". It would add a string to the payload for a
case the tally already shows, and `pipeline-state-is-one-payload` prefers no
new field without a reader that needs it.

## R2. What a task's description is

**Decision**: A task is a line whose quoted-out form holds `[ ]` (incomplete)
or `[x]` / `[X]` (ticked). Its description comes from the raw line: the first
checkbox, the task ID right after it, and any run of `[P]` and `[USn]` tags
right after the ID are removed, then runs of whitespace collapse to one space
and the ends are stripped.

**Rationale**: Only the ID and tags that spec-kit assigns are removed, and only
where spec-kit writes them. A task ID mentioned later in the text, such as
"depends on T012", stays part of the description. A re-run that renumbers it
changes the description of an incomplete task and reopens the step, which is
the safe direction. Removing every ID on the line would let a new task that
differs from an old one only in its dependencies hide as old work.

A line holding two checkboxes counts once for matching, and it is incomplete
when any box on it is. The tally counts both boxes. Reading the line by its
first box alone would let `[x] … [ ] …` hide the incomplete half, so the rule
reads the line as incomplete, which can only reopen the step.

**Alternatives considered**: Removing every `T\d+` on the line. Rejected for
the reason above.

## R3. Descriptions come from the raw line, not the quoted-out one

**Decision**: Which lines are tasks is decided on `quoted_out(text)`, and each
task's description is taken from the same line of the raw text.

**Rationale**: `quoted_out` deletes inline code spans rather than blanking them
(`_blanked`, `re.sub(r"`[^`\n]+`", "", line)`). Two tasks that differ only
inside backticks, such as "Add `foo`" and "Add `bar`", would otherwise share a
description, and a new one could hide as an old one. `_blanked` keeps one
output line per input line, so the two texts line up by index.

## R4. The fence around the copy

**Decision**: The writer fences the copy with tildes, one longer than the
longest fence marker of either character on any line of the copy, and never
shorter than four. Every line is checked, not only the lines a walk reads as
fences. The opener carries the info string `markdown`.

**Rationale**: `_md.closes_fence` closes a block only on the same character,
at least as long as the opener, with no info string. A backtick fence inside
the copy can't close a tilde fence, and a tilde line inside it is shorter by
construction. Checking every line matters because a `~~~~~~` line nested
inside a backtick block is not a fence to the walk, but it would still close
a shorter tilde fence around the copy. The reader finds the `## Tasks at completion` heading outside
any fence with `_md.walk`, then takes the lines inside the next block. Four is
the minimum so the example in the level-3 record reads as written.

## R5. The copy's final newline

**Decision**: The writer adds a newline before the closing fence only when
`tasks.md` does not already end in one. The reader returns the block's lines
joined with newlines and one final newline.

**Rationale**: A copy read back is identical to a `tasks.md` that ends in a
newline, which every file `/speckit.tasks` writes does. A file without one
reads back with one added. That changes no task, so it changes no verdict.
FR-004 is amended to say so.

## R6. The pipeline position check reads the one inference

**Decision**: `wfctl step complete implement` calls `build_report` and refuses
when `report.current` is neither `implement` nor `None`. `None` is the story
complete, which is where the pipeline sits when every box is ticked and no
definition of done is configured.

**Rationale**: `build_report` is the one inference every view renders, and it
writes nothing (checked: no write, append, unlink, or mkdir in its body), so
calling it from a writer has no side effect. Reading `_infer_steps` directly
would skip the host-block hold and the pass holds that `current` already
accounts for.

**Alternatives considered**: Refusing unless `implement` is exactly current,
as first proposed in clarify. It refuses a normal finish where every box is
ticked and no definition of done is configured, as the clarify scan records.

## R7. Epic sub-issues

**Decision**: No change for a branch claimed by an epic.

**Rationale**: `resolve_spec_dir` returns the epic's feature directory for a
claimed sub-issue, so its `tasks.md` and its one completion record are the
epic's. That is true before this change and after it. The new rule reads that
record the same way it reads any other, and `wfctl step complete implement`
on a sub-issue branch writes the epic's record, as writing the file by hand
did. The clarify scan deferred this question here, and this is the answer.

## R8. Where the record's path lives

**Decision**: `_completion.RECORD = Path("checklists") / "implement-complete.md"`,
used by `_tasks_open`, the `tasks` reader, and the new command.
`wfctl/_archive.py` keeps its own string, since `_SPEC_MAP` is a table of
plain paths and its order is its numbering.

**Rationale**: Three readers and one writer now name the path, where two
readers named it before. One constant keeps the writer from drifting from the
readers.
