# brainstorm.software-design does not apply to session-continuity

The removal hook appends one worktree-span event on its success path, after it saves the specs. worktree-span-read-from-git already decides when it writes and what it reads, and no other structure was weighed.
