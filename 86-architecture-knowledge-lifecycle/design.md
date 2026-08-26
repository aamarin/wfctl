# Architecture Knowledge Lifecycle

Epic #86. This design establishes the model and the decomposition; the child
issues implement it.

## Problem Statement

How might we make architectural decisions outlive the conversation that produced
them, so the reasoning behind a boundary is available to whoever — human or agent
— touches it next?

## Recommended Direction

wfctl captures *what we decided to build* well and *why the boundary sits there*
not at all. The `design-levels` skill already demands a **Boundaries and
Ownership** section and names its absence as a red flag. Across the eleven
designs written so far, `Problem Statement` appears in eight and
`Boundaries and Ownership` in **zero**. An instruction alone has a perfect
failure record here, so the fix cannot be another instruction.

The direction is to make the level-2 gate's answer *be* the durable record
rather than a section that then has to be copied into one. A decision is written
once, as a file under a configurable `arch_root` (default `docs/architecture/`,
committed in-tree), in MADR-simple format with one added field: **who owns this
truth, and why the other side cannot compute it**. No ADR format on the market
carries that field, and it is the one thing `design-levels` exists to extract.

Records are immutable once accepted — superseding writes a new record and flips
the old one's status, per the ADR convention. Only accepted records are loaded as
the architectural contract; superseded and rejected ones stay on disk, readable
by humans, invisible to agents by default. Keeping both live in one pile is the
failure that makes an agent guess which decision binds.

Committing in-tree buys something a separate decisions repo would throw away: the
record and the code implementing it land in the **same commit**, so `git show`
returns both, and git supplies the edit history for free. The file carries only
what git cannot answer — which decision replaced which, why, and what state it is
in now.

## Boundaries and Ownership

**"Is this decision binding right now?"** — the record's `status` field owns it,
declared in the file. An agent cannot derive it from content: given a directory
of markdown, nothing distinguishes a March decision from the August one that
replaced it.

**"Where do this repo's architecture records live?"** — the repo's manifest owns
it, via an `arch_root` key resolving exactly as `spec_root` does
(`WFCTL_ARCH_DIR` → this repo's manifest → main checkout's manifest → default).
An environment variable cannot own it: it is process-global, so exporting it from
a shell profile redirects every repo wfctl touches.

**"Has the design step produced a record?"** — wfctl owns it, by checking the
filesystem. The agent cannot: a self-report of completion is unfalsifiable. This
is the same reasoning already applied to verification in #69, and the same
answer. It does **not** belong in `doctor`, which explicitly refuses checks
describing what the user has or has not done.

**"What does an agent load as the architectural contract?"** — wfctl owns the
projection, filtering to accepted-only, via `wfctl arch context`. The agent
cannot be handed the whole directory and trusted to filter: superseded records
read as live, which is precisely the confusion the status field exists to
prevent.

**"Where does a given piece of knowledge belong?"** — placement is decided by
scope first, then by what is constrained:

```
a fact about one file            → that file's own frontmatter
a constraint on the system       → docs/architecture/
guidance for the worker          → AGENTS.md
```

`AGENTS.md` and `docs/architecture/` therefore do not overlap and do not need
syncing. The overlap that exists today is content sitting in the wrong file:
*Rules that are not obvious* is largely a decisions document wearing a guidance
hat. "Do not edit `i-have-adhd`" is the worked example — the per-file fact
belongs in that skill's frontmatter (where `license: MIT` already half-encodes
it), the general decision to vendor-and-layer rather than fork belongs in a
record, and neither belongs in `AGENTS.md`.

**"What belongs in the CLI rather than a skill?"**

```
wfctl owns whatever about the workflow must be identical no matter
which agent is driving. Skills are the layer allowed to vary.
```

Every existing verb passes that test: session position, path resolution,
installation, integrity, tracker normalization. `arch-root` and the advance
check fit existing groups. `arch context` does not — it is a deliberate sixth
kind, rendering project domain content, and is justified narrowly below.

## Key Assumptions to Validate

- [ ] **That wiring capture into the level-2 gate actually produces records.**
      Test: after issue A ships, check whether the next three features have
      records. The baseline to beat is 0 of 11.
- [ ] **That MADR-simple plus one field holds real decisions.** Partly tested
      already — the `spec_root` decision was traced through it and the ownership
      field generated a level-3 requirement (the main-checkout fallback) that the
      decision statement alone did not imply. Test two more from `AGENTS.md` and
      see whether anything fails to fit.
