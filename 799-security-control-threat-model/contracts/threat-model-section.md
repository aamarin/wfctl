# Contract: the threat model section

The author writes it, and the security reviewer reads it. Both follow
`architecture-decisions/references/threat-model.md`.

```markdown
## Threat model

### Defends against

<who the control stops, and who it doesn't>

### Must keep catching

1. <what the form is>: `<form>`

### Accepts

1. <what the form is>: `<form>`

<why these are accepted>

### Must let through

1. <what the form is>: `<form>`
```

The reviewer's report gains one line per record judged against, under its
`## security-and-hardening` heading:

```markdown
Judged against: docs/architecture/accept-check-threat-model.md (proposed)
```

A change to a control that no record has a threat model for is a finding:

```markdown
# Finding 1: Security control changed with no threat model: `wfctl/_review_gate.py:290`
```

Breaking changes to this contract are a rename of any of the four `###`
headings or of `## Threat model`. The heading test fails on either.
