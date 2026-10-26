# Quickstart: check the design gate end to end

Run this after the code and skill changes are in, from the `648-design-gate`
worktree.

Every `wfctl` below runs the working tree through `$WFCTL`. A bare `wfctl` is
the copy on PATH, which doesn't have this change, so it shows no
`software-design` row and refuses `brainstorm.software-design` as an unknown
pass.

1. Install the working tree's skills:

   ```bash
   uv run wfctl install-skills --prune --yes --agent claude
   ```

2. Make a scratch repository with a trunk, and a feature branch with
   `design.md` and an architecture answer:

   ```bash
   WFCTL="uv run --project /Users/andremarin/Development/wfctl/wt/648-design-gate wfctl"
   SCRATCH=$(mktemp -d)
   git -C "$SCRATCH" init -b main
   git -C "$SCRATCH" commit --allow-empty -m init
   git -C "$SCRATCH" switch -c 1-scratch
   cd "$SCRATCH"
   $WFCTL arch none --reason "scratch"
   mkdir -p specs/1-scratch && echo "# design" > specs/1-scratch/design.md
   ```

3. `$WFCTL status` holds brainstorm on `software-design` and prints both
   answers under `next:`.

4. Write and commit only the design record:

   ```bash
   mkdir -p docs/architecture/design
   echo "# scratch" > docs/architecture/design/scratch.md
   git add docs/architecture/design/scratch.md
   git commit -m "scratch record" -- docs/architecture/design/scratch.md
   ```

   `$WFCTL status` shows `software-design   ●` and specify is current. Then
   undo the commit and remove the file, leaving the declaration and `specs/`
   in place:

   ```bash
   git reset --soft HEAD~1
   git rm --cached docs/architecture/design/scratch.md
   rm docs/architecture/design/scratch.md
   ```

5. Run `$WFCTL step none brainstorm.software-design --reason "no new module"`.
   `$WFCTL status` hides the row and specify is current. `$WFCTL status --all`
   shows `claimed: no new module`.

6. Write `specs/1-scratch/spec.md` and remove the claim:

   ```bash
   echo "# spec" > specs/1-scratch/spec.md
   rm docs/architecture/step-claims/1-scratch/brainstorm.software-design.md
   ```

   Confirm with `$WFCTL status` that brainstorm doesn't hold.

7. Read the installed `design-levels`, `speckit-brainstorm`, and
   `software-design-decisions` skills under
   `/Users/andremarin/Development/wfctl/wt/648-design-gate/.claude/skills/`,
   since nothing is installed in the scratch repository. Confirm each names
   `wfctl step none brainstorm.software-design` where it covers a change with
   no structural choice. Test 13 checks the same thing in the source.

8. Check User Story 5 in a second scratch repository whose architecture folder
   is outside the project, with no `wfctl.json`:

   ```bash
   OUTSIDE=$(mktemp -d)
   SCRATCH2=$(mktemp -d)
   git -C "$SCRATCH2" init -b main
   git -C "$SCRATCH2" commit --allow-empty -m init
   git -C "$SCRATCH2" switch -c 2-scratch
   cd "$SCRATCH2"
   export WFCTL_ARCH_DIR="$OUTSIDE"
   mkdir -p specs/2-scratch && echo "# design" > specs/2-scratch/design.md
   ```

   `$WFCTL check config` exits 1 and reports that the architecture folder is
   outside the project. `$WFCTL status` holds brainstorm on `architecture` with
   `git can't see whether this branch wrote a record`, and
   the remedy under `next:` names `trunk` and `design_record_checks`. Then:

   ```bash
   echo '{ "design_record_checks": "off" }' > wfctl.json
   ```

   `$WFCTL status --all` shows both checks as `turned off by
   design_record_checks in wfctl.json`, and `$WFCTL check config` exits 0.
   Run `unset WFCTL_ARCH_DIR` when done.
