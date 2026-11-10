# CLI contract: architecture views

The output each command adds or changes. Tests pin these strings with `NO_COLOR` set.

## `wfctl arch context`

A `Views` block is added at the end of the output, after every line about records. Paths are relative to the repository root when the architecture root is inside it (rule 4).

Branch listing `architecture-records, design-method`, in wfctl's repository after this change:

```
Views
  docs/architecture/views/system-context.md
  docs/architecture/views/container.md
  missing: docs/architecture/views/components/architecture-records.md
  missing: docs/architecture/views/components/design-method.md
```

Branch listing no contexts, same repository:

```
Views
  docs/architecture/views/system-context.md
  docs/architecture/views/container.md
  missing: docs/architecture/views/components/evidence-and-derivation.md
  missing: docs/architecture/views/components/architecture-records.md
  missing: docs/architecture/views/components/design-method.md
  missing: docs/architecture/views/components/install-and-drift.md
  missing: docs/architecture/views/components/session-continuity.md
  missing: docs/architecture/views/components/attention.md
  missing: docs/architecture/views/components/worktree-guard.md
```

Repository with no architecture folder:

```
Views
  missing: docs/architecture/views/system-context.md
  missing: docs/architecture/views/container.md
```

A present view whose covered code has moved on, or that wfctl can't check, prints with a mark in place of its plain path:

```
Views
  stale: docs/architecture/views/container.md (12 commits to wfctl/ since the view changed)
  unchecked: docs/architecture/views/system-context.md (no covers line)
  unchecked: docs/architecture/views/components/attention.md (covers names wfctl/attn/, which doesn't exist)
  unchecked: /Users/me/specs-arch/views/container.md (not in this repository's history)
```

Rules:

1. Present views print before missing ones, whether marked or not. Within each group, the system context view comes first, then the container view, then component views in the order the `Contexts` line lists them.
2. `--all` prints every component view, the same way it prints every record.
3. The block never changes the exit code. `arch context` exits 0 whatever is missing, stale, or unchecked.
4. View paths print the same way the records footer prints the architecture root, through `_paths.arch_location`: relative to the repository root when the root is inside it, and absolute when it isn't.
5. A view is stale when `git rev-list --count <view's last commit>..HEAD -- <covers paths>` is above 0. The count in the line is that number, and the paths are the `covers` line's paths, joined by `, `.
6. A view with no commit yet prints as a plain path, since it's being drawn now. wfctl knows a view has no commit only when `git log` exits 0 with empty output.
7. If either `git` call exits non-zero, the view prints as `unchecked: <path> (not in this repository's history)`. This happens when the architecture root is outside the working tree, the directory isn't a git repository, or `git` isn't installed. The exit code stays 0, as rule 3 says.

## `wfctl arch accept`

Each refusal this change adds prints in the shape `design.md` agreed: a `✗ <slug> <problem>.` line, then an indented `Fix:` line, wrapped at the terminal width. The record's path follows the last one.

```
✗ review-record-in-git-notes declares a sequence diagram but doesn't draw one.
  Fix: under '## Boundary', add a '### sequence' heading with a mermaid
  sequenceDiagram, including the step that fails (an alt block or a -x message).

  docs/architecture/review-record-in-git-notes.md
```

The other three:

```
✗ review-record-in-git-notes declares state twice.
  Fix: list each kind once in 'diagram:'.
✗ review-record-in-git-notes draws a '### component' heading, but 'diagram:' doesn't declare component.
  Fix: add component to the list, or remove the heading.
✗ review-record-in-git-notes declares 'flow', which is not a diagram kind.
  Fix: use data-flow, component, state, or sequence.
```

The existing blockers keep their shape: one `✗ <slug> cannot be accepted yet.` line with one indented line per problem. A record with both kinds of problem prints that block first, then each new refusal. For a record declaring one kind, the existing `no drawing: add a fenced block under '## Boundary'` line is unchanged. A record declaring more than one kind with no drawing at all prints one new refusal per declared kind, and not the `no drawing` line, so the same problem isn't reported twice.

## `wfctl doctor`

A proposed record gets one warning per problem, in the existing finding shape:

```
⚠ review-record-in-git-notes: declares a sequence diagram but doesn't draw one
⚠ review-record-in-git-notes: declares state twice
⚠ review-record-in-git-notes: draws a '### component' heading, but 'diagram:' doesn't declare component
```

A kind that isn't one of the four stays an error on every status, now named per kind:

```
✗ some-record: declares diagram 'flow', which is not a diagram kind
```

## No refusals from views

No command, pipeline step, or PR check refuses because a view is missing, stale, or unchecked (FR-007). The worktree guard, `wfctl verify`, and the brainstorm gate don't read views.
