"""Common fixtures and HA mocks for Duplicacy tests."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Lightweight HA stubs – enough for real imports to succeed
# ---------------------------------------------------------------------------

def _make_ha_mocks():
    """Create minimal mocks for homeassistant modules so imports work."""
    mods: dict[str, Any] = {}

    mods["homeassistant"] = MagicMock()
    mods["homeassistant.core"] = MagicMock()

    # --- homeassistant.const ---
    const = ModuleType("homeassistant.const")
    const.Platform = MagicMock()
    const.Platform.SENSOR = "sensor"
    const.Platform.BINARY_SENSOR = "binary_sensor"
    const.EntityCategory = MagicMock()
    const.UnitOfInformation = MagicMock()
    const.UnitOfInformation.BYTES = "B"
    const.UnitOfTime = MagicMock()
    const.UnitOfTime.SECONDS = "s"
    mods["homeassistant.const"] = const

    # --- config_entries ---
    config_entries_mod = ModuleType("homeassistant.config_entries")

    class _ConfigFlowResult(dict):
        pass

    class _ConfigFlow:
        """Minimal stand-in for ConfigFlow."""
        VERSION = 1

        def __init_subclass__(cls, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)

        async def async_set_unique_id(self, uid):
            pass

        def _abort_if_unique_id_configured(self):
            pass

        def async_show_form(self, *, step_id, data_schema, errors=None):
            return _ConfigFlowResult(
                type="form", step_id=step_id, errors=errors or {}
            )

        def async_create_entry(self, *, title, data):
            return _ConfigFlowResult(type="create_entry", title=title, data=data)

    config_entries_mod.ConfigFlow = _ConfigFlow
    config_entries_mod.ConfigEntry = MagicMock()
    config_entries_mod.ConfigFlowResult = _ConfigFlowResult
    mods["homeassistant.config_entries"] = config_entries_mod

    # --- helpers ---
    for mod_name in [
        "homeassistant.helpers",
        "homeassistant.helpers.aiohttp_client",
        "homeassistant.helpers.entity_platform",
    ]:
        mods[mod_name] = MagicMock()

    # --- helpers.device_registry ---
    device_reg = MagicMock()
    device_reg.DeviceInfo = dict  # Use real dict so DeviceInfo(...) works
    mods["homeassistant.helpers.device_registry"] = device_reg

    # --- helpers.update_coordinator ---
    uc_mod = ModuleType("homeassistant.helpers.update_coordinator")

    class _FakeCoordinatorEntity:
        """Minimal stand-in for CoordinatorEntity."""
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, coordinator):
            self.coordinator = coordinator

    class _FakeDataUpdateCoordinator:
        """Minimal stand-in for DataUpdateCoordinator."""
        data: dict | None = None

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)

        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, logger, *, name, update_interval):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval

        async def async_config_entry_first_refresh(self):
            self.data = await self._async_update_data()

        async def _async_update_data(self):
            raise NotImplementedError

    class _UpdateFailed(Exception):
        pass

    uc_mod.CoordinatorEntity = _FakeCoordinatorEntity
    uc_mod.DataUpdateCoordinator = _FakeDataUpdateCoordinator
    uc_mod.UpdateFailed = _UpdateFailed
    mods["homeassistant.helpers.update_coordinator"] = uc_mod

    # --- sensor component ---
    sensor_mod = ModuleType("homeassistant.components.sensor")
    sensor_mod.SensorDeviceClass = MagicMock()
    sensor_mod.SensorDeviceClass.TIMESTAMP = "timestamp"
    sensor_mod.SensorDeviceClass.DURATION = "duration"
    sensor_mod.SensorDeviceClass.DATA_RATE = "data_rate"
    sensor_mod.SensorDeviceClass.DATA_SIZE = "data_size"
    sensor_mod.SensorStateClass = MagicMock()
    sensor_mod.SensorStateClass.TOTAL_INCREASING = "total_increasing"

    from dataclasses import dataclass, field

    @dataclass(frozen=True, kw_only=True)
    class _SensorEntityDescription:
        key: str = ""
        translation_key: str | None = None
        device_class: str | None = None
        native_unit_of_measurement: str | None = None
        suggested_display_precision: int | None = None
        state_class: str | None = None
        icon: str | None = None

    class _SensorEntity:
        entity_description = None
        _attr_unique_id: str | None = None
        _attr_has_entity_name: bool = False
        _attr_device_info: dict | None = None

        @property
        def native_value(self):
            return None

    sensor_mod.SensorEntityDescription = _SensorEntityDescription
    sensor_mod.SensorEntity = _SensorEntity
    mods["homeassistant.components"] = MagicMock()
    mods["homeassistant.components.sensor"] = sensor_mod

    # --- binary_sensor component ---
    bs_mod = ModuleType("homeassistant.components.binary_sensor")
    bs_mod.BinarySensorDeviceClass = MagicMock()
    bs_mod.BinarySensorDeviceClass.RUNNING = "running"

    @dataclass(frozen=True, kw_only=True)
    class _BinarySensorEntityDescription:
        key: str = ""
        translation_key: str | None = None
        device_class: str | None = None
        icon: str | None = None

    class _BinarySensorEntity:
        entity_description = None
        _attr_unique_id: str | None = None
        _attr_has_entity_name: bool = False
        _attr_device_info: dict | None = None

        @property
        def is_on(self):
            return None

    bs_mod.BinarySensorEntityDescription = _BinarySensorEntityDescription
    bs_mod.BinarySensorEntity = _BinarySensorEntity
    mods["homeassistant.components.binary_sensor"] = bs_mod

    # --- data_entry_flow ---
    mods["homeassistant.data_entry_flow"] = MagicMock()

    return mods


_ha_mocks = _make_ha_mocks()
for name, mod in _ha_mocks.items():
    sys.modules[name] = mod


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

MOCK_METRICS_TEXT = """\
# HELP duplicacy_backup_last_success_timestamp_seconds Timestamp of the last successful backup
# TYPE duplicacy_backup_last_success_timestamp_seconds gauge
duplicacy_backup_last_success_timestamp_seconds{snapshot_id="documents",storage_target="b2",machine="server1"} 1704067200
# HELP duplicacy_backup_last_duration_seconds Duration of the last backup
# TYPE duplicacy_backup_last_duration_seconds gauge
duplicacy_backup_last_duration_seconds{snapshot_id="documents",storage_target="b2",machine="server1"} 120.5
# HELP duplicacy_backup_running Whether a backup is currently running
# TYPE duplicacy_backup_running gauge
duplicacy_backup_running{snapshot_id="documents",storage_target="b2",machine="server1"} 0
# HELP duplicacy_backup_progress_ratio Progress ratio
# TYPE duplicacy_backup_progress_ratio gauge
duplicacy_backup_progress_ratio{snapshot_id="documents",storage_target="b2",machine="server1"} 1.0
# HELP duplicacy_backup_last_exit_code Exit code of the last backup
# TYPE duplicacy_backup_last_exit_code gauge
duplicacy_backup_last_exit_code{snapshot_id="documents",storage_target="b2",machine="server1"} 0
# HELP duplicacy_prune_running Whether a prune is running
# TYPE duplicacy_prune_running gauge
duplicacy_prune_running{storage_target="b2",machine="server1"} 0
# HELP duplicacy_backup_speed_bytes_per_second Backup speed
# TYPE duplicacy_backup_speed_bytes_per_second gauge
duplicacy_backup_speed_bytes_per_second{snapshot_id="documents",storage_target="b2",machine="server1"} 5242880
# HELP duplicacy_backup_last_bytes_uploaded Bytes uploaded last backup
# TYPE duplicacy_backup_last_bytes_uploaded gauge
duplicacy_backup_last_bytes_uploaded{snapshot_id="documents",storage_target="b2",machine="server1"} 104857600
# HELP duplicacy_backup_last_bytes_new New bytes last backup
# TYPE duplicacy_backup_last_bytes_new gauge
duplicacy_backup_last_bytes_new{snapshot_id="documents",storage_target="b2",machine="server1"} 52428800
# HELP duplicacy_backup_last_files_total Total files last backup
# TYPE duplicacy_backup_last_files_total gauge
duplicacy_backup_last_files_total{snapshot_id="documents",storage_target="b2",machine="server1"} 1500
# HELP duplicacy_backup_last_files_new New files last backup
# TYPE duplicacy_backup_last_files_new gauge
duplicacy_backup_last_files_new{snapshot_id="documents",storage_target="b2",machine="server1"} 25
# HELP duplicacy_backup_last_revision Last revision number
# TYPE duplicacy_backup_last_revision gauge
duplicacy_backup_last_revision{snapshot_id="documents",storage_target="b2",machine="server1"} 42
# HELP duplicacy_backup_chunks_uploaded Chunks uploaded
# TYPE duplicacy_backup_chunks_uploaded gauge
duplicacy_backup_chunks_uploaded{snapshot_id="documents",storage_target="b2",machine="server1"} 100
# HELP duplicacy_backup_chunks_skipped Chunks skipped
# TYPE duplicacy_backup_chunks_skipped gauge
duplicacy_backup_chunks_skipped{snapshot_id="documents",storage_target="b2",machine="server1"} 50
# HELP duplicacy_backup_last_chunks_new New chunks last backup
# TYPE duplicacy_backup_last_chunks_new gauge
duplicacy_backup_last_chunks_new{snapshot_id="documents",storage_target="b2",machine="server1"} 10
# HELP duplicacy_backup_bytes_uploaded_total Total bytes uploaded
# TYPE duplicacy_backup_bytes_uploaded_total counter
duplicacy_backup_bytes_uploaded_total{snapshot_id="documents",storage_target="b2",machine="server1"} 1073741824
# HELP duplicacy_prune_last_success_timestamp_seconds Last prune success
# TYPE duplicacy_prune_last_success_timestamp_seconds gauge
duplicacy_prune_last_success_timestamp_seconds{storage_target="b2",machine="server1"} 1704060000
"""

MOCK_METRICS_PARSED = {
    ("documents", "b2"): {
        "machine": "server1",
        "duplicacy_backup_last_success_timestamp_seconds": 1704067200.0,
        "duplicacy_backup_last_duration_seconds": 120.5,
        "duplicacy_backup_running": 0.0,
        "duplicacy_backup_progress_ratio": 1.0,
        "duplicacy_backup_last_exit_code": 0.0,
        "duplicacy_prune_running": 0.0,
        "duplicacy_backup_speed_bytes_per_second": 5242880.0,
        "duplicacy_backup_last_bytes_uploaded": 104857600.0,
        "duplicacy_backup_last_bytes_new": 52428800.0,
        "duplicacy_backup_last_files_total": 1500.0,
        "duplicacy_backup_last_files_new": 25.0,
        "duplicacy_backup_last_revision": 42.0,
        "duplicacy_backup_chunks_uploaded": 100.0,
        "duplicacy_backup_chunks_skipped": 50.0,
        "duplicacy_backup_last_chunks_new": 10.0,
        "duplicacy_backup_bytes_uploaded_total": 1073741824.0,
        "duplicacy_prune_last_success_timestamp_seconds": 1704060000.0,
    }
}

# Full metrics with multiple snapshot/storage combos
MOCK_METRICS_MULTI = {
    ("documents", "b2"): {
        "machine": "server1",
        "duplicacy_backup_last_success_timestamp_seconds": 1704067200.0,
        "duplicacy_backup_last_duration_seconds": 120.5,
        "duplicacy_backup_running": 0.0,
        "duplicacy_backup_progress_ratio": 1.0,
        "duplicacy_backup_last_exit_code": 0.0,
        "duplicacy_prune_running": 0.0,
    },
    ("photos", "s3"): {
        "machine": "server2",
        "duplicacy_backup_last_success_timestamp_seconds": 1704070000.0,
        "duplicacy_backup_last_duration_seconds": 300.0,
        "duplicacy_backup_running": 1.0,
        "duplicacy_backup_progress_ratio": 0.75,
        "duplicacy_backup_last_exit_code": 1.0,
        "duplicacy_prune_running": 1.0,
    },
}
