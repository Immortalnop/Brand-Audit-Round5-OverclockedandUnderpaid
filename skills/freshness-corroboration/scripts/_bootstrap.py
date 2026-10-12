"""_bootstrap.py -- locate the marketplace root and put its shared modules on sys.path.

Skills in this marketplace share one library (`common/`) so that every check,
score and wording rule is defined once. A skill folder copied out on its own
cannot reach that library; instead of failing later with an obscure ImportError,
this module walks up from its own location to the folder containing
marketplace.json and exits with a clear message if there is none.
"""
import os
import sys

SCRIPT_DIRS = ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
               "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
               "skills/entity-corroboration-agent/scripts")


def marketplace_root(start=None):
    here = os.path.abspath(start or os.path.dirname(__file__))
    while True:
        if os.path.isfile(os.path.join(here, "marketplace.json")) and os.path.isdir(os.path.join(here, "common")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def ensure_paths():
    root = marketplace_root()
    if root is None:
        sys.stderr.write("This skill is part of the brand-ai-readiness-audit marketplace and needs its shared "
                         "common/ library. Install the whole marketplace folder (the one containing "
                         "marketplace.json), not a single skill folder.\n")
        raise SystemExit(2)
    for rel in SCRIPT_DIRS:
        path = os.path.join(root, rel)
        if path not in sys.path:
            sys.path.insert(0, path)
    return root
