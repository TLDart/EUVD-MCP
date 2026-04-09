"""
In-process metrics for the EUVD MCP server.

Tracks per-tool request counts, latencies, error rates, and cache hit/miss ratios.
All counters are in-memory and reset on restart — suitable for dashboards and
health checks via the /metrics endpoint.
"""

from time import monotonic
from typing import Any


class _Metrics:
    def __init__(self) -> None:
        self._start = monotonic()
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.requests_total: dict[str, int] = {}
        self.errors_total: dict[str, int] = {}
        self._latency_sum: dict[str, float] = {}
        self._latency_count: dict[str, int] = {}

    @property
    def uptime_seconds(self) -> float:
        return monotonic() - self._start

    def record_request(self, name: str, latency_ms: float) -> None:
        self.requests_total[name] = self.requests_total.get(name, 0) + 1
        self._latency_sum[name] = self._latency_sum.get(name, 0.0) + latency_ms
        self._latency_count[name] = self._latency_count.get(name, 0) + 1

    def record_error(self, name: str, error_type: str) -> None:
        key = f"{name}.{error_type}"
        self.errors_total[key] = self.errors_total.get(key, 0) + 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def to_dict(self) -> dict[str, Any]:
        total = self.cache_hits + self.cache_misses
        hit_rate = round(self.cache_hits / total, 4) if total > 0 else None
        avg_latency = {
            k: round(self._latency_sum[k] / self._latency_count[k], 2)
            for k in self._latency_count
            if self._latency_count[k] > 0
        }
        return {
            "uptime_seconds": round(self.uptime_seconds, 2),
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": hit_rate,
            },
            "requests_total": dict(self.requests_total),
            "errors_total": dict(self.errors_total),
            "avg_latency_ms": avg_latency,
        }


metrics = _Metrics()
