Implementation complete: 2026-08-18

32/32 tasks. 407 tests passing, mypy and ruff clean.

Commits: 61c027a (workmux template), afbcfd7 (exit-code contract), 4afc68e
(abandoned entries + step-command test).

Two findings during implementation, both recorded in tasks.md:

- `.agents/trackers/` is shared ground — `install-skills --tracker github`
  records into it and `/scaffold-tracker` documents it for hand-authoring. The
  planned recorded-parent scan would have failed a repo's build over its own
  tracker config. Fixed destinations exclude it by construction. **Closed here,
  no follow-up**: nothing else in wfctl enumerates that directory — every access
  is by exact filename — so this scan was the only thing the mixing could have
  broken. Pinned by a test so tightening the scan set cannot reintroduce it.
- Three tests asserted the old exit-code convention, two of them for checks the
  plan believed untested. They were coverage pointing the wrong way, not missing
  coverage.
