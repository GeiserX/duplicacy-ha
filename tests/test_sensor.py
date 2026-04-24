"""Tests for Duplicacy sensor entities."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.duplicacy.sensor import (
    SENSOR_DESCRIPTIONS,
    DuplicacySensor,
    DuplicacySensorDescription,
    _ratio_to_percent,
    _timestamp_from_unix,
    async_setup_entry,
)
from custom_components.duplicacy.const import DOMAIN

from .conftest import MOCK_METRICS_PARSED, MOCK_METRICS_MULTI


# ---------------------------------------------------------------------------
# _timestamp_from_unix
# ---------------------------------------------------------------------------

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


def test_timestamp_from_unix_small_positive() -> None:
    """Test small positive value still works."""
    result = _timestamp_from_unix(1.0)
    assert isinstance(result, datetime)


# ---------------------------------------------------------------------------
# _ratio_to_percent
# ---------------------------------------------------------------------------

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


def test_ratio_to_percent_precision() -> None:
    """Test rounding to 2 decimal places."""
    assert _ratio_to_percent(0.33333) == 33.33


# ---------------------------------------------------------------------------
# DuplicacySensorDescription
# ---------------------------------------------------------------------------

def test_sensor_descriptions_count() -> None:
    """Test that all 15 sensor descriptions are defined."""
    assert len(SENSOR_DESCRIPTIONS) == 15


def test_sensor_descriptions_unique_keys() -> None:
    """Test that all sensor description keys are unique."""
    keys = [d.key for d in SENSOR_DESCRIPTIONS]
    assert len(keys) == len(set(keys))


def test_sensor_descriptions_unique_metrics() -> None:
    """Test that all sensor description metrics are unique."""
    metrics = [d.metric for d in SENSOR_DESCRIPTIONS]
    assert len(metrics) == len(set(metrics))


def test_sensor_description_default_value_fn() -> None:
    """Test default value_fn is identity."""
    desc = DuplicacySensorDescription(key="test", metric="test_metric")
    assert desc.value_fn(42.0) == 42.0
    assert desc.value_fn(None) is None


def test_sensor_description_custom_value_fn() -> None:
    """Test custom value_fn works."""
    desc = DuplicacySensorDescription(
        key="test",
        metric="test_metric",
        value_fn=_ratio_to_percent,
    )
    assert desc.value_fn(0.5) == 50.0


# ---------------------------------------------------------------------------
# Helper to create a sensor instance
# ---------------------------------------------------------------------------

def _make_coordinator(data=None):
    """Create a mock coordinator with given data."""
    coordinator = MagicMock()
    coordinator.data = data
    return coordinator


def _make_sensor(coordinator, key, entry_id, desc):
    """Create a DuplicacySensor instance."""
    return DuplicacySensor(coordinator, key, entry_id, desc)


# ---------------------------------------------------------------------------
# DuplicacySensor
# ---------------------------------------------------------------------------

class TestDuplicacySensor:
    """Tests for the DuplicacySensor class."""

    def test_unique_id_format(self) -> None:
        """Test unique ID is constructed properly."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = SENSOR_DESCRIPTIONS[0]  # last_success
        sensor = _make_sensor(coordinator, ("documents", "b2"), "entry1", desc)

        assert sensor._attr_unique_id == "entry1_documents_b2_last_success"

    def test_entity_description_stored(self) -> None:
        """Test entity_description is stored on init."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = SENSOR_DESCRIPTIONS[0]
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.entity_description is desc

    def test_native_value_with_identity_fn(self) -> None:
        """Test native_value for a metric with identity value_fn."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        # last_duration uses identity fn
        desc = SENSOR_DESCRIPTIONS[1]  # last_duration
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.native_value == 120.5

    def test_native_value_with_timestamp_fn(self) -> None:
        """Test native_value for timestamp sensor returns datetime."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = SENSOR_DESCRIPTIONS[0]  # last_success (timestamp)
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        result = sensor.native_value
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC

    def test_native_value_with_ratio_fn(self) -> None:
        """Test native_value for progress sensor returns percentage."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = SENSOR_DESCRIPTIONS[3]  # progress (ratio_to_percent)
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.native_value == 100.0

    def test_native_value_none_when_no_data(self) -> None:
        """Test native_value returns None when coordinator has no data."""
        coordinator = _make_coordinator(None)
        desc = SENSOR_DESCRIPTIONS[0]
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.native_value is None

    def test_native_value_none_when_key_missing(self) -> None:
        """Test native_value returns None when key not in data."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = SENSOR_DESCRIPTIONS[0]
        sensor = _make_sensor(coordinator, ("nonexistent", "key"), "e1", desc)

        assert sensor.native_value is None

    def test_native_value_none_when_metric_missing(self) -> None:
        """Test native_value returns None when specific metric not present."""
        data = {("documents", "b2"): {"machine": "s1"}}
        coordinator = _make_coordinator(data)
        desc = SENSOR_DESCRIPTIONS[0]
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        # metric is missing, value_fn(_timestamp_from_unix) receives None
        result = sensor.native_value
        assert result is None

    def test_icon_exit_code_success(self) -> None:
        """Test icon for exit code 0."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        # Find the exit_code description
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "exit_code")
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.icon == "mdi:check-circle"

    def test_icon_exit_code_failure(self) -> None:
        """Test icon for non-zero exit code."""
        data = {
            ("documents", "b2"): {
                "machine": "s1",
                "duplicacy_backup_last_exit_code": 1.0,
            }
        }
        coordinator = _make_coordinator(data)
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "exit_code")
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.icon == "mdi:alert-circle"

    def test_icon_exit_code_no_metrics(self) -> None:
        """Test icon for exit code when metrics is None."""
        coordinator = _make_coordinator(None)
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "exit_code")
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        # When metrics is None/falsy, falls through to mdi:check-circle
        assert sensor.icon == "mdi:check-circle"

    def test_icon_non_exit_code(self) -> None:
        """Test icon for a non-exit-code sensor uses description icon."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "speed")
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.icon == "mdi:speedometer"

    def test_all_sensor_descriptions_have_metrics_in_mock(self) -> None:
        """Test that MOCK_METRICS_PARSED covers all sensor descriptions."""
        key = ("documents", "b2")
        metrics = MOCK_METRICS_PARSED[key]
        for desc in SENSOR_DESCRIPTIONS:
            assert desc.metric in metrics, f"Missing metric {desc.metric} in mock data"

    def test_prune_last_success_timestamp(self) -> None:
        """Test prune_last_success uses timestamp fn."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "prune_last_success")
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        result = sensor.native_value
        assert isinstance(result, datetime)

    def test_bytes_uploaded_value(self) -> None:
        """Test bytes_uploaded sensor reads correct value."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "bytes_uploaded")
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.native_value == 104857600.0

    def test_files_total_value(self) -> None:
        """Test files_total sensor reads correct value."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "files_total")
        sensor = _make_sensor(coordinator, ("documents", "b2"), "e1", desc)

        assert sensor.native_value == 1500.0


