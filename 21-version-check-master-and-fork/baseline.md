# T001 Baseline — the defect, captured before any edit

Recorded 2026-08-17 on the development machine, for the PR description.

```
$ wfctl doctor
✓ wfctl 0.14.0 — latest
✓ base: skills up to date (9ee468a)
$ echo $?
0
```

State at the time of that run:

| | Value |
| --- | --- |
| installed commit (`direct_url.json`) | `d8688f6eec75c2a8eac3a94f3fc44e25041d22a9` |
| branch tip (`origin/master`) | `271bb2c` |
| distance | 3 commits |
| installed version | 0.14.0 |
| version on the branch | 0.15.0 |
| newest release tag | v0.14.0 |

The build is three commits behind the branch it was installed from, and is
missing the entire skills-vendoring change (#47/#49). `doctor` reports it as
current, at exit 0, because the version string matches the newest tag — which is
exactly the defect issue #21 describes.

This is also the fixture SC-006 and T025 verify against: after the fix, the same
command on the same build must report drift.
