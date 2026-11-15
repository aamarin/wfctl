# Quickstart: SVG drawings

How to check the change works, once it's built. Run each command from the worktree root.

## 0. Before the first edit to `_records.py`

Dump today's results for every record, as research R-010 describes:

```bash
uv run python <scratchpad>/drawing_corpus.py before
```

The script writes `accept_problems` and the `validate` findings for each record in `docs/architecture/` to `<scratchpad>/before.json`. It lives in the scratchpad and isn't committed.

## 1. The suite and the static checks

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy
python3 .github/scripts/check_imports.py
```

All four pass. The new tests are:

1. `tests/test_arch_drawing_svg.py` covers the SVG reader:
   - labels with `<tspan>` text joined, and the `failing-step` class among other classes
   - each problem in `data-model.md`, including a DOCTYPE, a directory named `x.svg`, a leading-slash link, a symlink out of `drawings/`, and two SVG links under one heading
   - the full `accept_problems` list for a one-kind and a multi-kind record with a problem, showing the problem line in place of `no drawing` or `doesn't draw one`, never beside it
   - a doctor warning for a one-kind proposed record in each problem case, and for an accepted record with a missing SVG
   - the edge warning with each `text-anchor`, no warning without a `viewBox` or `width`, and the font-size lookup order from research R-005
   - the "file missi" fixture at `x="708"`, start-anchored in a 760-wide `viewBox`, which warns, and the corrected label, which doesn't
   - each check run once with an SVG summary and once with a fence summary
2. `tests/test_arch_drawing_fingerprint.py` covers the sign-off:
   - the `accepted` Log line ends with each SVG's link and fingerprint, in heading order, and a fence record's line is unchanged
   - a CRLF copy and an LF copy of the same SVG get the same fingerprint
   - doctor warns about an accepted record whose SVG changed, and not about one that matches or has no fingerprint
   - accept on that record appends a `redrawn` line, leaves `status: accepted`, keeps `accepted_on` at the original date, and clears the warning
   - accept on an accepted record whose SVG matches refuses as today
3. `tests/test_review_gate.py`, extended: `wfctl arch accept x --agreed y` and `uv run wfctl arch accept x --agreed y` are refused, `wfctl arch accept --dry-run -- x` isn't, a `--dry-run` on one command doesn't let a second accept through, and `--dry-run` inside a quoted citation doesn't count.
   `tests/test_record_gate.py` and `tests/test_design_gate_drawing.py`, extended: a branch whose only record change is a `redrawn` line passes the record gate with "no boundary moved" in place, and the design gate still reads that answer. An `accepted` line added beside the `redrawn` line still counts as a record change.
   The design gate also gets a redraw as the branch's only arch-root change with no "no boundary moved" in place, once with a domain-page name list and once without. Both read the boundary question as unanswered. Without the name list, this is the general check, which the third review's plan missed.
   `tests/test_redraw_only.py` covers `arch.redraw_only` without git. Each case breaks one condition and returns false: a proposed record, an empty diff, a `redrawn`-shaped bullet added under `## Decision`, an added line that isn't a `redrawn` line, and a removed line. A Log whose last line had no newline still reads as a redraw. A line `_append_log` writes matches `REDRAWN_LINE`.
   `tests/test_paths_redraw.py` runs `record_change` and `decided_on_this_branch` on a real git repo. An uncommitted edit beside a committed redraw counts. An untracked record counts. A record with no trunk to compare against counts.
   `tests/test_scan_files.py`, extended: a redraw-only branch prints no `record:` line for that record, and its `Boundary` line reads as unanswered.
   The fingerprint tests also cover a redraw refused because the edited SVG dropped `failing-step`, and a redraw of an SVG with no fingerprint on the Log.
4. `tests/test_drawing_style_links.py`: each of the four links to `design-levels/references/drawing-style.md` resolves.
5. `tests/test_design_gate_drawing.py`, extended: a branch whose only arch-root change is an SVG in `drawings/` hasn't answered the boundary question. It's written first, and seen failing before `DRAWINGS_DIR` joins `non_record_subtrees`.

