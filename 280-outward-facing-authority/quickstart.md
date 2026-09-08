# Quickstart: notify authority

## Grant it, then walk away

```bash
# In the worktree, before starting the agent:
uv run wfctl start --allow-notify

# Or during triage, on the issue — no terminal needed:
gh issue edit 280 --add-label authority:notify
```

Either place grants it. Check what took:

```bash
uv run wfctl status
#280  280-outward-facing-authority
may notify people — you allowed it on issue #280
```

## Take it away

```bash
uv run wfctl start --deny-notify        # explicit no; beats a label
gh issue edit 280 --remove-label authority:notify   # back to silent
```

A deny beats a label. Removing the label only returns the issue to silent — if
someone granted locally, that still stands.

## The default, which is the path most runs take

```bash
uv run wfctl status
will not notify anyone — nobody has allowed it for this work
```

Nothing granted, nothing said no. The run will decline anything that notifies
people and report that it declined.

## See what a run did with it

```bash
grep notify-action "$(uv run wfctl state-dir)/events.jsonl"
{"ts":"2026-09-08T14:07:02Z","event":"notify-action","action":"issue-create","count":6}
{"ts":"2026-09-08T14:07:44Z","event":"notify-action","action":"push","count":1}
```

The event log is the record. Everything else — the session summary, the PR body
— is a rendering of it.

## Verifying the refusal, which is the half that gets skipped

An exercise where the grant was always present has not tested this feature.

```bash
rm -f "$(uv run wfctl state-dir)/notify.json"
gh issue edit 280 --remove-label authority:notify
# then run the step that would create issues, and confirm:
#   - the tracker is unchanged
#   - the output names the missing grant
#   - the run continues rather than erroring
```
