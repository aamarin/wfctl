# Move the mirror switch out of skill frontmatter

## Problem Statement

How might we make every skill wfctl ships a valid Agent Skill, without losing the
ability to decide which of them Claude discovers natively?

Six of the 28 shipped skills carry a top-level `deployment: skill` key that the
Agent Skills spec does not allow. The key is wfctl's own invention, read once by
`_skill_deployment()` and used to mirror a skill into `.claude/skills/`. Nothing
breaks today, but wfctl installs the same tree into `.claude/`, `.bob/` and
`.github/skills/`, and the spec is the only contract those clients share.

Verified with the reference validator over all 28 skills:

```
$ skills-ref validate wfctl/agents/skills/<each>

FAIL architecture-decisions         :: Unexpected fields in frontmatter: deployment
FAIL conversation-response-shape    :: Unexpected fields in frontmatter: deployment
FAIL design-levels                  :: Unexpected fields in frontmatter: deployment
FAIL receiving-code-review          :: Unexpected fields in frontmatter: deployment
FAIL using-superpowers              :: Unexpected fields in frontmatter: deployment
FAIL verification-before-completion :: Unexpected fields in frontmatter: deployment
FAIL i-have-adhd                    :: Unexpected fields in frontmatter: disable-model-invocation

21 valid · 7 failed
```

## Recommended Direction

**Delete the frontmatter switch. Name the mirrored skills in `cli.py` instead.**

```python
_MIRRORED_SKILLS = frozenset({
    "architecture-decisions",
    "conversation-response-shape",
    "design-levels",
    "i-have-adhd",
    "receiving-code-review",
    "using-superpowers",
    "verification-before-completion",
})
```

`_skill_deployment()` is deleted rather than ported, and
`_claude_native_skill_mirror()` tests `item.name in _MIRRORED_SKILLS`. No skill
file carries a wfctl-specific key, so the bundle goes to 27 valid / 1 failed —
the remaining failure being `i-have-adhd`'s `disable-model-invocation`, which is
vendored and out of scope.

The issue as filed proposed moving the key under `metadata` instead, which the
spec permits as an arbitrary string map. That was rejected for two reasons. The
first is mechanical: wfctl depends only on `typer` and `rich`, so frontmatter is
scanned line by line, and finding `wfctl-deployment` nested under `metadata:`
means hand-rolling indentation tracking — the spec-compliant shape costs *more*
parsing code than the violating one. The second is architectural, and decides
it: `layer-model` already states that `install-skills` owns what lands in each
layer. Under frontmatter that was half-false, because a skill file owned part of
the answer. Moving the switch into the installer makes the code match a claim
the record already makes.

This also closes #108. A vendored skill could never carry the key — the next
upstream pull drops it — so the mirror decision had nowhere to live for a file
wfctl does not own. With the switch in `cli.py`, `i-have-adhd` is just another
name in the list, and the vendored/owned distinction disappears from the
mechanism entirely.

## Boundaries and Ownership

Authority for "what lands in `.claude/`" belongs to `install-skills`, not to the
skill files.

```
skill files                        │  install-skills
───────────────────────────────────┼──────────────────────────────────
wfctl/agents/skills/<name>/        │
  SKILL.md                         │
    name · description · license   │
    (spec fields only)             │
                                   │
  content ─────────────────────────┼─►  .agents/skills/<name>
                                   │
  "put me in .claude too" ─────────┼──✗  no skill states this any more
                                   │
                                   │    _MIRRORED_SKILLS decides
                                   │      → .claude/skills/<name>
                                   │
                                   │    recorded in .wf-skills-manifest.json
```

**Why the skill file cannot own this.** A fact's durability is decided by
whoever rewrites the file. For a vendored skill, upstream rewrites it, so
anything wfctl writes there is a borrowed decision that expires without notice.
That argument is `vendor-upstream-skills`' own, applied a second time.

For the six skills wfctl *does* rewrite, frontmatter would be durable — but
`layer-model` has already assigned layer contents to the installer, and splitting
the answer across two owners is what `knowledge-placement` exists to prevent.
One home, and it is the installer.

**No new architecture record.** `layer-model` and `knowledge-placement` between
them already answer this; a third record restating them would be the duplication
they forbid. Two sentences in `layer-model` become false and are amended:

- "Only skills whose frontmatter carries `deployment: skill` are mirrored into
  `.claude/skills/`."
- "a vendored skill cannot opt in: the key would have to go in a file the
  project does not own, and the next upstream pull would drop it."

The second was added by #107; this change is what reverses it.

`vendor-upstream-skills` needs no change — the mechanism no longer treats
vendored skills specially at all.

## Key Assumptions to Validate

Checked during design, with the check that settled each:

- [x] **The `deployment` key is the only spec violation that is ours** — ran
      `skills-ref validate` over all 28 skills; 6 `deployment`, 1 vendored.
- [x] **`_skill_deployment()` has exactly one call site** — grep; only
      `_claude_native_skill_mirror()` reads it.
