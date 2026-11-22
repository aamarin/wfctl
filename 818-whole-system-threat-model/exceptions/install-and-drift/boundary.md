# No new boundary for install-and-drift

No boundary moves in install-and-drift. The change adds threat-baseline and _lib to the existing mirrored-skills list and one entry to the ignore list install-skills already writes, so install still owns the same files the same way. threat-model installs under .agents/ only, like every other skill that isn't mirrored.
