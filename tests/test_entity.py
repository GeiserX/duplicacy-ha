"""Tests for the Duplicacy base entity."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.duplicacy.entity import DuplicacyEntity
from custom_components.duplicacy.const import DOMAIN

from .conftest import MOCK_METRICS_PARSED


def _make_coordinator(data=None):
    """Create a mock coordinator with the given data."""
    coordinator = MagicMock()
    coordinator.data = data
    return coordinator


class TestDuplicacyEntity:
    """Tests for the DuplicacyEntity base class."""

    def test_init_sets_device_info(self) -> None:
        """Test that __init__ sets device_info correctly."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        key = ("documents", "b2")
        entry_id = "test_entry"

        entity = DuplicacyEntity(coordinator, key, entry_id)

        assert entity._key == key
        assert entity._attr_has_entity_name is True
        info = entity._attr_device_info
        assert (DOMAIN, "test_entry_documents_b2") in info["identifiers"]
        assert "documents" in info["name"]
        assert "b2" in info["name"]
        assert info["manufacturer"] == "Duplicacy"
        assert info["model"] == "Duplicacy Backup"

    def test_init_stores_coordinator(self) -> None:
        """Test that __init__ stores the coordinator reference."""
        coordinator = _make_coordinator()
        entity = DuplicacyEntity(coordinator, ("a", "b"), "eid")
        assert entity.coordinator is coordinator

    def test_metrics_returns_data_for_key(self) -> None:
        """Test _metrics property returns the correct dict for the key."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        key = ("documents", "b2")
        entity = DuplicacyEntity(coordinator, key, "eid")

        metrics = entity._metrics
        assert metrics is not None
        assert metrics["machine"] == "server1"
        assert metrics["duplicacy_backup_running"] == 0.0

    def test_metrics_returns_none_when_data_is_none(self) -> None:
        """Test _metrics returns None when coordinator.data is None."""
        coordinator = _make_coordinator(None)
        entity = DuplicacyEntity(coordinator, ("a", "b"), "eid")
        assert entity._metrics is None

    def test_metrics_returns_none_for_missing_key(self) -> None:
        """Test _metrics returns None when key is not in data."""
        coordinator = _make_coordinator(MOCK_METRICS_PARSED)
        entity = DuplicacyEntity(coordinator, ("nonexistent", "key"), "eid")
        assert entity._metrics is None

    def test_device_id_format(self) -> None:
        """Test the device identifier format."""
        coordinator = _make_coordinator()
        entity = DuplicacyEntity(coordinator, ("snap", "store"), "entry123")

        info = entity._attr_device_info
        expected_id = "entry123_snap_store"
        assert (DOMAIN, expected_id) in info["identifiers"]

    def test_device_name_uses_arrow(self) -> None:
        """Test device name contains unicode arrow between snapshot and storage."""
        coordinator = _make_coordinator()
        entity = DuplicacyEntity(coordinator, ("mysnap", "mystore"), "eid")

        info = entity._attr_device_info
        assert info["name"] == "mysnap \u2192 mystore"
