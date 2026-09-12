# Quickstart — level3 downstream (#326)

How to see this working, and how to see it failing. The suite does not verify a
change under `wfctl/agents/` at all — it checks that skills ship and
cross-reference, not that they read well — so these are the verification, not a
demonstration of it.

## Get the change into a tree you can run

```bash
uv run wfctl install-skills
uv run wfctl doctor
```

`uv run`, not a bare `wfctl`. This repository has two on PATH and they carry
different bundles; a bare `wfctl install-skills` installs *its own* copy of the
wrapper you just edited, the command succeeds, the tree looks installed, and your
change is nowhere in it.

## The happy path (US1)

This feature is its own fixture — `design.md` lists one record.

```bash
uv run wfctl feature-paths          # FEATURE_DIR
grep -A4 "## Software design decisions" "<FEATURE_DIR>/design.md"
```

Then run `/speckit.plan`. Expect in its closing report:

```
Design records: 1 listed in design.md
  docs/architecture/design/326-contradiction-is-a-seventh-pass.md
```

A run against a feature whose `design.md` lists nothing has not tested this.

Repeat with `/speckit.tasks` and `/speckit.implement`. Same path, same count.

## The contradiction (US2)

The one that settles whether the whole approach works. Two runs, and the second
is what proves the severity split is real rather than described.

```bash
# 1. temporarily ratify the record
sed -i '' 's/^status: proposed/status: approved/' \
  docs/architecture/design/326-contradiction-is-a-seventh-pass.md
```

Add to `tasks.md` a task that reverses its `Decision` — the record chose a model
pass over a command, so:

```
- [ ] T0XX Add `wfctl design check-tasks` comparing declared invariants
```

Run `/speckit.analyze`. Expect a CRITICAL finding naming the record by path and
quoting T0XX.

```bash
# 2. put it back and re-run
sed -i '' 's/^status: approved/status: proposed/' \
  docs/architecture/design/326-contradiction-is-a-seventh-pass.md
```

Run `/speckit.analyze` again. Same task, same record, now a **warning**.

Then revert the task. It was a fixture, not work.

**A clean verdict on the first run falsifies the design, not the
implementation.** That the pass can see a prose contradiction at all is the
assumption `326-contradiction-is-a-seventh-pass` records as the bet everything
rests on. If it reads clean, the finding belongs in that record's `Log` and the
decision is reopened — it does not belong in a bug fix.

## The three empty states (US3)

```bash
# none listed
#   edit a scratch design.md so the section carries prose only

# unknown
#   run against a feature directory with no design.md at all
```

Each of the four steps, against each state. Expect two different lines, neither
of them silence:

```
Design records: none — design.md records no level-3 decision
Design records: unknown — no design.md at <FEATURE_DIR>
```

## The scan file

After the analyze runs above:

```bash
uv run wfctl arch-root
cat "<arch-root>/scans/121-analyze.md"
uv run wfctl arch check "<arch-root>/scans/121-analyze.md"
```

Pass G sits between `F · Inconsistency` and `Requirement-to-task coverage`, and
`Requirement-to-task coverage` is still the only row carrying a percentage.
`arch check` exiting 0 is what says a reviewer will read it.

## Definition of done

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

All four, all through `uv run`. `doctor` compares the installed tree against the
bundle carried by whichever wfctl you invoked, so it answers "does the installed
tree match the source I am editing" only when invoked the same way
`install-skills` was.
