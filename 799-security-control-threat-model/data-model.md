# Data model: Security control threat model

No stored state. The one structure is a section of a Markdown record.

## Threat model section

A `## Threat model` heading in a level-2 record, with these `###` parts in
this order:

| Part | Required | Holds |
| --- | --- | --- |
| `Defends against` | yes | Who the control stops and who it doesn't, in prose |
| `Must keep catching` | yes, may be empty for a removal | Numbered list. Each item is a short description, a colon, and one backticked form |
| `Accepts` | yes | Numbered list of forms the control gives up, then why |
| `Must let through` | no | Numbered list of ordinary work the control must not refuse, in the same item shape |

Validation:

- The heading names are fixed, since `reviewing-security` searches for them.
  A test compares the reference's headings with the ones the skill names.
- In this repository, each item under `Must keep catching` and
  `Must let through` in `accept-check-threat-model.md` carries exactly one
  backticked command, and a test runs it.

Relationships: the record's `governs` field names the contexts the control
sits in, which is how `wfctl arch context` prints it on a branch that changes
the control.
