"""Sensor entities for the Duplicacy integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import MetricKey
from .const import DOMAIN
from .coordinator import DuplicacyCoordinator
from .entity import DuplicacyEntity


def _timestamp_from_unix(value: float | None) -> datetime | None:
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=UTC)


def _ratio_to_percent(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 100, 2)


@dataclass(frozen=True, kw_only=True)
class DuplicacySensorDescription(SensorEntityDescription):
    """Extended sensor description with metric name and value transform."""

    metric: str
    value_fn: Callable[[float | None], Any] = lambda v: v


SENSOR_DESCRIPTIONS: tuple[DuplicacySensorDescription, ...] = (
    DuplicacySensorDescription(
        key="last_success",
        translation_key="last_success",
        metric="duplicacy_backup_last_success_timestamp_seconds",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_timestamp_from_unix,
    ),
    DuplicacySensorDescription(
        key="last_duration",
        translation_key="last_duration",
        metric="duplicacy_backup_last_duration_seconds",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_display_precision=0,
    ),
    DuplicacySensorDescription(
        key="speed",
        translation_key="speed",
        metric="duplicacy_backup_speed_bytes_per_second",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement="B/s",
        suggested_display_precision=1,
        icon="mdi:speedometer",
    ),
    DuplicacySensorDescription(
        key="progress",
        translation_key="progress",
        metric="duplicacy_backup_progress_ratio",
        native_unit_of_measurement="%",
        icon="mdi:progress-clock",
        suggested_display_precision=1,
        value_fn=_ratio_to_percent,
    ),
    DuplicacySensorDescription(
        key="bytes_uploaded",
        translation_key="bytes_uploaded",
        metric="duplicacy_backup_last_bytes_uploaded",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
    ),
    DuplicacySensorDescription(
        key="bytes_new",
        translation_key="bytes_new",
        metric="duplicacy_backup_last_bytes_new",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
    ),
    DuplicacySensorDescription(
        key="files_total",
        translation_key="files_total",
        metric="duplicacy_backup_last_files_total",
        icon="mdi:file-multiple",
    ),
    DuplicacySensorDescription(
        key="files_new",
        translation_key="files_new",
        metric="duplicacy_backup_last_files_new",
        icon="mdi:file-plus",
    ),
    DuplicacySensorDescription(
        key="exit_code",
        translation_key="exit_code",
        metric="duplicacy_backup_last_exit_code",
        icon="mdi:check-circle",
    ),
    DuplicacySensorDescription(
        key="revision",
        translation_key="revision",
        metric="duplicacy_backup_last_revision",
        icon="mdi:counter",
    ),
    DuplicacySensorDescription(
        key="chunks_uploaded",
        translation_key="chunks_uploaded",
        metric="duplicacy_backup_chunks_uploaded",
        icon="mdi:upload",
    ),
    DuplicacySensorDescription(
        key="chunks_skipped",
        translation_key="chunks_skipped",
        metric="duplicacy_backup_chunks_skipped",
        icon="mdi:skip-next",
    ),
    DuplicacySensorDescription(
        key="chunks_new",
        translation_key="chunks_new",
        metric="duplicacy_backup_last_chunks_new",
        icon="mdi:package-variant",
    ),
    DuplicacySensorDescription(
        key="bytes_uploaded_total",
        translation_key="bytes_uploaded_total",
        metric="duplicacy_backup_bytes_uploaded_total",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DuplicacySensorDescription(
        key="prune_last_success",
        translation_key="prune_last_success",
        metric="duplicacy_prune_last_success_timestamp_seconds",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_timestamp_from_unix,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DuplicacyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[DuplicacySensor] = []
    for key, metrics in (coordinator.data or {}).items():
        for desc in SENSOR_DESCRIPTIONS:
            if desc.metric in metrics:
                entities.append(
                    DuplicacySensor(coordinator, key, entry.entry_id, desc)
                )

    async_add_entities(entities)


class DuplicacySensor(DuplicacyEntity, SensorEntity):
    """Sensor entity for a Duplicacy metric."""

    entity_description: DuplicacySensorDescription

    def __init__(
        self,
        coordinator: DuplicacyCoordinator,
        key: MetricKey,
        entry_id: str,
        description: DuplicacySensorDescription,
    ) -> None:
        super().__init__(coordinator, key, entry_id)
        self.entity_description = description
        snapshot_id, storage_target = key
        self._attr_unique_id = (
            f"{entry_id}_{snapshot_id}_{storage_target}_{description.key}"
        )

    @property
    def native_value(self) -> Any:
        metrics = self._metrics
        if metrics is None:
            return None
        raw = metrics.get(self.entity_description.metric)
        return self.entity_description.value_fn(raw)

    @property
    def icon(self) -> str | None:
        if self.entity_description.key == "exit_code":
            metrics = self._metrics
            if metrics and metrics.get(self.entity_description.metric, 0) != 0:
                return "mdi:alert-circle"
            return "mdi:check-circle"
        return self.entity_description.icon
