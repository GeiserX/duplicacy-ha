"""Common fixtures and HA mocks for Duplicacy tests."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _make_ha_mocks():
    """Create minimal mocks for homeassistant modules so imports work."""
    mods = {}

    mods["homeassistant"] = MagicMock()
    mods["homeassistant.core"] = MagicMock()

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

    mods["homeassistant.config_entries"] = MagicMock()

    for mod_name in [
        "homeassistant.helpers",
        "homeassistant.helpers.aiohttp_client",
        "homeassistant.helpers.device_registry",
        "homeassistant.helpers.entity_platform",
        "homeassistant.helpers.update_coordinator",
    ]:
        mods[mod_name] = MagicMock()

    sensor_mod = MagicMock()
    sensor_mod.SensorDeviceClass = MagicMock()
    sensor_mod.SensorDeviceClass.TIMESTAMP = "timestamp"
    sensor_mod.SensorDeviceClass.DURATION = "duration"
    sensor_mod.SensorDeviceClass.DATA_RATE = "data_rate"
    sensor_mod.SensorDeviceClass.DATA_SIZE = "data_size"
    sensor_mod.SensorStateClass = MagicMock()
    sensor_mod.SensorStateClass.TOTAL_INCREASING = "total_increasing"
    mods["homeassistant.components"] = MagicMock()
    mods["homeassistant.components.sensor"] = sensor_mod
    mods["homeassistant.components.binary_sensor"] = MagicMock()
    mods["homeassistant.data_entry_flow"] = MagicMock()

    return mods


_ha_mocks = _make_ha_mocks()
for name, mod in _ha_mocks.items():
    sys.modules[name] = mod


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
duplicacy_prune_running{snapshot_id="documents",storage_target="b2",machine="server1"} 0
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
    }
}
