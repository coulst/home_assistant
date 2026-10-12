"""The Coul Street EVSE integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import CoulstEvseCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from pymodbus.client import AsyncModbusTcpClient

    _LOGGER.debug(
        "Setting up %s at %s:%s (unit %s)",
        entry.title,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data["unit_id"],
    )
    client = AsyncModbusTcpClient(entry.data[CONF_HOST], port=entry.data[CONF_PORT])
    if not await client.connect():
        from homeassistant.exceptions import ConfigEntryNotReady

        raise ConfigEntryNotReady(
            f"Could not connect to EVSE Modbus TCP server at"
            f" {entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
        )

    _LOGGER.debug("Modbus TCP connection established")
    coordinator = CoulstEvseCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        _LOGGER.debug("Unloading %s", entry.title)
        coordinator: CoulstEvseCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.client.close()
    return unload_ok
