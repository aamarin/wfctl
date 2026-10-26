# CLI contract: design gate (#648)

## `wfctl status`, held on the pass

A branch with `design.md` and an architecture answer, and no software design
answer:

```
brainstorm   ▶  ← current
  architecture      ●
  software-design   ▶  no software design record for this change
  design-doc        ○
specify      ○
…
plan         ○
  plan-review       ○
  plan-walkthrough  ○
…
next: /speckit.brainstorm
  Either record the structural choice this change makes — one file under:
      docs/architecture/design/
  or state that it makes none:
      wfctl step none brainstorm.software-design --reason "<why>"
```

`design-doc` reads `○` while the pass holds, because every pass after a held
one is `pending`.

The pass column is the 2-space indent plus the longest pass name in the
payload plus two spaces, so every glyph has a gap before it. With the built-in
`plan-walkthrough`, that's 20 columns in every repository. The location line is
`arch_location(<arch-root>/design, repo_root)`, which is always repo-relative
here, since an arch root outside the tree holds on the git reason below
instead.

## `wfctl status`, held because git can't answer

With no base branch, or an architecture folder outside the project, both
checks hold on the same reason:

```
brainstorm   ▶  ← current
  architecture      ▶  git can't see whether this branch wrote a record
  software-design   ○
  design-doc        ○
…
next: /speckit.brainstorm
  If this repo's base branch isn't main, master, or dev, name it in wfctl.json:
      { "trunk": "<branch>" }
  If wfctl.json already names one, run `wfctl check config` to see what's wrong.
  If the architecture folder is outside the project, turn these checks off:
      { "design_record_checks": "off" }
```

`software-design` reads `○` because the held `architecture` check comes first.

## `wfctl status --all`, checks turned off

```
brainstorm   ●
  architecture      –  turned off by design_record_checks in wfctl.json
  software-design   –  turned off by design_record_checks in wfctl.json
  design-doc        ●
```

The glyph is whatever `status` draws today for a `skipped` pass.

`wfctl next` and `wfctl resume` write the same remedy to `next-step.md` under
`how:`, as they do for the architecture pass.

## `wfctl status`, answered by a claim

The `software-design` row is hidden. `wfctl status --all` shows:

```
  software-design   –  claimed: no new module or pattern
```

## `wfctl status`, answered by a record

```
  software-design   ●
```

## `wfctl status --json`

The payload version stays `1.3`. A pass list is data, and adding a pass adds an
element, not a field.

While the pass holds, the brainstorm step carries:

```json
{
  "name": "brainstorm",
  "state": "in_progress",
  "reason": "no software design record for this change",
  "remedy": "  Either record the structural choice this change makes — one file under:\n      docs/architecture/design/\n  or state that it makes none:\n      wfctl step none brainstorm.software-design --reason \"<why>\"",
  "sub_steps": [
    {"name": "architecture", "state": "done"},
    {"name": "software-design", "state": "in_progress", "command": "/speckit.brainstorm"},
    {"name": "design-doc", "state": "pending"}
  ]
}
```

Fields not shown keep today's values.

## `wfctl step none brainstorm.software-design --reason "…"`

Unchanged. It writes the claim and exits 0, with or without `wfctl.json`.

## `wfctl check config`

With `brainstorm: [{"name": "software-design", …}]` in `wfctl.json`:

```
brainstorm.software-design is wfctl's own pass; rename the declared one
```

This is today's message for any built-in name.

With `{ "design_record_checks": "yes" }`:

```
'design_record_checks' is 'yes'; use "on" or "off"
```

With the arch root outside the project and the setting not `"off"`:

```
the architecture folder is outside the project, so git can't check it, and every branch will be held at brainstorm; set "design_record_checks": "off"
```
