# Repairing what `doctor` reports

Open this file from `start-session` step 1 when `wfctl doctor --session` prints
anything other than a ✓. A green run needs none of it.

## A layer behind or drifted

**If it reports any layer's skills behind or drifted, bring them level now.**
Doctor names the layer on each finding and prints the command that repairs
*that* layer. **Run what it printed, once per reported layer, with `--prune
--yes` appended.** Those two flags are this step's, not doctor's: doctor prints
the repair for the drift and no policy on top of it, and the policy here is that
the refresh runs unattended. So the two most common lines are:

```bash
wfctl install-skills --prune --yes                   # a `base` finding
wfctl install-skills --prune --yes --agent claude    # a `claude` finding
```

**The printed command is the part that governs; those two are only its common
shapes.** A layer installed from a source someone named is repaired by a line
carrying `--from <that source>`, and running the bare form instead does not fail.
It succeeds, reinstalls the release over the branch being tested, and reports
the layer green. That is a repair destroying the thing it was called to check,
and nothing downstream would say so.

Copy the printed path as printed. It is quoted when it needs to be, and a path
carrying a space or a bracket is one this step has already got wrong.

Then run `wfctl doctor --session` again and check it is green before moving on.
Without the second run the report says "refreshed" over a tree that is still
drifted: a layer is rewritten only when it is asked for by name, so a run that
omits `--agent` leaves that layer exactly as stale as it found it.

`--prune` also clears paths a past install left behind when they were renamed
upstream, and doctor prints the exact command per layer. Copy that, because a
bare `install-skills --prune` diffs only the base layer and leaves a `.claude/`
path where it found it.

## A refusal from `install-skills`

**A refusal is not a repair that failed halfway. It is one that never ran.**
`install-skills` exits 1, having copied nothing, when the repo's
`.claude/settings.json` no longer carries a managed permission rule wfctl
recorded:

```
✗ .claude/settings.json no longer carries Bash(cd:*), which wfctl installed.
  Nothing was installed. …
```

So the skills drift the repair was called for is still there, and the ✓ this
step is watching for will not arrive. Report the refusal in step 7 verbatim, and
say that the layers named in the finding are still stale.

**Do not run `--force` to clear it.** That flag re-asserts the rule *and* records
it as wfctl's, so a later `uninstall-skills` deletes a line the repo may have
written itself. That is a transfer of ownership, and it is the user's call
rather than the agent's. `wfctl doctor` is green by design in this state, so the
refusal is the only thing that will say it, and a session that clears it quietly
leaves nobody who knows.

## The two `ℹ` notices

`--prune` reaches only paths still on record. Doctor's dim `ℹ` lines are another
matter, and since #178 there are two of them. They share a marker and both leave
the exit code alone, but what to do about them is opposite, so tell them apart by
what they say.

`ℹ … not on record under a directory wfctl installs into` lists paths in wfctl's
destinations that it cannot show are its own, which is what a skill you placed
there yourself looks like. **Delete nothing on the strength of that block.** Its
own line says wfctl is leaving the path alone.

`ℹ no agent layer — .agents/ only` is the one to act on. It reports what is on
record now, that this tree has the base layer and no agent layer, not how it got
that way. `WFCTL_AGENT` unset at `workmux add` is the usual cause.

There are two repairs and the notice names only one of them. Setting
`WFCTL_AGENT` in a shell profile fixes the *next* worktree. It installs nothing
into this one, and doctor goes on printing the notice until something does. What
fixes this one is:

```bash
wfctl install-skills --prune --yes --agent "$WFCTL_AGENT"
```

Run it only when that variable is already set. The environment naming the agent
is the sanctioned source under `no-hardcoded-agent`, and a name you picked
yourself is not.

**Append `--from <path>` when `.wf-skills-manifest.json` records a `source` for
the *base* layer.** Installing an agent layer rewrites base as well, asked for or
not. So the bare form reinstalls the release over the checkout being tested,
drops the recorded source on its way out, and leaves doctor reporting green
against a bundle nobody chose. That is the `--from` hazard above, met from the
side where it is hardest to see: base was *current*, so doctor printed no repair
line for you to copy the flag from.

With `WFCTL_AGENT` unset there is nothing here for you to run. The profile is the
user's to edit, like the tool upgrade below, so surface it and do not write it.
That also makes this the one line the "run doctor again and check it is green"
rule does not reach. It will still be there, so carry it to step 7 rather than
treating the step as unfinished.

## Running unattended

`--yes` is what keeps the repair non-interactive, and it is not free. It skips
the prompt that would otherwise list pre-existing files being overwritten, which
are files *not* on wfctl's record and possibly someone's own. They are backed up
and the run says where, so this is recoverable, not silent. If that is not a
trade you want made unattended, drop `--yes` and answer the prompt.

## The same wfctl for both

Run `doctor` and `install-skills` through the **same** wfctl. They compare the
installed tree against the bundle carried by whichever one you invoked, so two
different wfctls disagree permanently, and whichever installed last is the one
that reports clean. In most repos there is only one and this costs you nothing to
honour. In a repo that develops wfctl itself there are two, such as a bare
`wfctl` and `uv run wfctl`. That project's own AGENTS.md says which to use, and
it governs.

## The tool behind

The **tool** being behind is a different call and stays the user's: `uv tool
install --upgrade …` changes what is installed on the machine, not what this
repo holds. Surface it as a one-line heads-up. It is not a blocker.
