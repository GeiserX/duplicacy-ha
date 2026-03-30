"""DataUpdateCoordinator for the Duplicacy integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DuplicacyApiClient, DuplicacyApiError, MetricKey
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DuplicacyCoordinator(DataUpdateCoordinator[dict[MetricKey, dict[str, Any]]]):
    """Coordinator that polls the Duplicacy Prometheus exporter."""

    def __init__(self, hass: HomeAssistant, client: DuplicacyApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[MetricKey, dict[str, Any]]:
        try:
            return await self.client.get_metrics()
        except DuplicacyApiError as err:
            raise UpdateFailed(str(err)) from err
