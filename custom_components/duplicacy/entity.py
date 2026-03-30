"""Base entity for the Duplicacy integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import MetricKey
from .const import DOMAIN
from .coordinator import DuplicacyCoordinator


class DuplicacyEntity(CoordinatorEntity[DuplicacyCoordinator]):
    """Base class for Duplicacy entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DuplicacyCoordinator,
        key: MetricKey,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        snapshot_id, storage_target = key

        device_id = f"{entry_id}_{snapshot_id}_{storage_target}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"{snapshot_id} \u2192 {storage_target}",
            manufacturer="Duplicacy",
            model="Duplicacy Backup",
        )

    @property
    def _metrics(self) -> dict | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)