# ---------------------------------------------------------------------------
# async_setup_entry
# ---------------------------------------------------------------------------

class TestAsyncSetupEntry:
    """Tests for sensor async_setup_entry."""

    @pytest.mark.asyncio
    async def test_creates_entities_for_matching_metrics(self) -> None:
        """Test that entities are created for each metric present in data."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        hass = MagicMock()
        hass.data = {DOMAIN: {"entry1": coordinator}}

        entry = MagicMock()
        entry.entry_id = "entry1"

        added: list = []
        async_add_entities = MagicMock(side_effect=lambda e: added.extend(e))

        await async_setup_entry(hass, entry, async_add_entities)

        async_add_entities.assert_called_once()
        # All 15 sensor descriptions should match since mock has all metrics
        assert len(added) == 15

    @pytest.mark.asyncio
    async def test_skips_missing_metrics(self) -> None:
        """Test that sensors are not created for missing metrics."""
        data = {
            ("documents", "b2"): {
                "machine": "s1",
                "duplicacy_backup_last_duration_seconds": 60.0,
            }
        }
        coordinator = _make_coordinator(data)
        hass = MagicMock()
        hass.data = {DOMAIN: {"e1": coordinator}}

        entry = MagicMock()
        entry.entry_id = "e1"

        added: list = []
        async_add_entities = MagicMock(side_effect=lambda e: added.extend(e))

        await async_setup_entry(hass, entry, async_add_entities)

        # Only last_duration should match
        assert len(added) == 1

    @pytest.mark.asyncio
    async def test_creates_entities_for_multiple_keys(self) -> None:
        """Test entities are created for each snapshot/storage combo."""
        coordinator = _make_coordinator(MOCK_METRICS_MULTI)
        hass = MagicMock()
        hass.data = {DOMAIN: {"e1": coordinator}}

        entry = MagicMock()
        entry.entry_id = "e1"

        added: list = []
        async_add_entities = MagicMock(side_effect=lambda e: added.extend(e))

        await async_setup_entry(hass, entry, async_add_entities)

        # 2 keys, each with 6 metrics that match sensor descriptions
        # (last_success, last_duration, progress, exit_code, prune_last_success, last_revision... etc)
        assert len(added) > 2  # At least some entities per key
        # Verify both keys are represented
        unique_ids = [e._attr_unique_id for e in added]
        has_docs = any("documents_b2" in uid for uid in unique_ids)
        has_photos = any("photos_s3" in uid for uid in unique_ids)
        assert has_docs
        assert has_photos

    @pytest.mark.asyncio
    async def test_no_entities_when_data_is_none(self) -> None:
        """Test no entities created when coordinator data is None."""
        coordinator = _make_coordinator(None)
        hass = MagicMock()
        hass.data = {DOMAIN: {"e1": coordinator}}

        entry = MagicMock()
        entry.entry_id = "e1"

        added: list = []
        async_add_entities = MagicMock(side_effect=lambda e: added.extend(e))

        await async_setup_entry(hass, entry, async_add_entities)

        assert len(added) == 0

    @pytest.mark.asyncio
    async def test_no_entities_when_data_is_empty(self) -> None:
        """Test no entities when coordinator data is empty dict."""
        coordinator = _make_coordinator({})
        hass = MagicMock()
        hass.data = {DOMAIN: {"e1": coordinator}}

        entry = MagicMock()
        entry.entry_id = "e1"

        added: list = []
        async_add_entities = MagicMock(side_effect=lambda e: added.extend(e))

        await async_setup_entry(hass, entry, async_add_entities)

        assert len(added) == 0
