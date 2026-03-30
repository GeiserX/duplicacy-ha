"""Config flow for the Duplicacy Backup Monitor integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .api import DuplicacyApiClient, DuplicacyConnectionError
from .const import CONF_URL, DEFAULT_URL, DOMAIN


class DuplicacyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duplicacy Backup Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")

            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()

            try:
                async with aiohttp.ClientSession() as session:
                    client = DuplicacyApiClient(url, session)
                    await client.check_health()
            except DuplicacyConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Duplicacy ({url})",
                    data={CONF_URL: url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_URL, default=DEFAULT_URL): str}
            ),
            errors=errors,
        )
