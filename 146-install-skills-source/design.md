# Install skills from a named source, and record which one

Issue #146. Closes the source half; the hand-placed-skills half is split to a
new issue (see *Not Doing*).

## Problem Statement

How might we let someone install skills from a checkout other than the running
wheel — a PR branch, another worktree, a consumer repo pointed at a wfctl source
tree — without `doctor` reporting that install as permanent drift and prescribing
a remedy that destroys it?

## Recommended Direction

`install-skills` gains `--from <path>`, naming the bundle root to copy from. The
manifest records that path beside the `content_hash` it already records. `doctor`
re-reads the recorded root and compares against *it* rather than against the
running wheel's bundle.

The flag alone is not the feature. `_bundle.BUNDLE_ROOT` is the installed
package's own directory and `doctor` recomputes its reference from it on every
run, so an install from anywhere else reads as drift forever — and the remedy
`doctor` prints reinstalls the release, undoing the thing being tested. Moving
the reference point into the manifest is the decision; the flag is its interface.

**Why this is still worth doing after #75 closed.** #156 changed
`.workmux.yaml:81` to `uv run wfctl install-skills`, so a worktree *of this repo*
now installs the branch it checked out. That was `--from .`'s headline case and
it is handled elsewhere. What survives:

- **Cross-checkout** — `--from ../116-pr`. `uv run` resolves wfctl from the
  current worktree's lockfile and cannot reach another checkout's bundle.
- **Consumer repos** — pfms and the firmware repos have no wfctl source tree, so
  `uv run wfctl` does not exist there. For a consumer, installing skills from a
  branch or a PR has no mechanism at all today.

**The driver is documented, not hypothetical.** `AGENTS.md:43-55` (added
2026-09-04) instructs a human to hold the invariant by hand:

> Their bundles are never byte-identical, so they never both report clean —
> whichever one installed last is the one that reports green, and the other
> reports drift. Neither verdict is more true than the other.
>
> So pick one and use it for `install-skills` and `doctor` both.

That paragraph exists because nothing records the install source. It was
demonstrated live during this design session: after rebasing onto `4c3b546`,
`uv run wfctl doctor` reported

```
⬆ base: bundled skills changed since install
    update: wfctl install-skills          ← bare; the wrong command in this repo
```

`doctor` printed a remedy that contradicts `AGENTS.md`, because it has no way to
know which wfctl installed the tree. No `--from` was involved.

## Boundaries and Ownership

The full decision is recorded at
`docs/architecture/drift-is-measured-against-the-recorded-source.md` (status:
`proposed`). Summary of its `Owns truth`:

**The repo's manifest owns *"which bundle produced this install, and what did it
hash to?"***. It is written by `install-skills` at copy time, from the argument
the caller supplied.

`doctor` cannot compute it. Two installs from different sources can be
byte-identical — a branch whose skills happen to match the release produces
exactly the release's tree — so nothing in the installed files distinguishes
them. Provenance is knowable only to the process that did the copying, and only
at the moment it copied.

The running wheel cannot supply it either. It is a property of the machine
`doctor` runs on, not of the repo `doctor` inspects; the same repo inspected by
two differently-versioned wfctl installs would get two answers to a question that
has one.

```
install-skills                  │  doctor
────────────────────────────────┼────────────────────────────────
install time                    │
  resolves --from → bundle root │
  hashes THAT root              │
  records source + hash      ───┼─►  (nothing yet)
                                │
session start                   │
  (nothing)                     │    reads source from manifest
                                │    re-hashes THAT root
                                │    compares to recorded hash
                                │
  "it came from the release" ───┼──✗  never inferred from the bytes
```

## Behavior

`doctor`'s reachable states after this change, each string judged in its state:

```
✓ base: skills current (wfctl 0.16.0)
    — default install, tree matches. Unchanged from today.

✓ base: skills current (from ../116-pr)
    — --from install, source unmoved.

⬆ base: source changed since install — ../116-pr
    update: wfctl install-skills --prune --yes --from ../116-pr
    — the edit-install-test loop. Exit 1.

⚠ base: installed from ../116-pr — source is gone, can't check
    — recorded root no longer on disk. Warning, not a finding: the repo is
      not wrong, the answer is unreachable. Exit code unchanged.
```

