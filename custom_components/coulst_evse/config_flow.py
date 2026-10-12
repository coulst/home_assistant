"""Config flow for the Coul Street EVSE integration.

Just a host/port/unit-id form for now - see examples/ha_integration/README.md for the
mDNS auto-discovery that's planned but not wired up yet.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_PORT, DEFAULT_UNIT_ID, DOMAIN, EXPECTED_MAP_VERSION

CONF_UNIT_ID = "unit_id"

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
    }
)


class CoulstEvseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a single Coul Street EVSE charger."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            info, errors = await self._async_try_connect(user_input)
            if not errors:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_UNIT_ID]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Coul Street EVSE ({user_input[CONF_HOST]})",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        "unit_id": user_input[CONF_UNIT_ID],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def _async_try_connect(
        self, user_input: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, str]]:
        from pymodbus.client import AsyncModbusTcpClient

        from .const import INPUT_MAP_VERSION

        client = AsyncModbusTcpClient(user_input[CONF_HOST], port=user_input[CONF_PORT])
        errors: dict[str, str] = {}
        try:
            if not await client.connect():
                errors["base"] = "cannot_connect"
                return {}, errors

            result = await client.read_input_registers(
                address=INPUT_MAP_VERSION, count=1, slave=user_input[CONF_UNIT_ID]
            )
            if result.isError():
                errors["base"] = "cannot_connect"
            elif result.registers[0] != EXPECTED_MAP_VERSION:
                errors["base"] = "unsupported_map_version"
        except Exception:  # noqa: BLE001 - surfaced to the user as cannot_connect
            errors["base"] = "cannot_connect"
        finally:
            client.close()

        return {}, errors
