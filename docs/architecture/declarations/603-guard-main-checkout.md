# No new boundary — 603-guard-main-checkout

The guard adopts the rule the spec store already applies, that a commit in the main checkout never counts as a commit to a store. Asking git which branch a commit lands on is already the store's job under spec-storage-read-from-git, and the store has blocked the main checkout since 9ddb8cd. No component gains or loses authority. The guard now refuses one commit it used to allow, into a state folder inside the main checkout when the spec root is the main checkout, and that is the guard catching up with the store rather than a new rule.