**The remedy line must carry `--from`.** `/start-session` step 2 (rewritten by
#156) tells the agent that on any drift finding it should "run what it printed,
once per reported layer, adding `--prune`" — and then shows two literal examples
with no `--from`. If `doctor` prints a bare command, the next session start
reinstalls the release and destroys the `--from` install. That is #146's trap
relocated from `doctor`'s text into the skill that acts on it. The skill's
examples need a line saying the printed command governs.

## Verified claims

Checked against `origin/main` at `4c3b546`, not from memory:

- `_bundle.content_hash` has exactly two call sites — `cli.py` install and
  `cli.py` doctor. #38's `--prune` added none; it diffs `prior_items` and never
  hashes.
- `content_hash(root)` already takes a root. `doctor` needs no signature change
  to re-hash a recorded source.
- `_bundle.BUNDLE_ROOT` is read at call time at every site. `conftest.py`'s
  autouse `bundle` fixture monkeypatches the module attribute, so a `--from`
  parameter defaulting to `_bundle.BUNDLE_ROOT` at call time leaves every
  existing install test working.
- `.wf-skills-manifest.json` is gitignored; `wfctl.json` is tracked. The recorded
  source is per-checkout, so it belongs in the former — recording it in the
  tracked file would dirty a branch every time someone installed from a path.
- `install-skills` plans only items the bundle ships (`for item in src.iterdir()`),
  so a hand-placed skill is never offered for overwrite. Two of #146's three
  hand-placed bullets already hold.
- `the-underscore-is-the-module-contract` (proposed, #149) does not bind
  `BUNDLE_ROOT` — it is a public name inside `_bundle`, not an underscore
  crossing.

## Key Assumptions to Validate

- [ ] **A relative `--from` survives being recorded.** `--from ../116-pr`
      resolves against the caller's cwd; `doctor` may run from elsewhere. Store
      the resolved absolute path. Test: install with a relative `--from`, run
      `doctor` from a subdirectory.
- [ ] **`--prune` composes with `--from`.** Prune removes recorded paths the new
      source no longer ships. Test: install from a source missing one skill,
      confirm prune removes it and `doctor` stays green.
- [ ] **A consumer repo can actually name a wfctl checkout.** Test: run
      `--from ~/Development/wfctl/wt/<branch>/wfctl` from pfms and confirm the
      install and a subsequent `doctor` both behave.
- [ ] **`--from .` probing does not mask a genuine mistake.** If `<path>/agents`
      is absent and `<path>/wfctl/agents` present, the latter is used. Test: a
      path with neither must fail naming what it looked for, not fall through to
      the release.

## MVP Scope

**In:**

- `--from <path>` on `install-skills`, defaulting to `_bundle.BUNDLE_ROOT` read
  at call time.
- The resolution seam in `_bundle` exposed as a **public** name, so the module
  contract record does not force a rename later.
- `source` recorded in each manifest layer entry, beside `content_hash`.
- `doctor` re-hashes the recorded source; the four states above; the remedy line
  carries `--from` when a non-default source is recorded.
- One line in `start-session`'s step 2 saying doctor's printed command governs
  over the literal examples.

**Out:** everything in *Not Doing*.

## Not Doing (and Why)

- **Git refs and PR numbers (`--from pr-116`).** One row of three needs it, and
  what it saves is a `workmux add` you would plausibly want anyway — you are
  about to read that PR's skills, and a worktree is where you read them. It costs
  a `git archive` extraction, a temp-dir lifecycle, and a rule for which repo
  resolves the ref. Additive to the same seam later if it turns out to be the
  common case.
- **Wheels and sdists as a source.** Answers none of the three failures the issue
  observed.
- **Hand-placed skill ownership.** Split to its own issue. Two of its three
  bullets already hold; the third — `doctor`'s abandoned scan reporting an
  unrecorded, untracked directory — needs new state of its own (a way to mark a
  path locally owned) and shares no code with the source seam.
- **Per-layer content hashes.** `_bundle.content_hash` documents why the digest
  is whole-tree: `agents/trackers/github.json` belongs to no layer. Provenance
  solves the false-drift problem without splitting the digest.
- **Symlinking the mirrored skills.** `_MIRRORED_SKILLS` copies on purpose —
  symlinks break under `core.symlinks=false` and on Windows, and a symlink cannot
  drift, which is the property `doctor` relies on.
- **Auto-inferring the source from the worktree's checkout.** Rejected as a
  default in the issue: a worktree silently running unreleased skills makes every
  bug report ambiguous about which version produced it. Opt in per install.
- **#106, optional bundle layers.** A different question — what wfctl ships,
  versus where wfctl installs from.

## Open Questions

- **Per-layer or per-manifest?** Every layer in one manifest carries the same
  `content_hash` today, computed once. The recorded source is likewise a property
  of the install, not of a layer. Recording it per-layer beside `content_hash` is
  consistent with what is there; recording it once at the manifest root is
  smaller. Consistency wins unless someone argues otherwise at `speckit.plan`.
- **Record status.** `drift-is-measured-against-the-recorded-source` is
  `proposed`, and `wfctl arch context` lists only accepted records. Flipping it is
  the human's call, made at PR review, not here.
