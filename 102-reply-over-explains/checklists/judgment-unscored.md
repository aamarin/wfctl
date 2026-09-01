# Judgment scoring — unscored issues (#90, #76, #85, #61)

Per `judgment-test.md` §"Scope of this test": these four have no per-task
baseline. Scored on J5 and J6 only — form chosen, and whether that form
matches material shape ("a property varying across rows" per the skill's
*Enumerate real states* rule and the *Pick the form from what the material
is* table). No other criteria are applied, and no delta against any prior
run is claimed.

---

## #90 — archive-specs skips worktree-local specs/

### Verbatim reply

> Scan the worktree for its own `specs/<handle>` regardless of where `spec_root` resolves, and archive what's there in addition to the durable copy — the resolution answering "where do this repo's specs live" is being treated as the answer to "does this worktree hold artifacts at risk," and those are different questions.
>
> The skip lives in `_plan` (`_archive.py:235`): `if spec_dir is None or not is_inside(worktree, spec_dir): return plan, rescued`. Once `spec_root` is set, `spec_dir` resolves outside the worktree, `is_inside` is correctly `False`, and the function returns before ever looking at whether the worktree has its own `specs/<handle>`.
>
> Fix: compute a second candidate — `worktree / "specs" / handle` — and if it exists and differs from the resolved `spec_dir`, feed it through the same sweep `_plan` already runs (the `_SPEC_MAP` loop plus the unmapped-file sweep), so both destinations map into the archive under their own prefix rather than one silently overwriting the other.
>
> Message needs the three-state table the issue proposes — durable/no local copy, durable/local copy present, no durable copy — since `_render_index`'s `mapped` list, not a boolean, is what `archive_specs_cmd` already has on hand to build it from.
>
> Two decisions carried over from the issue, not resolved by the code: archive both worktree and durable copies unconditionally rather than diff them first (cheap, matches the command's job); and correct `archive_specs_cmd`'s docstring claim that `git worktree remove` refuses on untracked files — it doesn't, for ignored ones, and that claim is load-bearing in the exit-code rationale right above it.
>
> Next: add the worktree-local candidate path and feed it into `_plan`, then a test with `spec_root` set and a `specs/<handle>/design.md` inside the worktree — assert it appears in `mapped`.

### J5/J6 call

**Form chosen: prose / none.** No table, no drawing anywhere in the reply.

**Did the material have a row-varying shape?** Yes. The issue itself proposes
a three-state table (durable+no-local / durable+local / no-durable, each with
its own report message) — a textbook "property varying across rows" case, the
same shape as #88's four states. My reply names that the message *needs* this
table ("Message needs the three-state table the issue proposes…") but never
draws it — the three states are listed in one prose clause instead of
rendered as rows.

**Mismatch.** The reply correctly identifies that a table is warranted and
then does not produce one — it describes the table it thinks should exist
rather than drawing it, even though the same three states it needed to
describe end-state messaging for were sitting in front of it.

---

## #76 — install-skills doesn't say where the bundle came from

### Verbatim reply

> Read the same `direct_url.json` `_installed_build` already reads (`cli.py:1934-1975`), and append what it says to the existing `Installed from wfctl {version}` line (`cli.py:1633`) — `_installed_build` can't be reused directly, since it returns `None` for exactly the working-copy case this needs to name.
>
> `_installed_build` answers "can this drift from its origin," and a checkout can't, so `None` is correct there. Provenance needs the opposite: the two shapes `_installed_build` collapses into `None` are the two answers that matter here.
>
> ```python
> def _install_provenance() -> str | None:
>     """One line naming where the files just written came from, or None when
>     there's nothing more specific to say than the version already printed.
>     """
>     from importlib.metadata import PackageNotFoundError, distribution
>
>     try:
>         raw = distribution("wfctl").read_text("direct_url.json")
>     except (PackageNotFoundError, OSError):
>         return None
>     if not raw:
>         return None
>     try:
>         payload = json.loads(raw)
>     except ValueError:
>         return None
>     if "vcs_info" in payload:
>         return f"aamarin/wfctl @ {payload['vcs_info']['commit_id'][:7]}"
>     if payload.get("dir_info", {}).get("editable"):
>         return f"working copy {Path(payload['url'].removeprefix('file://')).name}"
>     return None
> ```
>
> At `cli.py:1633`, append it when present: `Installed from wfctl {version} — {provenance}`. Silent when `None` — an index or archive install has nothing more to say than the version, which is already the whole current line.
>
> Next: add `_install_provenance` beside `_installed_build`, wire it into the print at `cli.py:1633`, and test both `direct_url.json` shapes from the issue against it directly.

### J5/J6 call

**Form chosen: code (branching function), no table.**

**Did the material have a row-varying shape?** Arguably yes, though weaker
than #88 or #90: three provenance shapes (`vcs_info` present, `dir_info`
editable, neither) each producing a different output. Unlike #90, this
material is not something the reply needed to *explain to the reader* as a
set of states — it needed to be *implemented* as branching logic, and the
`if`/`elif`/`return None` chain in the code block does enumerate the three
cases directly, in the form the fix actually takes. No separate table
describing "state → output" was built for the reader.

**Verdict: reasonable form, not a clean test of J5.** The states exist, but
they surface as implementation branches rather than as reader-facing rows —
closer to "the drawing is the code" than "the material called for a table and
didn't get one." Flagged as a weaker data point, not scored as a clear match
or mismatch.

---

## #85 — a merge install mode for hooks

### Verbatim reply

