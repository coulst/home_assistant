"""Button to clear the Modbus current limit (write 0 to holding register 0).

Writing 0 takes Modbus out of the charger's limit arbitration entirely - it does not stop
charging; that's switch.evse_charging_permitted.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, HOLDING_LIMIT_AMPS
from .coordinator import CoulstEvseCoordinator
from .entity import CoulstEvseEntity

CLEAR_LIMIT_DESCRIPTION = ButtonEntityDescription(
    key="clear_current_limit",
    translation_key="clear_current_limit",
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CoulstEvseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EvseClearCurrentLimitButton(coordinator, entry.entry_id)])


class EvseClearCurrentLimitButton(CoulstEvseEntity, ButtonEntity):
    entity_description = CLEAR_LIMIT_DESCRIPTION

    def __init__(self, coordinator: CoulstEvseCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, CLEAR_LIMIT_DESCRIPTION.key)

    async def async_press(self) -> None:
        await self.coordinator.async_write_register(HOLDING_LIMIT_AMPS, 0)
        await self.coordinator.async_request_refresh()