- [ ] **That the advance check can be enforced without being routed around.**
      `AGENTS.md` already states that a change drawing no new boundary needs no
      design. The check must therefore have an explicit "no boundary changed"
      answer, or it becomes a nuisance on trivial PRs and gets disabled — which
      returns us to the 0-of-11 baseline with extra machinery.
- [ ] **That `arch context` earns being a CLI verb.** Falsification test:

      ```
      if `wfctl arch context` is still equivalent to
          grep -l "^status: accepted" "$(wfctl arch-root)"/*.md
      in a year, it did not need to exist.
      ```

      It is justified today by one mechanical fact, not by determinism: hooks are
      seeded by `install-config`, which is seed-once, so filter logic placed in
      hook shell can never be fixed forward in repos already seeded. The CLI
      upgrades; the seeded hook does not. It earns its place properly when the
      filter becomes something grep gets wrong — records scoped to subtrees, or
      applicability conditions. Neither exists yet and neither is being built for.

## MVP Scope

**Issue A — the capture path** (~11 files). `arch_root` resolution plus a
`wfctl arch-root` command mirroring `spec-root`; the ADR skill in MADR-simple
form with the ownership field, invoked from the `design-levels` level-2 gate;
two or three seed records for decisions currently contested; and retirement of
the orphaned `wfctl promote`, which today reads a file nothing writes and writes
a file nothing reads.

**Issue B — the consumption path and the migration** (~8 files), in this order:

1. `wfctl arch context` — the accepted-only projection, wired into session start
   next to where `AGENTS.md` is already read.
2. The advance check — refuses to pass the design step without a record.
3. Move the misplaced content out of `AGENTS.md`: the layer model, the
   mirror-vs-seed-once rule, and the committed-config constraint become records;
   the `i-have-adhd` rule moves to that skill's frontmatter.

Step 3 depends on step 1 and the order is not cosmetic. `AGENTS.md` is loaded
automatically every session; `docs/architecture/` is loaded by nobody until the
projection exists. Moving the layer model out first would mean an agent asked to
fix a typo edits `.agents/skills/…` — which reads correctly, passes the suite,
and ships nothing, because `.agents/` is gitignored install output.

A ships before B specifically to test whether B's *check* is needed. If wiring
capture into the gate produces records unaided, the check is cheaper to skip than
to build; if it does not, A's failure is the evidence that justifies it. The
*projection* is not conditional — it is the prerequisite for step 3.

## Not Doing (and Why)

- **Bulk backfill of existing decisions** — an agent inferring rationale from
  prose it is reading for the first time produces reconstructions, not records.
  Value comes from writing at decision time. Only the specific `AGENTS.md`
  content identified as misplaced gets moved.
- **Separate constraint and ownership units** — three cross-linked stores means
  three lifecycles and a link-integrity checker. One page per decision until a
  rule demonstrably outlives its decision often enough to hurt.
- **Full MADR 4.0** — RACI frontmatter (decision-makers, consulted, informed) is
  team ceremony a small repo leaves blank.
- **A changelog inside each record** — git already logs every edit, and the
  in-tree choice keeps the record and its implementing code in one commit.
- **Instructing agents to "review git log for full history"** — unbounded, so it
  is either skipped or dumps hundreds of commits into context. The file stands
  alone; git is a targeted lookup.
- **Generating `AGENTS.md` from records** — no drift by construction, but it ends
  hand-authoring a file whose value is that it is hand-authored. Unnecessary once
  the two files stop overlapping.
- **A PR-time boundary check** — fires after the thinking is finished, and is
  substantially harder to build than the advance check.

## Open Questions

- How does the advance check recognise that a change draws no new boundary,
  without that escape becoming the default answer?
- Does `arch_root` need the main-checkout fallback `spec_root` has? That fallback
  exists because the manifest is gitignored and regenerated per worktree; an
  in-tree committed default resolves identically everywhere, so it may be dead
  weight.
- Two skills named `idea-refine` collide (#61): the copy that writes `design.md`
  is unreachable by the Skill tool, and the reachable one never writes it. Does
  that handoff need fixing before this pipeline is relied on?
- Does the `i-have-adhd` frontmatter need an explicit `vendored: true`, or is
  `license:` a sufficient marker once the general decision is recorded?
