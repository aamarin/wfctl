# Quickstart: check an open change

## Turn it on

Two files, once per repository.

Declare the field reads in the tracker config. `install-skills` ships this for
the GitHub config, so a repository on the shipped tracker gets it for free:

```json
"verbs":   { "fields": ["gh","issue","view","{id}","--json","labels,assignees,milestone,projectItems","--jq","…"] },
"changes": { "fields": ["gh","pr","view","{id}","--json","labels,assignees,milestone,projectItems,reviewRequests","--jq","…"] }
```

Declare what your repository requires, in `wfctl.json`, which is committed:

```json
{ "change_check": ["assignees"] }
```

Leave the key out entirely if the issue is the only expectation you want. That is
the right answer for a repository whose triage you do not control.

Check the config parses:

```bash
uv run wfctl tracker-check github
```

## Run it

```bash
uv run wfctl change check 301
```

A change that is missing things:

```
⚠ labels        empty; issue has authority:notify
⚠ projectItems  empty; issue has wfctl
⚠ assignees     empty; required by wfctl.json
exit 1
```

The same change once the sidebar is filled:

```
✓ labels        enhancement, P1
✓ assignees     aamarin
✓ projectItems  wfctl
exit 0
```

A repository that requires nothing, whose issue carries nothing:

```
ℹ 305: nothing to check — wfctl.json requires no fields, and the issue has none set
exit 0
```

`ℹ` never means the check passed. It means there was no verdict to give.

## Where it runs from

`opening-a-change` Step 6 invokes it, the same way Step 5 invokes
`wfctl check-body`. The change identifier is the one that step just created, so
the branch's issue and the change agree by construction.

Run it by hand any time against an open change on the current branch.

## What it does not do

It never edits anything. It reads two records and prints a verdict; filling the
sidebar is still `gh pr edit`, which Step 6 already covers.

It says nothing about a field your repository has not required and your issue
does not carry. A repository that never uses milestones never sees the word.

## Exercising it for real

The suite cannot test this feature's actual claim — it can assert the comparison
reports what it is handed, never that the command fires against a real change
with a real empty sidebar. The exercise:

1. Open a throwaway change with nothing set.
2. Run the check; confirm it names every unset field.
3. Fill them.
4. Run it again; confirm it goes quiet.

Step 4 is the half that matters. An exercise that stopped at step 2 has not shown
the check can ever pass, which is exactly what a noisy check fails.
