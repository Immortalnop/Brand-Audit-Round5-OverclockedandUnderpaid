"""Summarize saved execution evidence without rerunning or labelling sites.

The agent triage notes are review aids, not correctness labels or a score. Source
reports/packets/outcomes remain byte-for-byte unchanged. Timings include host
packet reading and assessment, through the original Markdown write timestamp.
"""
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = 'ae61edfd60b47b39fc442ec392845de95696e8d5'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def distribution(values):
    values = sorted(values)
    return {'n': len(values), 'p50_s': round(statistics.median(values), 3),
            'p95_nearest_rank_s': round(values[math.ceil(.95 * len(values)) - 1], 3)}


def rehearsals():
    rows = []
    for name in ('final-1', 'final-2', 'final-3', 'final-4', 'failed-about-final'):
        folder = ROOT / 'verification/rehearsals' / name
        core, merge = (read(folder / ('entrypoint-' + stage + '.json')) for stage in ('core', 'merge'))
        final = read(folder / 'final-report.json')
        requests = [json.loads(line) for line in (folder / 'requests.jsonl').read_text().splitlines()]
        before = int((folder / 'requests-before-merge.txt').read_text())
        assert len(requests) == before
        assert len((folder / 'acquisition-calls.jsonl').read_text().splitlines()) == 1
        assert not any(request['at_unix'] >= merge['started_at_unix'] for request in requests)
        render_record = folder / 'render-write.json'
        if not render_record.exists():
            write(render_record, {'original_markdown_written_at_unix': (folder / 'final-report.md').stat().st_mtime,
                                 'sha256': digest(folder / 'final-report.md'),
                                 'measurement': 'Original filesystem write timestamp captured before copying/committing artifacts; not an instrumented user-request start.'})
        rendering = read(render_record)
        assert rendering['sha256'] == digest(folder / 'final-report.md')
        workflow = rendering['original_markdown_written_at_unix'] - core['started_at_unix']
        host = merge['finished_at_unix'] - core['finished_at_unix']
        deadline = final['timing']['agent_stage_budget_s']
        assert final['code_version'] == '8.4.0+' + FREEZE[:12]
        assert final['packet_sha256'] == read(folder / 'evidence.json')['packet_sha256']
        rows.append({'name': name, 'site': final['site'], 'candidate_commit': FREEZE,
                     'workflow_to_markdown_s': round(workflow, 3), 'host_through_merge_s': round(host, 3),
                     'host_allowance_s': deadline, 'host_allowance_exceeded': host > deadline,
                     'assessment_status': final['coverage']['agent_stage']['assessment_status'],
                     'checks_assessed': final['coverage']['agent_stage']['checks_assessed'],
                     'acquisition_calls': 1, 'request_count': before, 'merge_and_render_requests': 0,
                     'actual_requests_by_host_path': dict(Counter(request['host'] + request['path'] for request in requests)),
                     'test_only_private_target': name == 'failed-about-final',
                     'original_markdown_written_at_unix': rendering['original_markdown_written_at_unix'],
                     'hashes': {p.name: digest(p) for p in folder.iterdir() if p.is_file()}})
    public = rows[:4]
    chosen = rows[1:4]
    write(ROOT / 'verification/rehearsals/final-summary.json', {
        'candidate_commit': FREEZE, 'capabilities': {'local_reading': True, 'search': False, 'vision': False, 'rendering': False},
        'measurement_scope': 'Entrypoint invocation through original final Markdown write; includes host reading/assessment/outcome/merge. The earlier overall user request start and intended laptop identity were not instrumented.',
        'host_enforcement': 'Advisory deadline; core process hard stop is enforced. Late host runs are retained.',
        'public_rehearsals': distribution([r['workflow_to_markdown_s'] for r in public]),
        'chosen_python_workflow_three_runs': distribution([r['workflow_to_markdown_s'] for r in chosen]),
        'public_late_host_runs': sum(r['host_allowance_exceeded'] for r in public),
        'screen_recording': 'unverified', 'runs': rows})


