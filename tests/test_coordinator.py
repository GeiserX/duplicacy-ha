"""Tests for the Duplicacy coordinator."""

from __future__ import annotations

import logging
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.duplicacy.api import DuplicacyApiError, DuplicacyConnectionError
from custom_components.duplicacy.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from custom_components.duplicacy.coordinator import DuplicacyCoordinator

from .conftest import MOCK_METRICS_PARSED

# Import UpdateFailed from where our stub lives
from homeassistant.helpers.update_coordinator import UpdateFailed


def _make_client(metrics=None, error=None):
    """Create a mock API client."""
    client = MagicMock()
    if error:
        client.get_metrics = AsyncMock(side_effect=error)
    else:
        client.get_metrics = AsyncMock(return_value=metrics or {})
    return client


def _make_hass():
    """Create a minimal mock hass object."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_default_scan_interval() -> None:
    """Verify default scan interval is 30 seconds."""
    assert DEFAULT_SCAN_INTERVAL == 30


# ---------------------------------------------------------------------------
# DuplicacyCoordinator – __init__
# ---------------------------------------------------------------------------

class TestCoordinatorInit:
    """Tests for coordinator initialization."""

    def test_stores_client(self) -> None:
        """Test that the client is stored."""
        client = _make_client()
        coordinator = DuplicacyCoordinator(_make_hass(), client)
        assert coordinator.client is client

    def test_name_is_domain(self) -> None:
        """Test that the coordinator name is the domain."""
        client = _make_client()
        coordinator = DuplicacyCoordinator(_make_hass(), client)
        assert coordinator.name == DOMAIN

    def test_update_interval(self) -> None:
        """Test update interval matches the constant."""
        client = _make_client()
        coordinator = DuplicacyCoordinator(_make_hass(), client)
        assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)

    def test_passes_hass(self) -> None:
        """Test that hass is passed to the parent."""
        hass = _make_hass()
        client = _make_client()
        coordinator = DuplicacyCoordinator(hass, client)
        assert coordinator.hass is hass


# ---------------------------------------------------------------------------
# DuplicacyCoordinator – _async_update_data
# ---------------------------------------------------------------------------

class TestCoordinatorUpdate:
    """Tests for coordinator data fetching."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Test successful metric fetch stores data."""
        client = _make_client(metrics=MOCK_METRICS_PARSED)
        coordinator = DuplicacyCoordinator(_make_hass(), client)

        result = await coordinator._async_update_data()

        assert result is MOCK_METRICS_PARSED
        client.get_metrics.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_api_error_raises_update_failed(self) -> None:
        """Test that DuplicacyApiError is wrapped in UpdateFailed."""
        client = _make_client(error=DuplicacyApiError("test error"))
        coordinator = DuplicacyCoordinator(_make_hass(), client)

        with pytest.raises(UpdateFailed, match="test error"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_connection_error_raises_update_failed(self) -> None:
        """Test that DuplicacyConnectionError is wrapped in UpdateFailed."""
        client = _make_client(error=DuplicacyConnectionError("unreachable"))
        coordinator = DuplicacyCoordinator(_make_hass(), client)

        with pytest.raises(UpdateFailed, match="unreachable"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_first_refresh_calls_update(self) -> None:
        """Test async_config_entry_first_refresh calls _async_update_data."""
        client = _make_client(metrics=MOCK_METRICS_PARSED)
        coordinator = DuplicacyCoordinator(_make_hass(), client)

        await coordinator.async_config_entry_first_refresh()

        assert coordinator.data is MOCK_METRICS_PARSED
        client.get_metrics.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_metrics_returned(self) -> None:
        """Test fetching returns empty dict when no metrics."""
        client = _make_client(metrics={})
        coordinator = DuplicacyCoordinator(_make_hass(), client)

        result = await coordinator._async_update_data()
        assert result == {}
