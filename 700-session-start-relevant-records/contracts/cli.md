# CLI contract: `wfctl arch context` and the session report

## `wfctl arch context [--all]`

Exit 0 in every case.

Narrowed (at least one accepted record left out):

```
# Architectural contract — 6 of 28 accepted decisions apply to this branch
Contexts: install-and-drift

<slug and decision, per record, as today>

22 accepted records govern only other contexts — `wfctl arch context --all` prints them
<the existing "N records not shown (…)" line, unchanged>
```

Not narrowed because the branch lists no contexts (name list present):

```
# Architectural contract — 28 accepted decisions

<records>

Every accepted record is printed, since design.md lists no contexts for this branch yet.
<the existing "N records not shown (…)" line>
```

Not narrowed because a listed name is unknown:

```
<header and records as above>
⚠ Every accepted record is printed, since design.md lists sesion-continuity, which isn't on the domain page.
```

No name list, nothing left out, or `--all`: exactly today's output.

Singular forms: `1 of 28 accepted decisions applies`, `1 accepted record governs
only other contexts`.

## `wfctl status --session`

```
Records: 6 of 28 accepted apply to this branch · `wfctl arch context` prints them, `--all` prints every one
```

Not narrowed:

```
Records: 28 accepted · `wfctl arch context` prints them
```

## `wfctl status --session --json`

Adds `applying_records` (`int | null`) beside `accepted_records`. The session
keys become eleven.
