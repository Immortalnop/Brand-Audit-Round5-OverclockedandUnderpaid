"""Shared network allowance for one audit.

Every Transport inside the controlled Python audit charges one ledger, so the
ceilings in the report are the ones actually enforced. The ledger has two
pools: "site" (the audited origin, including robots.txt, retries, redirect hops,
a re-anchored origin, the HTTPS probe, media, llms.txt link checks and the
optional headless browser) and "external" (knowledge graphs, linked profiles,
the PageSpeed API and a configured search provider). A stage may keep a
stricter limit of its own; it never gets a fresh copy of the shared one.

Accounting model: a request is reserved before it is sent, together with the
largest number of bytes it may read. When it finishes, the bytes it actually
used (the larger of wire and decoded bytes) are kept and the rest of the
reservation is refunded. A refused reservation sends nothing. A request is
never refunded: one that failed was still sent.

The optional headless browser runs in a child process that cannot share this
lock. Before it starts, the parent reserves a fixed slice of the site pool and
the child's own transport is capped at that slice; the slice is charged in full
because a killed child reports nothing back.

Host-agent tool calls (the agent stage's searches and page views) never pass
through here and are not counted in it.
"""
import threading

POOLS = ("site", "external")


class NetworkBudget:
    def __init__(self, site_requests, site_bytes, external_requests, external_bytes):
        self._lock = threading.Lock()
        self._limits = {"site": (int(site_requests), int(site_bytes)),
                        "external": (int(external_requests), int(external_bytes))}
        self._used = {pool: [0, 0] for pool in POOLS}
        self._stages = {}
        self._refused = {pool: 0 for pool in POOLS}

    def reserve(self, pool, stage, max_bytes, requests=1):
        """Bytes granted for `requests` new requests (at least 1), or 0 when the
        pool cannot take them. The requests are counted at once."""
        with self._lock:
            req_cap, byte_cap = self._limits[pool]
            used = self._used[pool]
            left = byte_cap - used[1]
            if used[0] + requests > req_cap or left <= 0:
                self._refused[pool] += 1
                return 0
            granted = max(0, min(int(max_bytes), left))
            if granted <= 0:
                self._refused[pool] += 1
                return 0
            used[0] += requests
            used[1] += granted
            entry = self._stages.setdefault(stage, {"pool": pool, "requests": 0, "bytes": 0})
            entry["requests"] += requests
            entry["bytes"] += granted
            return granted

    def settle(self, pool, stage, granted, used_bytes):
        """Keep used_bytes of a reservation of granted bytes; refund the rest."""
        refund = max(0, int(granted) - max(0, int(used_bytes)))
        if not refund:
            return
        with self._lock:
            self._used[pool][1] -= refund
            self._stages[stage]["bytes"] -= refund

    def remaining(self, pool):
        with self._lock:
            req_cap, byte_cap = self._limits[pool]
            used = self._used[pool]
            return max(0, req_cap - used[0]), max(0, byte_cap - used[1])

    def snapshot(self):
        with self._lock:
            pools = {pool: {"max_requests": self._limits[pool][0], "max_bytes": self._limits[pool][1],
                            "requests": self._used[pool][0], "bytes": self._used[pool][1],
                            "refused": self._refused[pool]} for pool in POOLS}
            stages = {name: dict(v) for name, v in sorted(self._stages.items())}
        return {"accounting": "reserve before send; unused bytes refunded; bytes are the larger of wire and "
                              "decoded bytes",
                "pools": pools, "stages": stages,
                "total_requests": sum(p["requests"] for p in pools.values()),
                "total_bytes": sum(p["bytes"] for p in pools.values()),
                "not_counted": ["host-agent tool calls (agent stage searches and page views)"]}


def from_limits(limits):
    return NetworkBudget(limits.MAX_TOTAL_HTTP_REQUESTS, limits.MAX_TOTAL_BYTES,
                         limits.MAX_EXTERNAL_HTTP_REQUESTS, limits.MAX_EXTERNAL_BYTES)


# The ledger of the audit running in this process. Each audit runs in its own
# worker process (run_audit._run_bounded), so one process holds one audit; a
# Transport made with no explicit ledger charges this one.
_ACTIVE = {"budget": None}


def activate(budget):
    _ACTIVE["budget"] = budget
    return budget


def deactivate(budget=None):
    if budget is None or _ACTIVE["budget"] is budget:
        _ACTIVE["budget"] = None


def active():
    return _ACTIVE["budget"]
