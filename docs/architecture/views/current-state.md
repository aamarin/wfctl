# wfctl as it stands

A drawing of the modules wfctl ships, the bands they fall into, and the three
places the bands do not hold. It **describes**; it does not constrain. The
records under `docs/architecture/` constrain, and this file lives one directory
down from them because `_arch.load_records` globs `*.md` non-recursively at the
arch root — a view placed there would be read as a record and reach agents
through `wfctl arch context` as if someone had agreed to it.

Derived from `wfctl/*.py` at `793fd95`. What keeps it honest is
`tests/test_architecture_view.py`, which re-derives the import graph and fails
when this drawing stops matching it. See **Staleness** below.

```
   ╭─ surface ─────────────────────────────────────────────────────────╮
   │ _entry 35                                          2 out · 0 in   │
   │   └─► cli 5266                                    15 out · 1 in   │
   │   └─► _hook 110                                    1 out · 2 in   │
   ╰───────────────────────────────────────────────────────────────────╯
      │      ╎ 2 private crossings into _pipeline
      │      ╎ 2 into _paths ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╮
      ▼      ▼                                                           ┊
   ╭─ domain ─────────────────────────────────────────────────────╮      ┊
   │ _pipeline 439   _predicates 603   _arch 458   _archive 339   │      ┊
   │ _guard 293      _verify 245      _tracker 497   _workmux 274 │      ┊
   │ _settings 173   _shape 260       _session 486   _bundle 126  │      ┊
   │ _body 399       _change 199                                  │      ┊
   ╰──────────────────────────────────────────────────────────────╯      ┊
      │ ▲                                                                ┊
      │ ┊  _paths      → _tracker.load_key_pattern      ← the one upward ┊
      ▼ ┊  _tracker    → _paths.DEFAULT_KEY_PATTERN        edge, and the ┊
   ╭─ resolution ─────────────────────────────────────╮     only cycle   ┊
   │ _paths 660      _manifest 42                     │◄────────────────╌╯
   ╰──────────────────────────────────────────────────╯

   ╭─ mechanism ──────────────────────────────────────╮  ◄── _arch _session
   │ _io 43                            0 out · 5 in   │      _tracker
   │ _md 98                            0 out · 3 in   │      _verify cli
   ╰──────────────────────────────────────────────────╯  ◄── _arch _body
                                                             _shape
```

`_entry` is drawn above the two it reaches because it is the only one with no
importer: it is what the console script resolves to, and it decides which of the
other two answers. `_hook` reaches `_guard` directly and nothing else, which is
what lets the guard run without `cli` — see the surface split below. The line
counts were re-derived for #314, which split `_pipeline` into it and `_predicates`
and is why this drawing changed at all. The four crossings are unchanged: the
split moved helpers `_pipeline` used privately into a module that now owns them,
so `_pipeline` reaches them by public name and no fifth crossing was added.

`_io` is drawn at the bottom because it may be imported from anywhere and
imports nothing back — not because resolution reaches it. Neither `_paths` nor
`_manifest` imports `_io`; its five importers are the four domain modules and
`cli`, named beside the box. A band below another is *available* to it, not
used by it.

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
| **mechanism** | Primitives with no subject of their own: replacing a file without a half-written one surviving a crash, and finding where a fenced block starts and ends. | It would be correct in a program that was not wfctl. |

The bands were recovered from the graph, not imposed on it: 13 of 14 modules
already obey them. That is the useful finding — a layering exists and nobody had
written it down, so nothing could hold it.

## What separates each band, and what breaks if it moves

**surface / domain.** `cli` holds every `typer` decorator and every
`typer.Exit`, and no domain module imports `typer`. Move that line and the
domain modules become unusable from anything but a terminal — the pipeline
inference that `speckit-orchestrate` reads would come back wrapped in ANSI, and
`pipeline-state-is-one-payload` would have no payload to transform. `cli` is
3627 lines because it is the one place all thirteen meet; that is a consequence
of the boundary, not evidence against it.

The boundary holds for control flow and **leaks on output** — see below. It is
drawn here as one line because that is how it reads from the import graph, which
is the third thing this drawing cannot show you.

**domain / resolution.** `_paths` answers "where" and never "what should happen
next". Move the line up and every domain module grows its own idea of where the
spec dir is, which is the split-artifact failure `resolve_spec_dir`'s docstring
already refuses. Move it down and `_paths` starts deciding pipeline questions.

**resolution / mechanism.** Both modules here know nothing about wfctl: `_io`
knows about tempfiles and `os.replace`, `_md` about where a fenced block starts
and ends. Neither can name a spec dir, a branch or a pipeline step, and that is
what the band collects.

**The band was called `durability` until `_md` joined it, and the rename is the
correction rather than the change.** The third column has always been the
admission rule and it decided every module here; the name and the "owns" cell
described the single member that happened to satisfy it, so a second member
satisfying the same rule and writing no bytes made them read as a contradiction.
Naming the band after its own test is what stops the next generic primitive
having to argue about a word.

