# Quickstart: verifying the changed rubric

1. Run the three checks: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`.
2. Install the edited skills and confirm no drift: `uv run wfctl install-skills`, then `uv run wfctl doctor`.
3. Search for a stale pass count: `grep -rn "six-pass\|six lenses\|six passes" wfctl/agents/` prints nothing.
4. Dispatch one fresh reviewer with the saved brief at `$(wfctl state-dir)/experiment-pfms-1011/brief.md` and the installed `.agents/skills/code-review/SKILL.md` as its rubric, over PFMS `7cde6095..996f5e5c`, read-only. Its report names the interest-rate mismatch and the plan goal overflow at WARNING or above, and carries both trail lists (SC-001, SC-002).
5. Dispatch one fresh reviewer with the same rubric over a docs-only commit in this repo. Its report carries the one-line "none" statement in place of the trail (SC-003).
