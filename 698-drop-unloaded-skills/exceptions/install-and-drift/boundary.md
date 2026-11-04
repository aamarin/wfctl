# No new boundary for install-and-drift

The installer keeps the same three modes and the same removal rule. A skill dropped from the bundle becomes a path the manifest recorded and this install did not write, which is the orphan case install-skills already reports and --prune already removes. No ownership moves between wfctl and the consumer repo.
