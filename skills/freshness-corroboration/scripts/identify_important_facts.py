"""identify_important_facts.py -- sequential, CPU-only ranking over the claims artifact.
Must run between the independent and dependent batches; never scheduled inside a
thread pool."""
from models import intermediate_artifact

_TYPE_WEIGHT = {"structured": 1.0, "contact": 0.8, "price": 0.6, "date": 0.5}


def identify_important_facts(claims_artifact, deadline):
    claims = claims_artifact.get("data", {}).get("claims", [])

    def score(c):
        return c.get("importance", 0.5) * _TYPE_WEIGHT.get(c["type"], 0.4) + c.get("confidence", 0.5) * 0.2

    ranked = sorted(claims, key=score, reverse=True)
    return intermediate_artifact("important_facts", data={"facts": ranked[:20]})
