# wfctl as it stands

A drawing of the modules wfctl ships, the bands they fall into, and the two
places the bands do not hold. It **describes**; it does not constrain. The
records under `docs/architecture/` constrain, and this file lives one directory
down from them because `_arch.load_records` globs `*.md` non-recursively at the
arch root — a view placed there would be read as a record and reach agents
through `wfctl arch context` as if someone had agreed to it.

Derived from `wfctl/*.py` at `5ba013e`. What keeps it honest is
`tests/test_architecture_view.py`, which re-derives the import graph and fails
when this drawing stops matching it. See **Staleness** below.

```
   ╭─ surface ─────────────────────────────────────────────────────────╮
   │ cli 3566                                          13 out · 0 in   │
   ╰───────────────────────────────────────────────────────────────────╯
      │ ╌╌ 4 private crossings ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╮
      ▼                                                              ┊
   ╭─ domain ─────────────────────────────────────────────────────╮   ┊
   │ _pipeline 442   _arch 359   _archive 339   _guard 286        │◄──╯
   │ _verify 245     _tracker 227   _workmux 191   _settings 173  │
   │ _session 102    _bundle 92                                   │
   ╰──────────────────────────────────────────────────────────────╯
      │ ▲
      │ ┊  _paths      → _tracker.load_key_pattern      ← the one upward
      ▼ ┊  _tracker    → _paths.DEFAULT_KEY_PATTERN        edge, and the
   ╭─ resolution ─────────────────────────────────────╮     only cycle
   │ _paths 446      _manifest 42                     │
   ╰──────────────────────────────────────────────────╯
      │
      ▼
   ╭─ durability ─────────────────────────────────────╮
   │ _io 66                            0 out · 5 in   │
   ╰──────────────────────────────────────────────────╯
```

**An arrow is an import that exists in the source today.** `A → B` means some
statement in `A` imports a name from `B`, whether at module load or inside a
function. It does not mean a call at runtime, a data flow, or a dependency
anyone intended. Numbers are lines of code; `out`/`in` count modules, not
imports.

**A band groups modules by what they may depend on**, not by subject. Edges run
downward or sideways: a module may import anything in its own band or any band
below it. One edge runs upward, and it is drawn.

## The bands

| Band | What it owns | Test that a module belongs |
|---|---|---|
| **surface** | Everything a user or agent can invoke: argument parsing, console output, exit codes. | Removing it changes what `wfctl --help` lists. |
| **domain** | One area of wfctl's subject each — the pipeline, the records, the archive, the tracker, worktrees, settings. | It answers a question about wfctl's problem, not about this machine. |
| **resolution** | Where things are on *this* checkout: repo root, branch, spec root, arch root, state dir, the manifest that declares them. | Its answer changes when you move the checkout, not when you change the feature. |
| **durability** | Getting bytes onto disk without a half-written file surviving a crash. | It would be correct in a program that was not wfctl. |

The bands were recovered from the graph, not imposed on it: 13 of 14 modules
already obey them. That is the useful finding — a layering exists and nobody had
written it down, so nothing could hold it.

## What separates each band, and what breaks if it moves

**surface / domain.** `cli` holds every `typer` decorator, every `console.print`
and every `typer.Exit`; no domain module imports `typer`. Move the line and the
domain modules become unusable from anything but a terminal — the pipeline
inference that `speckit-orchestrate` reads would come back wrapped in ANSI, and
`pipeline-state-is-one-payload` would have no payload to transform. `cli` is
3568 lines because it is the one place all thirteen meet; that is a consequence
of the boundary, not evidence against it.

**domain / resolution.** `_paths` answers "where" and never "what should happen
next". Move the line up and every domain module grows its own idea of where the
spec dir is, which is the split-artifact failure `resolve_spec_dir`'s docstring
already refuses. Move it down and `_paths` starts deciding pipeline questions.

**resolution / durability.** `_io` knows about tempfiles and `os.replace` and
nothing about wfctl. Move the line and atomicity gets reimplemented per caller;
the first one to write a plain `open(...).write()` loses a `next-step.md` to a
crash and nothing announces it.

## Where the bands do not hold

### One cycle, over one constant

```
   _paths.resolve_spec_dir  ──► _tracker.load_key_pattern(repo_root)
   _tracker.load_key_pattern ──► _paths.DEFAULT_KEY_PATTERN
```

Both are function-local imports carrying a comment that says why
(`_paths.py:379`, `_tracker.py:129`). The cycle is not accidental and it is not
harmless: it is held open by two authors each having noticed. Everything
crossing it is one string, `r"\d+"`. Decided in
`tracker-owns-the-issue-key-shape`.

### Four private names crossing into `cli`

```
   cli → _paths._SPEC_DIR_OVERRIDE       "WFCTL_SPEC_DIR"
   cli → _paths._STATE_DIR_OVERRIDE      "WFCTL_STATE_DIR"
   cli → _pipeline._current_step_name    which step still blocks
   cli → _pipeline._infer_steps          the whole inference
```

Named without line numbers on purpose: these four are the `crossings` block
below, which the test holds. A line number here would be a second copy that
nothing checks, and `cli.py`'s numbers moved twice while this file was written.

`_pipeline.py:53` states the rule the module intends — *"Public because `cli`
imports them — the data above stays private"* — and two names on that same
module break it. Decided in `the-underscore-is-the-module-contract`.

## Two things the drawing cannot show

**`_pipeline`'s public entry point is dead.** `infer_pipeline` (line 354) has
zero production callers and one test assertion; `_infer_steps` (line 131) is
what `cli` and every other test call. The underscore is answering "what is this
module's surface?" backwards. #115 is blocked on the same question.

**`_io` is not purely a durability layer.** Four functions: `write_json_atomic`
and `write_md_atomic` would be correct in any program; `append_event` knows the
filename `events.jsonl`; `load_agentconfig` knows `current.json` and has zero
callers anywhere, tests included. Decided in
`io-owns-durability-not-domain-files`.

## The pipeline, one layer up

`_STEPS` (`_pipeline.py:21`) is eight entries, each a command and one `auto`
flag. The first entry, `brainstorm`, runs the four gates `design-levels`
defines, two of which write durable records. One flag governs four gates, so
"return to level 2" — a routing outcome #122's record format and #127 both emit
— names a destination the step table cannot address. Decided in
`brainstorm-is-one-step-with-addressable-levels`.

## Staleness

The drawing is checked, not trusted. `tests/test_architecture_view.py` parses
the three blocks below out of *this file*, re-derives the import graph from
`wfctl/*.py` with an AST pass, and fails if they disagree. A new module with no
band, an edge that runs upward, a fifth private crossing, or a crossing that
gets fixed without the drawing being updated — each of those turns the drawing
red rather than stale.

What the check does not cover: the prose, the line counts, and whether a band
still means what its row in the table says. Those go stale silently, and a
reader who finds them wrong should edit them.

```layers
surface     cli
domain      _pipeline _arch _archive _guard _verify _tracker _workmux _settings _session _bundle
resolution  _paths _manifest
durability  _io
```

```upward
_paths -> _tracker
```

```crossings
cli -> _paths._SPEC_DIR_OVERRIDE
cli -> _paths._STATE_DIR_OVERRIDE
cli -> _pipeline._current_step_name
cli -> _pipeline._infer_steps
```
