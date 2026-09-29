"""Quota observation and threshold alerts; never uses a model request."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class QuotaAlert:
    threshold: int
    bucket_id: str
    bucket_name: str
    window: str
    used_percent: int
    resets_at: int | None
    observed_at: datetime
    message: str


@dataclass(frozen=True, slots=True)
class QuotaBucket:
    bucket_id: str
    bucket_name: str
    window: str
    used_percent: int
    window_duration_mins: int | None
    resets_at: int | None
    spend_control_reached: bool | None


@dataclass(slots=True)
class QuotaState:
    blocked: bool
    unknown: bool
    buckets: list[QuotaBucket] = field(default_factory=list)
    alerts: list[QuotaAlert] = field(default_factory=list)


class QuotaMonitor:
    def __init__(self, thresholds: tuple[int, ...] = (20, 10)):
        self.thresholds = tuple(sorted(thresholds, reverse=True))
        self._seen: set[tuple[Any, ...]] = set()

    def observe(
        self,
        response: dict[str, Any],
        *,
        node_id: str,
        now: datetime,
    ) -> QuotaState:
        snapshots = self._snapshots(response)
        if snapshots is None:
            return QuotaState(blocked=False, unknown=True)

        buckets: list[QuotaBucket] = []
        alerts: list[QuotaAlert] = []
        unknown = response.get("ordinaryUsageAllowed") is None
        blocked = response.get("ordinaryUsageAllowed") is False

        for snapshot in snapshots:
            bucket_id = str(snapshot.get("limitId") or "default")
            bucket_name = str(snapshot.get("limitName") or bucket_id)
            spend_control = snapshot.get("spendControlReached")
            if spend_control is True:
                blocked = True
            elif spend_control is None:
                unknown = True
            for window_name in ("primary", "secondary"):
                window = snapshot.get(window_name)
                if window is None:
                    continue
                used = window.get("usedPercent")
                if used is None:
                    unknown = True
                    continue
                bucket = QuotaBucket(
                    bucket_id=bucket_id,
                    bucket_name=bucket_name,
                    window=window_name,
                    used_percent=int(used),
                    window_duration_mins=window.get("windowDurationMins"),
                    resets_at=window.get("resetsAt"),
                    spend_control_reached=spend_control,
                )
                buckets.append(bucket)
                remaining = 100 - bucket.used_percent
                for threshold in self.thresholds:
                    if remaining > threshold:
                        continue
                    key = (
                        node_id,
                        bucket.bucket_id,
                        bucket.window,
                        threshold,
                        bucket.resets_at,
                    )
                    if key in self._seen:
                        continue
                    self._seen.add(key)
                    alerts.append(
                        QuotaAlert(
                            threshold=threshold,
                            bucket_id=bucket.bucket_id,
                            bucket_name=bucket.bucket_name,
                            window=bucket.window,
                            used_percent=bucket.used_percent,
                            resets_at=bucket.resets_at,
                            observed_at=now,
                            message=(
                                f"{node_id} {bucket.bucket_name} {bucket.window} "
                                f"remaining {remaining}%"
                            ),
                        )
                    )

        if not buckets:
            unknown = True
        return QuotaState(
            blocked=blocked,
            unknown=unknown,
            buckets=buckets,
            alerts=alerts,
        )

    @staticmethod
    def _snapshots(response: dict[str, Any]) -> list[dict[str, Any]] | None:
        by_id = response.get("rateLimitsByLimitId")
        if isinstance(by_id, dict) and by_id:
            return [value for value in by_id.values() if isinstance(value, dict)]
        single = response.get("rateLimits")
        if isinstance(single, dict):
            return [single]
        return None
