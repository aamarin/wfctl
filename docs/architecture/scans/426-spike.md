# Overlay boundary spike — #426

## Session 2026-09-22

- Verdict: inconclusive
- Question: can Spec Kit execute one wfctl-governed obligation without becoming
  the authority on whether that obligation was satisfied?
- Answer: the boundary holds. None of #426's three stop conditions was met.
- Recommendation: the ordering half of #339 should **not** move yet, for two
  reasons unrelated to the boundary — `command`, the step type the migration
  needs, cannot name a project-local command; and an overlay cannot anchor to a
  wfctl pass that has no Spec Kit step, which is every built-in pass.

**`inconclusive`, not `satisfied`, and the reason is clause 1 of #426's "Done
when".** That clause reads "one pass runs end to end under Spec Kit with wfctl
judging it", and no run in this document does. Dispatch was observed against a
shell shim standing in for the agent CLI, and the `ui-contract.md` that tests 4
and 5 turn on was written by hand rather than produced by a dispatched step. The
instrument was chosen deliberately and is defended in *Fixture* below; what it
cannot do is establish that clause. The other two clauses — five written answers
and a recommendation on #339 — are met.

So every finding here is about the *mechanism*, measured directly, and none of
it rests on a pass having run to completion. That is enough to price the
migration and not enough to call the spike's own gate satisfied.

The spike ran against upstream `fcfc7e8` (`1.0.9.dev0`), the commit
`a-run-cursor-is-execution-state-not-evidence` verified its evidence at,
installed into a throwaway virtualenv and pointed at a throwaway repository on
branch `77-ui-overlay-demo`. Nothing in this repository's own `wfctl.json` was
touched. Every fixture the tests below refer to is reproduced at the end of this
file.

### Results

| # | Test | Result |
| --- | --- | --- |
| 1 | Insertion — can an overlay insert `ui-design` at the right position? | Pass for placement, **Fail for ordering** |
| 2 | Invocation — can a `command` step dispatch a project-local skill? | **Fail** |
| 3 | Missing command — what happens when it is not installed? | **Fail, worse than expected** |
| 4 | Evidence separation — does wfctl reach `done` from the artifact alone? | Pass, with a qualification |
| 5 | Divergence — do the cursor and wfctl disagree without contradicting? | Pass, exactly as predicted |

### 1 · Insertion — placement passes, ordering fails

Two different questions hide in "at the right position", and they come apart.
**Placement** is whether an overlay can put a step at a named point in the
workflow. **Ordering** is whether it can express the position wfctl already
expresses — `wfctl.json`'s `before`/`after` graph, which positions a declared
pass relative to *any* sibling under the step. Placement passes. Ordering does
not.

Placement first. A `slot` declared in the base at the extension point and filled
by `replace`:

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

Now ordering, which the first run of this test never reached because the
fixture's `wfctl.json` declared no `before`/`after` at all. Measured since, both
sides, same fixture.

wfctl's half works and all four of its properties are real. A declared pass
positioned ahead of one of wfctl's *own* passes is accepted and ordered —
`before: architecture`, rendered with `--all` because the branch still carries a
claim from test 5:

```
brainstorm   ●
  ui-design     –  claimed: this change adds no UI surface
  architecture  ●
  design-doc    ●
```

and the three ways a graph can be wrong are each a `check config` finding rather
than a silent drop:

```
✗ wfctl.json:
  - brainstorm.ui-design names sibling 'nonexistent-pass', which is not declared
under brainstorm
  - brainstorm.ui-review names itself as a sibling
```

```
✗ wfctl.json:
  - brainstorm: the stated order cannot be satisfied — architecture, design-doc,
ui-design, ui-review
```

The overlay's half cannot express that. An overlay anchors to a **base step
id**, and wfctl's built-in passes are not steps — `brainstorm` ships
`architecture` and `design-doc` as sub-steps of one pipeline step
(`wfctl/_pipeline.py:103-110`), and the workflow has a single `brainstorm` step.
So the edit wfctl accepts is the edit Spec Kit refuses:

```
Error: Invalid workflow: Overlay 'order-before-architecture' has invalid edits:
  - Edit 0: anchor 'architecture' does not match any base step id.
```

The remedy works and is worth pricing rather than dismissing. Declaring each
built-in pass as its own step in the base workflow makes the anchor resolve, and
the insertion lands where wfctl puts it:

```
  Steps (13):
    → brainstorm [shell]
    → ui-design [command]
    → architecture [shell]
    → design-doc [shell]
    …
```

What it costs is that the Spec Kit workflow now carries a copy of wfctl's
built-in pass model, by hand, kept in sync by nobody. wfctl adding a pass to a
step is then a change in two repositories, and a base workflow that has drifted
produces an anchor error at load rather than a wrong order at runtime — which is
the good failure mode, but it is still a second place the same structure is
written down.

That is not stop condition 3: what is duplicated is wfctl's *structure*, not its
completion predicates, and nothing here teaches Spec Kit when a pass is
satisfied. It is close enough to the line to be worth naming for #421, and it is
the second independent reason under *Recommendation* below.

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