`tests/test_arch_labels.py` imports `fence_labels` from `wfctl/arch/_drawing.py` instead of calling `_records._labels`, and its assertions don't change. The two `sequence` assertions in `tests/test_arch_diagram_kinds.py` take the new `_DRAWING_FIX` text. The tests that accept for real patch `_at_terminal`, in `tests/test_arch_accept.py`, `tests/test_arch_accept_drawing.py`, and the pasted-bullet test in `tests/test_arch_accept_dry_run.py`.

The SVG reader tests also cover a UTF-16 file carrying a DOCTYPE, and a UTF-8 file declaring `encoding="UTF-16"` (research R-001).

## 2. No record's result changed

```bash
uv run python <scratchpad>/drawing_corpus.py after
```

The script dumps the results again and diffs them against `before.json`. The only differences are the `no drawing` line's new wording and `record-drawing-can-be-svg` (SC-002). Paste the summary line into the PR's verification notes.

## 3. A record whose only drawing is an SVG

```bash
uv run wfctl arch accept --dry-run -- record-drawing-can-be-svg
```

With its mermaid block removed, nothing about the drawing blocks it (SC-003). Rename the SVG temporarily and run it again. It refuses with `drawing links drawings/record-drawing-can-be-svg-data-flow.svg, which doesn't exist`, and doesn't also print `no drawing`.

## 4. The edge warning

Recreate the "file missi" overflow. In a scratch copy of the record's SVG, put `<text x="708" y="180" class="label">file missing</text>` back as commit `0d7e56d` had it, link it from a scratch proposed record, and run:

```bash
uv run wfctl doctor
```

It warns `drawing label 'file missing' runs past the drawing's edge`. Put the corrected label back, and the warning goes away (SC-005). Delete the scratch files.

## 5. The skills

```bash
uv run wfctl install-skills
uv run wfctl doctor
```

`doctor` reports nothing new. Then have an agent draw one record's SVG from the `architecture-decisions` skill, render it with `qlmanage -t -s 1200 -o <scratchpad> <file>.svg`, and check it against each rule in `drawing-style.md`.

`grep -rn "refused-edge" wfctl/agents/skills` finds the rule stated only in `drawing-style.md`. Other hits are links or template examples (SC-006).

`grep -rn -i "mermaid" wfctl/agents/skills/design-levels/SKILL.md wfctl/agents/skills/architecture-decisions/SKILL.md wfctl/agents/skills/model-the-domain/SKILL.md wfctl/agents/skills/model-the-domain/references/visual-language.md` finds no sentence saying a record is drawn in mermaid, or that acceptance needs a fence. Mermaid appears only as the other accepted format for a record, and as the format for a domain document.

## 6. The sign-off, from your own terminal

This step is the user's, since the guard refuses the real accept from the agent's shell. In a scratch clone, accept a proposed record whose drawing is an SVG:

```bash
wfctl arch accept <slug> --agreed "scratch check"
```

The `accepted` Log line ends with `drawing drawings/<file>.svg sha256:<12 hex>`. Move one box in the SVG, and `wfctl doctor` warns that the drawing changed since it was accepted. Run the same accept again, and it appends a `redrawn` line, and the warning goes away (SC-007).

From the agent's shell, the same command is refused by the guard, and `wfctl arch accept --dry-run -- <slug>` runs (SC-008).

## 7. The phone check

Before the PR merges, open `record-drawing-can-be-svg.md` on the branch in the GitHub mobile app, once with the phone in light mode and once in dark mode. The drawing's background and labels follow the phone's setting, as they do on the desktop site. If either mode shows dark labels on a dark page, the drawing needs a fallback before shipping, and the PR waits for it.

## 8. Config

```bash
uv run wfctl check config
```

Reports nothing new.
