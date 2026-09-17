# Quickstart: checking #384 by hand

Run these from the worktree once the implementation is done.

1. The suite, lint and types all pass:

   ```bash
   uv run pytest -q
   uv run ruff check wfctl/ tests/
   uv run mypy wfctl/
   ```

2. The removed commands are gone and the new ones are listed:

   ```bash
   uv run wfctl --help | grep -E "report-|notify|blocked"
   ```

   It should list `report-action` and `report-block` only.

3. A hold is placed, and recording the action lifts it:

   ```bash
   uv run wfctl report-block push --reason "trying it"
   uv run wfctl status            # current step held on push
   uv run wfctl report-action push  # names the hold it lifted
   uv run wfctl status            # step no longer held
   ```

4. The status payload has lost the grant:

   ```bash
   uv run wfctl status --json | python3 -c "import json,sys; d=json.load(sys.stdin); print('notify' in d, len(d['facts']))"
   ```

   It should print `False 3`.

5. No old names remain:

   ```bash
   grep -rnE "allow.notify|notify_source|outward actions authorized|authority:notify|wfctl notify|wfctl blocked" wfctl README.md docs AGENTS.md
   ```

   Only superseded records and history log lines should match.

6. The skills install cleanly:

   ```bash
   uv run wfctl install-skills --prune --yes --agent claude
   uv run wfctl doctor
   ```

   Then read `end-session`, `speckit-delivery-plan` and `scaffold-tracker` as
   installed under `.claude/` and `.agents/`.

7. **Ask the maintainer first.** This writes to the tracker. With no grant:

   ```bash
   uv run wfctl issue label <throwaway-issue> --action add --label test
   ```

   The host decides whether it runs, and wfctl prints no refusal.
