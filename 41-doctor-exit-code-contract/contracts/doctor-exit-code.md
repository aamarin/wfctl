# Contract: `wfctl doctor` exit codes and check signatures

The interface this feature defines. Two audiences: anything that runs `doctor`
and reads its exit code, and anyone adding a sixth check later.

## Command contract

```
wfctl doctor
```

| Exit code | Meaning |
| --- | --- |
| `0` | No check found drift. Includes checks that could not determine an answer. |
| `1` | At least one check found drift, and it was still present when the run ended. |

The code describes the repository's state **when the run finishes**, not what was
observed along the way. A check that offers a fix, has it accepted, and applies it
leaves nothing found — so a run that repaired its only finding exits `0`.

`doctor` always runs every applicable check before exiting. A finding never
short-circuits the remaining checks, so one run reports everything wrong at once.

### What `0` does and does not promise

`0` means *doctor found nothing wrong*. It does **not** mean *everything was
verified*. A check that could not reach the network, or found no recorded value to
compare against, contributes `0` while printing why.

This is deliberate and is the weaker of the two available guarantees. The
alternative — treating "could not determine" as failure — makes a brief network
outage fail a build that has no repository problem. Callers needing the stronger
guarantee must read the output, not the code.

## Check signature contract

```python
def _check_<name>(repo_root: Path) -> bool:
    """Report <what>. Return True if drift was found and still stands."""
```

| Return | Condition |
| --- | --- |
| `True` | Drift found, and still present when the check returns. |
| `False` | No drift found. |
| `False` | Could not determine — offline, unreadable, or nothing recorded to compare. Must print why. |
| `False` | Drift found and repaired during this run. |

`doctor_cmd` ORs each result into `exit_code`. Adding a check means adding one
call to that sequence; there is no registry to enlist in.

### Rules for a new check

1. **Return `False` when you cannot tell.** Never let an unreachable network or an
   unreadable file contribute `True`. Say so in the output instead — a silent
   `False` is indistinguishable from a pass.
2. **Print before returning.** The return value carries no message. A `True` with
   no output fails a build with no explanation of what to fix.
3. **Stay silent when there is nothing to report.** A check that always prints
   trains the reader to skim past the one that matters.
4. **Report only.** Checks do not delete or move files. The one check that writes
   does so only after an interactive confirmation, and never without a terminal.
5. **Return early on absence.** A repository that never adopted the thing being
   checked is not drifting. `_check_workmux_hook` returns before anything else
   when there is no `.workmux.yaml`.

## Excluded from this contract

`_check_wfctl_version` keeps its `int` return for now. It already contributes an
exit code correctly and is not part of the defect; it is being rewritten end to
end by separate work (#21, #35 B1) and converts to `bool` there, as the last step
on code that work has already replaced. Converting it here would edit the exact
lines that rewrite replaces.

## Output vocabulary

Unchanged by this feature; recorded because new checks must match it.

| Marker | Meaning | Exit contribution |
| --- | --- | --- |
| `✓` green | Checked, current | `0` |
| `⬆` cyan | Behind; an upgrade or re-install is available | `1` |
| `⚠` yellow | Drift found, or could not determine | `1` or `0` — see above |
| `✗` red | Error: unreachable, or the tool's own install is broken | `1` |

`⚠` is the one marker that maps to either code. That is a consequence of the
could-not-determine rule, not an inconsistency: both cases warn a person, and only
one of them is a repository problem.

## Behaviour by scenario

| Scenario | Output | Exit |
| --- | --- | --- |
| Clean repository, network reachable | `✓` lines only | `0` |
| Teardown hook not wired, offer declined | `⚠` + remedy | `1` |
| Teardown hook not wired, offer accepted and applied | `⚠` + `✓` wired | `0` |
| Teardown hook not wired, no terminal | `⚠` + "run from a terminal" | `1` |
| Version lookup fails (offline) | `⚠` couldn't check | `0` |
| Layer recorded before content hashing | `⚠` unmeasurable | `0` |
| Abandoned entry present | `⚠` naming each entry | `1` |
| Abandoned directory holding N files | `⚠` naming it once | `1` |
| Nothing installed | early return, no abandoned-entry scan | unchanged |
| Bundled trees missing from the wfctl install | `✗` | `1` |
| Not in a git repository | `⚠` + skip repo checks | version check only |
