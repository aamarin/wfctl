# No new boundary — 494-orphan-detection

Adds a new check in cli.py (_check_abandoned_entries) that compares manifest-recorded paths against the bundle using direct .exists() probes — no component boundary moved or drawn. No new module; all changes are in existing files (_bundle.py and cli.py).
