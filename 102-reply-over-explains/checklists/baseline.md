# Pre-change baseline (T001)

Recorded 2026-08-31, before any edit on `102-reply-over-explains`.

| Measure | Value | Expected by |
| --- | --- | --- |
| `SKILL.md` line count | **388** | `plan.md` budget — ceiling 450 |
| C-6 violations (wfctl inside fenced examples) | **4 lines, 2 blocks** | `research.md` §4 |
| Test suite | 648 passed | — |
| Working tree | clean except untracked `.DS_Store` | — |

C-6 hits, verbatim:

```
✓  $ wfctl end
✗  "The design only changed how wfctl reads completion — the agent still
     → also runs wfctl verify                (the new step)
   wfctl status
```

Blocks at `SKILL.md:207` (literal-output example) and `SKILL.md:292`
(*Untangling* worked example). The second is a whole wfctl scenario, not a
swappable identifier — see `research.md` §4.
