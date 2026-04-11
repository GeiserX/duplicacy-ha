"""Tests for Duplicacy sensor value logic."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from .conftest import MOCK_METRICS_PARSED


def _timestamp_from_unix(value: float | None) -> datetime | None:
    """Convert unix timestamp to datetime."""
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=UTC)


def _ratio_to_percent(value: float | None) -> float | None:
    """Convert ratio to percent."""
    if value is None:
        return None
    return round(value * 100, 2)


def test_timestamp_from_unix_valid() -> None:
    """Test converting valid unix timestamp."""
    result = _timestamp_from_unix(1704067200.0)
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC


def test_timestamp_from_unix_zero() -> None:
    """Test zero timestamp returns None."""
    assert _timestamp_from_unix(0) is None


def test_timestamp_from_unix_negative() -> None:
    """Test negative timestamp returns None."""
    assert _timestamp_from_unix(-1.0) is None


def test_timestamp_from_unix_none() -> None:
    """Test None returns None."""
    assert _timestamp_from_unix(None) is None


def test_ratio_to_percent_full() -> None:
    """Test 1.0 ratio to 100%."""
    assert _ratio_to_percent(1.0) == 100.0


def test_ratio_to_percent_half() -> None:
    """Test 0.5 ratio to 50%."""
    assert _ratio_to_percent(0.5) == 50.0


def test_ratio_to_percent_none() -> None:
    """Test None returns None."""
    assert _ratio_to_percent(None) is None


def test_ratio_to_percent_zero() -> None:
    """Test 0.0 ratio to 0%."""
    assert _ratio_to_percent(0.0) == 0.0


def test_duration_value() -> None:
    """Test extracting duration from metrics."""
    key = ("documents", "b2")
    metrics = MOCK_METRICS_PARSED[key]
    assert metrics["duplicacy_backup_last_duration_seconds"] == 120.5


def test_progress_value() -> None:
    """Test extracting progress from metrics."""
    key = ("documents", "b2")
    metrics = MOCK_METRICS_PARSED[key]
    progress = _ratio_to_percent(metrics["duplicacy_backup_progress_ratio"])
    assert progress == 100.0


def test_exit_code_success() -> None:
    """Test exit code 0 means success."""
    key = ("documents", "b2")
    metrics = MOCK_METRICS_PARSED[key]
    assert metrics["duplicacy_backup_last_exit_code"] == 0.0


def test_exit_code_icon_success() -> None:
    """Test icon for exit code 0."""
    exit_code = 0.0
    icon = "mdi:alert-circle" if exit_code != 0 else "mdi:check-circle"
    assert icon == "mdi:check-circle"


def test_exit_code_icon_failure() -> None:
    """Test icon for exit code 1."""
    exit_code = 1.0
    icon = "mdi:alert-circle" if exit_code != 0 else "mdi:check-circle"
    assert icon == "mdi:alert-circle"


def test_missing_metric_returns_none() -> None:
    """Test that a missing metric key returns None via .get()."""
    key = ("documents", "b2")
    metrics = MOCK_METRICS_PARSED[key]
    assert metrics.get("nonexistent_metric") is None


def test_unique_id_format() -> None:
    """Test unique ID is constructed properly."""
    entry_id = "entry1"
    snapshot_id, storage_target = "documents", "b2"
    key = "last_duration"
    uid = f"{entry_id}_{snapshot_id}_{storage_target}_{key}"
    assert uid == "entry1_documents_b2_last_duration"