# These notes reflect the inspected saved findings and immutable observations.
# They deliberately avoid tp/fp/irrelevant labels, which await a person.
NOTES = {
    'noindex': 'Literal noindex is recorded. Confirm publication intent before classifying a defect or removing it; contact/error pages can deliberately exclude indexing.',
    'media-schema-missing': 'Embedding and absence of corresponding markup are recorded. Optional enrichment requires an intended consumer; media does not universally require this markup.',
    'social-metadata': 'Missing fields are recorded in the sampled raw metadata. Platform fallback and actual preview rendering were not tested.',
    'heading-hierarchy': 'Recorded heading sequences contain jumps. Review navigation, section semantics and accessible reading order before prescribing a hierarchy change.',
    'missing-description': 'The sampled metadata has no nonempty description. Search engines can extract text; no lost visibility is measured.',
    'responsive-images': 'The first candidate image lacks recorded responsive variants. Verify viewport, CSS and whether this image is substantial before changing it.',
    'title-length': 'Recorded character counts cross the heuristic boundary. Short brand titles and long product names may be appropriate; display width was not measured.',
    'h1': 'The recorded raw heading list has no H1 in the affected sample. Combined orientation advice needs visual/content review, not a whole-page absence claim.',
    'breadcrumb-mismatch': 'Breadcrumb features and absent corresponding JSON-LD are recorded. Optional schema is not a universal retrieval requirement.',
    'missing-landmarks': 'The raw parser did not record main/article landmarks. Review the actual accessibility tree and equivalent roles before implementation.',
    'missing-canonical': 'No canonical declaration is recorded. Duplicate content was not established; self-canonical advice needs site context.',
    'twitter-card': 'No supported card value is recorded; legacy product values may be present. Platform fallback was not tested.',
    'audience-segment-missing': 'The bounded title/heading/link pattern check found no named segment. This does not establish absence of audience language in prose or usefulness of new segment pages.',
    'control-name-missing': 'The parser recorded unnamed controls. A browser accessibility tree, referenced labels and runtime state were not inspected; verify before accepting confirmed status.',
    'kg-link-missing': 'Organization sameAs values do not name a Wikidata/Wikipedia source. A suitable entity was not searched or established; optional enrichment only.',
    'markup-ratio': 'The recorded raw byte ratio crosses a heuristic threshold. It does not establish deficient content or a ranking penalty.',
    'answer-headings': 'The sampled English headings are not question-shaped. Product pages may not need that format; usefulness depends on actual audience questions.',
    'sitemap-lastmod-unreliable': 'Sampled lastmod values are uniform. Uniformity alone does not prove generation time; compare publisher change logs before accepting that explanation.',
    'review-platform-missing': 'No matching review/directory link was recorded in the sample. External existence was not searched; directory recommendations need relevance review.',
    'location-markup-missing': 'Address signals and absent JSON-LD location fields are recorded. Verify source ownership and whether optional location markup is appropriate before accepting defect status or snippets.',
    'image-weight': 'Probes record image format and some sizes. Format alone does not prove avoidable weight; viewport, visual quality, CSS dimensions and conversion savings were not measured.',
    'alt-text-quality': 'Repeated avatar labels were recorded. Check adjacent author/link text and decorative intent before requiring distinct alternatives.',
    'author-credentials-weak': 'No Article author property was recorded on the blog listing. Check page type and existing linked profiles; missing credentials in prose is not established.',
    'cwv-risk': 'Raw resource/dimension hints support a possible risk. This is not measured LCP/CLS and needs browser or field data.',
    'contact-markup-missing': 'Visible contact signals and absent structured contact fields are recorded. Optional reuse advice, without a measured visibility benefit.',
    'cross-origin-canonical': 'The canonical origin differs. Same-organization subdomains may be intentional; validate deployment/canonical policy before changing it.',
    'image-sizing': 'Raw width/height attributes are absent. CSS sizing and viewport positions were not measured.',
    'sitemap-unavailable': 'The bounded sitemap candidate was absent. Other undiscovered sitemap locations or valid deliberate absence remain possible.',
    'no-jsonld': 'The sample records zero JSON-LD blocks. This is optional enrichment advice; microdata/RDFa and other consumer formats are distinct.',
    'table-headers-missing': 'A table with no th cells is recorded. Check layout/data intent and alternative accessible header associations before accepting defect status.',
    'image-context-missing': 'The parser recorded missing alternatives around sampled images. Verify decorative intent and equivalent nearby impact statistics before prescribing alt text.',
    'missing-alt': 'The parser recorded missing alternatives around sampled images. Verify decorative intent and equivalent nearby impact statistics before prescribing alt text.',
    'ai-crawler-unchecked': 'Robots acquisition failed and content was unassessed. Do not infer a website defect or crawler ban from this environment observation.',
    'robots-unreachable': 'Robots acquisition failed and content was unassessed. Do not infer a website defect or crawler ban from this environment observation.'}


