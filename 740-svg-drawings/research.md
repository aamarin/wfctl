# Research: SVG drawings

Each entry is a decision the plan rests on, why it was made, and what else was weighed.

## R-001: Parse SVG with `xml.etree.ElementTree`

- Decision: `read_svg` reads the file as bytes and decodes them as UTF-8, refusing a file that doesn't decode. It then refuses the decoded text if it contains `<!DOCTYPE`, in any case, and otherwise parses that same text with `xml.etree.ElementTree.fromstring`. A `ParseError`, an `OSError` (such as a directory named `x.svg`, or no read permission), or a `ValueError` (which covers `UnicodeDecodeError`) becomes the `can't be read` problem. None of them reaches the user as a traceback.
- Why decode first: a check on the raw bytes misses a UTF-16 or UTF-32 file, where `<!DOCTYPE` is spread across two or four bytes per character, and expat still parses the DOCTYPE (PR-019). Requiring UTF-8 closes that gap with one rule, and costs nothing, since GitHub and every drawing the style file teaches are UTF-8. The parser reads the same decoded text the DOCTYPE check read, so an encoding named in the XML declaration can't make the two see different characters. The implementation tests this with a UTF-16 file carrying a DOCTYPE, and with a UTF-8 file declaring `encoding="UTF-16"`.
- Rationale: It's in the standard library, so wfctl stays dependency-free. Entity expansion needs a DOCTYPE to declare the entities, and a hand-drawn SVG needs none. Refusing a DOCTYPE removes the entity question on every machine, whatever expat version the local Python links. Distribution builds of CPython often link the system libexpat, so the version is a property of the machine, not of Python 3.11 (PR-013). `wfctl doctor` runs over records in repositories the user didn't write, so a read failure has to come back as a problem line.
- Alternatives considered: Checking `pyexpat.version_info` once relies on version numbers to mean safety, and still needs a fallback for an old build. `defusedxml` adds a runtime dependency for a threat that needs a malicious commit to the repo's own arch root. Regular expressions over the raw text would misread nested `<tspan>` elements and comments.

## R-002: Find elements by local name, ignoring the namespace

- Decision: Match `text`, `tspan`, `style`, and `g` by the part of the tag after `}`, so `{http://www.w3.org/2000/svg}text` and a bare `text` both match.
- Rationale: A hand-written SVG may or may not declare `xmlns`. GitHub needs it to render, but a test fixture or a draft might leave it out, and the check shouldn't depend on it.
- Alternatives considered: Requiring the SVG namespace would refuse a drawing over a detail unrelated to what it shows.

## R-003: A label's width is 0.6 × font size per character

- Decision: The estimated width of a label is `len(text) × 0.6 × font_size`. Its extent depends on `text-anchor`: `start` covers `[x, x + w]`, `middle` covers `[x - w/2, x + w/2]`, and `end` covers `[x - w, x]`. A label is past the edge when its extent leaves `[min_x, min_x + width]`.
- Rationale: 0.6 is the usual average advance width for the sans-serif stacks GitHub uses, and it's slightly generous, so it errs toward a warning. On the existing SVG, "answers the boundary question" at 13px, centered at x=480, estimates to 223 units wide, which fits comfortably in 760. The "file missi" case was `<text x="708" y="180" class="label">file missing</text>`, start-anchored in a 760-wide `viewBox` (commit `0d7e56d`). Its 12 characters at 13px estimate to 93.6 units, so the label covers 708 to 801.6 and the warning fires. A test fixture recreates that exact label (PR-011).
- Alternatives considered: Per-character width tables are more accurate, but they depend on the font, and the SVG names a font stack, not one font. Rendering needs a tool wfctl doesn't ship (`design.md`, Not Doing 2).

## R-004: The edge comes from `viewBox`, then `width`

- Decision: The edge is `viewBox`'s min-x and width when the root has a `viewBox`. Otherwise it's `0` to the root's `width` attribute, with a trailing `px` stripped. A `width` given as a percentage, or no `viewBox` and no `width`, means no edge, so no warning.
- Rationale: `viewBox` is the coordinate system the `x` values are written in, so it's the right edge to compare against. A percentage width has no fixed size to measure against.
- Alternatives considered: Using the `width` attribute first would compare user-space coordinates against a display size whenever the two differ.

## R-005: Font size lookup order (clarify Q4)

- Decision: For each `<text>`, wfctl takes the first of these:
  1. A `font-size` attribute on the `<text>` itself.
  2. A rule in a `<style>` block whose selector is one class the `<text>` carries, such as `.name { font-size: 14px }`.
  3. A `font-size` attribute on the nearest ancestor that has one, including the root `<svg>`.
  4. A class rule matching that ancestor's class.
  5. 16, the SVG default.

  A selector list such as `.name, .label { … }` counts as one rule per class. Rules inside an `@media` block are skipped, since those carry the dark-mode colors and a font size set there applies only in one theme. Any other selector, such as `text.name` or `g .label`, isn't read.
- Rationale: This follows how the browser resolves it closely enough for the drawings the style teaches: the element's own attribute or class wins over an inherited value. The existing SVG sets `font-size="13"` on the root and `font-size: 14px` on `.name`, and this order gives 14 for the box names and 13 for the edge labels, which matches the rendered drawing.
- Alternatives considered: Attributes only (the first recommendation) would give every `.name` label 13 instead of 14 on the existing SVG. A full CSS parser is a dependency for one warning.

## R-006: Labels inside a `transform` are measured as written

- Decision: wfctl ignores `transform` attributes on a label or its groups, and measures the label at its written `x`.
- Rationale: The drawing style teaches absolute coordinates on a grid, so a translated group is uncommon. Applying transforms means composing matrices for one warning.
- Alternatives considered: Skipping any label inside a transformed group avoids a false warning but also hides real ones. Measuring as written is the simpler rule, and `drawing-style.md` tells the author to avoid `transform` on text.

## R-007: The image link is found by a markdown image pattern outside fences

- Decision: Under a heading, wfctl looks for `![alt](target)` on lines outside a fence, using `_md.walk_lines` the way `_drawing` already walks lines. An image whose target ends in `.svg`, isn't a URL (no `://`), and isn't `data:` is an SVG link. Any other image isn't a drawing. A heading with two SVG links is a problem, for the reason R-009 gives: a record carrying two drawings would pass with one of them unchecked (PR-014).
- Rationale: GitHub renders that form inline, and it's what `record-drawing-can-be-svg.md` already uses. An HTML `<img>` tag also renders, but nothing teaches it, and accepting it would mean parsing HTML in markdown. Two fences under one heading keep today's rule, where the first wins. The same reason applies to them, but refusing them would change acceptance results for existing records, which FR-011 rules out.
- Alternatives considered: Accepting `<img src>` as well. We didn't, for the reason above. A record that uses one gets "no drawing" and the fix line says to use a markdown image.

## R-008: A link outside `drawings/` is refused, not ignored

- Decision: The link is resolved against the record's folder, following symlinks, and checked for containment after resolving. If the resolved path isn't inside `<arch-root>/drawings/`, the summary carries a problem saying to move the file there. A link starting with `/` gets its own problem, because GitHub reads it from the repo root while a join to the record's folder reads it from the filesystem root. Telling that author to move a file that's already in `drawings/` would send them looking in the wrong place (PR-008).
- Rationale: The design gate excludes folders, not file types. An SVG anywhere else under the arch root would count as a changed record (`record-drawing-can-be-svg`, Considered).
- Alternatives considered: Ignoring it, so the record gets "no drawing". That hides the reason and sends the author looking for a missing file that exists.

## R-009: One heading with both a fence and an SVG link is a problem on the summary

- Decision: When a heading's subsection holds both a fence and an SVG link, the summary carries the problem "has both an SVG and a fenced block: keep one". Acceptance refuses it, and doctor warns while proposed (clarify Q1).
- Rationale: A record carrying two drawings would pass with one of them unchecked.
- Alternatives considered: First-wins and SVG-wins, both rejected in clarify.

## R-010: A one-off comparison shows no record's result changed

- Decision: Before the first edit to `_records.py`, a script in the session scratchpad dumps `accept_problems` and the `validate` findings for every record in `docs/architecture/` to a JSON file. After the change, the same script dumps them again and diffs the two. Two differences are allowed:
  1. The `no drawing` line's new wording (`contracts/cli.md`), on the 38 records that print it today.
  2. `record-drawing-can-be-svg`, which FR-016 changes on purpose.

  Any other difference fails the check. The result goes in the PR's verification notes, and nothing about it is committed.
- Rationale: FR-011 and SC-002 promise no change for the 47 mermaid records, and running old code against new code on the same records shows it directly. 44 of the 85 records are proposed and still being edited, so a committed snapshot of live records would fail the next branch that adds or edits one, for reasons unrelated to drawings (PR-006). The fence behavior stays pinned by the existing fixture-based tests, `test_arch_labels.py`, `test_arch_accept_drawing.py`, and `test_arch_diagram_kinds.py`. They run with three kinds of edit and no others: `test_arch_labels.py` imports `fence_labels` from its new module, two `sequence` assertions in `test_arch_diagram_kinds.py` take the new fix text, and the tests that accept for real patch `_at_terminal` (R-013).
- Alternatives considered: A committed snapshot limited to the 85 slugs as of this branch, skipping any record whose file changed since. It still breaks on an edit to one of those records, and the skip rule hides exactly the records most likely to regress. Re-taking the snapshot after the change proves nothing.
- FR-011 rewords two kinds of fix text. The `_DRAWING_FIX` entries print only under `wfctl arch accept`, since `accept_problems` carries only a refusal's problem half. The `no drawing` line is an `accept_blockers` string, so `accept_problems` carries it whole. That's why the comparison sees the `no drawing` line's change and none of the `_DRAWING_FIX` changes (PR-015). `validate` carries neither.

## R-011: The fingerprint goes on the Log line `arch accept` already writes

- Decision: When the record's drawing is an SVG, `accept` appends ` · drawing <link> sha256:<12 hex>` to the citation it passes to `_set_status`, once per SVG, in heading order. The hash is SHA-256 over the file's bytes with CRLF replaced by LF, cut to 12 hex digits. `accepted_on` keeps working, since it matches only the date and the `accepted` word at the start of the line.
- Rationale: The Log line is where the user's agreement is recorded, and the fingerprint says which version of the drawing that agreement covers. Putting it on the same line means one transition writes one line, as `_set_status`'s docstring requires. Twelve hex digits catch any accidental edit. The threat is an edit nobody looked at, not a forged collision, and a hand edit to the Log line shows in the PR diff like any other change to an accepted record. CRLF is normalized because git's `core.autocrlf` can rewrite line endings on checkout, which would warn on a drawing nobody changed.
- Alternatives considered: A separate `drawing` frontmatter field. It changes the frontmatter on every redraw, and the frontmatter holds what the record is, not who agreed to what. A sidecar file in `drawings/`. It splits one agreement across two files, and the design gate doesn't see `drawings/`.

## R-012: A changed drawing is signed off with `arch accept`, as a `redrawn` Log line

- Decision: `wfctl arch accept` on an accepted record whose SVG no longer matches its fingerprint appends `- <date>  redrawn     — <citation> · drawing <link> sha256:<new>`, and leaves the status unchanged. The append goes through a new `_append_log` helper, which `_set_status` also calls so the two can't format a Log line differently. Doctor compares each SVG against the last `accepted` or `redrawn` line naming that link. When every fingerprint matches, or the record has no SVG, accept refuses an accepted record as it does today.
- Rationale: The doctor warning needs a way to clear, or it becomes noise the user learns to ignore. The user already chose acceptance as the visual sign-off, so the same command clears it. The `accept` refusal on a non-proposed record exists so that a second `accepted` line can't claim a second agreement. A `redrawn` line claims something different, that the user looked at the new drawing, so it doesn't weaken that guard. It writes no `accepted` word, so `accepted_on` still reports the original date.
- Alternatives considered: An `approve-drawing` subcommand. The user rejected it as too verbose. Clearing the warning by superseding the record. That's the right answer for a change in meaning, but a layout fix would then cost a new record.

## R-013: The guard and a terminal check keep `arch accept` from agents

- Decision: `_review_gate.read` refuses a command matching `\bwfctl\s+arch\s+accept\b` unless the same command carries `--dry-run` as a whole shell word. It checks each part of the text split by `_SEPARATOR` on its own, so a `--dry-run` on one command doesn't let a second accept through. It splits each part with `shlex.split`, so `--agreed "after a --dry-run"` doesn't count, and a part `shlex` can't split is refused. `arch_accept_cmd` calls `_at_terminal()` when `--dry-run` is off, and refuses when stdin or stdout isn't a terminal. The call sits after every existing refusal and immediately before the write, because the parity tests in `tests/test_arch_accept_dry_run.py` require a dry run to make every refusal the real run makes, and a dry run never reaches the terminal check. The refusal reads `✗ wfctl arch accept is for a person to run in their own terminal, not an agent. An agent can run it with --dry-run.`
- Rationale: This is the shape the sign-off and import-approval commands already use: a text check the guard makes before the command runs, and a terminal check behind it for any form the text check doesn't recognize. The pattern is tighter than the sign-off pattern, which matches the two words anywhere in the text. "arch" and "accept" appear together in many commit messages and skill edits in this repo, and requiring `wfctl arch accept` as consecutive words still catches every direct form. `--dry-run` stays open because the brainstorm skill grants it, and the design gate prints it as the fix line for a drawing acceptance would refuse.
- Amended after the #769 review panels: the text check reads shell words rather than raw text, since the panels got a real accept past the pattern above in eighteen ways. The guard deletes backslash-newlines before splitting the command into parts. It splits each part with `shlex.split(comments=True)`, then looks for `arch accept` after a word naming wfctl. A word holding `$` or a backtick counts in any of the three positions, since the guard can't see what it expands to. A word holding whitespace is read as a command of its own, for the script `bash -c` runs. A `--dry-run` counts only where wfctl would read it as the flag: not after `#`, not as the value of `--agreed`, not as a redirect target, not after `--`, and never in a part holding a command substitution. The hook's substring test runs on the text with quotes and backslashes removed, and passes on `arch` as well as `accept`.
- A second panel round added three more rules. The literal name `wfctl`, in any case, followed by an expansion in the same word or the next one matches, since one variable can hold both words and `wfctl${IFS}arch${IFS}accept` splits only when the shell runs it. A glob such as `wf?tl` names wfctl. zsh's `>!`, `>|`, and `{fd}>` count as redirects.
- The code panel's second round on the squashed branch found the check failing in both directions, and the guard now reads commands differently. Previously, it split the text at `;`, `&`, `|`, and newlines before reading words. That split broke a quoted `bash -c` script in two, neither half parsed, and the fallback pattern wanted the lowercase name, so `bash -c "true; WFCTL arch accept …"` got through. A brace such as `{arch,}` got through too. In the other direction, the guard refused a commit message, a release note, or a grep that only names the command, and `grep -n wfctl "$f"`. Currently, `shlex` splits commands only at separators outside quotes, and a brace counts as an expansion. The outer command matches the name anywhere, unless its program is a text tool such as `grep` or `echo`. A quoted word is read again in one of two ways. It's a script when it follows a `-c` option or is an argument to a shell, and the name then has to start a command there, past assignments, runners such as `env` and `uv run`, and shell keywords such as `do`. Any other quoted word is prose, and only a `$(…)` or a backtick inside it runs, or a name right after a quote or a bracket, such as awk's or perl's `system("wfctl …")`. Every quoted word reads as a script when a shell is among the commands, since `echo '…' | sh` runs the echoed text. When `shlex` can't split the text, the fallback pattern reads the name in any case, through an expansion or a glob.
- The two checks together still have a gap. An invocation that hides from the text check and runs under the pseudo-terminal `script` provides passes both. Examples include arguments fed through `xargs` from stdin, a shell function wrapping wfctl, `eval`, a name built entirely from variables (`${W}ctl`), a glob name with the words in a variable (`A="arch accept …"; wf?tl $A`), a runner the guard doesn't know inside a quoted script (`bash -c "nice -n 5 wfctl arch accept …"`), an interpreter that builds the words as a list (`python -c "subprocess.run(['wfctl', 'arch', 'accept', …])"`), and words written in ANSI-C escapes (`$'w\146ctl' $'\141rch' $'\141ccept'`). No text rule can close that, and we accept it on the same tamper-evident ceiling R-011 sets. The fix would be a sign-off an agent can't produce.
- Alternatives considered: A separate issue. We folded it in because it's the same small pattern the guard already applies to two commands, and the fingerprint means nothing if an agent can accept a drawing nobody looked at. The terminal check alone. A pseudo-terminal satisfies it, which is why the guard's text check sits in front of it.
- Tests that call `arch_accept_cmd` without `--dry-run` through `CliRunner` patch `_at_terminal` to return true, as the sign-off tests do. That covers the real-accept tests in `tests/test_arch_accept.py` and `tests/test_arch_accept_drawing.py`, and `test_a_citation_pasted_from_a_bullet_is_a_citation_and_not_a_flag` in `tests/test_arch_accept_dry_run.py` (PR-021).

## R-014: A record changed only by `redrawn` lines isn't a changed record

- Decision: The check is split in two, the part that reads a record and the part that asks git.
  1. `wfctl/arch/_records.py` gets `redraw_only(diff: str, text: str) -> bool`, exported from the `wfctl.arch` package. `diff` is a `git diff -U0` of one record from the branch point, and `text` is the record as the diff leaves it. It returns true only when all four of these hold:
     1. `parse_status(text)` is `accepted`.
     2. The diff adds at least one line. An empty diff is not a redraw.
     3. Every added line matches `REDRAWN_LINE`, apart from the re-added last line condition 4 allows, and its line number on the new side, read from the hunk header, falls inside `## Log` as `_section_bounds` finds it in `text`, with `text` split on `\n` alone, as git counts lines.
     4. The diff removes no line, with one exception. When the old file's last line had no newline, the diff removes it with a `\ No newline at end of file` marker and adds it back unchanged, since `_append_log` adds the missing newline before it appends.
  2. `REDRAWN_LINE` is a compiled pattern in `_records.py`, beside `_LOG_STATUS_WIDTH`. `_append_log` builds the line and `redraw_only` matches it in the same module, and a test checks that a line `_append_log` writes matches the pattern (PR-027).
  3. `wfctl/_paths.py` gets the git side. `record_change(repo_root, path) -> tuple[str, str] | None` returns the diff from the merge base of the trunk and `HEAD` to the working tree, uncommitted edits included, and the file's current text. It returns None when there's no trunk, when git fails, when the merge base has no file at that path, or when the working tree has no file there. As a result, a new or untracked record is never a redraw (PR-025), and neither is a record deleted on the branch, which `records_on_this_branch` lists because `git status` and `git diff` report deletions.
  4. `records_on_this_branch` takes a keyword `skip: Callable[[str, str], bool] | None`. When it's set, a changed record is left out of the listing when `record_change` returns a pair and `skip` returns true for it. A None from `record_change` keeps the record. `_paths` is core and can't import `wfctl.arch`, so the caller passes `skip=arch.redraw_only`.
  5. `_paths` also gets `decided_on_this_branch(repo_root, arch, exclude, skip) -> bool | None`, a three-state sibling of `touched_on_this_branch`. It returns `touched_on_this_branch`'s None or False unchanged. When that returns true, it lists the changed paths and returns false only when every one is a record that `skip` drops.

  Five readers pass `skip=arch.redraw_only`:
  1. `_record_gate.touched`, which runs `git diff -U0 <trunk>...<head>` and `git show <head>:<path>` through the guard's session, so a git error refuses, as every error in the guard does.
  2. `_evidence.branch_records`, which the per-context design gate and the `architecture accepted` fact read.
  3. `_evidence._level_records` for level 3.
  4. The `record:` lines in `cli.py`.
  5. `_evidence._architecture_answered` and `cli._observe`'s `Boundary` line, which switch from `touched_on_this_branch` to `decided_on_this_branch`. Both answer the boundary question for a repo whose domain page lists no contexts, and the third review missed them (PR-020).
- Rationale: A redraw is the user's sign-off on a layout fix, not a new decision. Without the exclusion, the record gate refuses the PR of a branch that truthfully says no boundary moved, and tells the author to delete that answer. Once deleted, the design gate counts a picture plus a Log line as the boundary answer, which is what moving SVGs into `drawings/` was meant to prevent (PR-020).

  Each of the four conditions closes a way to pass a real change off as a redraw. Requiring an added line stops an uncommitted record, whose committed diff is empty, from reading as a redraw. Diffing to the working tree catches an uncommitted edit beside a committed redraw (PR-025). Requiring the lines inside `## Log` of an accepted record stops a bullet shaped like a Log line in `## Decision`, or a `redrawn` line on a proposed record, from skipping the gates (PR-026). Any other edit in the same record, including a hand-written `accepted` line, still counts.

  A hand-written `redrawn` line doesn't count, and we accept that gap. Anyone can compute the fingerprint, so an agent could change an SVG, append a matching `redrawn` line, and clear both the doctor warning and the record gate. Only the PR diff then shows the edit. That is the same tamper-evident, not unforgeable, ceiling R-011 sets for the Log line, and closing it would need a sign-off an agent can't produce, which nothing in wfctl provides today.

  The check that reads a record lives in `wfctl.arch` because the Log's format belongs to the module that writes it. The evidence context already imports `wfctl.arch`, so no new arrow goes on the Context Map. The git side lives in `_paths` beside `non_record_subtrees`, since that's where AGENTS.md sends a new reader of the arch root to find the exclusions it has to make.
- Alternatives considered: Keeping fingerprints in a file under `drawings/`, which the gates already ignore. We didn't choose it because an edit to that file would be invisible to the gates and harder to spot in the PR diff, and catching an unreviewed edit is the reason for the fingerprint. A rule that a redraw must land on its own branch. It's a rule nothing checks, and it still trips the record gate on that branch. A copy of the Log pattern in `_paths`, as the third review's plan had it. We didn't choose it because the writer and the reader would then spell one format in two modules, with nothing to keep them in step.
