# Quickstart: issue edit verb

After the change is built, run these from the worktree:

1. Refresh the tracker config, since a plain `install-skills` never refreshes
   one that already exists:

   ```bash
   uv run wfctl install-skills --tracker github
   uv run wfctl tracker-check
   ```

   `edit` is in the verb list.

2. Edit a real issue's body, using text with several lines, backticks, and
   quotes:

   ```bash
   uv run wfctl issue edit <id> --body "$(cat body.md)"
   ```

   The issue's URL prints, and the body on GitHub matches `body.md`.

3. Confirm the write was recorded:

   ```bash
   grep issue-edit "$(uv run wfctl state-dir)/events.jsonl"
   ```

   One line appears for the edit.

4. Check the usage errors send nothing:

   ```bash
   uv run wfctl issue edit <id>          # ✗ 'edit' needs --title, --body, or both
   uv run wfctl issue edit --body "B"    # ✗ 'edit' requires an issue id
   ```
