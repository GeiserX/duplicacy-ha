"""Binary sensor entities for the Duplicacy integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import MetricKey
from .const import DOMAIN
from .coordinator import DuplicacyCoordinator
from .entity import DuplicacyEntity


@dataclass(frozen=True, kw_only=True)
class DuplicacyBinarySensorDescription(BinarySensorEntityDescription):
    """Extended binary sensor description with metric name."""

    metric: str


BINARY_SENSOR_DESCRIPTIONS: tuple[DuplicacyBinarySensorDescription, ...] = (
    DuplicacyBinarySensorDescription(
        key="backup_running",
        translation_key="backup_running",
        metric="duplicacy_backup_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:backup-restore",
    ),
    DuplicacyBinarySensorDescription(
        key="prune_running",
        translation_key="prune_running",
        metric="duplicacy_prune_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:delete-sweep",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DuplicacyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[DuplicacyBinarySensor] = []
    for key, metrics in (coordinator.data or {}).items():
        for desc in BINARY_SENSOR_DESCRIPTIONS:
            if desc.metric in metrics:
                entities.append(
                    DuplicacyBinarySensor(coordinator, key, entry.entry_id, desc)
                )

    async_add_entities(entities)


class DuplicacyBinarySensor(DuplicacyEntity, BinarySensorEntity):
    """Binary sensor entity for a Duplicacy running state."""

    entity_description: DuplicacyBinarySensorDescription

    def __init__(
        self,
        coordinator: DuplicacyCoordinator,
        key: MetricKey,
        entry_id: str,
        description: DuplicacyBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, key, entry_id)
        self.entity_description = description
        snapshot_id, storage_target = key
        self._attr_unique_id = (
            f"{entry_id}_{snapshot_id}_{storage_target}_{description.key}"
        )

    @property
    def is_on(self) -> bool | None:
        metrics = self._metrics
        if metrics is None:
            return None
        value = metrics.get(self.entity_description.metric)
        if value is None:
            return None
        return value == 1.0
