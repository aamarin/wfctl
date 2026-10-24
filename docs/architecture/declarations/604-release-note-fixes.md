# No new boundary — 604-release-note-fixes

These four fixes stay inside the release scripts and CI. The release note check still decides whether a change committed its note. In a pull request run, it now compares against the branch the pull request targets instead of main, and the change-carries-release-note record still holds, since it describes the local run, which still compares against main. The CI change only stops runs on main from cancelling each other, and the type checker now also covers the release scripts. Nothing changes who owns a value or where a boundary sits.
