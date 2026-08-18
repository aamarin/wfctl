# Review: working changes on `21-version-check-master-and-fork`

Adversarial pass by a reviewer given only the diff, the spec, and the project
rules — no session history. Three BLOCKERs, two WARNINGs, one NIT. Each was
reproduced against the real code before being accepted; one was rejected on the
merits after reproduction.

## Findings

```
BLOCKER  wfctl/cli.py:L1686 — url from direct_url.json passed to `git ls-remote`
                              without `--`; a recorded url of `--upload-pack=<cmd>`
                              executes <cmd> on every doctor run, i.e. every
                              session start → add `--` before the url
BLOCKER  wfctl/cli.py:L1662 — a pinned install returned None, discarding the origin
                              url along with drift-eligibility; a pinned fork build
                              was told to upgrade from upstream, violating FR-012
                            → keep the url, gate only the comparison on `pinned`
BLOCKER  wfctl/cli.py:L1776 — drift + failed tag query exits 1, but FR-009a said
                              "MUST exit zero"  → REJECTED, spec amended instead
WARNING  data-model.md:L32  — specifies `--refs`, which the code deliberately omits
                              and a regression test forbids → doc corrected
WARNING  wfctl/cli.py:L1786 — 4th warning variant had no assertion on its text
                            → test added
NIT      wfctl/cli.py:L1769 — `origin == _WFCTL_REPO` is exact string equality
                            → comment added stating the assumption and its cost
```

## The rejected BLOCKER

The reviewer was right that the code contradicted FR-009a. It was wrong about
which side to change, because the contradiction is **inside the spec**:

- FR-006: "Drift MUST produce a non-zero exit code."
- FR-009a (as written): "When any query fails … MUST exit zero."

Both apply when the tag query fails while the branch query proves drift —
reachable on any fork install, since those are two independent queries.
Following FR-009a there would exit 0 on a build positively identified as stale,
which is precisely the silent false-negative this feature exists to remove, and
would defeat SC-001. FR-006 wins. FR-009a is amended to "zero unless a
comparison that did run found something actionable", the reasoning recorded
inline, and `test_known_drift_still_exits_nonzero_when_the_tag_query_fails`
pins the behaviour.

## Why the tests missed all three

Every accepted finding lives in a combination the test matrix did not cross:
fork × pinned, fork × partial failure, and untrusted-input-shaped url. The
suite asserted heavily on the states the design enumerated and not at all on
their products. Each fix ships with the test that would have caught it.

The injection finding is the sharper lesson: no amount of behavioural testing
would have found it, because the stub cannot execute anything. It is only
visible by asserting on argv, or by running the real binary — which is also how
the `--refs` defect was found earlier in implementation. Two of this change's
three worst defects were invisible to a passing test suite.

net: −0 lines (the `_Build` NamedTuple adds ~10; the security fix and its
comment ~6; both buy correctness that was absent)

**Verdict: Approve after fixes.** 422 tests pass, ruff and mypy clean, and the
drift path re-verified end to end against a real install: clean at tip (exit 0),
drift block at exit 1, remedy naming the recorded origin.
