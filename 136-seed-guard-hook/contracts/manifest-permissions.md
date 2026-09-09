# Contract: `manifest[<layer>]["permissions"]`

Written by `install-skills`, read by `uninstall-skills` and `doctor`. The layer
key is the agent layer, `claude` today.

## Shape

A list of records, each:

```json
{ "path": "<repo-relative settings file>",
  "rule": "<the exact string wfctl installed>",
  "added": true }
```

At most one record per `(path, rule)`. Order is not meaningful.

## Producer — `install-skills`

- Emits a record for every rule wfctl manages in that layer, whether or not this
  run changed anything. A rule already correct is still one wfctl owns and must
  account for on the way out.
- `added` is taken from the prior record when one exists for the same
  `(path, rule)`. Only when no prior record exists is it observed from the file:
  `true` when the rule was absent and this run added it, `false` when it was
  already there.
- A run that cannot read or write the settings file re-emits the prior record
  unchanged. The manifest layer is rewritten whole, so a record not re-emitted is
  gone, and with it wfctl's claim on an entry still in the consumer's file.

## Consumer — `uninstall-skills`

Removes the rule only when **both** hold:

- the record says `added: true`, and
- the file still carries `rule` exactly.

Anything else leaves the entry in place. When the record says `added: true` and
the text no longer matches, uninstall reports the file, the text found, and
`rule` — so a reader can tell a deliberate narrowing from a stale leftover.

## Consumer — `doctor`

Compares `rule` against the file and reports present or gone. Never *behind*: the
rule carries no version, so there is nothing for it to be behind. The report is a
`⚠` line and does not change the exit code.

## Guarantees this contract does not make

- **Durability.** The manifest is gitignored by convention. A fresh clone has no
  record, so uninstall there removes nothing — the same degradation the managed
  hooks already have, chosen deliberately as the safe side.
- **Standing preference.** A record says what happened at install time, never what
  the project wants. #313 owns that gap; until it lands, the refusal message is
  where a project learns its options.
