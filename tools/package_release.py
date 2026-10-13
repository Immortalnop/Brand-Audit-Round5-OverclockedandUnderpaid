"""package_release.py -- build the release archive from an explicit allowlist.

Usage:
    python tools/package_release.py [out_dir]

Writes <out_dir>/brand-ai-readiness-audit-<version>.zip (default out_dir: dist/,
which git ignores) and prints what it packed. Only the intended runtime,
reference, example and test assets are packed:

    marketplace.json, README.md, skills/, common/, examples/, tests/, replay/

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
import io
import os
import re
import subprocess
import sys
import zipfile
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE_FILES = ("marketplace.json", "README.md")
INCLUDE_DIRS = ("skills", "common", "examples", "tests", "replay")
_SKIP_DIRS = {"__pycache__", ".pytest_cache", "benchmark_runs", ".git", '.venv', '.mypy_cache', '.ruff_cache', 'node_modules'}
_SKIP_FILE = re.compile(r"\.(?:pyc|pyo|pdf|sqlite3?|db)(?:-(?:wal|shm|journal))?$|^\.env(?:\..*)?$|\.(?:pem|key)$|^id_(?:rsa|ed25519)$", re.I)
_SECRET = re.compile(rb"(?:PAGESPEED_API_KEY|SEARCH_API_KEY)\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}")
# Public, committed localhost test material documented in this fixture folder.
# It authenticates no production service and is needed for TLS safety controls.
_PUBLIC_TLS_FIXTURES = {'tests/tls-fixtures/ca.pem', 'tests/tls-fixtures/server.pem', 'tests/tls-fixtures/server-key.pem'}


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20,
                              check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def release_files(root=None):
    """Relative paths of every file the archive holds, sorted."""
    root = root or ROOT
    files = [f for f in INCLUDE_FILES if os.path.isfile(os.path.join(root, f))]
    for top in INCLUDE_DIRS:
        for folder, dirs, names in os.walk(os.path.join(root, top)):
            dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
            for name in sorted(names):
                path = os.path.join(folder, name)
                rel = os.path.relpath(path, root).replace(os.sep, '/')
                if not _SKIP_FILE.search(name) or rel in _PUBLIC_TLS_FIXTURES:
                    if os.path.islink(path):
                        raise SystemExit('refusing to package symbolic link: ' + path)
                    files.append(rel)
    return sorted(files)


def release_record():
    manifest = json.load(open(os.path.join(ROOT, "marketplace.json"), encoding="utf-8"))
    status = _git("status", "--porcelain")
    return {"name": manifest["name"], "version": manifest["version"], "commit": _git("rev-parse", "HEAD"),
            "uncommitted_changes": None if status is None else bool(status)}


def build(out_dir, root=None, record=None):
    root = root or ROOT
    record = record or release_record()
    files = release_files(root)
    for rel in files:
        with open(os.path.join(root, rel), "rb") as handle:
            if _SECRET.search(handle.read()):
                raise SystemExit(f"refusing to package {rel}: it looks like it holds a provider key")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{record['name']}-{record['version']}.zip")
    descriptor, temporary = tempfile.mkstemp(prefix='.release-', suffix='.zip', dir=out_dir)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for rel in files:
                archive.write(os.path.join(root, rel), rel)
            archive.writestr("RELEASE.json", json.dumps(dict(record, files=len(files)), indent=2) + "\n")
        if os.path.getsize(temporary) > 50 * 1024 * 1024:
            raise SystemExit('release exceeds 50 MiB limit')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path, record, files


def build_committed(out_dir):
    """Package HEAD without touching user-owned working files or staging state."""
    commit = _git('rev-parse', 'HEAD')
    if not commit or not re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})', commit):
        raise SystemExit('committed build requires valid Git HEAD')
    content = subprocess.run(['git', 'archive', commit], cwd=ROOT, capture_output=True,
                             timeout=30, check=True).stdout
    with tempfile.TemporaryDirectory(prefix='brand-release-') as tree:
        with tarfile.open(fileobj=io.BytesIO(content)) as archive:
            for member in archive.getmembers():
                parts = member.name.split('/')
                if member.name.startswith('/') or '..' in parts or not (member.isfile() or member.isdir()):
                    raise SystemExit('unsupported path in committed snapshot: ' + member.name)
                target = os.path.join(tree, *parts)
                if member.isdir():
                    os.makedirs(target, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with archive.extractfile(member) as source, open(target, 'wb') as dest:
                        dest.write(source.read())
        with open(os.path.join(tree, 'marketplace.json'), encoding='utf-8') as handle:
            manifest = json.load(handle)
        record = {'name': manifest['name'], 'version': manifest['version'], 'commit': commit,
                  'uncommitted_changes': False, 'source': 'committed_git_snapshot'}
        return build(out_dir, tree, record)


def main(argv):
    args = argv[1:]
    committed = '--committed' in args
    args = [a for a in args if a != '--committed']
    out_dir = args[0] if args else os.path.join(ROOT, "dist")
    path, record, files = build_committed(out_dir) if committed else build(out_dir)
    print(f"packed {len(files)} files into {path}")
    print(json.dumps(record))
    if record["uncommitted_changes"]:
        print("warning: the working tree has uncommitted changes; commit before building the release",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
