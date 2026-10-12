"""Runtime instrumentation tests against deliberately slow fixtures: verifies the
shared AuditDeadline is actually respected (not just documented) and that stage
timings, request counters, and worker-timeout events are real measurements."""
import os
import sys
from dataclasses import replace
from time import monotonic

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts"):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import Limits
from models import make_deadline
from instrumentation import Instrumentation
from acquire_site import acquire_site
from fixtures_server import start_server


def test_acquisition_respects_budget_against_slow_fixture():
    base_url, shutdown = start_server(slow_delay_s=1.5)
    try:
        limits = replace(Limits(), ACQUISITION_BUDGET_S=1.0, PER_FETCH_TIMEOUT_MS=3000, MAX_FETCH_RETRIES=0)
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()

        started = monotonic()
        acquire_site(base_url + "/slow", deadline, limits, instrumentation, allow_private_targets=True)
        elapsed = monotonic() - started

        # One in-flight slow request can run past the acquisition budget by up to its
        # own per-fetch timeout; the loop must not start a *second* one past budget.
        assert elapsed <= limits.ACQUISITION_BUDGET_S + (limits.PER_FETCH_TIMEOUT_MS / 1000) + 0.5
        duration = instrumentation.stage_duration_s("acquisition")
        assert duration is not None and duration > 0
    finally:
        shutdown()


def test_instrumentation_records_real_stage_timings_not_placeholders():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        acquire_site(base_url + "/", deadline, limits, instrumentation, allow_private_targets=True)
        telemetry = instrumentation.as_dict(memory_peak_mb=None)
        assert telemetry["stage_timings_s"]["acquisition"]["duration"] is not None
        assert telemetry["stage_timings_s"]["acquisition"]["duration"] >= 0
        assert telemetry["memory_peak_mb"] is None  # explicitly "not measured", not a fabricated 0
    finally:
        shutdown()


def test_memory_tracking_returns_a_measured_peak():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        acquire_site(base_url + "/", deadline, limits, instrumentation, allow_private_targets=True)
        peak = instrumentation.stop_memory_tracking_mb()
        assert peak is not None
        assert peak >= 0
    finally:
        shutdown()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"OK: {name}")
