"""Tests for the Duplicacy integration __init__ (setup/unload)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.duplicacy import (
    PLATFORMS,
    async_remove_config_entry_device,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.duplicacy.const import CONF_URL, DOMAIN

from .conftest import MOCK_METRICS_PARSED


def _make_hass():
    """Create a mock hass with data dict."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


def _make_entry(entry_id="test_entry", url="http://localhost:9750"):
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = {CONF_URL: url}
    return entry


# ---------------------------------------------------------------------------
# PLATFORMS constant
# ---------------------------------------------------------------------------

def test_platforms_includes_sensor() -> None:
    """Test sensor platform is registered."""
    assert "sensor" in PLATFORMS


def test_platforms_includes_binary_sensor() -> None:
    """Test binary_sensor platform is registered."""
    assert "binary_sensor" in PLATFORMS


def test_platforms_count() -> None:
    """Test exactly 2 platforms are registered."""
    assert len(PLATFORMS) == 2


# ---------------------------------------------------------------------------
# async_setup_entry
# ---------------------------------------------------------------------------

class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.asyncio
    async def test_returns_true(self) -> None:
        """Test that setup returns True on success."""
        hass = _make_hass()
        entry = _make_entry()

        with patch(
            "custom_components.duplicacy.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.duplicacy.DuplicacyApiClient",
        ) as mock_client_cls, patch(
            "custom_components.duplicacy.DuplicacyCoordinator",
        ) as mock_coord_cls:
            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            result = await async_setup_entry(hass, entry)

        assert result is True

    @pytest.mark.asyncio
    async def test_stores_coordinator_in_hass_data(self) -> None:
        """Test that coordinator is stored in hass.data[DOMAIN][entry_id]."""
        hass = _make_hass()
        entry = _make_entry()

        with patch(
            "custom_components.duplicacy.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.duplicacy.DuplicacyApiClient",
        ), patch(
            "custom_components.duplicacy.DuplicacyCoordinator",
        ) as mock_coord_cls:
            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            await async_setup_entry(hass, entry)

        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]
        assert hass.data[DOMAIN][entry.entry_id] is mock_coordinator

    @pytest.mark.asyncio
    async def test_calls_first_refresh(self) -> None:
        """Test that async_config_entry_first_refresh is called."""
        hass = _make_hass()
        entry = _make_entry()

        with patch(
            "custom_components.duplicacy.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.duplicacy.DuplicacyApiClient",
        ), patch(
            "custom_components.duplicacy.DuplicacyCoordinator",
        ) as mock_coord_cls:
            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            await async_setup_entry(hass, entry)

        mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_forwards_platform_setups(self) -> None:
        """Test that platform setups are forwarded."""
        hass = _make_hass()
        entry = _make_entry()

        with patch(
            "custom_components.duplicacy.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.duplicacy.DuplicacyApiClient",
        ), patch(
            "custom_components.duplicacy.DuplicacyCoordinator",
        ) as mock_coord_cls:
            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            await async_setup_entry(hass, entry)

        hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
            entry, PLATFORMS
        )

    @pytest.mark.asyncio
    async def test_creates_client_with_url(self) -> None:
        """Test API client is created with the URL from config entry."""
        hass = _make_hass()
        entry = _make_entry(url="http://myhost:9750")

        with patch(
            "custom_components.duplicacy.async_get_clientsession",
            return_value=MagicMock(),
        ) as mock_get_session, patch(
            "custom_components.duplicacy.DuplicacyApiClient",
        ) as mock_client_cls, patch(
            "custom_components.duplicacy.DuplicacyCoordinator",
        ) as mock_coord_cls:
            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            await async_setup_entry(hass, entry)

        mock_client_cls.assert_called_once_with(
            "http://myhost:9750", mock_get_session.return_value
        )

    @pytest.mark.asyncio
    async def test_creates_coordinator_with_client(self) -> None:
        """Test coordinator is created with hass and client."""
        hass = _make_hass()
        entry = _make_entry()

        with patch(
            "custom_components.duplicacy.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.duplicacy.DuplicacyApiClient",
        ) as mock_client_cls, patch(
            "custom_components.duplicacy.DuplicacyCoordinator",
        ) as mock_coord_cls:
            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            await async_setup_entry(hass, entry)

        mock_coord_cls.assert_called_once_with(hass, mock_client_cls.return_value)


# ---------------------------------------------------------------------------
# async_unload_entry
# ---------------------------------------------------------------------------

