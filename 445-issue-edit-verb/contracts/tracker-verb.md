# Contract: the `edit` tracker verb

A backend declares `edit` in the `verbs` section of its tracker config.

| Placeholder | Value |
| --- | --- |
| `{id}` | the issue id |
| `{field}` | `title` or `body` |
| `{value}` | the new text for that field |
| `{me}` | the config's `identity`, as for every verb |

Any other placeholder is a `tracker-check` finding.

The GitHub backend:

```json
"edit": ["gh", "issue", "edit", "{id}", "--{field}", "{value}"]
```

A tracker whose CLI doesn't name its flags `--title` and `--body` points the
verb at a script shipped beside its config, which maps the field name to its
own flag:

```json
"edit": ["bash", ".agents/trackers/jira-issue-edit.sh", "{id}", "{field}", "{value}"]
```

wfctl calls the verb once per field and treats a non-zero exit as that field's
write failing.
