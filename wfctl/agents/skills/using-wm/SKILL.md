---
name: using-wm
description: Reference for workmux (wm) — git worktrees + tmux as isolated dev environments. Use when starting work on a new branch, switching work streams, or when using-git-worktrees Step 1a asks for a native worktree tool.
---

# using-wm: Isolated Development Environments (workmux)

`wm` (workmux) treats each git branch as a complete isolated environment: a
linked worktree on the filesystem plus a persistent tmux session with a
configured pane layout and agent. Per-project setup (naming, ports, `.env`,
file copies) is applied automatically via hooks — so worktrees come up ready to
run, unlike raw `git worktree add`.

## The one rule agents must not forget

```bash
wm add <branch> --background        # -b for short
```

**Always pass `--background` (`-b`) when creating or opening from agent code.**
The foreground forms run `tmux switch-client`, which needs a TTY and
blocks/fails in a non-interactive context (headless agent, CI, mobile).
`--background` still runs all hooks and file ops — it just skips the attach.
This is what makes worktree creation work through an AI agent.

Get the path after creating:

```bash
wm add my-feature --background
cd "$(wm path my-feature)"
```

## Agent control plane (safe to script — no tmux attach)

```bash
wm list                 # all worktrees + agent/window status
wm list --pr            # with GitHub PR status
wm path <handle>        # print worktree filesystem path
wm status [<handle>...] # agent status (working / waiting / done)
wm add <branch> -b      # create worktree + session in background
wm open <handle> -b     # ensure/open window in background
```

`<handle>` is the worktree directory name (slugified branch). Both `add` and
`open` accept `-o/--open-if-exists` to be idempotent.

## Human UI (do NOT call from agent code — attaches tmux)

```bash
wm add <branch>         # foreground: switches you into the new window
wm open <handle>        # switch/attach to a window
wm dashboard            # TUI of all active agents
wm merge [<branch>]     # merge, then clean up worktree + window + branch
wm rm <handle>          # remove worktree + branch + window
```

`wm merge` and `wm rm` are destructive — **confirm with the user before
running them from agent code.**

## Project conventions live in `.workmux.yaml`

Do not assume defaults. A project's `.workmux.yaml` defines the real behavior —
read it before creating worktrees:

- `worktree_dir` / `worktree_naming` — where worktrees land and how they're named
- `window_prefix`, `mode` (`window` vs `session`), `panes`/`windows` layout
- `base_branch` — default base for new worktrees
- `post_create` / `pre_remove` hooks — setup that may allocate ports or rewrite
  `.env`. Available env vars include `$WM_HANDLE` and `$WM_WORKTREE_PATH`. A
  failing `post_create` aborts `wm add` but leaves the worktree on disk.

workmux has no hook that runs before a worktree is created, so a branch-name
rule is not enforced at creation. In a repo that uses wfctl, `wfctl start`
enforces it: a session in a worktree whose branch names no open issue is
refused, with the command that fixes it. Name the branch for the issue before
`wm add` rather than after.

`wm config reference` prints the full documented option set.

## Rules

**Do:**
- Pass `--background`/`-b` for every agent-driven `add`/`open`.
- Read `.workmux.yaml` first — branch naming and setup are project-specific.
- Use `wm path <handle>` to get the directory, then `cd` in.
- Run `wm list` / `wm status` freely — read-only.

**Don't:**
- Run foreground `wm add`/`wm open` from agent code — they attach tmux (needs a TTY).
- Use raw `git worktree add` — skips hooks and file ops.
- Auto-run `wm merge`/`wm rm` — destructive; confirm first.

## Relationship to `using-git-worktrees`

At Step 1a ("is there a native worktree tool?") the answer is **yes**:
`wm add <branch> --background` is that tool. Run the background form yourself
and `cd` via `wm path`, or ask the user to run the foreground form if they want
to land in the window. Skip the git fallback and the `.worktrees/` gitignore
check — workmux owns the worktree directory.
