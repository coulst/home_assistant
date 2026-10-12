"""Number entity for the EVSE's load-management current limit (holding register 0).

Valid writes are 0, or MIN_LIMIT_AMPS up to the charger's reported max circuit current.
Anything in between is REFUSED by the firmware with Modbus exception 3 rather than
clamped - that's deliberate, so a misconfigured controller is obvious instead of silently
charging at the wrong rate. The slider's range is set to [MIN_LIMIT_AMPS, max_circuit_a] to
match; use button.evse_clear_current_limit to write the 0 that takes Modbus out of the
charger's limit arbitration entirely (0 does not stop charging - that's the charging-
permitted switch).
"""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, HOLDING_LIMIT_AMPS, MAX_LIMIT_AMPS_FALLBACK, MIN_LIMIT_AMPS
from .coordinator import CoulstEvseCoordinator
from .entity import CoulstEvseEntity

CURRENT_LIMIT_DESCRIPTION = NumberEntityDescription(
    key="current_limit",
    translation_key="current_limit",
    device_class=NumberDeviceClass.CURRENT,
    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    native_min_value=MIN_LIMIT_AMPS,
    native_step=1,
    mode=NumberMode.SLIDER,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CoulstEvseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EvseCurrentLimitNumber(coordinator, entry.entry_id)])


class EvseCurrentLimitNumber(CoulstEvseEntity, NumberEntity):
    entity_description = CURRENT_LIMIT_DESCRIPTION

    def __init__(self, coordinator: CoulstEvseCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, CURRENT_LIMIT_DESCRIPTION.key)

    @property
    def native_max_value(self) -> float:
        max_circuit_a = self.coordinator.data.max_circuit_a
        return max_circuit_a if max_circuit_a > 0 else MAX_LIMIT_AMPS_FALLBACK

    @property
    def native_value(self) -> float | None:
        limit = self.coordinator.data.holding_limit_amps
        # 0 means "no Modbus limit asserted" - leave the slider at its floor rather than 0,
        # which isn't a selectable value in [MIN_LIMIT_AMPS, max].
        return limit if limit >= MIN_LIMIT_AMPS else MIN_LIMIT_AMPS

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.write_register(
            address=HOLDING_LIMIT_AMPS, value=int(value), slave=self.coordinator.unit_id
        )
        await self.coordinator.async_request_refresh()
