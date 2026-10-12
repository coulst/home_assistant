"""Config flow for the Coul Street EVSE integration.

A manual host/port/unit-id form, plus zeroconf discovery off the "_modbus._tcp" service
the firmware advertises (components/network/src/wifi_manager.cpp,
WifiManager::advertiseModbusService()) whenever Modbus TCP is enabled on the charger.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import DEFAULT_PORT, DEFAULT_UNIT_ID, DOMAIN, EXPECTED_MAP_VERSION

_LOGGER = logging.getLogger(__name__)

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

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        _LOGGER.debug(
            "Zeroconf discovered %s (%s:%s)", discovery_info.name, host, port
        )

        await self.async_set_unique_id(f"{host}:{port}:{DEFAULT_UNIT_ID}")
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        self._discovered_host = host
        self._discovered_port = port
        self.context["title_placeholders"] = {"host": host}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        assert self._discovered_host is not None

        if user_input is not None:
            _, errors = await self._async_try_connect(
                {
                    CONF_HOST: self._discovered_host,
                    CONF_PORT: self._discovered_port,
                    CONF_UNIT_ID: DEFAULT_UNIT_ID,
                }
            )
            if errors:
                return self.async_abort(reason="cannot_connect")

            return self.async_create_entry(
                title=f"Coul Street EVSE ({self._discovered_host})",
                data={
                    CONF_HOST: self._discovered_host,
                    CONF_PORT: self._discovered_port,
                    "unit_id": DEFAULT_UNIT_ID,
                },
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"host": self._discovered_host},
        )

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

        from .const import INPUT_MAP_VERSION, unit_kwarg

        client = AsyncModbusTcpClient(user_input[CONF_HOST], port=user_input[CONF_PORT])
        errors: dict[str, str] = {}
        _LOGGER.debug(
            "Testing connection to %s:%s (unit %s)",
            user_input[CONF_HOST],
            user_input[CONF_PORT],
            user_input[CONF_UNIT_ID],
        )
        try:
            if not await client.connect():
                _LOGGER.debug("TCP connect to %s failed", user_input[CONF_HOST])
                errors["base"] = "cannot_connect"
                return {}, errors

            result = await client.read_input_registers(
                address=INPUT_MAP_VERSION, count=1, **unit_kwarg(user_input[CONF_UNIT_ID])
            )
            _LOGGER.debug("Map version read result: %s", result)
            if result.isError():
                errors["base"] = "cannot_connect"
            elif result.registers[0] != EXPECTED_MAP_VERSION:
                errors["base"] = "unsupported_map_version"
        except Exception:  # noqa: BLE001 - surfaced to the user as cannot_connect
            _LOGGER.exception("Failed to connect to %s", user_input[CONF_HOST])
            errors["base"] = "cannot_connect"
        finally:
            client.close()

        return {}, errors
