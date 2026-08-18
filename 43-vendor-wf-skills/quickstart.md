# Quickstart: Vendor wf-skills

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

How to get the change running locally and confirm it works. Every step is
runnable; nothing here assumes the implementation is finished.

---

## 1. Populate the bundle

The vendored tree is a copy of wf-skills at its final tip, with the dots stripped.
Do it once, from a clean clone rather than from this repo's own installed
`.agents/` — the installed copy has no `trackers/` or `configs/` (they are never
installed into a repo, only seeded), so copying from it would silently ship an
incomplete bundle.

```bash
git clone --depth=1 https://github.com/aamarin/wf-skills /tmp/wfs
mkdir -p wfctl/agents wfctl/specify
cp -R /tmp/wfs/.agents/skills   wfctl/agents/skills
cp -R /tmp/wfs/.agents/commands wfctl/agents/commands
cp -R /tmp/wfs/.agents/trackers wfctl/agents/trackers
cp -R /tmp/wfs/.agents/configs  wfctl/agents/configs
cp -R /tmp/wfs/.specify/scripts    wfctl/specify/scripts
cp -R /tmp/wfs/.specify/templates  wfctl/specify/templates
```

Then confirm the exec bit survived the copy and is what git records — a wheel
faithfully preserves `644`, so this is the step that decides it:

```bash
ls -l wfctl/specify/scripts/bash/          # expect -rwxr-xr-x
git add wfctl/agents wfctl/specify
git ls-files -s wfctl/specify/scripts/bash # expect mode 100755, not 100644
```

If any is `100644`: `git update-index --chmod=+x wfctl/specify/scripts/bash/*.sh`.

## 2. Verify the wheel actually carries it

This is the check the whole feature rests on, and the one the current suite cannot
make. Run it before writing any code that reads the bundle.

```bash
uv build --wheel
python - <<'PY'
import zipfile, glob
z = zipfile.ZipFile(sorted(glob.glob("dist/*.whl"))[-1])
names = [n for n in z.namelist() if n.startswith("wfctl/agents") or n.startswith("wfctl/specify")]
print(f"{len(names)} bundled files")
for n in names:
    if n.endswith(".sh"):
        mode = z.getinfo(n).external_attr >> 16
        print(f"  {n}: {'exec' if mode & 0o111 else 'NOT EXECUTABLE'}")
PY
```

Zero bundled files means `[tool.setuptools.package-data]` is missing or its globs
are wrong. A `.sh` reported `NOT EXECUTABLE` means step 1's `git ls-files -s` check
was skipped.

## 3. Install it clean and use it

Not editable, not the source tree — an editable install reads `wfctl/agents/`
straight off disk and would pass even with the wheel shipping nothing.

```bash
uv tool install --force ./dist/wfctl-*.whl

mkdir -p /tmp/scratch-repo && git -C /tmp/scratch-repo init
cd /tmp/scratch-repo
wfctl install-skills --yes
ls .agents/skills .agents/commands .specify/scripts/bash
```

Expect no `Cloning…` line and a sub-second run. Then prove the network is gone:

```bash
wfctl install-skills --yes --tracker github   # still works with wifi off
wfctl doctor                                  # skills verdict, no ls-remote
```

## 4. Exercise the staleness states

All four states are reachable by hand.

```bash
# current
wfctl doctor                    # ✓ base: skills current (wfctl 0.15.0)

# stale, versions equal — the editable-dev case
python -c "import json,pathlib; p=pathlib.Path('.wf-skills-manifest.json'); \
m=json.loads(p.read_text()); m['base']['content_hash']='deadbeef'; \
p.write_text(json.dumps(m))"
wfctl doctor                    # ⬆ base: bundled skills changed since install

# stale, versions differ
python -c "import json,pathlib; p=pathlib.Path('.wf-skills-manifest.json'); \
m=json.loads(p.read_text()); m['base']['wfctl_version']='0.14.0'; \
p.write_text(json.dumps(m))"
wfctl doctor                    # ⬆ … installed by wfctl 0.14.0, running 0.15.0

# migration — a record from before this change
python -c "import json,pathlib; p=pathlib.Path('.wf-skills-manifest.json'); \
m=json.loads(p.read_text()); del m['base']['content_hash']; \
m['base']['commit']='9ee468a'; p.write_text(json.dumps(m))"
wfctl doctor                    # ⚠ base: installed before content hashing
wfctl install-skills --yes      # rewrites it
wfctl doctor                    # ✓ current, and repo/ref/commit are gone
```

## 5. Confirm the re-install is a content no-op

On a repo that already installed from the wf-skills tip the bundle was copied
from, the new install should change nothing but the manifest.

```bash
cd <a repo with skills installed>
git status --porcelain .agents .specify   # note the baseline
wfctl install-skills --yes
git status --porcelain .agents .specify   # expect the same
```

Both trees are gitignored in wfctl itself, so run this in a consuming repo — or
compare with `diff -r` against a copy taken before the install.

## 6. Run the suite

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
uv run mypy
```

The suite should now pass with the machine offline. If it hangs, something still
shells out to git against a remote — the `GIT_TERMINAL_PROMPT` workaround that
used to make that fail fast is gone, so a hang is the symptom.
