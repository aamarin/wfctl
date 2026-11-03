# `spec` does not apply

No behavior change: approve-imports already promises to show the diff of each changed trusted file before it asks for approval, and when git diff fails it shows nothing and asks anyway; the fix makes it stop instead, adding no command, flag, file, or persistent state. No significant design decision: one function in _review_notes.py checks a return code and a timeout it ignored. No ownership change: nothing moves between components, and the command still owns the approval prompt.
