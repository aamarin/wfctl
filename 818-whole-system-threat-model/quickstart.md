# Quickstart: checking the feature by hand

Run these from the worktree after implementation.

1. Install from the working tree and check the helper resolves:

   ```bash
   uv run wfctl install-skills --prune --yes --agent claude
   ls .claude/skills/threat-model .claude/skills/threat-baseline .claude/skills/_lib
   python3 .claude/skills/_lib/checkpoint.py load ./.threat-model-state
   ```

   The last command prints `{"status": "absent"}`.

2. Check the pass in a scratch repository. Make a branch, add a level-2 record whose body has a `## Threat model` heading, and commit it. `uv run wfctl status` shows `threat-baseline ▶` and `next: /threat-baseline`. Commit an empty `THREAT_MODEL.md` at the root, and the pass reads `●`.

3. Check the skip. On a branch whose records carry no `## Threat model`, the pass reads skipped and brainstorm advances as before.

4. Check the trigger separation. In a Claude Code session on the installed tree, ask for the threat model of one security control at design time. The session writes a `## Threat model` section in a level-2 record and doesn't load `threat-model`.

5. Build wfctl's own baseline. Run `/threat-baseline` and confirm `THREAT_MODEL.md` opens with the working-map line and ends with the rejected-fixes section, then commit it.

6. Finish with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl doctor`, and `uv run wfctl verify`.
