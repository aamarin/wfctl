# `spec` does not apply

No behavior change: wfctl's code, commands, flags, output, and stored state are untouched; the edit fills in this repository's own wfctl.json using the review key wfctl already supports. No significant design decision: reverting is one edit to wfctl.json. No ownership change: nothing moves between components; wfctl still reads the review key from main and the review skill still runs each reviewer.
