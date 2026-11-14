# Clarify scans for #571

## Session 2026-10-14

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/571-release-automation/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Resolved |
| Terminology & Consistency | Clear |
| Completion Signals | Resolved |
| Misc / Placeholders | Clear |

### Findings

- **Edge Cases & Failure Handling** — the check read only a note's file name.
  The failure message suggests `uv run towncrier create 571.change.md`, and
  towncrier 26.9.0 run that way writes a note holding only "Add your info
  here", measured in a scratch folder on 2026-10-14. That note passed the check
  and would have reached the release draft as a line.
  Q: Should the check read a note's content, or only its file name? → A: It
  fails a note that is empty, whitespace only, or still holds the placeholder,
  and names the file (FR-003a, User Story 1 scenario 8).
  Basis: Andre chose A.
  Decided against **fail only an empty note**: it leaves the one note the
  suggested command produces passing, so the placeholder reaches the draft
  unless review catches it.
  Decided against **file names only**: it leaves both the empty note and the
  placeholder to review, and each costs the check one string comparison.
- **Domain & Data Model** — the spec didn't say how the release script decides
  that a merged pull request came with a note. `design.md` assumed it matches
  the issue number at the front of the branch name, and that can't match a
  `+<name>` note for a branch with no issue, so such a merge would be listed as
  missing a note it has.
  Q: How does the release script decide a merged pull request came with a note?
  → A: By whether the merge commit itself added a file under `changes/`, read
  from git (FR-009, User Story 2 scenario 5).
  Basis: Andre chose A.
  Decided against **match on the issue number in the branch name**: every
  merged branch with no issue number is listed as missing a note, whatever it
  committed.
  Decided against **match on the issue number, and on a `+<branch-name>` note
  for a branch with no issue**: it works only when the note's name repeats the
  branch's, which nothing requires, and it still guesses at what git can say
  directly.
- **Constraints & Tradeoffs** — the spec removed the "Type of Change" checkboxes
  from "the pull request template", and wfctl has two identical copies of it.
  `.github/pull_request_template.md` is this repository's own, and
  `wfctl/agents/configs/github/.github/pull_request_template.md` is copied into
  every project set up with the GitHub tracker. Editing the second would break
  SC-005.
  Q: Which pull request template loses the "Type of Change" checkboxes? → A:
  This repository's own only. The shipped template keeps them (FR-018, User
  Story 4 scenario 3).
  Basis: Andre chose A.
  Decided against **remove them from both**: projects that install the template
  have no release notes to take the checkboxes' place, and SC-005 and
  `design.md`'s Not Doing both rule out changing what wfctl ships.
  Decided against **keep them in both**: two fields asking one question will
  disagree, which is what the spec's assumption removed them for.
- **Completion Signals** — SC-001 says every pull request merged after this
  feature carries a note, and `main` has no branch protection and no ruleset,
  read from the GitHub API on 2026-10-14. So a red CI run refuses nothing, and
  the criterion holds only because Andre doesn't merge one.
  Q: Should `main` require the release note check to pass before a pull request
  merges? → A: No. The check fails CI where Andre sees it, as tests and lint do,
  and the release script lists any merge that got through (SC-001, Assumptions).
  #599 tracks requiring it once someone other than Andre can merge.
  Basis: Andre chose A after asking why not B, and asked for #599.
  Decided against **require the check, with a bypass for the release push**: a
  GitHub bypass is granted to a person or a role rather than to a kind of push,
  so the bypass that lets Andre push the release also lets him merge a red pull
  request. Andre is the only person who merges, and agents merge with his login,
  so the rule would refuse nobody.
  Decided against **require the check, and send the release commit through a
  pull request**: it would enforce the check, at the cost of changing how a
  release is cut, which this feature keeps as a push straight to `main`. It
  also means choosing whether test, wheel, and lint become required too, which
  is a larger call than #571. Both are in #599's scope.

## Session 2026-10-15

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/571-release-automation/spec.md § Clarifications

The first plan review raised both questions, and this session reopened the
2026-10-14 answer on protecting `main`. The answers below replace it.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Resolved |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Edge Cases & Failure Handling** — the plan had the tag job fall back to
  GitHub's generated notes when the release commit's body was empty. That
  publishes the list this feature exists to replace, and nobody sees it happen.
  Q: What does the tag job do when the release commit's body is empty? → A: It
  fails before it tags anything, so no tag and no release are published, and it
  never falls back to the generated notes (FR-016, User Story 3 scenario 4).
  Basis: Andre chose A.
  Decided against **fall back to the generated notes**: the release goes out
  with the notes nobody wrote, which is the failure the feature removes.
- **Constraints & Tradeoffs** — failing the tag job blocks only the publish.
  With `main` unprotected, the version bump still lands on `main`, and the
  release is half done until someone repairs it by hand.
  Q: Should `main` require the checks before a pull request merges? → A: Yes.
  `main` is protected with no bypass, Andre included, so a release reaches
  `main` through its own pull request like any other change (FR-004, FR-013,
  FR-020, User Story 5). #599 is folded into this feature.
  Basis: Andre chose A. This replaces the 2026-10-14 answer above.
  Decided against **no protection, as decided on 2026-10-14**: a red pull
  request and a release with no notes can both reach `main`, and only Andre's
  attention stops them.
  Decided against **protection with a bypass for the release push**: GitHub
  grants a bypass to a person rather than to a kind of push, and agents merge
  with Andre's login, so the bypass would cover every red merge as well.
