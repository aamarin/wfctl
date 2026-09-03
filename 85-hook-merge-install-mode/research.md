# Research: merge install mode

No `NEEDS CLARIFICATION` markers remain in `plan.md`'s Technical Context — the
brainstorm (`design.md`) and clarify session already resolved the open
questions. This document instead records what two unreviewed candidate
implementations already tried, which is a form of prior art rather than a
literature search.

## Prior art: two candidate branches

Both were written before the design settled (per `design.md`'s Checked-vs-Assumed
table), against a `main` that #112 has since changed underneath them. Neither
applies cleanly. Both are read here for what to keep and what to discard —
`git show <branch>:<path>` reaches either without merging or rebasing them.

### Decision: adapt `_settings.py` from variant C (`worktree-agent-a5dc310d043b4fb76`)

**Rationale**: 172 lines, pure functions over an already-parsed dict — no I/O, no
`wfctl.*` import, matching the constraint `_workmux.py` already holds for the
same reason (a round-trip test is three dict literals, not a repo on disk). Its
shape already matches every accepted decision: `MANAGED_PREFIX = "wfctl hook "`
as the ownership marker, replace-in-place on a matching entry, append when none
exists, upward-pruning removal (group → event → `hooks` key), defensive
type-checking so a hand-edited file that doesn't match the expected shape is
"not ours" rather than a crash. Its own test file
(`tests/test_settings_merge.py`) exercises exactly the round-trip the spec's
Validation Strategy calls for and needs no rewrite to keep testing the right
thing.

**Alternatives considered**: Writing `_settings.py` fresh. Rejected — the
candidate already embodies the accepted architecture record's Decision table
byte for byte (unit = entry, found by command prefix, replace not duplicate),
and discarding working, already-defensive code to re-derive the same design
saves nothing.

### Decision: discard both candidates' digest-sourcing mechanism

**Rationale**: Variant C's `hook_cmd` reads a skill's `description` frontmatter
key — the mechanism `design.md` explicitly rejected (`description` tells a model
*when to load* a skill and ends by naming the slash command that activates it,
noise once already loaded). Variant F's `_reinforcements` reads a `reinforce:`
frontmatter key — also rejected, and now unbuildable: `test_skill_frontmatter.py`
enforces a fixed key set (`allowed-tools`, `compatibility`, `description`,
`license`, `metadata`, `name`) and fails on any other top-level key. The settled
answer (design ledger #8, spec FR-012) is a sibling `digest.md` file next to each
skill, read at runtime — a new file, not an edit to a skill wfctl may not own
(`vendor-upstream-skills`).

**What transfers anyway**: variant F's `_reinforcements` function is structurally
right — "for every installed skill opting in" is a directory scan, not a static
list — and that scan pattern (iterate `.agents/skills/*/`, check for the marker,
collect `(name, text)` pairs) is what the new digest lookup should follow, just
reading a file's contents instead of a frontmatter line.

**Alternatives considered**: variant C's `_MERGE_TARGETS` embeds a hardcoded
skill list per event (`("i-have-adhd", "conversation-response-shape")`) baked
into the installed command string itself. Rejected — it contradicts design
ledger #7 ("one entry per event, printing whatever digests are installed"): a
new skill's digest should reach a consumer's next session without the merge
command changing, and a hardcoded list means every existing install reports
"behind" the moment a skill gains a digest, which is `doctor` noise for a change
that needed no re-install.

### Decision: command name is `wfctl hook user-prompt`, no arguments

**Rationale**: Design ledger #5 and #6, settled during brainstorm — namespace
then event, and the entry names no agent because its file location already
scopes it. Neither candidate branch used this name (both predate the ledger);
variant C parameterized the command with a skill list, variant F used
`wfctl hook reinforce` (named for the mechanism, not the event). The event name
is what generalizes correctly — decision #7's reasoning: "a second managed hook
later is a different event, not a different skill."

**Consequence for `doctor`'s freshness check**: because the command string is now
fixed rather than skill-list-derived, "behind" narrows to a smaller set of real
cases (wfctl renamed or removed the subcommand, or the entry was hand-edited to
something close but wrong) rather than variant C's richer "missing a newly
digest-bearing skill" signal. That signal moves to `wfctl hook user-prompt`
itself, which is silent when nothing has a digest (FR-012) rather than something
`doctor` needs to detect — the hook's own exit-0-empty-output behavior already is
the degrade path.

## Decision: reuse the install/uninstall/doctor wiring shape, generalized

**Rationale**: Variant C's `_read_settings` / `_write_settings` / `_json_indent`
/ `_merge_hooks` / `_unmerge_hooks` / `_check_managed_hooks` functions in
`cli.py` implement exactly the behaviors `spec.md`'s functional requirements
name — write-only-on-change (FR-004), fail-loud-without-blocking-the-rest on
invalid JSON (FR-010), indent-and-newline preservation without a
format-preserving parser (Assumptions), upward-pruning uninstall (FR-006, FR-007)
— and the manifest bookkeeping already lands `merged` as a sibling of `items`,
matching FR-014. The generalization needed is narrow: `_MERGE_TARGETS` becomes
`(path, event)` pairs with no embedded skill list, since the command is now
static and the skill scan happens inside `wfctl hook user-prompt` at call time,
not at install time.

**Alternatives considered**: Writing the CLI wiring from scratch against the
current `cli.py`. Rejected for the same reason as `_settings.py` — the shape is
already correct and already carries the rationale comments the accepted
`install-modes` record echoes almost verbatim (both were written by the same
design process, just before the record was formally amended).

## Open items carried into Phase 1, not blocking it

- Exact digest file lookup order and malformed-digest handling (empty file,
  file present but unreadable) — a data-model question, resolved in
  `data-model.md`.
- Whether `wfctl hook user-prompt`'s output format matches variant C's
  (`"These skills are active and govern this response:"` header plus one
  bullet per skill) or something simpler — a contract question, resolved in
  `contracts/hook-command.md`.
