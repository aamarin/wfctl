# Overlay boundary spike — #426

## Session 2026-09-22

- Verdict: the boundary holds; the migration does not follow from it
- Question: can Spec Kit execute one wfctl-governed obligation without becoming
  the authority on whether that obligation was satisfied?
- Answer: yes. None of #426's three stop conditions was met.
- Recommendation: the ordering half of #339 should **not** move yet, for a
  reason unrelated to the boundary — `command`, the step type the migration
  needs, cannot name a project-local command.

The spike ran against upstream `fcfc7e8` (`1.0.9.dev0`), the commit
`a-run-cursor-is-execution-state-not-evidence` verified its evidence at,
installed into a throwaway virtualenv and pointed at a throwaway repository on
branch `77-ui-overlay-demo`. Nothing in this repository's own `wfctl.json` was
touched; the fixture is reproduced in full at the end of this file.

### Results

| # | Test | Result |
| --- | --- | --- |
| 1 | Insertion — can an overlay insert `ui-design` at the right position? | Pass |
| 2 | Invocation — can a `command` step dispatch a project-local skill? | **Fail** |
| 3 | Missing command — what happens when it is not installed? | **Fail, worse than expected** |
| 4 | Evidence separation — does wfctl reach `done` from the artifact alone? | Pass, with a qualification |
| 5 | Divergence — do the cursor and wfctl disagree without contradicting? | Pass, exactly as predicted |

### 1 · Insertion — pass

Both mechanisms place the pass where wfctl's ordering puts it. A `slot` declared
in the base at the extension point and filled by `replace`:

```
brainstorm → ui-design → specify → clarify → …
```

and an independent overlay using `insert_before: specify` composed with it
without interfering, giving `brainstorm → ui-design → ui-review → specify`.

Anchor validation is real and refuses an unsatisfiable edit before anything
runs:

```
Error: Invalid workflow: Overlay 'bad-anchor' has invalid edits:
  - Edit 0: anchor 'nonexistent-step' does not match any base step id.
```

That is the property `wfctl.json`'s `before`/`after` graph carries, and it
survives the move intact — which makes test 3's result the sharper one, because
it is the same kind of check and it does *not*.

One operational detail that would cost a day to rediscover: overlays are
resolved only when a workflow is loaded **by installed id**. A local YAML path
short-circuits ahead of the resolver (`workflows/engine.py:941`), so
`specify workflow run ./my-workflow.yml` silently ignores every overlay in the
project. The fixture therefore installs the base at
`.specify/workflows/wfctl-pipeline/workflow.yml` rather than running a file.

### 2 · Invocation — fail

A `command` step dispatches, but it cannot name a command outside the
`speckit.*` namespace. The step was declared as

```yaml
- id: ui-design
  type: command
  command: /pfms-ui-design-workflow
```

and the argv that reached the agent CLI was

```
-p
/speckit-/pfms-ui-design-workflow
```

`SkillsIntegration.build_command_invocation` (`integrations/base.py:1696`)
strips a leading `speckit.` if present and then prefixes `speckit-`
unconditionally. The markdown-agent path (`integrations/base.py:352`) makes the
same assumption with different punctuation, producing `/speckit.<stem>`. This is
not a Claude Code quirk; it is the contract every integration implements. A
`command` step is a *Spec Kit command* step, and its name is a stem within that
namespace rather than an arbitrary slash command.

The working route is the `prompt` step, which sends the string through
untouched — verified, same shim, same fixture:

```
-p
/pfms-ui-design-workflow
```

That is a real escape hatch and it costs the thing the migration was for. A
`prompt` step carries no notion of a named command: nothing validates it,
nothing lists it, `specify workflow info` shows a prompt rather than a
dispatch, and the string is opaque to every tool on both sides. Expressing
wfctl's passes as prompt steps buys sequencing and gives up the declaration.

### 3 · Missing command — fail, and worse than #426 expected

The issue predicted the failure would surface at dispatch. It does not surface
at all. With `/pfms-ui-design-workflow` installed nowhere — no `.claude/skills/`,
no `.claude/commands/`, nothing — the run reported:

```
  ▸ [ui-design] /pfms-ui-design-workflow …
  ▸ [specify] shell …
  …
Status: completed
```

