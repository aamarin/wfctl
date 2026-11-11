---
covers: [wfctl/_entry.py, wfctl/_hook.py, wfctl/_restart.py, wfctl/_restart_send.py, wfctl/_io.py, wfctl/_spec_store.py, wfctl/_review_notes.py, .github/workflows/]
---

# wfctl container view

wfctl runs as four separate processes and keeps its data in five stores. The
`wfctl` command does most of the work. The worktree guard and the session
restart hook are the same executable started by the agent host on a hook, and
the restart hook sends its keystrokes from a detached process of its own. CI
runs `wfctl` again on GitHub to check a PR's reviews.

Question: which parts of wfctl run or store data separately, and which way do
their dependencies point?

## Drawing

The stores rarely change shape, so they sit above the line, and every arrow
points up into them. No arrow points from a store down to a process, so the
drawing has no red arrow.

```mermaid
flowchart TB
  subgraph stable["Rarely change"]
    state["State dir<br/>events.jsonl, session-summary.md"]
    specs["Spec store<br/>spec root and specs-trunk"]
    notes["Review notes<br/>refs/notes/wfctl-review"]
    arch["Architecture root<br/>docs/architecture/"]
    skills["Installed skills<br/>.agents/, .claude/"]
  end
  subgraph volatile["Change often"]
    cli["wfctl command<br/>_entry.main → cli.app"]
    guard["Worktree guard<br/>_hook.worktree_guard"]
    restart["Session restart hook<br/>_restart.hook_main"]
    sender["Restart sender<br/>_restart_send"]
    ci["CI review job<br/>.github/workflows/review.yml"]
  end

  cli -->|"calls _io.append_event"| state
  cli -->|"calls _spec_store.store"| specs
  cli -->|"calls _review_notes.record"| notes
  cli -->|"calls arch.load_records"| arch
  cli -->|"install_skills_cmd copies wfctl/agents/"| skills
  guard -->|"calls _review_gate.refusal"| notes
  restart -->|"runs python -m wfctl._restart_send"| sender
  ci -->|"runs wfctl check reviews"| notes
```

## Notes

The installed skills are drawn as a store because `install-skills` writes them
and the agent reads them, and their shape changes only when wfctl ships a new
version. The skills tell the agent which `wfctl` commands to run, but that is an
instruction the agent follows, not an import, so it has no arrow.

The guard reaches the review notes through `_review_gate`, which reads them with
`_review`. It's drawn as one arrow because both modules run inside the guard's
process.
