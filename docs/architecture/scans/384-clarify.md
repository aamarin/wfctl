# Clarify scan — #384

## Session 2026-09-15

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/384-strip-allow-notify/spec.md § Clarifications

Run unattended at the user's request ("go and can you go unattended?"). Every
answer below is the recommendation the question was rendered with, taken from
the repository. Nobody picked it.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Deferred |

### Findings

- **Interaction & UX Flow** — FR-015 said skills ask "in an attended session" and try the action "in an unattended run", but nothing said how a skill can tell which one it is in.
  Q: How does a skill know it is running unattended? → A: It doesn't detect anything. It asks as written, and a run where nobody answers tries the action.
  Basis: design.md says "An attended session still asks before reaching outside the repo, exactly as its skills already say. An unattended run simply tries." The `speckit.clarify` wrapper handles its own unanswered pauses the same way, and says why that isn't tied to `auto_approve`: that setting moves design approval, not permission to act. A signal for "attended" itself belongs to #127.
  Decided against **B — read `auto_approve`**: that setting is about who approves design gates. Tying outward actions to it would bring back a wfctl setting that decides whether a run may act, which is the proxy level 2 removes.
  Decided against **C — a new environment variable for unattended runs**: that is a new switch whose only job is permission, which again is what level 2 removes. It also overlaps with #127.
- **Edge Cases & Failure Handling** — `blocked --clear` checked that a hold existed before releasing it, so a mistyped action name was caught (the FR-014 comment in `cli.py`). With `--clear` removed, `report-action` releases holds, and the spec didn't say whether it reports that.
  Q: What does `report-action` say about holds? → A: It names the hold it lifted, if any. Otherwise it says only that the action was recorded, and it never refuses.
  Basis: the check in `blocked --clear` existed so that a clean exit could not be mistaken for a release. Printing the lifted hold keeps that signal. A refusal can't, because recording a push with nothing held is the normal case, as in `end-session`.
  Decided against **B — refuse when no hold matches**: it would refuse every ordinary push.
  Decided against **C — print only "recorded"**: a typo in the name would look exactly like a successful release. That is the failure the old check existed to catch.
- **Integration & External Dependencies** — the level-3 record renames `blocked` to `report-block`, but the spec named only `--reason` and the held step. It didn't say whether the rest of `blocked`'s behaviour (reason required, step inferred, the complete-pipeline fallback, the no-spec-dir case) carries over.
  Q: Does `report-block` keep all of `blocked`'s behaviour apart from `--clear`? → A: Yes.
  Basis: `384-the-agent-reports-through-two-flat-verbs` changes the name and removes `--clear`, and nothing else. Every other branch in `blocked_cmd` has a reason recorded in its comments (FR-008, FR-010 of #364), and none of those reasons depended on the grant.
  No options offered — short answer.

### Outstanding

None. No question was withdrawn, and the spec has no `[NEEDS CLARIFICATION` markers.

### Deferred

- **Misc / Placeholders** — the exact wording of the host-permission line in `wfctl status` (FR-013). It is a wording choice with no effect on scope or tests beyond "does not imply wfctl has rules", and `plan.md` is where output strings get settled.
