"""Release allowlist, portable provenance and preserved source assets."""
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('package_release',ROOT/'tools/package_release.py')
# Packaging tool is intentionally absent from the distributed runtime. Its
# tests skip in extracted packages, whose contents/runtime are verified below.
if not (ROOT/'tools/package_release.py').exists():
    pytest.skip('build tooling is excluded by the runtime allowlist',allow_module_level=True)
package=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


def tree(tmp_path):
    (tmp_path/'marketplace.json').write_text('{"name":"brand-ai-readiness-audit","version":"8.4.0"}')
    (tmp_path/'README.md').write_text('Runtime')
    (tmp_path/'common').mkdir()
    (tmp_path/'common'/'runtime.py').write_text('print("runtime")')
    return tmp_path


def test_allowlist_omits_databases_journals_keys_plans_and_caches(tmp_path):
    root=tree(tmp_path)
    (root/'Plan.md').write_text('preserve')
    (root/'donor.zip').write_bytes(b'preserve')
    for name in ('x.sqlite','x.sqlite-wal','x.sqlite-shm','x.db-journal','.env','x.pem','id_rsa'):
        (root/'common'/name).write_text('private')
    (root/'common'/'__pycache__').mkdir()
    (root/'common'/'__pycache__'/'x.pyc').write_bytes(b'cache')
    files=package.release_files(root)
    assert files==['README.md','common/runtime.py','marketplace.json']
    assert (root/'Plan.md').read_text()=='preserve'
    assert (root/'donor.zip').read_bytes()==b'preserve'


def test_symlinks_cannot_pull_unlisted_external_content_into_release(tmp_path):
    root=tree(tmp_path)
    (root/'common'/'alias.py').symlink_to('/etc/hostname')
    with pytest.raises(SystemExit,match='symbolic link'):
        package.release_files(root)


def test_release_writer_records_actual_commit_and_is_portable(tmp_path):
    root=tree(tmp_path/'src') if (tmp_path/'src').mkdir() is None else None
    record={'name':'brand-ai-readiness-audit','version':'8.4.0','commit':'a'*40,'uncommitted_changes':False}
    path,written,files=package.build(tmp_path/'out',root,record)
    with zipfile.ZipFile(path) as archive:
        assert json.loads(archive.read('RELEASE.json'))['commit']==record['commit']
        assert set(archive.namelist())==set(files)|{'RELEASE.json'}
        assert archive.testzip() is None


def test_committed_build_excludes_existing_user_assets_without_reset(tmp_path):
    path,record,files=package.build_committed(tmp_path)
    assert record['uncommitted_changes'] is False
    assert not any(name.endswith(('.zip','.sqlite','.pdf')) or name.startswith(('Plan','final_version_plan','benchmark_runs')) for name in files)
    assert 'common/schema_values.py' in files
    with zipfile.ZipFile(path) as archive:
        assert 'RELEASE.json' in archive.namelist() and archive.testzip() is None
