"""Tests for Duplicacy binary sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.duplicacy.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    DuplicacyBinarySensor,
    DuplicacyBinarySensorDescription,
    async_setup_entry,
)
from custom_components.duplicacy.const import DOMAIN

from .conftest import MOCK_METRICS_PARSED, MOCK_METRICS_MULTI


def _make_coordinator(data=None):
    """Create a mock coordinator with given data."""
    coordinator = MagicMock()
    coordinator.data = data
    return coordinator


# ---------------------------------------------------------------------------
# DuplicacyBinarySensorDescription
# ---------------------------------------------------------------------------

def test_binary_sensor_descriptions_count() -> None:
    """Test that both binary sensor descriptions are defined."""
    assert len(BINARY_SENSOR_DESCRIPTIONS) == 2


def test_binary_sensor_descriptions_keys() -> None:
    """Test the keys of binary sensor descriptions."""
    keys = {d.key for d in BINARY_SENSOR_DESCRIPTIONS}
    assert keys == {"backup_running", "prune_running"}


def test_binary_sensor_descriptions_metrics() -> None:
    """Test the metric names of binary sensor descriptions."""
    metrics = {d.metric for d in BINARY_SENSOR_DESCRIPTIONS}
    assert metrics == {"duplicacy_backup_running", "duplicacy_prune_running"}


# ---------------------------------------------------------------------------
# DuplicacyBinarySensor
# ---------------------------------------------------------------------------

class TestDuplicacyBinarySensor:
    """Tests for the DuplicacyBinarySensor class."""

    def test_unique_id_format(self) -> None:
        """Test unique ID is constructed properly."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = BINARY_SENSOR_DESCRIPTIONS[0]  # backup_running
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "entry1", desc
        )

        assert sensor._attr_unique_id == "entry1_documents_b2_backup_running"

    def test_entity_description_stored(self) -> None:
        """Test entity_description is stored on init."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = BINARY_SENSOR_DESCRIPTIONS[0]
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "e1", desc
        )
        assert sensor.entity_description is desc

    def test_is_on_false_when_metric_zero(self) -> None:
        """Test is_on returns False when metric value is 0."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = BINARY_SENSOR_DESCRIPTIONS[0]  # backup_running
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "e1", desc
        )
        # In MOCK_METRICS_PARSED, backup_running is 0.0
        assert sensor.is_on is False

    def test_is_on_true_when_metric_one(self) -> None:
        """Test is_on returns True when metric value is 1."""
        data = {
            ("documents", "b2"): {
                "machine": "s1",
                "duplicacy_backup_running": 1.0,
            }
        }
        coordinator = _make_coordinator(data)
        desc = BINARY_SENSOR_DESCRIPTIONS[0]  # backup_running
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "e1", desc
        )
        assert sensor.is_on is True

    def test_is_on_none_when_no_data(self) -> None:
        """Test is_on returns None when coordinator has no data."""
        coordinator = _make_coordinator(None)
        desc = BINARY_SENSOR_DESCRIPTIONS[0]
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "e1", desc
        )
        assert sensor.is_on is None

    def test_is_on_none_when_key_missing(self) -> None:
        """Test is_on returns None when key not in data."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = BINARY_SENSOR_DESCRIPTIONS[0]
        sensor = DuplicacyBinarySensor(
            coordinator, ("nonexistent", "key"), "e1", desc
        )
        assert sensor.is_on is None

    def test_is_on_none_when_metric_missing(self) -> None:
        """Test is_on returns None when metric not in metrics dict."""
        data = {("documents", "b2"): {"machine": "s1"}}
        coordinator = _make_coordinator(data)
        desc = BINARY_SENSOR_DESCRIPTIONS[0]  # backup_running
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "e1", desc
        )
        assert sensor.is_on is None

    def test_prune_running_false(self) -> None:
        """Test prune_running is False when metric is 0."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        desc = BINARY_SENSOR_DESCRIPTIONS[1]  # prune_running
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "e1", desc
        )
        assert sensor.is_on is False

    def test_prune_running_true(self) -> None:
        """Test prune_running is True when metric is 1."""
        data = {
            ("documents", "b2"): {
                "machine": "s1",
                "duplicacy_prune_running": 1.0,
            }
        }
        coordinator = _make_coordinator(data)
        desc = BINARY_SENSOR_DESCRIPTIONS[1]  # prune_running
        sensor = DuplicacyBinarySensor(
            coordinator, ("documents", "b2"), "e1", desc
        )
        assert sensor.is_on is True


# ---------------------------------------------------------------------------
# async_setup_entry
# ---------------------------------------------------------------------------

class TestAsyncSetupEntry:
    """Tests for binary_sensor async_setup_entry."""

    @pytest.mark.asyncio
    async def test_creates_entities_for_matching_metrics(self) -> None:
        """Test entities created for each binary metric in data."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        hass = MagicMock()
        hass.data = {DOMAIN: {"entry1": coordinator}}

        entry = MagicMock()
        entry.entry_id = "entry1"

        added: list = []
        async_add_entities = MagicMock(side_effect=lambda e: added.extend(e))

        await async_setup_entry(hass, entry, async_add_entities)

        async_add_entities.assert_called_once()
        # 2 descriptions, both present in mock data
        assert len(added) == 2

    @pytest.mark.asyncio
    async def test_skips_missing_metrics(self) -> None:
        """Test sensors not created for missing metrics."""
        data = {
            ("documents", "b2"): {
                "machine": "s1",
                "duplicacy_backup_running": 0.0,
                # prune_running is absent
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

        assert len(added) == 1

    @pytest.mark.asyncio
    async def test_creates_entities_for_multiple_keys(self) -> None:
        """Test entities created for multiple snapshot/storage combos."""
        coordinator = _make_coordinator(MOCK_METRICS_MULTI)
        hass = MagicMock()
        hass.data = {DOMAIN: {"e1": coordinator}}

        entry = MagicMock()
        entry.entry_id = "e1"

        added: list = []
        async_add_entities = MagicMock(side_effect=lambda e: added.extend(e))

        await async_setup_entry(hass, entry, async_add_entities)

        # 2 keys * 2 descriptions = 4 entities
        assert len(added) == 4

    @pytest.mark.asyncio
    async def test_no_entities_when_data_is_none(self) -> None:
        """Test no entities when coordinator data is None."""
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
