# Quickstart: checking the design checks by context

Run this after `uv run wfctl install-skills --agent claude`, on a scratch branch named for an open issue, in a repo whose domain page carries the two header lines.

1. Write a `design.md` whose header lists one context:

   ```
   # Scratch

   Contexts: session-continuity
   ```

2. Add a level-2 record with `governs: install-and-drift` and commit it. The record needs a `diagram:` field and a fenced drawing under `## Boundary`, because the drawing check holds the row before step 3 can read done. Run `uv run wfctl status`. The `architecture` row reads `no architecture record governs session-continuity`.
3. Change the record to `governs: session-continuity` and commit. The row reads done.
4. Revert the record to `install-and-drift`, then run `uv run wfctl arch none --context session-continuity --reason "Scratch check"`. The row reads done, and `uv run wfctl status --all` shows `session-continuity: no — Scratch check`.
5. Run `uv run wfctl arch none --reason "Scratch check"` with no `--context`. It refuses and names the option.
6. Change the `Contexts` line to `session-continuty`. The row reads `session-continuty is not a context on the domain page`.
7. Remove the `Contexts` line. The row reads `design.md lists no contexts`.
8. Give the record `governs: sesion-continuity` and run `uv run wfctl doctor`. It reports the record and the name.
9. Repeat steps 2 to 4 for the software design check, with a level-3 record under `design/` and `wfctl step none brainstorm.software-design --context`.

Delete the scratch branch and its spec folder afterwards.
