"""Duplicacy Backup Monitor integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DuplicacyApiClient
from .const import CONF_URL, DOMAIN
from .coordinator import DuplicacyCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers import device_registry as dr

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Duplicacy from a config entry."""
    session = async_get_clientsession(hass)
    client = DuplicacyApiClient(entry.data[CONF_URL], session)

    coordinator = DuplicacyCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Duplicacy config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow deleting a device from the UI when it is no longer reported.

    Each device represents one ``(snapshot_id, storage_target)`` backup. When the
    exporter stops reporting a backup — e.g. the old combined device that 0.5.0+
    replaced with per-folder devices — its key disappears from the coordinator
    and the device becomes stale. Returning ``True`` lets the user remove such a
    device; a device that is still live is kept (HA would re-create it anyway).
    """
    # The entry can be unloaded (e.g. the exporter is unreachable) at the moment
    # the user cleans up a device, so read the coordinator defensively: a device
    # the integration cannot currently see counts as not-live and is removable.
    coordinator = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    live_data = coordinator.data if coordinator is not None else None
    live_device_ids = {
        f"{config_entry.entry_id}_{snapshot_id}_{storage_target}"
        for snapshot_id, storage_target in (live_data or {})
    }
    return not any(
        identifier in live_device_ids
        for domain, identifier in device_entry.identifiers
        if domain == DOMAIN
    )
