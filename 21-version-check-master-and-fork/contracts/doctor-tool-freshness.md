# Contract: `wfctl doctor` tool-freshness rows

The CLI's user-facing contract for this feature. Line shapes below are what tests
assert on and what `start-session` reads.

## Scope

The first row(s) of `wfctl doctor` output, produced by the tool-freshness check.
The skills rows that follow are unchanged by this feature.

## Output shapes

**Current, nothing to say** — byte-identical to today:

```
✓ wfctl 0.15.0 — latest
```

**Newer release available** — the branch line is suppressed. The version pair is
unchanged from today; the URL is not — it now follows the recorded origin:

```
⬆ wfctl 0.14.0 → 0.15.0 available
    upgrade: uv tool install --upgrade git+https://github.com/aamarin/wfctl.git
```

**Behind the branch tip** — new:

```
✓ wfctl 0.15.0 — latest release
⬆ build behind master — d8688f6 → 271bb2c
    bundled skills are from this build too
    reinstall: uv tool install --force git+https://github.com/aamarin/wfctl.git
```

- `master` is the branch name resolved from the remote, not a literal.
- Commits are abbreviated to 7 characters, matching the skills rows.
- **Every** remedy URL — the reinstall line here and the upgrade line above — is
  the recorded origin, so a fork build is always told to install from its own
  fork and never from upstream. The upstream constant is the fallback used only
  when no origin is recorded. Release *tags*, by contrast, always come from
  upstream; the two must not be conflated.
- No commit count appears — the available data proves difference, not distance.

**A check could not run** — exactly one line, naming what is missing:

```
⚠ wfctl 0.15.0 — couldn't check releases or branch (offline?)
⚠ wfctl 0.15.0 — latest release; couldn't check branch drift
⚠ wfctl 0.15.0 — couldn't check releases; build matches branch tip
```

## Exit codes

| Condition | Exit |
| --- | --- |
| current, or check unavailable | 0 |
| newer release available | 1 |
| build behind branch tip | 1 |

Doctor's overall exit code is the maximum across all its checks, as today.

## Colour

Unchanged vocabulary: green `✓` current, cyan `⬆` action available, yellow `⚠`
could not check. No new colour is introduced by this feature.

## Compatibility

- The `✓ wfctl <version> — latest` string is unchanged, so existing assertions
  and README examples remain accurate for the common case.
- No consumer gates on doctor's exit code today — verified by repository search
  before FR-006 was accepted. The only readers are README prose and
  `start-session`, which reads the output text.
