# `spec` does not apply

No behavior change: the intended output is already written down in #707, which asks for git's stderr in these messages to be escaped the same way #695 escapes the diff, and six messages that carry git's or the GitHub CLI's stderr didn't match it. No significant design decision: six messages in two functions of one module change, using the helper that's already there. No ownership change: nothing moves between components.
