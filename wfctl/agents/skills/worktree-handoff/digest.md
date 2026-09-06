SKILL.md governs; these break first.
1. New work gets its own worktree. A branch in the checkout you are standing
   in is the failure, not a shortcut.
2. Write the handoff to a file before `wm add`, never after — it is only
   injected at add time.
3. Both slots: `--prompt-file`, and the state dir's `session-summary.md`.
   `.workmux/` alone dies with the worktree.
4. Every decision carries its argument; every boundary carries its reason.
5. Name the route, and say to run `/start-session`.
