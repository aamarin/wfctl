# Quickstart: reproduce both arms by hand

The suite covers both arms, and the handoff asks for them by hand as well. A
run that saw only the configured arm has tested the safe half.

Work in a scratch repository, since this writes a feature directory and a
`wfctl.json`. Run every command below from the scratch repository as
`uv run --project <worktree> wfctl`, with `<worktree>` the checkout holding
this change. A bare `uv run wfctl` there resolves to the installed release,
which has no `step complete`.

## Set up

1. Create a repository with a feature whose `spec.md`, `plan.md`, plan review,
   `checklists/analysis-report.md`, and a keyed `delivery.md` are present, so
   the pipeline reaches `implement`. `_ANALYZED` in
   `tests/test_pipeline_payload_snapshot.py` is that set, its plan review
   comes from `REVIEWED` beside it, and `KEYED_DELIVERY` there is a delivery
   plan that works. Without `delivery.md`, the new task sends the story to
   `/speckit.decompose` instead, as the spec's edge cases say.
2. Write `tasks.md`:

   ```
   - [x] T001 Create project structure
   ```

3. Run `wfctl step complete implement`. It prints the recorded tally, and
   `checklists/implement-complete.md` now holds the copy.
4. Add a task:

   ```
   - [x] T001 Create project structure
   - [ ] T002 Migrate old records
   ```

## Without a definition of done

With no `verify` key in `wfctl.json`, run `wfctl status` and `wfctl next`.

Expected: `implement` is current with `1/2 done`, and the next command is
`/speckit.implement`. Before this change the story read complete.

## With a definition of done

Add `{"verify": [["true"]]}` to `wfctl.json`, and run the two commands again.

Expected: the same as above. Before this change, `next` gave `wfctl verify`.

## Ordinary edits

Tick T002 and run `wfctl step complete implement` again. Then add a note line
under T001, reword T001, and change a tag on T002. After each edit,
`wfctl status` shows `implement` closed.

## Too early

Delete `checklists/analysis-report.md` so `analyze` is current, then run
`wfctl step complete implement`.

Expected: exit 1, naming `analyze`, and the record is unchanged.
