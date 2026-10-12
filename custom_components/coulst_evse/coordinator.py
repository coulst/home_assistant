"""DataUpdateCoordinator for the Coul Street EVSE Modbus TCP map."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    unit_kwarg,
    EXPECTED_MAP_VERSION,
    HOLDING_CHARGE_PERMIT,
    HOLDING_HEARTBEAT,
    HOLDING_LIMIT_AMPS,
    INPUT_ACTIVE_POWER_W,
    INPUT_APPLIED_LIMIT_A,
    INPUT_BLOCK_COUNT,
    INPUT_BOARD_TEMP_DC,
    INPUT_CABLE_LOCK_STATE,
    INPUT_CHARGING_STATE,
    INPUT_CONTROL_STATE,
    INPUT_CURRENT_CA,
    INPUT_LIFETIME_WH,
    INPUT_LIMITING_SOURCE,
    INPUT_MAP_VERSION,
    INPUT_MAX_CABLE_A,
    INPUT_MAX_CIRCUIT_A,
    INPUT_MAX_USER_SET_A,
    INPUT_OFFERED_CURRENT_A,
    INPUT_PILOT_STATE,
    INPUT_RELAY_TEMP_DC,
    INPUT_SESSION_SECS,
    INPUT_SESSION_WH,
    INPUT_SINCE_WRITE_SECS,
    INPUT_SOCKET_TEMP_DC,
    INPUT_STATUS_FLAGS,
    INPUT_VFLAGS,
    INPUT_VOLTAGE_DV,
)

_LOGGER = logging.getLogger(__name__)


def _u32(regs: list[int], offset: int) -> int:
    """Join two registers at `offset` into a u32. High word first ("ABCD")."""
    return (regs[offset] << 16) | regs[offset + 1]


def _i16(value: int) -> int:
    """Reinterpret a raw 16-bit register as signed."""
    return value - 0x10000 if value >= 0x8000 else value


@dataclass
class EvseData:
    """A single poll of the EVSE's input register block."""

    map_version: int
    charging_state: int
    pilot_state: int
    cable_lock_state: int
    status_flags: int
    offered_current_a: int
    voltage_v: float
    current_a: float
    active_power_w: int
    session_energy_wh: int
    lifetime_energy_wh: int
    session_duration_s: int
    relay_temp_c: float | None
    board_temp_c: float | None
    socket_temp_c: float | None
    max_circuit_a: int
    max_user_set_a: int
    max_cable_a: int
    limiting_source: int
    vflags: int
    applied_limit_a: int
    control_state: int
    since_write_s: int
    holding_limit_amps: int
    charge_permit: bool


def _temp_or_none(raw_dc: int) -> float | None:
    signed = _i16(raw_dc)
    if signed == -32768:
        return None
    return round(signed / 10, 1)


class CoulstEvseCoordinator(DataUpdateCoordinator[EvseData]):
    """Polls the charger's input register block and keeps the latest snapshot."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.unit_id: int = entry.data["unit_id"]
        self._warned_map_version = False

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single holding register, logging the request and any error response."""
        _LOGGER.debug(
            "Writing holding register %s = %s (unit %s)", address, value, self.unit_id
        )
        result = await self.client.write_register(
            address=address, value=value, **unit_kwarg(self.unit_id)
        )
        if result.isError():
            _LOGGER.debug("Write to holding register %s failed: %s", address, result)
        else:
            _LOGGER.debug("Write to holding register %s acknowledged", address)

    async def _async_update_data(self) -> EvseData:
        _LOGGER.debug(
            "Polling %s input registers from %s (unit %s)",
            INPUT_BLOCK_COUNT,
            self.name,
            self.unit_id,
        )
        result = await self.client.read_input_registers(
            address=INPUT_MAP_VERSION, count=INPUT_BLOCK_COUNT, **unit_kwarg(self.unit_id)
        )
        if result.isError():
            _LOGGER.debug("Input register read failed: %s", result)
            raise UpdateFailed(f"Error reading EVSE input registers: {result}")
        _LOGGER.debug("Input registers: %s", result.registers)

        holding_result = await self.client.read_holding_registers(
            address=HOLDING_LIMIT_AMPS, count=2, **unit_kwarg(self.unit_id)
        )
        if holding_result.isError():
            _LOGGER.debug("Holding register read failed: %s", holding_result)
            raise UpdateFailed(f"Error reading EVSE holding registers: {holding_result}")
        _LOGGER.debug("Holding registers: %s", holding_result.registers)

        # Every poll refreshes the charger's failsafe heartbeat, so a non-zero failsafe
        # timeout configured in its web UI never trips just because nothing else is
        # writing to it. Non-fatal if it fails - telemetry is still good.
        try:
            await self.async_write_register(HOLDING_HEARTBEAT, 1)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Failed to refresh EVSE Modbus heartbeat", exc_info=True)

        regs = result.registers

        if regs[INPUT_MAP_VERSION] != EXPECTED_MAP_VERSION and not self._warned_map_version:
            _LOGGER.warning(
                "EVSE reports Modbus map version %s, this integration was built for"
                " version %s - readings may be wrong",
                regs[INPUT_MAP_VERSION],
                EXPECTED_MAP_VERSION,
            )
            self._warned_map_version = True

        return EvseData(
            map_version=regs[INPUT_MAP_VERSION],
            charging_state=regs[INPUT_CHARGING_STATE],
            pilot_state=regs[INPUT_PILOT_STATE],
            cable_lock_state=regs[INPUT_CABLE_LOCK_STATE],
            status_flags=regs[INPUT_STATUS_FLAGS],
            offered_current_a=regs[INPUT_OFFERED_CURRENT_A],
            voltage_v=round(regs[INPUT_VOLTAGE_DV] / 10, 1),
            current_a=round(regs[INPUT_CURRENT_CA] / 100, 2),
            active_power_w=_u32(regs, INPUT_ACTIVE_POWER_W),
            session_energy_wh=_u32(regs, INPUT_SESSION_WH),
            lifetime_energy_wh=_u32(regs, INPUT_LIFETIME_WH),
            session_duration_s=_u32(regs, INPUT_SESSION_SECS),
            relay_temp_c=_temp_or_none(regs[INPUT_RELAY_TEMP_DC]),
            board_temp_c=_temp_or_none(regs[INPUT_BOARD_TEMP_DC]),
            socket_temp_c=_temp_or_none(regs[INPUT_SOCKET_TEMP_DC]),
            max_circuit_a=regs[INPUT_MAX_CIRCUIT_A],
            max_user_set_a=regs[INPUT_MAX_USER_SET_A],
            max_cable_a=_i16(regs[INPUT_MAX_CABLE_A]),
            limiting_source=regs[INPUT_LIMITING_SOURCE],
            vflags=_u32(regs, INPUT_VFLAGS),
            applied_limit_a=regs[INPUT_APPLIED_LIMIT_A],
            control_state=regs[INPUT_CONTROL_STATE],
            since_write_s=_u32(regs, INPUT_SINCE_WRITE_SECS),
            holding_limit_amps=holding_result.registers[HOLDING_LIMIT_AMPS],
            charge_permit=bool(holding_result.registers[HOLDING_CHARGE_PERMIT]),
        )