def review_set():
    folder = ROOT / 'verification/review-set'
    manifest, runs = read(folder / 'manifest.json'), read(folder / 'runs.json')
    assert manifest['candidate_commit'] == FREEZE
    records, triage = [], []
    totals, severity = Counter(), Counter()
    for run in runs:
        source = folder / run['category']
        for name, expected in run['hashes'].items():
            assert digest(source / name) == expected, (run['category'], name)
        report, acquisition = read(source / 'base-report.json'), read(source / 'acquisition.json')
        pages = {}
        for page in acquisition['pages']:
            pages[page['url']] = page
            pages[page.get('final_url') or page['url']] = page
        for finding in report['findings']:
            cid = finding['check_id']
            note = NOTES.get(cid)
            if cid.startswith('page-type-schema-gap:'):
                note = 'Page-type and absent target schema types are recorded. Optional consumer enrichment, not universally required markup; confirm page classification.'
            assert note, cid
            if run['category'] == 'documentation' and cid == 'noindex':
                note += ' Here the page title is Page not found and the path is /en-US/404, making intentional noindex plausible.'
            if run['category'] == 'documentation' and cid == 'review-platform-missing':
                note += ' Commercial customer-review recommendations may be irrelevant to MDN documentation.'
            if run['category'] == 'local_business' and cid == 'location-markup-missing':
                note += ' The homepage address sample contains a New York supplier address; do not publish it as the bookstore location without verification.'
            missing = [url for url in finding['affected_pages'] if url not in pages]
            assert not missing or report['execution_status'] == 'insufficient_evidence', missing
            totals[finding['finding_type']] += 1
            severity[finding['severity']] += 1
            triage.append({'category': run['category'], 'finding_id': finding['id'], 'check_ids': ' '.join(finding['check_ids']),
                           'agent_triage_note': note, 'affected_urls_in_acquired_observations': not missing,
                           'reviewer_kind': 'agent', 'human_reviewed': False,
                           'source': str((source / 'acquisition.json').relative_to(ROOT)),
                           'report_sha256': digest(source / 'base-report.json')})
        records.append({'category': run['category'], 'status': report['execution_status'], 'findings': len(report['findings']),
                        'pages_analyzed': report['coverage']['pages_analyzed'], 'core_elapsed_s': report['timing']['core_elapsed_s'],
                        'network_requests': report['coverage']['network_budget']['total_requests'],
                        'network_bytes': report['coverage']['network_budget']['total_bytes']})
    with open(folder / 'agent-triage.csv', 'w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(triage[0]))
        writer.writeheader()
        writer.writerows(triage)
    write(folder / 'summary.json', {'candidate_commit': FREEZE, 'sites_attempted': len(runs),
          'status_counts': dict(Counter(r['status'] for r in records)), 'findings': sum(totals.values()),
          'finding_types': dict(totals), 'severity_counts': dict(severity),
          'high_critical_review': 'No high/critical findings were emitted; no positive precision denominator.',
          'human_labels': 0, 'agent_triage_rows': len(triage), 'independent_precision': None, 'independent_ECE': None,
          'triage_scope': 'Agent inspection of saved reports and immutable acquired observations. Human correctness/scope/status/severity/action labels remain blank. No tuning or independent accuracy claim.',
          'runs': records})


if __name__ == '__main__':
    rehearsals()
    review_set()
