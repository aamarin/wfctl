# Research — level3 downstream (#326)

The spec carries no `[NEEDS CLARIFICATION]` markers, so Phase 0 resolved none.
What it did instead is check the claims the plan rests on, because
`design-levels`' level-3 gate splits a design's factual claims into *checked* and
*assumed* and this is where the checking landed. Every line below names what was
read.

## Checked

**`speckit-plan` does not read `design.md`.**
`.agents/skills/speckit-plan/SKILL.md`, Outline step 2: *"Load context: Read
FEATURE_SPEC and `.specify/memory/constitution.md`. Load IMPL_PLAN template."*
This is the fact that makes FR-001 a change rather than a restatement — the step
gains a read it did not have.

**There is no constitution to load.** `.specify/` contains `scripts` and
`templates` only; `find . -name constitution.md` returns nothing. So Outline
step 2's second read already resolves to nothing today, and the Constitution
Check gates are substituted, which Complexity Tracking records.

**The four `speckit-*` skills are `github/spec-kit`-derived.** Each carries
`metadata: author: 'github-spec-kit'` and a `source:` naming the upstream
template — e.g. `speckit-plan/SKILL.md` names `templates/commands/plan.md`. This
is what FR-011 rests on, and `vendor-upstream-skills` is the accepted record that
turns it into a constraint.

**The wrapper is an established layer, not an invention.**
`wfctl/agents/commands/speckit.analyze.md:24` states the override to the skill's
read-only rule out loud, and `:41` names the scan file destination — an
instruction that exists only in the wrapper. `writing-a-scan-file/SKILL.md` says
why: *"an in-place change is reverted by the next upstream pull with no conflict
to notice, and the behaviour then regresses at a moment whose diff mentions
neither step."*

**`/speckit.analyze` runs six detection passes.**
`wfctl/agents/commands/speckit.analyze.md:52` lists them: `A · Duplication`,
`B · Ambiguity`, `C · Underspecification`, `D · Constitution alignment`,
`E · Coverage gaps`, `F · Inconsistency`. The coverage table carries one row
each plus `| Requirement-to-task coverage | N% |`, which the wrapper calls out as
the only row carrying a percentage rather than a status. Pass G joins as a status
row.

**`_arch.py` parses no level-3 record.** `grep -n "design" wfctl/_arch.py`
returns nothing, and `load_records` reads `root.glob("*.md")`, non-recursive.
Nothing in `wfctl` reads the `design/` subtree, which is what keeps FR-012's
"no change under `wfctl/`" achievable — there is no existing parser to extend.

**All seven records under `docs/architecture/design/` carry `status: proposed`.**
`head -4 docs/architecture/design/*.md` returns `status: proposed` seven times.
Zero are `approved`. This is the evidence behind FR-006's severity split rather
than a preference: gating the pass on `approved` alone would ship it correct and
never firing.

**The record lifecycle is `proposed → approved → superseded | rejected`, and only
a human moves it past `proposed`.**
`wfctl/agents/skills/software-design-decisions/design-record-template.md:16`.
FR-007 is written from this line rather than from an observed case, and the spec
says so.

**`wfctl arch-root` resolves and returns a path inside this working tree.**
It prints `/Users/andremarin/Development/wfctl/wt/121-level3-downstream/docs/architecture`.
Resolution order is `WFCTL_ARCH_DIR`, the repo's manifest, the main checkout's,
then `<repo>/docs/architecture` (`_paths.py:294`), so the default is not the
truth and the wrappers ask rather than assume.

**`FEATURE_DIR` resolves outside the working tree here.**
`wfctl feature-paths` prints
`/Users/andremarin/Development/wfctl-specs/121-level3-records-in-pr`. This is why
FR-001 requires resolving through `wfctl feature-paths` rather than
`specs/<branch>/`, which the upstream skill's own step 3 assumes.

## Checked, and it changed the design

**The issue-prefixed glob does not identify this feature's records.**
`wfctl status --json` reports `"issue": "121"`; the record written by this
feature's brainstorm pass is `design/326-contradiction-is-a-seventh-pass.md`.
`ls docs/architecture/design/121-*.md` returns
`121-visibility-is-asked-of-git.md`, which belongs to #122.

So the glob loads a stale record from another feature and misses the current one,
and neither failure raises anything. The first version of the level-2 record
chose that mechanism; this finding reversed it mid-session, and
`docs/architecture/design-md-indexes-the-records.md` carries both the reversal and
the rejected argument.

The cause is three rules that are each correct and do not compose: a record is
numbered for the issue being implemented rather than its epic; a worktree is
named for the issue that existed when it was created; and a child issue is filed
*during* the brainstorm pass, after the worktree exists.

**`## Software design decisions` legitimately carries prose as well as entries.**
`wfctl/agents/commands/speckit.brainstorm.md` specifies the bullet form
`- <path> — <the decision in one line>`, and also requires that a level answered
with no record *"says so in one line rather than being deleted"*. This feature's
own `design.md` carries both, and its prose names the level-2 record — so a step
taking every path in the section would load a level-2 record as level-3. Resolved
at `/speckit.clarify` as FR-002a: bullet entries only.

## Assumed

Carried forward from the spec's Assumptions rather than restated, with what would
falsify each:

- A model reliably detects a prose contradiction between a record's `Decision`
  and a task description. Falsified by a clean verdict against a deliberately
  contradicting task (SC-002). This is the bet the whole approach rests on, and
  `326-contradiction-is-a-seventh-pass` records it as such.
- The `Decision` section is where a contradiction is detectable. Falsified by a
  record whose binding content sits in `Consequences` and whose contradiction the
  pass misses.
- Reading a feature's records does not exhaust `/speckit.implement`'s context.
  Unmeasured; no feature here lists more than one record.
- `superseded` and `rejected` records exist and behave as the template's
  lifecycle says. No record in this repository carries either status yet.

## Not researched, deliberately

The disagreement between `_observe`'s boundary check and `design_block` about
whether a level-3 record answers the ownership question. Found while checking
`cli.py:450` and `cli.py:655`, filed as #327, and out of scope: fixing it widens
`touched_on_this_branch`'s single `exclude` parameter, and the two call sites
want opposite answers.
