"""package_release.py -- build the release archive from an explicit allowlist.

Usage:
    python tools/package_release.py [out_dir]

Writes <out_dir>/brand-ai-readiness-audit-<version>.zip (default out_dir: dist/,
which git ignores) and prints what it packed. Only the intended runtime,
reference, example and test assets are packed:

    marketplace.json, README.md, skills/, common/, examples/, tests/

Left out on purpose, and never deleted from the working copy: the planning
PDFs and notes (*.pdf, Plan.md, ROUND5_PLAN.md, Comparison.md), data/store.sqlite
(no code reads it), benchmark_runs/ (live-site runs and agent-made labels),
.env files, caches and this tools/ folder. A file that looks like a secret
stops the build.

The archive carries RELEASE.json: the version from marketplace.json, the git
commit it was built from and whether the working tree had uncommitted changes
(a release should be built from a clean, committed tree).
"""
import json
import os
import re
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE_FILES = ("marketplace.json", "README.md")
INCLUDE_DIRS = ("skills", "common", "examples", "tests")
_SKIP_DIRS = {"__pycache__", ".pytest_cache", "benchmark_runs", ".git"}
_SKIP_FILE = re.compile(r"\.(?:pyc|pyo|pdf|sqlite|db)$|^\.env(?:\..*)?$", re.I)
_SECRET = re.compile(rb"(?:PAGESPEED_API_KEY|SEARCH_API_KEY)\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}")


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20,
                              check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def release_files():
    """Relative paths of every file the archive holds, sorted."""
    files = [f for f in INCLUDE_FILES if os.path.isfile(os.path.join(ROOT, f))]
    for top in INCLUDE_DIRS:
        for folder, dirs, names in os.walk(os.path.join(ROOT, top)):
            dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
            for name in sorted(names):
                if not _SKIP_FILE.search(name):
                    files.append(os.path.relpath(os.path.join(folder, name), ROOT).replace(os.sep, "/"))
    return sorted(files)


def release_record():
    manifest = json.load(open(os.path.join(ROOT, "marketplace.json"), encoding="utf-8"))
    status = _git("status", "--porcelain")
    return {"name": manifest["name"], "version": manifest["version"], "commit": _git("rev-parse", "HEAD"),
            "uncommitted_changes": None if status is None else bool(status)}


def build(out_dir):
    record = release_record()
    files = release_files()
    for rel in files:
        with open(os.path.join(ROOT, rel), "rb") as handle:
            if _SECRET.search(handle.read()):
                raise SystemExit(f"refusing to package {rel}: it looks like it holds a provider key")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{record['name']}-{record['version']}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for rel in files:
            archive.write(os.path.join(ROOT, rel), rel)
        archive.writestr("RELEASE.json", json.dumps(dict(record, files=len(files)), indent=2) + "\n")
    return path, record, files


def main(argv):
    out_dir = argv[1] if len(argv) > 1 else os.path.join(ROOT, "dist")
    path, record, files = build(out_dir)
    print(f"packed {len(files)} files into {path}")
    print(json.dumps(record))
    if record["uncommitted_changes"]:
        print("warning: the working tree has uncommitted changes; commit before building the release",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
