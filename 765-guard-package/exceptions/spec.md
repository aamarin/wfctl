# `spec` does not apply

No behavior change: the guard allows and refuses exactly what it did, and wfctl hook keeps its name and payload. No significant design decision: contexts-are-packages already decided that the worktree guard becomes the guard package, and this change carries that out; the one message that moves is a private helper with one obvious home. No ownership change: the guard keeps the hook and the command rules, and evidence keeps the PR checks, as the domain page already draws them.
