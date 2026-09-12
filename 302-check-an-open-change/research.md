# Research: check an open change

No `NEEDS CLARIFICATION` markers entered the plan. This records what was checked
against the code rather than assumed, and the three prior art decisions the
implementation follows instead of re-deriving.

## What the tracker actually returns

`gh pr view 301 --json labels,assignees,milestone,projectItems,reviewRequests`
returns a list of **objects**, not of strings:

```json
{"labels":[{"id":"LA_kwDOTX0a188AAAACrnFbzg","name":"enhancement",
            "description":"New feature or request","color":"a2eeef"}], …}
```

`gh issue view 280 --json labels,assignees,milestone,projectItems` returns the
same key names with the same object shapes, so both sides of the comparison have
this. Unset reads as `"milestone":null` and `"projectItems":[]`, never as a
missing key.

Comparing objects would mean knowing that `name` identifies a label, `login` an
assignee and `title` a board item — GitHub's vocabulary re-entering wfctl through
the comparison. `docs/architecture/design/302-the-tracker-flattens-its-own-
shapes.md` resolves it: the verb is contracted to return scalars, and the tracker
flattens with `--jq`, which `gh` already ships.

## Prior art this follows rather than re-deriving

**The capture helper already exists.** `wfctl/_tracker.py:365`
`read_issue_labels` returns `(value, detail)` — `None, None` when nobody was
asked, `None, detail` when the answer did not arrive — with a 15-second bound
whose comment reads *"Unbounded, it would hang the command that every session
opens with."* `read_fields` generalises exactly this: same return shape, same
bound (FR-015), `json.loads` where that one splits lines. Its docstring also
records the trap to avoid: an earlier version parsed `gh`'s own `view` output and
*"read every other backend as having no labels, silently."*

**The pure/impure split is `check-body`'s.** `wfctl/_shape.py` and
`wfctl/_body.py` are pure string functions; the one piece of state `check-body`
needs — the verification record — is read by `_verification_finding()` in
`cli.py`, and that function's docstring says why: *"the state lives here, in the
command's own module, and neither of them learns what a git repository is."*
`_change.py` takes the same shape.

**The verb table already rejects an undeclared verb.** `wfctl/_tracker.py:42`
`ALLOWED_CHANGES = {"list": set(), "view": {"id"}}`, and `_check_section` rejects
anything outside it. So a backend that declares its own `changes.check` is
already refused today, with no new code — which is what makes `check` safe to
claim as a wfctl-owned verb on `wfctl change`.

## Verified against the repository

| Claim | How it was checked |
| --- | --- |
| `.agents/` is gitignored, `wfctl.json` is tracked | `git check-ignore -v` on both |
| `_tracker.dispatch` prints stdout and returns an exit code, so it cannot feed a parser | read `wfctl/_tracker.py:320-345` |
| `wfctl change` is a pure passthrough — every verb goes to the config | read `cli.py` `change_cmd` |
| #280 carries `authority:notify`; #301 carries `enhancement, P1` | `gh issue view 280`, `gh pr view 301` |

That last row is why the comparison is a set difference rather than an emptiness
test. #301's sidebar is filled today and still does not carry its issue's label,
so an emptiness test would report it clean — green-lighting the exact change that
motivated the issue, one step later than before.

## Still assumed

| Bet | What would falsify it |
| --- | --- |
| Adding `fields` to `ALLOWED` and `ALLOWED_CHANGES` is additive for configs in the wild | `wfctl tracker-check github` failing against an unmodified config |
| No existing test pins `change_cmd`'s passthrough shape against a wfctl-owned verb | the suite |
| `gh`'s `--jq` is present in whatever `gh` a consumer runs | a build without it; mitigated because a tracker needing more can write a script, as this repo's `create` verb already does |
