"""API client for the Duplicacy Prometheus exporter."""

from __future__ import annotations

import re
from typing import Any

import aiohttp


class DuplicacyApiError(Exception):
    """Base exception for Duplicacy API errors."""


class DuplicacyConnectionError(DuplicacyApiError):
    """Raised when the exporter is unreachable."""


MetricKey = tuple[str, str]  # (snapshot_id, storage_target)

_METRIC_LINE_RE = re.compile(
    r'^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)'
    r'(?:\{(?P<labels>[^}]*)\})?\s+'
    r'(?P<value>\S+)$'
)
_LABEL_RE = re.compile(r'(\w+)="([^"]*)"')


def _parse_labels(raw: str) -> dict[str, str]:
    return dict(_LABEL_RE.findall(raw))


def _parse_metrics(text: str) -> dict[MetricKey, dict[str, Any]]:
    """Parse Prometheus text exposition format into grouped metrics.

    Prune metrics are emitted without a ``snapshot_id`` label.  Instead of
    creating an orphan key ``("", storage_target)``, we defer them and fan
    them out to every backup key that shares the same ``storage_target``.
    """
    result: dict[MetricKey, dict[str, Any]] = {}
    # Collect prune metrics (no snapshot_id) keyed by storage_target
    deferred_prune: dict[str, dict[str, float]] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = _METRIC_LINE_RE.match(line)
        if not match:
            continue

        name = match.group("name")
        labels = _parse_labels(match.group("labels") or "")
        try:
            value = float(match.group("value"))
        except ValueError:
            continue

        snapshot_id = labels.get("snapshot_id", "")
        storage_target = labels.get("storage_target", "")
        machine = labels.get("machine", "")

        # Prune metrics lack snapshot_id — defer and fan out later
        if not snapshot_id and name.startswith("duplicacy_prune_"):
            deferred_prune.setdefault(storage_target, {})[name] = value
            continue

        key: MetricKey = (snapshot_id, storage_target)

        if key not in result:
            result[key] = {"machine": machine}

        result[key][name] = value

    # Fan-out deferred prune metrics to every backup key with matching storage
    for storage_target, prune_values in deferred_prune.items():
        for key, metrics in result.items():
            if key[1] == storage_target:
                metrics.update(prune_values)

    return result


class DuplicacyApiClient:
    """Async client for the Duplicacy Prometheus exporter."""

    def __init__(self, url: str, session: aiohttp.ClientSession) -> None:
        self._url = url.rstrip("/")
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=10)

    async def check_health(self) -> bool:
        try:
            async with self._session.get(
                f"{self._url}/health", timeout=self._timeout
            ) as resp:
                return resp.status == 200
        except (aiohttp.ClientError, TimeoutError) as err:
            raise DuplicacyConnectionError(
                f"Cannot reach exporter at {self._url}"
            ) from err

    async def get_metrics(self) -> dict[MetricKey, dict[str, Any]]:
        try:
            async with self._session.get(
                f"{self._url}/metrics", timeout=self._timeout
            ) as resp:
                if resp.status != 200:
                    raise DuplicacyApiError(
                        f"Exporter returned HTTP {resp.status}"
                    )
                text = await resp.text()
        except DuplicacyApiError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise DuplicacyConnectionError(
                f"Cannot reach exporter at {self._url}"
            ) from err

        return _parse_metrics(text)
