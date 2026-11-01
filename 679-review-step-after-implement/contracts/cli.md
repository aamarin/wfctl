# CLI contract: Review step after implement

## `wfctl spec none --reason "<reason>"`

Records that this branch's change needs no spec. Run it on an issue branch before any code.

Success, exit 0:

```
✓ Recorded: no spec needed — "No behavior change: … No significant design decision: … No ownership change: …"
  /…/wfctl-specs/679-example/exceptions/spec.md
  Put the reason in the PR body.
```

Refusals, exit 1, nothing written:

```
✗ --reason cannot be empty: answer each of the three spec questions.
✗ "<why>" is a placeholder, not a reason — answer each of the three spec questions.
✗ spec.md exists in this branch's spec folder, so the change already has a spec. Delete it first if the change needs none.
```

The third line names whichever of `design.md`, `spec.md`, `plan.md`, or `tasks.md` it found first, in that order.

A second run replaces the reason, as `arch none` does.

## `wfctl status`

After implement, before any review:

```
implement    ●
  store-specs       ●
review       ▶  ← current
                security, code: not reviewed yet (4 commits)
next: /fanning-out-code-review
```

After a review, one more commit, and `wfctl verify`:

```
review       ▶  ← current
                security, code: 1 commit unreviewed since 3f2a1c9
next: /fanning-out-code-review
```

Groups in different states share the step's line, one part each, such as `security: not reviewed yet (4 commits); code: 2 commits unreviewed since 3f2a1c9`, since the console prints a step's note on the step's own row. A branch a person signed off, with no completed run, counts from the signed-off commit and reads the second form.

A group past its round cap, or `review.rounds` of 0. The step blocks, so `auto` is false. The step line shows the reason, and the remedy follows it:

```
review       ▶  security has used its 3 review rounds, so a person has to sign off  ← current
  Ask the user to run `wfctl review sign-off` in their own terminal.
```

Every group has reviewed HEAD:

```
review       ●
Story complete — open PR or run `/end-session`.
```

A review config that can't be read:

```
review       ▶  can't read the review config: wfctl.json at 8d04e17: <problem>  ← current
  fix review in the wfctl.json the error names, then run wfctl check config
```

The problem names the file it came from, either the trunk's `wfctl.json`, such as `wfctl.json at origin/main`, or the branch's own at a commit, as above. The remedy is the same for both.

A trunk error gets no separate remedy line, since its message already names the fix, such as `can't find the trunk branch; set trunk in wfctl.json`.

A branch with a "no spec" answer in effect, before its first commit:

```
brainstorm … decompose  –  skipped: no spec
implement    ▶  no commits on this branch yet  ← current
  Make the change and commit it, then run `wfctl verify`.
review       ○
next: wfctl verify
```

The same branch after its first commit, before `wfctl verify`:

```
brainstorm … decompose  –  skipped: no spec
implement    ▶  unverified — run `wfctl verify`  ← current
review       ○
next: wfctl verify
```

A branch whose commits have all reached the trunk, such as one whose PR merged, reads the first form again. Nothing on disk tells "never started" from "already merged", and a merged worktree is usually removed.

A "no spec" answer beside a spec artifact:

```
⚠ brainstorm: exceptions/spec.md says no spec, but design.md exists
  rm /…/679-example/exceptions/spec.md
```

## `wfctl status --json`

`version` is `"1.4"`. `steps` has nine entries. `no_spec` is always present, as `{"reason", "path"}` or `null`. Every other key is unchanged.

On a no-spec branch, each of the seven skipped steps still lists every pass in `sub_steps`, each reading `skipped`. The `artifacts written` fact reads `n/a` with the detail `no spec recorded`.

## `wfctl check config`

A `steps.review` key in `wfctl.json` is a finding: `'review' takes no declared passes; its groups are set under the review key`.

## `wfctl step complete implement`

Accepted while the current step is `implement`, `review`, or none. Refused otherwise, with the message it prints today.

## `wfctl report-block <action>`

When the pipeline is complete, the block holds `implement`, as it does today.

## `wfctl check-body`

With a "no spec" answer in effect, a body that doesn't carry the reason gets one finding. An answer that a spec artifact outranks asks for nothing:

```
the no-spec reason isn't in the body: "<reason>"
```

## The worktree guard

Unchanged. It refuses `gh pr create` and `gh pr merge` on the same commits the review row counts, since both call `pending_at_head`. Its other refusals, such as a level-2 record still `proposed`, stay outside the review row, so the guard can refuse a PR while `review` reads done.