`CommandStep.validate()` (`workflows/steps/command/__init__.py:307`) checks that
`command` is present and is a string, and stops. The only thing that could
notice the command does not exist is the agent CLI's exit code, and an agent
handed an unknown slash command is not reliable about exiting non-zero — the
shim here exited 0, and a real agent asked to run a command it cannot find will
generally answer in prose and exit 0 too.

wfctl catches the same declaration today:

```
✗ wfctl.json:
  - brainstorm.ui-design names /pfms-ui-design-workflow, which is not installed
in this repository
```

So #339's "declared command missing → validation finding" is wfctl's property
and is not inherited by the move, exactly as the issue anticipated.

**Recommendation: it stays in `wfctl check config`, not `doctor`.** Whether a
repository's own declaration names a command that repository has is a fact about
that repository's configuration, which is `check config`'s stated remit and
explicitly not `doctor`'s — `doctor` reports drift between what wfctl installed
and what it now ships, and a `wfctl.json` declaration is neither. Moving it to
`doctor` would also change when it fires: `check config` runs against the
declaration being edited, which is the moment the author can still fix it.

A second finding falls out of the same test and is worth its own line. wfctl and
Spec Kit disagree about what "installed" means. `_is_installed`
(`wfctl/cli.py:5370`) looks for `<layer>/commands/<name>.md`; Spec Kit's Claude
integration installs skills at `.claude/skills/<name>/SKILL.md`. A command
installed the Spec Kit way is invisible to wfctl's check, and the check would
report a finding against a command that is present. That is a `wfctl` bug in any
repository that uses both tools, independent of whether sequencing ever moves.

### 4 · Evidence separation — pass, with a qualification

wfctl reaches `done` from the artifact and nothing else. `build_file_exists_reader`
resolves its path against the feature directory (`wfctl/_evidence.py:234`) and
touches nothing further, and a search of `wfctl/` for `state.json`,
`workflows/runs`, `run_id` and `current_step` finds no reference to Spec Kit's
run state at all. There is no code path by which the cursor could influence a
wfctl reading, so the separation is structural rather than a convention that
could erode.

The qualification is one #426 did not anticipate and it changes how test 5 has
to be staged. A declared pass's reader is **not consulted until its parent
step's own reading is `done`** (`wfctl/_pipeline.py:407`): a pass under a step
that has not finished its own half reports `pending` without its evidence being
read. With `ui-contract.md` written and `brainstorm` still pending, wfctl
reported

```
brainstorm   ○  ← current
  ui-design     ○
```

— the artifact was on disk and unread. Only once `brainstorm`'s own reading was
`done` (a record touched on the branch, then `design.md` written) did the pass
report `done`.

This is deliberate and documented in `_pass_states`' own docstring, and it is
not a defect. But it means the precise claim "wfctl derives a declared pass from
its evidence alone" is too strong: wfctl derives it from its evidence *and* its
parent step's evidence. Nothing about the boundary turns on this — every input
is still an artifact on the branch, and the cursor is still not among them — but
a G1/G2/H design that assumes a pass is independently readable would be wrong.

### 5 · Divergence — pass, exactly as predicted

With the runner paused on `ui-design` and `ui-contract.md` written by hand:

| | Spec Kit's cursor | wfctl's derivation |
| --- | --- | --- |
| reads | `status: paused` · `current_step_id: ui-design` | `ui-design: done` |
| answers | where this run resumes | whether the obligation was met |
| changed by writing the file | no | yes |

Both are correct throughout, and neither is stale. The cursor did not move
because no step was dispatched; wfctl's reading changed because the branch
changed. The record's claim survives contact: they contradict each other only
under the premise that they answer the same question.

### The `skipped` collision

Both meanings were produced in the same fixture, and they are as unlike as the
record says:

| | Spec Kit | wfctl |
| --- | --- | --- |
| produced by | an overlay filled no `slot` | `wfctl step none brainstorm.ui-design` |
| value | `status: "skipped"`, `output: {"slot": "pre-brainstorm"}` | `state: "skipped"`, `claimed: "this change adds no UI surface"` |
| a fact about | the workflow definition — true on every branch it runs on | this branch — a person's judgment |
| carries a reason | no | yes |
| where a reviewer finds it | `state.json`, inside a run directory | `docs/architecture/step-claims/`, in the diff |