`CommandStep.validate()` (`workflows/steps/command/__init__.py:307`) type-checks
the step's fields — `command` present and a string among them — and performs no
existence check on the command it names. That is the structural half, and it is
proven: there is no code path in Spec Kit by which a missing command becomes a
validation finding.

The run-level half is weaker, and the two are worth keeping apart. **Measured:**
the shim exited 0, Spec Kit consulted nothing else, and the run reported
`completed`. **Not measured:** what a real agent does when handed a slash
command it cannot find. The shim exits 0 by construction, so this fixture cannot
answer that, and the earlier draft of this section asserted that a real agent
would generally answer in prose and exit 0 too. That is a claim about agents in
general and nothing here establishes it.

It matters which one you carry forward. If the structural half is the whole
finding, a `command` step never notices a missing command and wfctl's own check
is the only one there is. If a real agent does reliably exit non-zero, the gap
narrows to a bad error message. The first is established; the second is open,
and cheap to settle with one run against a real CLI.

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

A second finding was noticed during this test and is **not** conditional on Spec
Kit, which is how an earlier draft of this section scoped it. `_is_installed`
(`wfctl/cli.py:5354-5373`) builds its search list from command destinations
alone —

```python
dirs = [dst for src, dst in _BASE_TARGETS if src == "agents/commands"]
```

— so it asks only `<layer>/commands/<name>.md` and is blind to every skills
layer, including the three wfctl installs itself. wfctl ships `agent-brief`,
`brainstorming`, `reading-design-records`, `using-wfctl`, `using-wm` and
`writing-a-scan-file` as skills with no command peer, so declaring a pass on any
one of them yields a `check config` finding against a command that is present,
on a machine that has never heard of Spec Kit.

Spec Kit makes it worse rather than causing it. Its Claude integration installs
at `.claude/skills/speckit-<name>/SKILL.md` — the prefix is forced, not optional
(`integrations/base.py:1813`, and `:1703` for the matching dispatch name) — so a
Spec Kit skill is invisible to the check twice over: wrong directory, and a name
the declaration never spelled.

Filed as #450 rather than left here, because it is a wfctl defect that stands
whether or not sequencing ever moves.

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

There is a second gate beside it, and naming only the first is the mistake this
paragraph exists to prevent. `_pass_states` cascades: the first pass whose
reading is not `done` sets a flag, and **every later sibling is reported
`pending` without its reader being called at all** (`wfctl/_pipeline.py:410-419`).
So a pass depends on its own evidence, its parent step's evidence, *and* every
earlier sibling's evidence.

That is not hypothetical for the configuration this spike ran. `brainstorm`
already ships two built-in passes, so a declared `ui-design` placed after them
sits behind two siblings before its own artifact is consulted:

```
   brainstorm reading            not done ──► every pass pending, none read
        │ done
        ▼
   architecture reading          not done ──► design-doc and ui-design pending,
        │ done                                neither read
        ▼
   design-doc reading            not done ──► ui-design pending, not read
        │ done
        ▼
   ui-design reading             ui-contract.md finally consulted
```

This is deliberate, documented in `_pass_states`' own docstring, and not a
defect. But it means "wfctl derives a declared pass from its evidence alone" is
wrong in two directions at once, and the correction has to carry both: a design
that assumes a pass is independently readable is wrong, and so is one that
assumes two *sibling* passes are independently readable of each other — which is
exactly the shape an overlay produces, since an overlay inserts siblings.

Nothing about the boundary turns on this. Every input is still an artifact on
the branch and the cursor is still not among them. Filed as #451 — not to change
the cascade, which is right, but because the claim it falsifies is one three
readers have now made.

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
| where a reviewer finds it | `state.json`, inside a run directory | `<arch-root>/step-claims/<branch>/`, in the diff |

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

The second reason is test 1's ordering half. An overlay anchors to a base step
id, and every one of wfctl's built-in passes is a sub-step with no step of its
own, so the `before`/`after` graph does not survive the move unless the base
workflow enumerates wfctl's pass model by hand. That is a maintenance coupling
in a second repository, and it is independent of the naming problem: fixing
`build_command_invocation` would not touch it.

Three things would change this answer:

1. Upstream accepting a `command` step that dispatches a non-`speckit` command
   name — a change to `build_command_invocation`'s contract, not to the engine.
2. A `command` step validating that its command is installed, which would also
   close test 3's structural half.
3. Overlays anchoring to something other than a base step id, or wfctl's
   built-in passes becoming steps in their own right — either would let the
   ordering graph move without being copied.

There is also a fourth route that needs no upstream change and is worth naming
so #421 prices it rather than rediscovers it: **publish the pass as a Spec Kit
extension command**, so that its name genuinely is a `speckit.*` stem and
`build_command_invocation` rewrites it to something that exists. That solves
test 2 by construction. It then lands at
`.claude/skills/speckit-<name>/SKILL.md`, which is precisely where wfctl's
`_is_installed` cannot see it — so today it trades test 2's failure for the
`check config` defect above, and becomes viable the moment that defect is fixed.