Move the line and each is reimplemented per caller, which is where both came
from. The first caller to write a plain `open(...).write()` loses a
`next-step.md` to a crash and nothing announces it; the three that each had
their own fence walker disagreed about what closes one, so a document quoting a
fenced example had the rest of the quotation scanned as prose.

## Where the bands do not hold

### One cycle, over one constant

```
   _paths.resolve_spec_dir  ──► _tracker.load_key_pattern(repo_root)
   _tracker.load_key_pattern ──► _paths.DEFAULT_KEY_PATTERN
```

Both are function-local imports, so neither breaks module load. Only one says
why: `_paths.py:379` carries *"lazy: avoids import cycle at module load"* and
`_tracker.py:129` carries nothing. So the cycle is survived rather than managed
— one author left a note and the next reader of `_tracker` has no way to learn
that the import's position is load-bearing. Everything crossing it is one
string, `r"\d+"`. Decided in `tracker-owns-the-issue-key-shape`.

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

### Two domain modules print, and the graph cannot see it

```
   _tracker.py:23   console = Console(highlight=False)    6 console.print
   _verify.py:25    console = Console(highlight=False)   10 console.print
   _paths.py:49     raise SystemExit("wfctl: not a git repository")
```

The surface band is supposed to own console output and exit codes. Two domain
modules emit rich markup directly, and `_paths` — a band lower still — exits the
process. Both were deliberate locally: `_tracker`'s `highlight=False` carries the
comment *"this output is parsed by agents, so keep it plain"*, which is a module
solving the ANSI problem for itself rather than being kept out of it.

**No arrow above shows this**, and no version of that drawing could: `rich` is a
third-party package, so a domain module importing it creates no *internal* edge.
The band model is defined over the import graph, and this leak is invisible to
it. That is a limit of the whole method here, not an omission in this diagram —
which is why it is written out rather than drawn.

Undecided. Unlike the three above, this one has no record: it was found during
review of this view rather than in the pass that produced it, and #149 phase 1
does not pre-decide what phase 2 moves.

### The surface band split, because importing it got expensive

```
   wfctl (console script)
     └─► _entry        argv dispatch, and nothing else
           ├─► _hook   one path: stdin, git, exit code       ~34 ms
           └─► cli     every other path: typer + rich        ~82 ms
```

`cli` is surface and always was. `_entry` and `_hook` are surface too, and they
exist because one caller could not afford to enter the band through `cli`:
`hook worktree-guard` runs before every Bash call an agent issues, and reaching
it through `cli` cost `typer` (47.5 ms) and `rich.console` (26.7 ms), neither of
which that path uses (#135).

So this is a band with two doors rather than a new band. The decision still
lives in `_guard`, one band down, and both doors reach it the same way — which
is what makes the split safe to have: `_entry` holds no policy, and `_hook` holds
no policy either beyond which fields of a payload it will trust.

**What this costs.** `cli` is no longer the only surface module, so "does `wfctl
--help` list it?" stops working as the band's membership test — it lists neither
of these. The test that still holds is the band's description rather than its
proxy: both parse input, both decide an exit code, and neither answers a question
about wfctl's subject.

## Two things the drawing cannot show

**`_pipeline`'s public entry point is dead.** `infer_pipeline` (line 354) has
zero production callers and one test assertion; `_infer_steps` (line 131) is
what `cli` and every other test call. The underscore is answering "what is this
module's surface?" backwards. #115 is blocked on the same question.

**`_io` is not purely mechanism.** Two functions: `write_atomic` would
be correct in any program; `append_event` knows the filename `events.jsonl`.
`load_agentconfig`, which knew `current.json` and had no callers, is gone — the
easy half of the same finding, cut ahead of the move. Decided in
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

**What the check does not cover**, in rising order of how much it would hurt:

- The prose, the line counts, and whether a band still means what its table row
  says. These go stale silently; a reader who finds one wrong should edit it.
- **The box art above.** The test reads the three fenced blocks, not the
  picture, so the drawing carries a second copy of band membership that nothing
  compares. Add a module to `layers` and forget the box and the suite stays
  green while the picture is wrong. Every review of this file found something in
  the drawing the blocks got right.
- **Anything that is not an import.** The band model is defined over the import
  graph, so a responsibility leaking through a third-party package — the two
  domain modules printing, above — creates no edge and cannot be caught here by
  any refinement of this check. It is the class of drift with no mechanical
  answer, and the reason "how would we know this went stale?" is answered with a
  test *and* a section admitting what the test cannot reach.

```layers
surface     cli _entry _hook
domain      _pipeline _predicates _arch _archive _guard _verify _tracker _workmux _settings _shape _session _bundle _body _change
resolution  _paths _manifest
mechanism   _io _md
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