- [x] **No stale-key compatibility window exists** — the install loop reads
      `src = _bundle.BUNDLE_ROOT / src_rel` (`cli.py:1463`) and passes those
      items to the mirror hook (`cli.py:1487`). Reader and skills ship in the
      same wheel; an installed `.agents/skills/` is only ever a destination.
      The issue's Compatibility section defends against a failure that cannot
      occur.
- [x] **Uninstall needs no change** — `uninstall_skills_cmd` iterates
      `entry["items"]` and `rmtree`s each; the install loop records the mirror
      under the `claude` layer (`cli.py:1487`), so it is removed like any other
      item.
- [x] **The mirror tests break structurally, not cosmetically** — all four build
      a synthetic skill named `native-skill` in a temp bundle and mark it in
      frontmatter. A `frozenset` of real names cannot see it. They must
      monkeypatch the constant, following the pattern the autouse `bundle`
      fixture already uses on `wfctl._bundle.BUNDLE_ROOT` (`conftest.py:107`).

Still open, to confirm at implement time:

- [ ] **`doctor` reports installed skills as behind in every consuming repo**
      after this ships, since six SKILL.md files change content. Expected, not a
      defect — confirm the message reads sensibly rather than alarmingly.

## MVP Scope

**In:**

1. `wfctl/cli.py` — delete `_skill_deployment()`; add `_MIRRORED_SKILLS` with
   the seven names; `_claude_native_skill_mirror()` tests membership by
   `item.name`.
2. Six `SKILL.md` files — drop the `deployment: skill` line, add nothing.
3. `wfctl/agents/skills/conversation-response-shape/SKILL.md` — its frontmatter
   comment (added in #107) explains itself in terms of `deployment: skill`;
   rewrite it against the new mechanism.
4. `docs/architecture/layer-model.md` — amend the two sentences above.
5. `tests/test_install_skills.py` — the four mirror tests monkeypatch
   `_MIRRORED_SKILLS` instead of writing frontmatter.
6. One new test: every name in `_MIRRORED_SKILLS` is a directory under
   `wfctl/agents/skills/`. It reads the real package path directly rather than
   `BUNDLE_ROOT`, so the autouse fixture does not interfere and no marker is
   needed.

Net: roughly −15 lines of parser, +10 of constant and guard.

**Out:** everything in "Not Doing".

**Behavioral outcome.** `.claude/skills/` goes from 6 entries to 7, gaining
`i-have-adhd` — which is the payload of #108: its brevity rules become
reloadable mid-session, as `conversation-response-shape`'s ordering rules
already are. The other 21 skills stay reachable only by typing their slash
command.

## Not Doing (and Why)

- **`metadata.wfctl-deployment` in frontmatter** — costs more parsing code than
  the key it replaces, given no YAML dependency, and leaves layer authority
  split between the skill file and the installer. This was the issue's own
  proposal; the mechanical and architectural arguments both landed against it.
- **Both mechanisms — in-file for owned skills, a list for vendored ones** —
  considered and dropped. It preserves locality, but requires a union rule, two
  mechanisms to document and test, and keeps the frontmatter parser alive for
  six files.
- **Moving skills to `.claude/skills/` for `--agent claude` instead of copying**
  — mechanically viable; the `../skills/` fallback in every command file was
  written for exactly this layout. Rejected because everything in
  `.claude/skills/` is offered to the model for auto-invocation, so all 28
  skills would become auto-invocable and `speckit-*` internals would start
  firing on their own. `layer-model` chose against that deliberately. It would
  also make `.claude/` non-additive and the base layer conditional.
- **A compatibility shim reading both keys for one release** — no window exists
  to shim. See Key Assumptions.
- **A `doctor` check flagging the flat key** — same reason; it would report a
  state that cannot arise.
- **`i-have-adhd`'s `disable-model-invocation`** — vendored from
  [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd). A local edit is
  reverted by the next pull; if it matters, it goes upstream.
- **A `skills-ref validate` pass as a test** — worth doing, separately. It fails
  on `i-have-adhd` today, so it needs a documented exemption list for vendored
  skills first, and that exemption's design is its own question. Tracked on #60.
- **Widening `doctor`'s orphan scan to `.claude/skills/`** — filed as #110.

## Open Questions

None blocking. Both follow-ups found during design are now tracked, and neither
is in scope here:

- **#110** — `doctor`'s orphan scan never covers `.claude/skills/`, so
  un-mirroring a skill later leaves a stale copy nothing reports. Not a
  regression, but this change makes the hole easier to reach. Deliberately a
  second diff: it touches orphan detection and the extras-hook contract, not
  `install-skills`, and it has a bob-only false-positive case to get right.
- **#60** — running `skills-ref validate` in CI so this class of defect cannot
  recur. Recorded as a comment there rather than a new issue. After this change
  the bundle has exactly one remaining failure, `i-have-adhd`, which makes that
  issue's exemption-list question concrete instead of hypothetical.
