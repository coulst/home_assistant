"""Switch entity for the EVSE's charge-permit holding register."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, HOLDING_CHARGE_PERMIT
from .coordinator import CoulstEvseCoordinator
from .entity import CoulstEvseEntity

CHARGING_PERMITTED_DESCRIPTION = SwitchEntityDescription(
    key="charging_permitted",
    translation_key="charging_permitted",
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CoulstEvseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EvseChargingPermittedSwitch(coordinator, entry.entry_id)])


class EvseChargingPermittedSwitch(CoulstEvseEntity, SwitchEntity):
    """Register 1: 0 suspends charging, 1 allows it. This is how you stop a charge."""

    entity_description = CHARGING_PERMITTED_DESCRIPTION

    def __init__(self, coordinator: CoulstEvseCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, CHARGING_PERMITTED_DESCRIPTION.key)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.charge_permit

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_write(1)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_write(0)

    async def _async_write(self, value: int) -> None:
        await self.coordinator.async_write_register(HOLDING_CHARGE_PERMIT, value)
        await self.coordinator.async_request_refresh()
