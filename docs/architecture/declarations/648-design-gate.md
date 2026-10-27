# No new boundary — 648-design-gate

This change adds a brainstorm check for the software design question and draws no new boundary. The check sits in Evidence and derivation and reads what the Design method produces, which is the same relationship the architecture check already has (domain/wfctl.md). The person on the branch still decides whether a structural choice was made, and records it as a file under design/ or with wfctl step none. wfctl only reads which of the two exists, as a-rule-is-expressed-as-a-check.md and an-absent-artifact-is-claimed-not-inferred.md already describe.
