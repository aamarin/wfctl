# Quickstart: declare pipeline step

What to run to see this working, and what the suite must grow. The project's
declared verification is unchanged and comes first:

```bash
uv run --frozen --extra dev pytest -q
uv run --frozen --extra dev ruff check wfctl/ tests/
uv run --frozen --extra dev mypy wfctl/
```

Then, because this touches `wfctl/agents/`:

```bash
uv run wfctl install-skills --prune --yes --agent claude
uv run wfctl doctor
```

`uv run`, not a bare `wfctl` — in this repo the two carry different bundles, and
only `uv run` answers the question this branch cares about.

## Declare a pass and walk a branch through it

The end-to-end exercise for User Story 1. A test that constructs the payload
directly has not tested that a repository can reach it.

1. In a scratch repository, add to `wfctl.json`, and seed the command as
   installed (`check config`'s own job is to say when it is not, so the
   exercise needs it present to reach the rest of the walkthrough):

   ```json
   { "steps": { "brainstorm": [
       { "name": "ui-design",
         "command": "/pfms-ui-design-workflow",
         "evidence": "ui-contract.md" } ] } }
   ```

   ```bash
   mkdir -p .agents/commands
   echo '# ui' > .agents/commands/pfms-ui-design-workflow.md
   ```

2. `uv run wfctl check config` — expect `✓ wfctl.json: 1 pass under 1 step`,
   exit 0.
3. `uv run wfctl status` — expect `ui-design` indented under `brainstorm`, after
   wfctl's own two passes, all three `○`: nothing under `brainstorm` has run
   yet, so the step's own reading is `pending` and no pass — declared or
   built-in — is evaluated ahead of it (research.md R7).
4. `uv run wfctl status --json` — expect the pass in `sub_steps` with
   `"manual": false` and `"claimed": null`.
5. Satisfy wfctl's own two passes — a record under `wfctl arch-root`, or
   `wfctl arch none --reason "…"`, and a `design.md` in the feature directory.
   Written order runs the tool's passes before the repository's (FR-003), so
   `ui-design` is not reachable before they are.
6. `uv run wfctl status` — `architecture` and `design-doc` now read `●`,
   `ui-design` reads `▶`, and `brainstorm` itself reads `▶` rather than `●`:
   the step's own artifacts are there, but a pass under it is still
   outstanding (research.md R7, FR-006).
7. Ask what to do next. Expect `/pfms-ui-design-workflow`, not
   `/speckit.brainstorm`, and `auto: false` — a declared pass defaults to
   requiring review.
8. Write `ui-contract.md` into the feature directory. Re-read the position:
   the pass reports `●` and the step moves on.

## Read wfctl's own passes

User Story 2, on a branch part-way through brainstorming. The existing
assertions read a named step's state out of a mapping and keep passing whether
or not the passes appear, so this one has to be looked at.

1. On a branch with an architecture record written and no `design.md`:
   `uv run wfctl status`.
2. Expect `architecture ●` and `design-doc ▶` — the outstanding pass draws the
   same glyph an outstanding step does — each on its own row, and `brainstorm
   ▶`.
3. Expect the next command to name what writes the outstanding artifact.
4. Confirm nothing on either row says it came from wfctl rather than from
   configuration (FR-011).

## Claim a pass away, twice

User Story 3, and SC-005.

1. `uv run wfctl step none brainstorm.ui-design --reason "backend-only change"`
   — expect `✓`, and the file under `<arch-root>/step-claims/<branch>/`.
2. `uv run wfctl status` — the row is gone.
3. `uv run wfctl status --all` — the row is back, carrying the reason.
4. Claim a second pass away. Re-read both claims: **both survive.**
5. Claim the first one away again with a different reason: one file, the new
   reason.
6. `uv run wfctl step none brainstorm.ui-design --reason "<why>"` — refused,
   and nothing written.

## The one where a wrong answer looks like success

SC-006. On a branch that has claimed a pass away and drawn no boundary:

```bash
uv run wfctl status
```

The design gate must still hold the work. If `brainstorm` reports clear, the
claim has been counted as a record and `non_record_subtrees` is missing
`step-claims/`.

## Tests to add

Named by what they catch, in the house style — the docstring says why the test
exists, not what it asserts.

| Test | Catches |
| --- | --- |
| a step with no declared passes renders exactly what it renders today | the regression every repository would see first |
| a pass under one step and a pass of the same name under another are both accepted | FR-002a read as global uniqueness |
| a bare name matching two passes is refused with both candidates named | FR-002c |
| a bare name is not resolved against the current step | FR-002c, the failure the references note argues is silent |
| a declared pass runs after wfctl's own, and `before` moves it ahead | FR-003 |
| a cycle in `before` / `after` is a finding, not an order | FR-003a |
| a pass declaring passes of its own is a finding, and the outer pass is not loaded | FR-004 |
| a step with one outstanding pass reports unfinished | FR-006 |
| a manual pass names the pass and never a command | FR-007, FR-022a |
| `evidence` resolves against the feature directory, not the repo root | R3 — the false-`done`-forever failure |
| two claims on one branch both survive | FR-015, SC-005 |
| a claim does not satisfy the boundary check | FR-016, SC-006 |
| `--all` shows a claimed pass with its reason; the default hides it | FR-018, FR-019 |
| `--json` carries a row the console hid | FR-020 |
| a declared pass defaults to `review_required`; a tool pass to `automatic` | FR-021 |
| an overridden declared pass is byte-identical to a tool pass in the payload | FR-021a, FR-011 |
| `check config` exits non-zero on each finding class | FR-022 |

`tests/pipeline_payload_snapshot.json` is rewritten wholesale by the new rows.
Its own docstring already names updating it as how a deliberate change in verdict
is declared. Exactly one assertion in the suite pins `current == "brainstorm"`;
the rest read a named step's state out of a mapping and are undisturbed.