class TestAsyncUnloadEntry:
    """Tests for async_unload_entry."""

    @pytest.mark.asyncio
    async def test_unload_returns_true(self) -> None:
        """Test successful unload returns True."""
        hass = _make_hass()
        entry = _make_entry()
        hass.data[DOMAIN] = {entry.entry_id: MagicMock()}

        result = await async_unload_entry(hass, entry)

        assert result is True

    @pytest.mark.asyncio
    async def test_unload_removes_coordinator(self) -> None:
        """Test coordinator is removed from hass.data on unload."""
        hass = _make_hass()
        entry = _make_entry()
        hass.data[DOMAIN] = {entry.entry_id: MagicMock()}

        await async_unload_entry(hass, entry)

        assert entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_calls_async_unload_platforms(self) -> None:
        """Test async_unload_platforms is called with correct platforms."""
        hass = _make_hass()
        entry = _make_entry()
        hass.data[DOMAIN] = {entry.entry_id: MagicMock()}

        await async_unload_entry(hass, entry)

        hass.config_entries.async_unload_platforms.assert_awaited_once_with(
            entry, PLATFORMS
        )

    @pytest.mark.asyncio
    async def test_unload_keeps_coordinator_on_failure(self) -> None:
        """Test coordinator is NOT removed when unload fails."""
        hass = _make_hass()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)
        entry = _make_entry()
        coordinator = MagicMock()
        hass.data[DOMAIN] = {entry.entry_id: coordinator}

        result = await async_unload_entry(hass, entry)

        assert result is False
        assert hass.data[DOMAIN][entry.entry_id] is coordinator


# ---------------------------------------------------------------------------
# async_remove_config_entry_device
# ---------------------------------------------------------------------------

def _hass_with_coordinator(entry, data):
    """Mock hass whose coordinator exposes the given coordinator.data."""
    hass = _make_hass()
    coordinator = MagicMock()
    coordinator.data = data
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    return hass


def _make_device(identifiers):
    """Minimal stand-in for a device registry entry."""
    return SimpleNamespace(identifiers=set(identifiers))


class TestAsyncRemoveConfigEntryDevice:
    """Tests for manual stale-device deletion (issue #12)."""

    @pytest.mark.asyncio
    async def test_stale_device_can_be_removed(self) -> None:
        """A device no longer reported by the exporter is removable."""
        entry = _make_entry()
        hass = _hass_with_coordinator(entry, {("docs", "b2"): {}})
        device = _make_device({(DOMAIN, f"{entry.entry_id}_old_combined_b2")})

        assert await async_remove_config_entry_device(hass, entry, device) is True

    @pytest.mark.asyncio
    async def test_live_device_is_kept(self) -> None:
        """A device still present in coordinator data cannot be removed."""
        entry = _make_entry()
        hass = _hass_with_coordinator(entry, {("docs", "b2"): {}})
        device = _make_device({(DOMAIN, f"{entry.entry_id}_docs_b2")})

        assert await async_remove_config_entry_device(hass, entry, device) is False

    @pytest.mark.asyncio
    async def test_none_coordinator_data_allows_removal(self) -> None:
        """With no live data, any device is treated as stale and removable."""
        entry = _make_entry()
        hass = _hass_with_coordinator(entry, None)
        device = _make_device({(DOMAIN, f"{entry.entry_id}_docs_b2")})

        assert await async_remove_config_entry_device(hass, entry, device) is True

    @pytest.mark.asyncio
    async def test_unloaded_entry_allows_removal(self) -> None:
        """An unloaded entry (exporter down) must not raise; removal is allowed."""
        entry = _make_entry()
        hass = _make_hass()  # no DOMAIN data at all
        device = _make_device({(DOMAIN, f"{entry.entry_id}_docs_b2")})

        assert await async_remove_config_entry_device(hass, entry, device) is True

    @pytest.mark.asyncio
    async def test_other_domain_identifier_ignored(self) -> None:
        """Identifiers from other integrations never block removal."""
        entry = _make_entry()
        hass = _hass_with_coordinator(entry, {("docs", "b2"): {}})
        device = _make_device({("other_integration", f"{entry.entry_id}_docs_b2")})

        assert await async_remove_config_entry_device(hass, entry, device) is True

    @pytest.mark.asyncio
    async def test_live_device_with_extra_identifier_kept(self) -> None:
        """A live device stays even when it also has a foreign identifier."""
        entry = _make_entry()
        hass = _hass_with_coordinator(entry, {("docs", "b2"): {}})
        device = _make_device({
            (DOMAIN, f"{entry.entry_id}_docs_b2"),
            ("other", "x"),
        })

        assert await async_remove_config_entry_device(hass, entry, device) is False
