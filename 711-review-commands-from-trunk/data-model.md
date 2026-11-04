# Data model

No new persisted state. `run.json` keeps its shape:

- `reviewers[].command`: now the trunk's command for the reviewer's model.
- `reviewers[].state`: `unavailable` also when the trunk has no command for the model, with `reason` set to `no command in wfctl.json on <ref>`.

In memory, `TrunkCommands` carries `commands` (model to command) and `ref` (the trunk's short name).
