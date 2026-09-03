# Review: a4dd5d5..HEAD (37c5e79, 70f3190, 0339d99) — reviewer r1

## Passes run

1. **Correctness** — read the full `SKILL.md`, the command wrapper, `wfctl/cli.py`'s
   `_MIRRORED_SKILLS` change, and `tests/test_review_fanout_skill.py`; ran the roster-check
   shell fence's logic by hand and via the test suite; traced `wfctl feature-paths` output
   against the skill's Step 1 claim; traced `_frontmatter`/`_key_value` in `wfctl/_arch.py`
   to confirm how the "no `disable-model-invocation`" check treats the comment lines inside
   this skill's frontmatter.
2. **Security** — n/a. No user input, no secrets, no network/subprocess calls beyond the
   tested shell fence, which only stats files under a directory the agent itself controls.
3. **Architecture** — checked the "layer, never edit" constraint against
   `docs/architecture/vendor-upstream-skills.md` and `knowledge-placement.md`; confirmed
   `requesting-code-review`, `code-review`, `receiving-code-review` are untouched
   (`git diff --stat` shows only the 4 new/changed files); checked the rebase-specific risk
   the task called out — read `wfctl/_guard.py` in full and the new `worktree-handoff` skill
   for conflicts with what this skill instructs an agent to do.
4. **Readability/simplification** — read the skill prose end to end for internal consistency
   (Step 1 → Step 3 handoff, dispatch instructions, disposition table).
5. **Performance** — n/a, static prose/test content, trivial loops.
6. **Over-engineering** — scanned for restated rubric, dead prose, unneeded abstraction.

Also ran the project's definition of done: `uv run pytest -q` (762 passed), `uv run ruff
check wfctl/ tests/` (clean), `uv run mypy wfctl/` (clean), `uv run wfctl doctor` (clean —
this worktree's installed `.agents/skills` and `.claude/skills` copies already match what
this diff ships).

## Findings

**WARNING** `wfctl/agents/skills/fanning-out-code-review/SKILL.md:96-102` (Step 3's roster
fence) — The fence reads `$FEATURE_DIR` as a shell variable:

```bash
REVIEWS="$FEATURE_DIR/reviews"
for id in r1 r2 r3; do
  if [ -s "$REVIEWS/$id.md" ]; then echo "reported  $id"; else echo "MISSING   $id"; fi
done
```

but nothing in Step 1 exports or binds `FEATURE_DIR` — `wfctl feature-paths` only prints
`FEATURE_DIR='…'` as text, and the Bash tool's own contract is that shell state does not
persist between commands. The only instruction that this fence needs `FEATURE_DIR`
substituted before running is a backward reference three paragraphs later ("substituted
like the path above"). A fresh reviewer that pastes the fence as its own Bash call without
first assigning the literal path gets `REVIEWS="/reviews"`, and the check this skill exists
for — telling a silent reviewer apart from a clean pass — reports every reviewer `MISSING`
regardless of what was actually written. It fails toward safety (over-asking, not a false
clean pass), so it's not a blocker, but it undercuts the one step the skill is built around.
Every other skill using this `FEATURE_DIR` convention (`agent-brief`, `end-session`,
`speckit-orchestrate`, `speckit.brainstorm.md`) states the substitution as prose next to
each use, not as a runnable shell variable inside a multi-line fence. → Make the fence
self-contained: give it its own first line, e.g. `FEATURE_DIR="<paste the real path from
Step 1>"`, so the block doesn't depend on an earlier paragraph.

**NIT** `wfctl/agents/skills/fanning-out-code-review/SKILL.md:4-8` — Comment lines
(`# No disable-model-invocation, …`) sit inside the YAML frontmatter block, between the two
`---` delimiters. No other shipped `SKILL.md` in the repo does this. It's valid YAML, and
`wfctl/_arch.py:_key_value` explicitly treats a `#`-prefixed line as declaring no key (by
design, predating this change), so wfctl's own tooling parses it correctly — confirmed by
`test_the_panel_skill_is_model_invocable` passing. The risk is untested and unverifiable
from this repo: whether Claude Code's own native frontmatter loader (the thing that
actually makes `.claude/skills/fanning-out-code-review/SKILL.md` model-discoverable) is as
tolerant. Low confidence, low risk — comments are ordinary YAML — but for consistency,
consider moving the rationale below the closing `---`, under "# Fanning out a code review",
where every other skill's rationale prose lives.

