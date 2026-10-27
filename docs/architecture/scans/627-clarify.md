# Clarify scan for #627

## Session 2026-10-24

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 2
- Detail: /Users/andremarin/Development/wfctl-specs/627-ci-review-check/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Deferred |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior**: the spec didn't say how a release PR
  passes. `release.py` opens a PR whose only commit is the version bump, no
  review group runs on it, and so a required `review` check would block every
  release.
  Q: How does a release PR get past the review check? → A: The maintainer
  signs off on the release commit by hand. `release.py` prints the command
  and doesn't sign off itself.
  Basis: the maintainer chose this in chat, after asking whether a scripted
  sign-off carried a risk from agents.
  Decided against **release.py signs off**: an agent can run the script by
  feeding it its answers. A scripted sign-off would let that agent cut, open,
  and merge a release with nobody involved, where the guard refuses a hand
  sign-off from an agent.
  Decided against **exempt by diff**: it carries the same agent risk as the
  scripted sign-off, and it's a second rule that has to stay in step with
  what `release.py` commits.
- **Interaction & UX Flow**: pushing the notes ref doesn't start a CI run, so
  a `review` job that failed before the notes arrived stays red. This happens
  on every commit pushed after a PR opens, and the approved failure message
  sends the user to `wfctl store reviews`, which sends the notes but doesn't
  rerun the job.
  Q: After the notes reach GitHub, how does a red review check turn green? →
  A: wfctl reruns the failed `review` job on the branch's open PR after any
  successful notes push.
  Basis: the maintainer chose the recommended option in chat.
  Decided against **the message says to rerun**: it leaves a manual step on
  every fix pushed after a PR opens, and a forgotten rerun blocks the merge.
  Decided against **push after review**: it's a skill instruction an agent
  can miss, and a stray push still needs a manual rerun.
  Decided against **leave as designed**: the design assumed the failure
  message covered the rerun, and it doesn't.

### Deferred

- **Integration & External Dependencies**: whether GitHub accepts a pushed
  notes ref and a PR job can fetch it, and what `actions/checkout` leaves on a
  PR run. Both need a throwaway push and CI run before plan, and the
  maintainer approves the push first. The spec records both as assumptions.
- **Constraints & Tradeoffs**: the CI subcommand's name and how the job finds
  the trunk. Neither changes what the user sees, so plan settles them. The
  spec records a default for each.