Until one of them lands, the recommendation is that G1 and G2 be scoped to the
overlay/ordering mechanism only if they also carry the prompt-step cost and the
pass-model duplication explicitly, and that H not assume a `command` step is
available for a wfctl-governed pass. Filing them stays #421's call.

**One scoping note for G1 specifically.** #421 defines G1 as inserting
`/speckit.clarify` and `/speckit.analyze` through overlays. Those names are
already inside the `speckit.*` namespace, so test 2's finding — a `command` step
cannot name a command *outside* it — does not reach G1 on its face. What does
reach G1 is the spelling: wfctl installs `.claude/commands/speckit.clarify.md`
while Spec Kit dispatches `/speckit-clarify` and installs
`.claude/skills/speckit-clarify/SKILL.md`. Whether those resolve to the same
thing was not tested here and should be G1's first question.

### Upstream drift, noted rather than acted on

Upstream `HEAD` at the time of this spike is `c31168a7` (`1.0.10.dev0`), four
calendar days after the commit the boundary record cites. In that window
`workflows/overlays/` became `workflows/overlay/` and `workflows/steps/` became
`workflows/step/`.

**Three of the record's path citations are stale against `HEAD`, not all of
them** — an earlier draft of this paragraph said "every", which prices the
version dependency at roughly three times its size. The renames reach
`workflows/overlays/schema.py:16`, `workflows/steps/gate/__init__.py:183` and
`workflows/steps/slot/__init__.py:49`. They do not reach the record's
`workflows/engine.py` citations, which are the majority of them and sit in a
directory neither rename touched. Every *behaviour* the record cites still
holds.

That is still the version-dependency cost the record's own "Considered" section
named, arriving before the migration it was named about — just at its real size,
which is a handful of paths per upstream reshuffle rather than a whole record.

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

**Four overlays were used, and which one is in play changes what a test
measures** — an earlier draft printed only the first and claimed the fixture was
reproduced in full, which left tests 1, 2 and 3 unreproducible. All four follow,
under `.specify/workflows/overlays/wfctl-pipeline/`.

`fill-ui-design.yml` — a gate. The choice is worth flagging rather than passing
over: a wfctl declared pass defaults to `on_finish: review_required`
(`_DECLARED_DEFAULT`), and a gate is the Spec Kit step type that maps to. That
mapping is an assertion this spike made in order to stage test 5, **not a result
it measured** — nothing wired the gate's approve/reject into a wfctl reading,
and a reader scoping G1/G2/H should not take "review_required maps to a gate" as
established. What the gate did buy is the paused cursor test 5 needs.

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

`fill-pre-brainstorm.yml` — the `prompt`-step route from test 2, the one that
dispatches the string untouched and carries no declaration:

```yaml
id: fill-pre-brainstorm
extends: wfctl-pipeline
priority: 15
edits:
  - replace: pre-brainstorm
    step:
      id: ui-design-dispatch
      type: prompt
      prompt: "/pfms-ui-design-workflow"
```

The `command`-step variant, which produced tests 2 and 3 — the same `replace`
as `fill-ui-design.yml` with the step body swapped. This is the overlay behind
§3's transcript, and the gate above could not have produced it:

```yaml
    step:
      id: ui-design
      type: command
      command: /pfms-ui-design-workflow
```

`order-before-architecture.yml` — test 1's ordering half, the one that is
refused until the base workflow declares `architecture` as a step:

```yaml
id: order-before-architecture
extends: wfctl-pipeline
priority: 20
edits:
  - insert_before: architecture
    step:
      id: ui-design
      type: command
      command: /pfms-ui-design-workflow
```

and the `bad-anchor` overlay from test 1's validation check is the same shape
with `insert_before: nonexistent-step`.

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
real CLI on `PATH`, recording its argv and exiting 0:

```sh
#!/bin/sh
printf '%s\n' "--- dispatch ---" >> "$S/dispatch.log"
for a in "$@"; do printf '%s\n' "$a" >> "$S/dispatch.log"; done
echo "shim: dispatched"
exit 0
```

Using the real agent would have made test 3 unreadable: the question there is
what Spec Kit does when the command is absent, and an agent that improvises an
answer supplies one. The cost of that choice is stated at the top of this file —
it is why the verdict is `inconclusive`, and why §3 separates what the shim
measured from what it cannot.

The `wfctl.json` above is the one tests 2 through 5 ran under. Test 1's ordering
half needed a `before` key the original had no occasion to carry, and was run
against this variant:

```json
{ "name": "ui-design",
  "command": "/pfms-ui-design-workflow",
  "evidence": "ui-contract.md",
  "before": "architecture" }
```

with two further variants for the finding classes — `"before":
"nonexistent-pass"` paired with a pass naming itself, and a two-pass cycle.
