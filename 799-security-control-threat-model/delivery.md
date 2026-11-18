# Delivery plan: #799 security control threat model

## File-touch matrix

| Task | Files |
| --- | --- |
| T001 | CREATE `wfctl/agents/skills/architecture-decisions/references/` |
| T002 | CREATE `wfctl/agents/skills/architecture-decisions/references/threat-model.md` |
| T003 | MODIFY `wfctl/agents/skills/architecture-decisions/SKILL.md` |
| T004 | MODIFY `wfctl/agents/skills/design-passes/SKILL.md` |
| T005 | MODIFY `wfctl/agents/skills/design-levels/SKILL.md` |
| T006 | MODIFY `wfctl/agents/skills/reviewing-security/SKILL.md` |
| T007 | MODIFY `wfctl/agents/skills/fanning-out-code-review/SKILL.md` |
| T008, T009 | CREATE `tests/test_accept_check_threat_model.py`; READ `wfctl/guard/_hook.py` |
| T010, T011 | CREATE `tests/test_threat_model_skills.py` |
| T012 | CREATE `changes/799.change.md` |
| T013-T015 | READ ONLY (install, walkthrough, checks) |
| T016 | done in brainstorm |

## PR boundaries

One PR. The change is size S: five skill edits, one reference, two tests, and a
note, with no code change. The skill edits only make sense together, since a
threat model nobody reviews against, or a review against a threat model nobody
writes, delivers nothing.

## Issue Grouping Map

| Issue | Tasks | PR |
| --- | --- | --- |
| #799 | T001-T016 | this branch |

## Waves

| Wave | Tasks |
| --- | --- |
| 1 | T001, T002, T009 |
| 2 | T003, T004, T005, T006, T007, T008, T010 |
| 3 | T011, T012 |
| 4 | T013, T014, T015 |