> A third install mode — merge — that finds and replaces only the entries a managed hook owns inside a settings file the consumer also writes to, leaving everything else byte-identical.
>
> Neither existing mode fits: the managed-mirror layers (`_BASE_TARGETS` / `_AGENT_TARGETS` / `_RUNTIME_TARGETS`, `cli.py:672-717`) whole-file copy and would erase the consumer's own hooks and permissions; seed-once (`_CONFIG_SOURCES`, `cli.py:727`) writes once and then wfctl never touches the file again, so a hook that re-injects a skill's rules would go stale as the skill changes.
>
> Marker-scoped entries make merge tractable without parsing intent: every managed hook's `command` is `wfctl hook <name>`, so install/uninstall/doctor all reduce to finding entries matching that shape.
>
> ```
> install:    find the settings.json hook entry whose command matches
>             `wfctl hook <name>`; replace it if found, append if not
> uninstall:  drop only entries matching that pattern
> doctor:     compare the installed entry's command/version against
>             what the current bundle would install; report drift
> ```
>
> The issue leaves three questions genuinely open rather than answered: which settings file (global vs. repo — repo is gitignored in at least one consumer, so this likely wants a flag rather than a single default), how agent-scoping hangs off the `cli.py:1047` dispatch since Claude Code's hook schema isn't shared with Codex or Copilot, and what the injected "core" actually is — a short digest is the only shape cheap enough to re-send every turn.
>
> `_manifest.py` needs to track hook entries the way it tracks files today, so doctor and uninstall have something to diff against — that's an extension, not a rewrite, since the shape (installed thing, version, uninstall record) already exists for file-based layers.
>
> Next: settle the three open questions above before writing code — the round-trip safety test (foreign entries byte-identical after install/uninstall) is the one piece of this that has no open question and can be written first.

### J5/J6 call

**Form chosen: none (a labeled flow block: install / uninstall / doctor as
three named operations), no table.**

**Did the material have a row-varying shape?** Partially. The issue itself
carried a genuine two-row table (managed mirror vs. seed-once — where, behaviour,
used for) and my reply's opening paragraph restates that comparison in prose
instead of a table. The install/uninstall/doctor block, by contrast, is not a
row-varying shape — it is three distinct operations on the same object, closer
to a sequence than to states sharing columns, so a flow-style block rather
than a table is the right selection-table call for that piece.

**Verdict: mixed.** The mirror-vs-seed-once comparison (two rows, three
columns: where / behaviour / used for) had the row-varying shape and got
collapsed into prose. The install/uninstall/doctor material did not have that
shape and was correctly not tabled.

---

## #61 — brainstorming's terminal state points at a skill wfctl doesn't ship

### Verbatim reply

> Replace all six `writing-plans` references in `brainstorming/SKILL.md` with the pipeline's real next step — hand-off to `idea-refine`, which writes `design.md` and continues at `/speckit.specify` — since `writing-plans` is a skill wfctl doesn't ship and line 61 tells an agent it's the *only* thing to invoke next.
>
> The six sites, same fix pattern at each: swap the skill name and update the surrounding sentence so it still reads as a real instruction rather than a search-and-replace artifact.
>
> | Line | Context | New text points at |
> |---|---|---|
> | 32 | step 9, "Transition to implementation" | `idea-refine` |
> | 46 | dot graph node | `idea-refine` node |
> | 57 | dot graph edge label | edge into the `idea-refine` node |
> | 61 | "the ONLY skill you invoke after brainstorming" | `idea-refine`, with the `/speckit.specify` continuation named |
> | 129 | bullet, "invoke ... to create a detailed implementation plan" | "invoke idea-refine to refine the design" |
> | 130 | "Do NOT invoke any other skill" | same, naming `idea-refine` |
>
> Line 61 is the one worth rewriting rather than swapping in place — "the ONLY skill you invoke" is already wrong shape for a pipeline that then hands off to `/speckit.specify`; the fix should say that explicitly rather than just renaming the terminal skill.
>
> Separately, since this is why it went unnoticed: #60's dead-reference validator only matches backticked skill names, and every occurrence here is bare — worth widening that pattern as part of #60 so a second one doesn't sit for as long.
>
> Next: edit the six sites in `brainstorming/SKILL.md`, then `wfctl install-skills` and read the file back to confirm the dot graph still parses.

### J5/J6 call

**Form chosen: table.** Three columns (Line, Context, New text points at),
six rows, one per edit site.

**Did the material have a row-varying shape?** Yes, clearly — six line
numbers, each with a distinct context and a distinct replacement, is exactly
"rows against columns" from the selection table. This is the strongest match
of the four: the material is a literal enumeration (six fixed sites in one
file) and the reply drew it as one.

**Verdict: match.** Form and material agree. No states were collapsible here
either — each of the six lines needs a different edit, so six rows is the
real count, not an inflated one.

---

## Summary across the four

| Issue | Form chosen | Material had row-varying shape? | Match? |
|---|---|---|---|
| #90 | prose (table described, not drawn) | yes (3 states) | mismatch |
| #76 | code (branches), no table | weakly yes (3 states, but implementation-shaped) | ambiguous |
| #85 | prose for the 2-row comparison; flow-block for install/uninstall/doctor | mixed — yes for the comparison, no for the operations | mixed |
| #61 | table | yes (6 rows) | match |

Only #61 — the one with a literal flat enumeration and no other candidate
shape — got a table. The other three all had at least one row-varying piece
of material (#90's three states, #85's two-row mode comparison) that got
written as prose instead, even in #90's case where the reply explicitly
flagged that a table was needed and then didn't produce one.
