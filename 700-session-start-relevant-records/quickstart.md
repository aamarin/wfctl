# Quickstart: check the narrowed session start by hand

1. In this worktree, make a scratch spec root with one context:

   ```bash
   mkdir -p "$SCRATCH/specs/700-session-start-relevant-records"
   printf '# t\n\nContexts: install-and-drift\n\n## x\n' > "$SCRATCH/specs/700-session-start-relevant-records/design.md"
   WFCTL_SPEC_DIR="$SCRATCH/specs" uv run wfctl arch context
   ```

   Expect 24 of 28 records, `contexts-are-packages` among them, the 23 with no
   `governs` field, and a line saying 4 were left out with `--all`.

2. Point `WFCTL_SPEC_DIR` at an empty directory and run it again. Expect all 28
   and the "lists no contexts" line.

3. `uv run wfctl arch context --all` prints all 28 with neither line.

4. `WFCTL_SPEC_DIR="$SCRATCH/specs" uv run wfctl status --session` shows
   `Records: 24 of 28 accepted apply to this branch`.
