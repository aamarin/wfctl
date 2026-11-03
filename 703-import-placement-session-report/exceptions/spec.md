# `spec` does not apply

No behavior change: wfctl runs the same way, and only the import check's baseline gains two lines for a module that already merged in #432. No significant design decision: the placement follows the domain page, which puts /start-session in Session continuity, and the violation line records an import that already exists. Either line can be reverted in one commit. No ownership change: no code moves, and #671 moves modules into their packages.
