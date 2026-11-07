# Contract: a code reviewer's report

The coordinator in `fanning-out-code-review` reads each reviewer's report. This feature adds one section to it, after the findings and before `net:` and the verdict.

```
## Review: <target>

WARNING signup.ts:L12 — form allows a 40-character username, server caps it at 32 (schema.ts:L8) → add maxlength 32
WARNING comments/list.vue:L30 — renders comment text unescaped; the preview got escaping in a1b2c3d (preview.vue:L14) → escape here too

Inputs traced
  username      form: 1–40 · server: 1–32 · column: varchar(64)   ← mismatch
  --rounds flag parser: int · check: ≥ 0 · wfctl.json: int          consistent

Rules checked
  comment text is escaped   preview ✓ · list ✗ · email digest ✓

net: −0 lines possible
Verdict: Request changes
```

- A consistent input takes one line.
- A layer the reviewer couldn't read is written `unknown (<reason>)`.
- A change with no inputs and no new rules writes one line in place of both lists: `Inputs traced: none — the change reads no outside value and adds no rule`.
- A layer mismatch is WARNING or above.
