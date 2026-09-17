codex
- `wfctl/_arch.py:425` — Input: `A --> B: known "invented shibboleth"`. Returns `['invented shibboleth', 'known']`; should return one transition label: `['known "invented shibboleth"']`. The de-duplication fix now splits a single mixed quoted label, causing false VR-007 warnings.

- `wfctl/_arch.py:423` — Input: `%% A --> B: invented shibboleth`. Returns `['invented shibboleth']`; should return `[]`. Mermaid ignores `%%` comments, including apparent diagram syntax.

- `wfctl/_arch.py:426` — Input: `A -->|invented shibboleth| B`. Returns `[]`; should return `['invented shibboleth']`. Pipe-delimited Mermaid edge labels are missed, so VR-007 fails to warn.

- `wfctl/_arch.py:428` — Input: `A --> B:::critical`. Returns `['::critical']`; should return `[]`. `:::` is Mermaid class syntax, not a transition label.

- `wfctl/_arch.py:423` — Input: `subgraph Storage Layer\nend`. Returns `[]`; should return `['Storage Layer']`. Bare subgraph titles are valid Mermaid labels and are missed.

- `wfctl/_arch.py:424` — Input: `A["Use [cache]"] --> B`. Returns `['"Use [cache']`; should return `['Use [cache]']`. The single-bracket regex terminates inside a quoted node label containing brackets.
hook: Stop
hook: Stop Completed
tokens used
138,644
- `wfctl/_arch.py:425` — Input: `A --> B: known "invented shibboleth"`. Returns `['invented shibboleth', 'known']`; should return one transition label: `['known "invented shibboleth"']`. The de-duplication fix now splits a single mixed quoted label, causing false VR-007 warnings.

- `wfctl/_arch.py:423` — Input: `%% A --> B: invented shibboleth`. Returns `['invented shibboleth']`; should return `[]`. Mermaid ignores `%%` comments, including apparent diagram syntax.
