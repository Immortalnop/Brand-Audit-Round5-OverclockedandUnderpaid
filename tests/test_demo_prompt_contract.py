"""The replay uses the same full prompt and a real, non-resettable start marker."""
from pathlib import Path
import json
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PROMPT=(ROOT/'replay/FINAL_AUDIT_PROMPT.txt').read_text()


def test_manifest_embeds_exact_canonical_prompt_and_keeps_metadata_blank():
    manifest=(ROOT/'replay/REPLAY_Overclocked_and_Underpaid_round5_final.txt').read_text()
    embedded=manifest.split('----- BEGIN AUDIT PROMPT -----\n',1)[1].split('----- END AUDIT PROMPT -----',1)[0]
    assert embedded==PROMPT
    for field in ('AGENT_HARNESS_VERSION','LLM_MODEL','LLM_MODEL_VERSION'):
        assert field+':\n' in manifest
    assert '--model claude-opus-5-5' in manifest
    assert '--tools "Read,Edit,Write,Bash,WebSearch,WebFetch,Skill"' in manifest
    assert '--plugin-dir ./Brand-AI-Readiness-Audit-round5-final_version' in manifest
    assert '/brand-audit:audit https://tartinebakery.com/' in manifest
    assert '"Edit(out/**)" "Write(out/**)"' in manifest
    assert 'MAX_PAGES: 6' not in PROMPT and '--max-pages 6' not in PROMPT


def test_clock_command_is_executable_and_cannot_replace_previous_outputs(tmp_path):
    out=tmp_path/'out';out.mkdir()
    command=next(line for line in PROMPT.splitlines() if line.startswith('python3 -c '))
    args=shlex.split(command);args[0]=sys.executable
    result=subprocess.run(args,cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode==0
    marker=out/'workflow-start.json';original=marker.read_bytes()
    assert json.loads(original)['workflow_started_at']==result.stdout.strip()
    repeated=subprocess.run(args,cwd=tmp_path,capture_output=True,text=True)
    assert repeated.returncode!=0 and marker.read_bytes()==original
