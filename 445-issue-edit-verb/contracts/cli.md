# Contract: `wfctl issue edit`

```
wfctl issue edit <id> [--title TEXT] [--body TEXT]
```

| Case | Output | Exit | Recorded |
| --- | --- | --- | --- |
| `--title` only, succeeds | the backend's stdout | 0 | one `issue-edit` |
| `--body` only, succeeds | the backend's stdout | 0 | one `issue-edit` |
| both, both succeed | the backend's stdout twice | 0 | two `issue-edit` |
| both, body fails | stdout, the backend's error, `✗ title changed, body write failed` | the backend's | one `issue-edit` |
| both, title fails | the backend's error, `✗ title write failed, body was not sent` | the backend's | none |
| one field, it fails | the backend's error | the backend's | none |
| neither field | `✗ 'edit' needs --title, --body, or both` | 2 | none |
| no id | `✗ 'edit' requires an issue id` | 2 | none |
| backend has no `edit` | `ℹ Tracker '<name>' does not support 'edit' — skipped`, once | 0 | none |
| no tracker configured | the existing "No tracker configured" notice, once | 0 | none |
| tracker config missing or invalid | the existing warning, once | 0 | none |

The id is never taken from the branch. Each value is passed to the backend as
one argument and never through a shell.