The claim also wins over a present artifact: with `ui-contract.md` on disk and
the pass reading `done`, `wfctl step none` moved it to `skipped` and it stayed
there. That is spec edge case 7 behaving as written, and it is the half Spec
Kit has no vocabulary for at all — there is no operation that says "this
extension point exists, applies here, and was deliberately not taken".

Nothing in the fixture conflated the two, because nothing had occasion to: the
two values never meet. They would meet the moment a single view rendered both,
which is what a migration would build.

### Stop conditions

None tripped.

- **Duplicating evidence into Spec Kit's run state** — did not happen and was
  not tempting. The run state records what each step returned; the evidence is
  a file under the feature directory, and no step needed to write the other's
  data.
- **Interpreting the cursor as feature state** — did not happen. wfctl has no
  reader for it.
- **Teaching two systems the same completion predicates** — did not happen.
  Spec Kit knows "dispatched, exit 0"; wfctl knows "artifact present, or claim
  present". Neither predicate is expressible in the other's terms, which is
  uncomfortable in test 3 and reassuring here.

### Recommendation

**Sequencing should not move yet, and the reason is test 2, not the boundary.**

The boundary is fine. Every test that asked whether wfctl can keep owning
evidence while Spec Kit owns execution came back yes, and the divergence case —
the one that would have killed it — behaved exactly as the record predicted.

What came back no is narrower and more damaging to the migration's purpose. A
wfctl pass is a *named command with a declaration attached*, and the only Spec
Kit step type that carries a name cannot carry this one. The choice on offer
today is a `command` step whose name is silently rewritten, or a `prompt` step
that is an opaque string. Neither is a declaration, and moving sequencing to
gain overlays while losing the declaration trades the thing wfctl is for.

Two things would change this answer, and both are cheap to state:

1. Upstream accepting a `command` step that dispatches a non-`speckit` command
   name — a change to `build_command_invocation`'s contract, not to the engine.
2. A `command` step validating that its command is installed, which would also
   close test 3.

Until one of them lands, the recommendation is that G1 and G2 be scoped to the
overlay/ordering mechanism only if they also carry the prompt-step cost
explicitly, and that H not assume a `command` step is available for a
wfctl-governed pass. Filing them stays #421's call.

### Upstream drift, noted rather than acted on

Upstream `HEAD` at the time of this spike is `c31168a7` (`1.0.10.dev0`), three
days after the commit the boundary record cites. In that window
`workflows/overlays/` became `workflows/overlay/` and `workflows/steps/` became
`workflows/step/`. Every path citation in
`a-run-cursor-is-execution-state-not-evidence` is therefore already stale
against `HEAD`, though every *behaviour* it cites still holds. That is the
version-dependency cost the record's own "Considered" section named, arriving
before the migration it was named about.

### Fixture

Base workflow, installed at `.specify/workflows/wfctl-pipeline/workflow.yml`:

```yaml
schema_version: "1.0"
workflow:
  id: wfctl-pipeline
  name: wfctl pipeline
  version: 1.0.0
  description: wfctl's eight-step pipeline expressed as a Spec Kit workflow
  integration: claude
steps:
  - id: pre-brainstorm
    type: slot
    name: pre-brainstorm
  - id: brainstorm
    type: shell
    run: echo "step brainstorm"
  - id: brainstorm-passes
    type: slot
    name: brainstorm-passes
  - id: specify
    type: shell
    run: echo "step specify"
  # clarify, plan, tasks, analyze, decompose, implement follow the same shape
```

Overlay, at `.specify/workflows/overlays/wfctl-pipeline/fill-ui-design.yml` —
a gate, because a declared pass defaults to `review_required` and a gate is what
that maps to:

```yaml
id: fill-ui-design
extends: wfctl-pipeline
priority: 10
edits:
  - replace: brainstorm-passes
    step:
      id: ui-design
      type: gate
      message: "ui-design pass: approve the UI contract before specify"
      options: [approve, reject]
```

The repository's `wfctl.json`:

```json
{
  "verify": [["true"]],
  "steps": {
    "brainstorm": [
      { "name": "ui-design",
        "command": "/pfms-ui-design-workflow",
        "evidence": "ui-contract.md" }
    ]
  }
}
```

Dispatch was observed with a shell script named `claude` placed ahead of the
real CLI on `PATH`, recording its argv and exiting 0. Using the real agent would
have made test 3 unreadable: the question there is what Spec Kit does when the
command is absent, and an agent that improvises an answer supplies one.
