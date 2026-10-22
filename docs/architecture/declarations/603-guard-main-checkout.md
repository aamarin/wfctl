# No new boundary — 603-guard-main-checkout

The guard adopts the rule the spec store already applies, that a commit in the main checkout never counts as a commit to a store. Asking git which branch a commit lands on is already the store's job under spec-storage-read-from-git, and the store has blocked the main checkout since 9ddb8cd. No component gains or loses authority, and the guard's verdicts do not change for any command, since another rule in the guard already refuses the main checkout as a shared folder.
