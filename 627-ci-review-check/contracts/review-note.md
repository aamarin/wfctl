# Review note contract

Ref: `refs/notes/wfctl-review`.

Grammar, one event per line:

```
line   = group-line | sign-line
group-line = "reviewed by " group
sign-line  = "signed off by a person"
group  = a review group name, as review_config.PLAIN_NAME accepts it
```

A reader:

1. Splits the note on newlines and strips each line.
2. Skips blank lines and lines matching neither form.
3. Treats `reviewed by <g>` as a review only when `<g>` is a group the
   trunk's or the head's `wfctl.json` lists.

A writer:

1. Writes only through wfctl (`record`), never `git notes add -f`, so an
   existing line is never rewritten.
2. Appends a line only when the note doesn't already hold it.

Joining two machines' notes uses `git notes merge -s cat_sort_uniq`, which
keeps every distinct line from both. The order of lines carries no meaning.
