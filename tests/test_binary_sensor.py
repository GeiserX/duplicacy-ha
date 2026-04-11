"""Tests for Duplicacy binary sensor logic."""

from __future__ import annotations

import pytest

from .conftest import MOCK_METRICS_PARSED


def _is_running(metrics: dict | None, metric_name: str) -> bool | None:
    """Replicate the binary sensor is_on logic."""
    if metrics is None:
        return None
    value = metrics.get(metric_name)
    if value is None:
        return None
    return value == 1.0


def test_backup_not_running() -> None:
    """Test backup is not running when metric is 0."""
    key = ("documents", "b2")
    result = _is_running(MOCK_METRICS_PARSED[key], "duplicacy_backup_running")
    assert result is False


def test_backup_running() -> None:
    """Test backup is running when metric is 1."""
    metrics = {**MOCK_METRICS_PARSED[("documents", "b2")], "duplicacy_backup_running": 1.0}
    result = _is_running(metrics, "duplicacy_backup_running")
    assert result is True


def test_prune_not_running() -> None:
    """Test prune is not running when metric is 0."""
    key = ("documents", "b2")
    result = _is_running(MOCK_METRICS_PARSED[key], "duplicacy_prune_running")
    assert result is False


def test_missing_metrics() -> None:
    """Test None when metrics are missing."""
    result = _is_running(None, "duplicacy_backup_running")
    assert result is None


def test_missing_metric_key() -> None:
    """Test None when specific metric key is missing."""
    result = _is_running({"machine": "s1"}, "duplicacy_backup_running")
    assert result is None