## Rebase-specific check (main gained #132 worktree-guard, #139 worktree-handoff, #138
doctor abandoned-entry scan)

- **`wfctl hook worktree-guard` (#132):** No conflict. The skill's Step 2 dispatch is
  explicit that reviewers "share a worktree with each other and with you" and must
  report-only — never a cross-worktree scenario the guard governs. The guard's own
  docstring notes it is quote-blind and variable-blind by design (`_guard.py:150-165`,
  "indirection… the path never appears at all"): the roster fence's `$FEATURE_DIR` is a
  shell variable reference, never a literal absolute path in the command text, so
  `_ABS_PATH.findall` finds nothing to check regardless of what the variable resolves to
  at runtime. That means the guard offers **no protection**, not a false refusal, in the one
  edge case the skill itself introduces risk in: Step 1's fallback line — "With no feature
  dir, set `FEATURE_DIR` yourself to any directory outside the worktree" — doesn't rule out
  picking a path that happens to be another live worktree, and if it did, the guard wouldn't
  catch it (indirection). Worth a line ruling that out explicitly, but it's a pre-existing
  guard limitation the skill merely doesn't work around, not a regression this diff causes.
  Confirmed no other command in the skill (Steps 1, 2, 6) is one the guard's read/mutate
  split would refuse from this worktree.
- **`worktree-handoff` skill (#139):** No overlap. That skill governs writing a handoff
  before a worktree is *created*; this skill's reviewers are dispatched as in-process
  subagents over the same tree, never new worktrees. Nothing in `fanning-out-code-review`
  invokes `git worktree add` / `workmux add`.
- **`doctor`'s abandoned-skill-mirror scan (#138):** No conflict. `fanning-out-code-review`
  is correctly added to `_MIRRORED_SKILLS` (alphabetically placed, `wfctl/cli.py:1205`), so
  its `.claude/skills/fanning-out-code-review` mirror is recorded, not orphaned. Verified
  live: `wfctl doctor` in this worktree reports clean (`✓ claude: skills current`), meaning
  the pre-installed `.agents/skills` and `.claude/skills` copies already match what this
  diff ships — no drift for the scan to catch.

## Acceptance criteria (issue #133) — spot check

All satisfied: model-invocable via `_MIRRORED_SKILLS` with no `disable-model-invocation` on
the `SKILL.md` (command wrapper correctly *does* carry it, matching every sibling pairing);
dispatch instructions carry the report-only/shared-worktree rule; every reviewer runs
`code-review` rather than a restated rubric (`test_the_panel_skill_does_not_restate_the_rubric`
derives the pass list from `code-review/SKILL.md` itself, so a renamed pass keeps the check
honest); the roster check is the explicit "reviewer went silent" step, tested under both
`sh` and `zsh` the way `test_skill_commands.py` tests `opening-a-change`'s lookup; the
disposition table requires applied/accepted/rejected with a reason for every finding; a
command wrapper exists, pairing with `requesting-code-review`/`receiving-code-review`'s
existing wrappers.

## Metric

net: 0 lines possible — dense-rationale prose matches the project's own style
(`code-review/SKILL.md` is comparably dense), and the test file's four tests each guard a
distinct, previously-broken failure mode (per their own docstrings) rather than restating
one assertion four ways.

## Verdict

**Approve**, with the Step 3 fence binding fixed before merge (or a follow-up filed with a
stated reason, per the code-review skill's own Step 6). Nothing found rises to a blocker:
tests, ruff, mypy, and `doctor` are all clean, the layering constraint is respected, and the
rebase onto #132/#138/#139 introduces no refusal or duplication — only a pre-existing guard
limitation the skill happens to sit next to.
