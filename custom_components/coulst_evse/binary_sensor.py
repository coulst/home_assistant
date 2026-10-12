"""Binary sensor entities, unpacking the EVSE's status flags bitfield (input register 4)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    STATUS_ACTIVE,
    STATUS_BOOT_LOCKED,
    STATUS_CHARGING,
    STATUS_COMM_ERROR,
    STATUS_ERROR,
    STATUS_OCPP_CONNECTED,
    STATUS_POWER_OFFERED,
    STATUS_VEHICLE_CONNECTED,
)
from .coordinator import CoulstEvseCoordinator, EvseData
from .entity import CoulstEvseEntity


@dataclass(frozen=True, kw_only=True)
class EvseBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[EvseData], bool] = lambda data: False


BINARY_SENSOR_DESCRIPTIONS: tuple[EvseBinarySensorDescription, ...] = (
    EvseBinarySensorDescription(
        key="vehicle_connected",
        translation_key="vehicle_connected",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda d: bool(d.status_flags & STATUS_VEHICLE_CONNECTED),
    ),
    EvseBinarySensorDescription(
        key="power_offered",
        translation_key="power_offered",
        value_fn=lambda d: bool(d.status_flags & STATUS_POWER_OFFERED),
    ),
    EvseBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda d: bool(d.status_flags & STATUS_CHARGING),
    ),
    EvseBinarySensorDescription(
        key="active",
        translation_key="active",
        value_fn=lambda d: bool(d.status_flags & STATUS_ACTIVE),
    ),
    EvseBinarySensorDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: bool(d.status_flags & STATUS_ERROR),
    ),
    EvseBinarySensorDescription(
        key="comm_error",
        translation_key="comm_error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        # The ESP32 has lost its serial link to the STM32 - everything else in the map is
        # stale when this is on, so it's the one worth alerting on.
        value_fn=lambda d: bool(d.status_flags & STATUS_COMM_ERROR),
    ),
    EvseBinarySensorDescription(
        key="boot_locked",
        translation_key="boot_locked",
        value_fn=lambda d: bool(d.status_flags & STATUS_BOOT_LOCKED),
    ),
    EvseBinarySensorDescription(
        key="ocpp_connected",
        translation_key="ocpp_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: bool(d.status_flags & STATUS_OCPP_CONNECTED),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CoulstEvseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EvseBinarySensor(coordinator, entry.entry_id, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class EvseBinarySensor(CoulstEvseEntity, BinarySensorEntity):
    entity_description: EvseBinarySensorDescription

    def __init__(
        self,
        coordinator: CoulstEvseCoordinator,
        entry_id: str,
        description: EvseBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, entry_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)
