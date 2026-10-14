"""Main audit outputs and supporting records, with flat-layout compatibility."""
from pathlib import Path
import re

VERIFICATION_DIR = 'verification'
PRIMARY_FILES = ('base-report.json', 'agent-outcomes.json', 'final-report.json',
                 'final-report.md', 'repair-prompt.md')
SUPPORT_FILES = ('README.md', 'workflow-start.json', 'workflow-context.json',
                 'workflow-instructions.md', 'evidence.json', 'agent-stage-notes.md',
                 'agent-image-fetch.json')

GUIDE = """# Audit artifacts and their connections

The run root keeps the main results. This verification/ directory keeps supporting
evidence, host research records and workflow metadata. Its name does not certify
that every finding is true or every AG check was assessed. Optional records exist
only when the corresponding operation actually ran.

Creation order:
1. workflow-start.json records the first-tool UTC clock. workflow-context.json
   stores the requested URL, page limit and paths. workflow-instructions.md binds
   the canonical procedure to this run. These bootstrap files precede acquisition.
2. ../base-report.json is the native engine's original report, acquired once.
   evidence.json is the same run's bounded, immutable evidence packet for AG checks.
3. ../agent-outcomes.json saves one outcome per AG check. agent-stage-notes.md
   records actual research, limitations and timings. Optional agent-image-fetch.json
   records the bounded download; I### image files are the downloaded candidates.
   A download receipt alone does not prove that an agent viewed an image.
4. ../final-report.json merges validated AG outcomes into the base locally, leaving
   the base and packet unchanged. With a non-ready packet, it is an unchanged-base
   fallback and reports the missing agent stage honestly.
5. ../final-report.md renders that final JSON without acquiring the site again.
6. ../repair-prompt.md includes the complete final report and available packet,
   outcomes and notes for a separate verification/repair task in the website's
   editable source repository. Images remain separate attachments. That task
   must verify findings before fixing them and preserve original audit artifacts.

The main connection is:
base report + evidence packet -> AG outcomes -> validated final report -> Markdown
and repair handoff. The clock and context identify this run; they do not add time
or supply website evidence. Native checks share one acquisition. The optional
packet-listed image download is a bounded host step, not another HTML crawl.
"""


def supporting_file(folder, name):
    """Prefer the current location; never silently combine duplicate sources."""
    folder = Path(folder)
    current, legacy = folder / VERIFICATION_DIR / name, folder / name
    if current.exists() and legacy.exists():
        raise ValueError('Supporting artifact exists in both flat and verification locations: ' + name)
    return current if current.exists() or not legacy.exists() else legacy


def image_files(folder):
    files = {}
    for directory in (Path(folder) / VERIFICATION_DIR, Path(folder)):
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and re.fullmatch(r'I\d{3}\.(?:png|jpg|jpeg|webp|gif)', path.name, re.I):
                if path.name in files:
                    raise ValueError('Image exists in both flat and verification locations: ' + path.name)
                files[path.name] = path
    return [files[name] for name in sorted(files)]


def artifact_listing(folder):
    folder = Path(folder)
    main = [name for name in PRIMARY_FILES if (folder / name).is_file()]
    support = []
    for name in SUPPORT_FILES:
        path = folder / VERIFICATION_DIR / name if name == 'README.md' else supporting_file(folder, name)
        if path.is_file():
            support.append(str(path.relative_to(folder)))
    support.extend(str(p.relative_to(folder)) for p in image_files(folder))
    return main, support
