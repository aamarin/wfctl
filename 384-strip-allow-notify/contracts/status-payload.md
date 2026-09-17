# Contract: `wfctl status --json`

Two keys come out, and `facts` goes from four entries to three. Every other key
and its meaning is unchanged.

| Key | Before | After |
| --- | --- | --- |
| `notify` | `bool` | absent |
| `notify_source` | one of seven strings | absent |
| `facts` | 4 entries, in a fixed order | 3 entries, in a fixed order: `artifacts written`, `definition of done`, `architecture accepted` |

A consumer that reads `facts[3]` breaks. The consumers inside this repository
are `end-session`, `speckit-delivery-plan`, `speckit.analyze` and
`scaffold-tracker`. They read `notify` and `notify_source` rather than the
fourth fact, and all of them change in this feature.
`test_pipeline_payload_snapshot` pins the new shape.
