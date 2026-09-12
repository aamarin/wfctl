# Check an open change's sidebar

## Problem Statement

How might we make "an open PR is not done until the sidebar is set" something
that disagrees when it is skipped, rather than a sentence everyone accepts and
nobody notices breaking?

## Recommended Direction

`wfctl change check <pr>` reads an open change and reports the fields that are
blank — but only the ones something already said should be filled. Two sources
say so: the branch's issue, whose fields the change is supposed to carry across,
and `wfctl.json`, where the repository names the fields it requires. Anything
neither source mentions is never printed.

The filter is the whole design. A check that reported every blank field would be
right about GitHub, wrong about Gerrit, and noisy in any repository that does not
use milestones — and a noisy check is learned around and then ignored, which
loses the prose *and* the check. So wfctl computes the verdict and holds no field
name of its own: the tracker config declares a `fields` verb returning a flat
JSON object, and the key names in that object are the backend's own vocabulary.

It is invoked, not automatic. `opening-a-change` Step 6 gains a line calling it,
the same way Step 5 already calls `check-body`. The check runs after the change
exists, because every field it is about only exists once the change is open.

## Boundaries and Ownership

**wfctl owns *"is this blank field a finding?"***. The tracker cannot: a verdict
computed per backend puts the finding/notice split into an unreviewed shell
script, one copy per tracker, and that split is the entire design.

**The repository and its tracker own *"which fields exist, what are they called,
and which are required?"***. wfctl cannot: any field name it hardcodes is one
tracker's vocabulary shipped as universal, and no constant is right for both a
repository that assigns every change and one whose triage is somebody else's.

**The tracker owns the shape its values arrive in.** Flattening happens in the
tracker config, so wfctl compares scalars and never descends into a payload.

Recorded at `docs/architecture/the-repo-names-the-fields-a-change-must-carry.md`
and `docs/architecture/design/302-the-tracker-flattens-its-own-shapes.md`.

## Key Assumptions to Validate

- [ ] Adding `fields` to `ALLOWED` and `ALLOWED_CHANGES` is additive for tracker
      configs already in the wild — run `wfctl tracker-check github` against the
      unmodified config.
- [ ] No existing test pins `wfctl change`'s pure-passthrough shape in a way a
      wfctl-owned `check` verb breaks — run the suite.
- [ ] `extract_issue_key` resolves the branch's issue in every state this needs,
      including a branch carrying no key — covered by the no-issue-key state.
- [ ] The check can actually pass. Open a throwaway change with an empty sidebar,
      confirm it names every unset field, then fill the sidebar and confirm it
      goes quiet. Running only the first half tests nothing a noisy check would
      fail.

## MVP Scope

**In.** A `fields` verb on both the `verbs` and `changes` sections of the tracker
contract, returning a flat JSON object. A `change_check` key in `wfctl.json`
naming required keys. `wfctl change check <pr>`, comparing key by key: a finding
when a required key is blank, when a key set on the issue is missing from the
change, or when `change_check` names a key the backend never emits. Scalars
compare as empty-versus-set; lists compare as a set difference, because Step 6
says a label the change earns is *added* to the issue's set, never swapped in for
it. `✓` for a key that could have been a finding and is not, `ℹ` when there was
nothing to check or the backend declined, and silence for everything else.

**Not in this PR.** #306 — a record whose `## Considered` section is empty passes
every check — was found during this design pass and is filed separately. It goes
to its own branch off `main`: `speckit-delivery-plan` holds that one PR closes
exactly one issue, and the earlier argument for pairing them was wrong, because
it priced a *stacked* PR. These two share no code, so they are parallel, and a
parallel PR costs nothing.

**Out.** Automatic invocation. A reviewer-count rule. Board *column* checking, as
opposed to board membership.

## Not Doing (and Why)

- **Hardcoding the field names in wfctl** — ships GitHub's vocabulary as
  universal. Gerrit has neither labels nor milestones, and this is the mistake
  #301 had to undo.
- **Treating the issue as the only source** — an issue bare in every field is
  triaged by nobody rather than triaged to nothing, so the check would go quiet
  exactly when triage was skipped.
- **A hardcoded floor for assignee** — right for a repository whose issues its
  author triages, wrong for one whose triage is controlled elsewhere. Only the
  person running it knows which they have.
- **Deriving the expectation from recent merged changes** — answers the
  single-collaborator reviewer question for free, but a repository that has been
  sloppy would teach the check to be sloppy.
- **Putting the policy in `.agents/trackers/<name>.json`** — that tree is
  gitignored and rewritten by `install-skills`, so the policy would work for one
  session and then vanish with no error.
- **Making `fields` replace the `labels` verb #301 added** — `labels` feeds the
  notify grant, which gates outward-facing authority. Migrating a security path
  onto a new reader for tidiness buys nothing today.
- **An `ℹ` line per field that is blank on both sides** — two lines on every
  change forever, saying the same thing every time. That is the shape people
  learn to skim.
- **Rewriting the sentence in `opening-a-change`** — already clear, already last.
  It is skipped because nothing disagrees, which is what #302 exists to fix.

## Open Questions

- Whether `wfctl change check` should eventually take no argument and resolve the
  branch's own change, removing the case where a mistyped id compares against the
  wrong issue. Deferred: the skill calls it with the change it just created.
- Whether a reviewer request that has already been answered should count as set.
  `reviewRequests` clears the moment a reviewer submits, so a repository listing
  it in `change_check` would see false findings after review lands. This is the
  backend's flattening to solve, not wfctl's.

## Software design decisions

- `docs/architecture/the-repo-names-the-fields-a-change-must-carry.md` — wfctl
  computes the verdict and holds no field name; the repository and its tracker
  supply everything the verdict is computed from.
- `docs/architecture/design/302-the-tracker-flattens-its-own-shapes.md` — the
  `fields` verb returns scalars, and the tracker flattens with its own client's
  tool, so wfctl never learns which key identifies a label.
