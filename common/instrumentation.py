"""instrumentation.py -- runtime instrumentation layer.

Records real, measured values -- never placeholders. Anything this process
cannot measure is left as None (see AS_TELEMETRY's explicit "unavailable"
handling) rather than a fabricated zero.
"""
from __future__ import annotations
import threading
import tracemalloc
import os
import sys
from dataclasses import dataclass, field
from time import monotonic
from typing import Optional


@dataclass
class Instrumentation:
    """Thread-safe recorder shared across the acquisition and analysis stages."""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    stage_timings: dict = field(default_factory=dict)          # stage -> {"start": t, "end": t}
    requests_attempted: int = 0
    requests_completed: int = 0
    requests_failed: int = 0
    bytes_downloaded: int = 0
    pages_skipped: int = 0
    pages_skipped_reasons: list = field(default_factory=list)
    external_fetches_attempted: int = 0
    external_fetches_completed: int = 0
    worker_timeout_events: list = field(default_factory=list)  # [{"stage":..,"worker":..,"at":..}]
    requests_retried: int = 0
    requests_timed_out: int = 0
    redirects_followed: int = 0
    responses_truncated: int = 0
    urls_deduplicated: int = 0
    safety_blocks: list = field(default_factory=list)  # [{"url":.., "reason":..}], capped
    _tracemalloc_started_here: bool = field(default=False, repr=False)
    _SAFETY_BLOCKS_CAP: int = field(default=50, repr=False)

    @staticmethod
    def process_rss_mb() -> Optional[float]:
        """Best-effort current process RSS; None when the platform exposes no safe API."""
        try:
            if sys.platform.startswith("linux"):
                with open("/proc/self/status", encoding="utf-8") as fh:
                    for line in fh:
                        if line.startswith("VmRSS:"):
                            return round(int(line.split()[1]) / 1024, 3)
            if sys.platform == "darwin":
                import resource
                return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024), 3)
            if os.name == "nt":
                import ctypes
                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
                counters = PROCESS_MEMORY_COUNTERS(); counters.cb = ctypes.sizeof(counters)
                if ctypes.windll.psapi.GetProcessMemoryInfo(-1, ctypes.byref(counters), counters.cb):
                    return round(counters.WorkingSetSize / (1024 * 1024), 3)
        except (OSError, ImportError, AttributeError, ValueError, TypeError):
            pass
        return None

    def start_stage(self, name: str) -> None:
        with self._lock:
            self.stage_timings[name] = {"start": monotonic(), "end": None}

    def end_stage(self, name: str) -> None:
        with self._lock:
            if name in self.stage_timings:
                self.stage_timings[name]["end"] = monotonic()

    def record_request(self, ok: bool, nbytes: int = 0, timed_out: bool = False) -> None:
        with self._lock:
            self.requests_attempted += 1
            if ok:
                self.requests_completed += 1
                self.bytes_downloaded += nbytes
            else:
                self.requests_failed += 1
                if timed_out:
                    self.requests_timed_out += 1

    def record_redirect(self) -> None:
        with self._lock:
            self.redirects_followed += 1

    def record_skip(self, reason: str) -> None:
        with self._lock:
            self.pages_skipped += 1
            self.pages_skipped_reasons.append(reason)

    def record_retry(self) -> None:
        with self._lock:
            self.requests_retried += 1

    def record_truncated(self) -> None:
        with self._lock:
            self.responses_truncated += 1

    def record_deduplicated(self) -> None:
        with self._lock:
            self.urls_deduplicated += 1

    def record_safety_block(self, url: str, reason: str) -> None:
        with self._lock:
            self.pages_skipped += 1
            self.pages_skipped_reasons.append(f"safety_block:{reason}")
            if len(self.safety_blocks) < self._SAFETY_BLOCKS_CAP:
                self.safety_blocks.append({"url": url, "reason": reason})

    def record_external_fetch(self, ok: bool) -> None:
        with self._lock:
            self.external_fetches_attempted += 1
            if ok:
                self.external_fetches_completed += 1

    def record_worker_timeout(self, stage: str, worker: str) -> None:
        with self._lock:
            self.worker_timeout_events.append({"stage": stage, "worker": worker, "at": monotonic()})

    def start_memory_tracking(self) -> None:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracemalloc_started_here = True

    def stop_memory_tracking_mb(self) -> Optional[float]:
        if not tracemalloc.is_tracing():
            return None
        _current, peak = tracemalloc.get_traced_memory()
        if self._tracemalloc_started_here:
            tracemalloc.stop()
        return round(peak / (1024 * 1024), 3)

    def stage_duration_s(self, name: str) -> Optional[float]:
        t = self.stage_timings.get(name)
        if not t or t["end"] is None:
            return None
        return round(t["end"] - t["start"], 3)

    def as_dict(self, memory_peak_mb: Optional[float]) -> dict:
        return {
            "stage_timings_s": {
                name: {"start": v["start"], "end": v["end"],
                       "duration": self.stage_duration_s(name)}
                for name, v in self.stage_timings.items()
            },
            "requests_attempted": self.requests_attempted,
            "requests_completed": self.requests_completed,
            "requests_failed": self.requests_failed,
            "requests_timed_out": self.requests_timed_out,
            "requests_retried": self.requests_retried,
            "redirects_followed": self.redirects_followed,
            "responses_truncated": self.responses_truncated,
            "urls_deduplicated": self.urls_deduplicated,
            "bytes_downloaded": self.bytes_downloaded,
            "pages_skipped": self.pages_skipped,
            "pages_skipped_reasons": self.pages_skipped_reasons,
            "safety_blocks": self.safety_blocks,
            "external_fetches_attempted": self.external_fetches_attempted,
            "external_fetches_completed": self.external_fetches_completed,
            "worker_timeout_events": self.worker_timeout_events,
            "memory_peak_mb": memory_peak_mb,  # Python allocation peak
            "process_rss_mb": self.process_rss_mb(),  # best-effort process RSS; may be None
        }
