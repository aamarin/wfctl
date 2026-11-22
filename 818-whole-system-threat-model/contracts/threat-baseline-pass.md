# Contract: the `threat-baseline` pass

What a user sees from `wfctl status`, `wfctl status --json`, and `wfctl step none` once this feature ships.

## `wfctl status`, paused

```
brainstorm   ▶  ← current
  architecture      ●
  threat-baseline   ▶  THREAT_MODEL.md isn't committed at the repository root
  software-design   ○
  design-doc        ○
…
next: /threat-baseline
```

The row shows the missing file as a display line, not as the step's reason. A reason would hold the brainstorm step, and a held step routes to `/speckit.brainstorm`, which doesn't build the file. A display line lets the pass route to its own command, the same way `plan-review` and `store-specs` do (#501).

As a result, the paused row shows no remedy block, so the `step none` line isn't on screen before `spec.md` exists. It still shows on the past-`spec.md` warning below.

## `wfctl status`, git couldn't answer

```
  threat-baseline   ▶  git can't see whether THREAT_MODEL.md is committed
```

When the failure is in listing the branch's records rather than reading `HEAD`, the row shows `GIT_UNANSWERED_REASON` and the remedy is `GIT_UNANSWERED_HELP`, as on the architecture pass. Both git rows keep a reason, so they hold the step. Running a command doesn't fix a missing trunk, since the trunk is the user's setting.

## `wfctl status`, skipped

```
  threat-baseline   ○  skipped — no record on this branch has a threat model
```

## `wfctl status --json`

The pass appears in the brainstorm step's `sub_steps`, in this order, with the existing fields. No field is added to the payload, and `wfctl/contracts/status-payload.json` doesn't list pass names, so it doesn't change. `tests/pipeline_payload_snapshot.json` does carry the brainstorm passes and gains the new one.

```json
{ "name": "threat-baseline", "state": "in_progress", "command": "/threat-baseline" }
```

Past `spec.md`, a missing baseline shows in the top-level `warnings` list:

```json
{ "step": "brainstorm", "pass": "threat-baseline",
  "reason": "THREAT_MODEL.md isn't committed at the repository root",
  "remedy": "…" }
```

The remedy labels the `step none` line as the user's, because `step none` has no check on who runs it and an unattended agent acts on remedies. The `threat-baseline` skill and wrapper say the same, and no shipped skill grants the command (FR-007b).

```
  Build and commit it:
      /threat-baseline
  If this repository keeps its baseline elsewhere, the user can say so.
  This is the user's decision, not the agent's:
      wfctl step none brainstorm.threat-baseline --reason "<why>"
```

## `wfctl step none`

```
$ wfctl step none brainstorm.threat-baseline --reason "Our baseline lives in the security team's wiki."
✓ Recorded: brainstorm.threat-baseline does not apply — "Our baseline lives in the security team's wiki."
  Put the reason in the PR body.
```

`--context` is refused for this pass, as for every pass except `brainstorm.software-design`.
