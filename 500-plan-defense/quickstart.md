# Quickstart: plan-walkthrough

Run these on a scratch branch after implementation, from this repository's
working tree. Each block names the story it proves.

## Install and declare (Story 5)

```bash
uv run wfctl install-skills --prune --yes --agent claude
uv run wfctl check config        # "✓ wfctl.json: 1 pass under 1 step", exit 0
uv run wfctl status              # plan-walkthrough listed under plan
```

## Unattended skip (Story 2)

```bash
uv run wfctl start --auto-approve
uv run wfctl status --json       # plan-walkthrough: skipped, needs_person true
git status --short               # no new file
```

## Refusal while auto-approve is on (Story 3, scenario 2)

Type `/plan-walkthrough`. It prints the refusal from
`contracts/plan-walkthrough-command.md` and writes nothing.

## A person comes back (Story 3, scenario 1, and Story 1)

```bash
uv run wfctl start --no-auto-approve
uv run wfctl status --json       # plan-walkthrough: in_progress
```

Type `/plan-walkthrough`, answer the questions, and then check:

```bash
ls "$(uv run wfctl state-dir)/walkthrough/"          # plan-<date-time>.md
cat <FEATURE_DIR>/plan-walkthrough.md                # Mode, Walked through, Date only
uv run wfctl status --json                       # plan-walkthrough: done
```

## The marker holds after auto-approve returns (Story 3, scenario 3)

```bash
uv run wfctl start --auto-approve
uv run wfctl status --json       # plan-walkthrough: done, not skipped
```

## Change mode (Story 4)

On a branch with commits, type `/plan-walkthrough change` and answer.
`change-walkthrough.md` names the `HEAD` commit, and a dirty tree gets the
uncommitted-changes line.
