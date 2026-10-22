---
status: proposed
---

# Each CI run on `main` gets its own concurrency group, and tag jobs queue in one group

## Context

`ci.yml` puts every run for one ref into one concurrency group, and cancels a
running run only on pull requests. The comment above it says this keeps a run
for every merge to `main`, but that isn't how GitHub treats the group. GitHub
lets one run wait in a group at a time, and cancels the waiting run when a
newer one arrives, whatever `cancel-in-progress` says.

Previously, this looked safe because `cancel-in-progress` was off for `main`.
Currently, when three merges reach `main` close together, the middle run is
cancelled before it starts. If that run is the release merge, its tests never
run on the release commit, and the tag waits for whichever later run passes.
That later run still tags the right commit, because `tag_release.py` finds the
release commit by its subject. The tag is just gated on a different commit's
checks, and it lands later than it should.

The tag job also relies on the group today without saying so. Because runs on
`main` never overlap, two tag jobs never run at the same time, and they never
both try to push the same tag.

## Verified

- `ci.yml` sets `group: ${{ github.workflow }}-${{ github.ref }}` and
  `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`. Both lines
  are unchanged since the file was created.
- GitHub's concurrency docs say: "By default, any existing `pending` job or
  workflow in the same concurrency group will be canceled", and
  `cancel-in-progress: true` is what "also" cancels a running one.
- The same docs describe `queue: max`, which lets up to 100 runs wait in a
  group, processed in first-in, first-out order. `queue: max` together with
  `cancel-in-progress: true` is a validation error.
- The docs' own example uses `github.run_id` in the group key as a fallback
  for a run with no head branch.
- `tag_release.py` finds the release commit with `git log --no-merges --grep`
  on the subject `chore(release): cut <version>`, and does nothing when the
  version is already tagged and released.

## Assumed

- `queue` is accepted on a job-level `concurrency` block, as the docs show for
  the workflow level. If it isn't, the workflow fails validation, and the pull
  request's own CI run shows that before anything merges.

## Direct baseline

Keep one group per ref, and turn on `queue: max` for the whole workflow, so
every run on `main` waits its turn and none is cancelled. This adds no new
group. It can't keep cancelling superseded pull request runs, though, since
`queue: max` and `cancel-in-progress: true` can't be set together. Every push
to a pull request would then queue behind the run it replaced.

## Decision

The workflow group is unique per run on `main` and stays per ref on pull
requests:

```yaml
group: ${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.ref || github.run_id }}
```

Pull request runs still cancel the run they replace. Runs on `main` no longer
share a group, so none of them waits behind another or is cancelled by one.

The tag job gets a group of its own, `release-tag`, with `queue: max`. Tag jobs
then run one at a time in the order they were queued, which keeps the ordering
the old workflow group gave them, and none of them is cancelled while it waits.

## Diagram

```
        baseline: one group, queue: max          decision

        ┌──────────────────────────┐   ┌───────────────┐  ┌──────────────────┐
        │ workflow group per ref,  │   │ workflow group│  │ release-tag group│
        │ queue: max               │   │ per PR ref, or│  │ queue: max (new) │
        └───▲──────────────▲───────┘   │ per run on    │  └────────▲─────────┘
            │ waits in     │ waits in  │ main          │           │ waits in
            │              │           └───▲───────▲───┘           │
            │              │               │ joins │ joins         │
   ┌────────┴─────┐ ┌──────┴───────┐ ┌─────┴────┐ ┌┴───────────┐ ┌─┴────────┐
   │ PR run       │ │ main run     │ │ PR run   │ │ main run   │ │ tag job  │
   │ (no longer   │ │ (tag job     │ │ (cancels │ │ (runs at   │ │ (one at  │
   │ cancels)     │ │ inside)      │ │ previous)│ │ once)      │ │ a time)  │
   └──────────────┘ └──────────────┘ └──────────┘ └────────────┘ └──────────┘
```

No boundary in force runs between these components, so neither graph draws a
divider. The change this is built to absorb is a new job on `main` that has to
run in order, as the tag job does. In the baseline, every job on `main` is
ordered, including the test jobs that don't need it, and pull requests lose
their cancellation. In the decision, a job that needs ordering joins a named
group, and the rest run at once. The decision has one group more, and it is
attached only to the job whose result depends on order.

## Considered

- One group for the whole workflow with `queue: max`, per Direct baseline. It
  is the smallest change. We didn't choose it because it gives up cancelling
  superseded pull request runs, and a pull request pushed three times would run
  CI three times in a row.
- Drop the workflow-level group entirely and keep only the tag job's group. It
  is simpler for `main`. We didn't choose it because pull requests would also
  lose their cancellation, which is the reason the group exists.
- Make the workflow group unique on `main` and leave the tag job without a
  group, so `tag_release.py` handles two runs at once. We didn't choose it
  because two tag jobs would both try to push the same tag, and one of them
  would fail red on `main` for a race rather than a fault.

## Consequences

Two merges close together now run their test jobs at the same time, which uses
more runner minutes at once but finishes sooner. Every merge to `main` gets its
own test run, the release merge included.

The `release-tag` group holds up to 100 waiting tag jobs. A tag job takes
seconds, so reaching that limit would take far more merges than this repository
sees.

## Verification

The suite doesn't run GitHub Actions, so this is checked on GitHub:

1. The pull request's own CI run passes workflow validation, which shows the
   group expression and the job-level `queue` are accepted.
2. Runs on the pull request still cancel the run they replace when a new
   commit is pushed.
3. After merge, two merges to `main` in quick succession both run to
   completion, and neither shows as cancelled.

## Log

- 2026-10-22  proposed  — #605. A run waiting on `main` could be cancelled
  before the release commit's tag job ran, and this records how runs on `main`
  are grouped instead.
