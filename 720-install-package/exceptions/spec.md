# `spec` does not apply

No behavior change: the five install and drift modules move into wfctl/install/ and every command reads and writes the same files and prints the same output. No significant design decision: contexts-are-packages already decided that each context is a package with lazy re-exports, and this move carries that decision out for one context. No ownership change: the install context still computes everything it computed, and the session check is handed the runner by the wiring instead of importing it.
