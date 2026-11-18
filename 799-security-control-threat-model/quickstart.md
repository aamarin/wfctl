# Quickstart: checking the threat-model step

1. Run `uv run wfctl install-skills` so `.agents/` carries the edited skills.
2. Pretend change: "Let the guard's accept check allow a commit message that
   holds a backticked `wfctl doctor`" (a #792 form).
3. Read `.agents/skills/design-passes/SKILL.md` step 1 as the agent would.
   Expect the design-decision question to read yes and send the change to
   `/speckit.brainstorm`.
4. Read `.agents/skills/design-levels/SKILL.md` level 2. Expect it to send the
   change to `.agents/skills/architecture-decisions/references/threat-model.md`
   before any code.
5. Read the reference. Expect the four parts and how to fill each.
6. Read `.agents/skills/reviewing-security/SKILL.md` as a reviewer of that
   change. Expect it to find `accept-check-threat-model.md` by its heading,
   judge the backticked form against "Must let through", and name the record.
7. Read `.agents/skills/fanning-out-code-review/SKILL.md` as the coordinator.
   Expect it to say the brief states no bar and names no record.
8. Run `uv run pytest -q tests/test_threat_model_skills.py tests/test_accept_check_threat_model.py`.
