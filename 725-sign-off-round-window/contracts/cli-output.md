# CLI output contract: `wfctl review start` after a sign-off

With no sign-off on the branch, every line is unchanged.

After a sign-off at `abc1234`, with a cap of 3:

```
security run 004 · round 1 of 3 since the sign-off at abc1234 · 1 commit since 9d8e7f6 · head b2c3d4e
```

When the group has used its window and a commit is left that the sign-off doesn't cover:

```
✗ security has run 3 of 3 rounds since the sign-off at abc1234, the most review.rounds allows
  Ask the user to run `wfctl review sign-off` in their own terminal.
```

When the group has used its window and the sign-off covers every commit left:

```
security has run 3 of 3 rounds since the sign-off at abc1234; the sign-off at abc1234 covers every commit left to review
```

A cap of 0 keeps today's wording ("review.rounds is 0, so security doesn't run"), with or without a sign-off.

`wfctl review sign-off` prints the same lines as today.
