"""Shared base entity for the Coul Street EVSE integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoulstEvseCoordinator


class CoulstEvseEntity(CoordinatorEntity[CoulstEvseCoordinator]):
    """Base entity tying every platform entity to one charger Device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CoulstEvseCoordinator, entry_id: str, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=coordinator.name,
            manufacturer="Coul Street",
            model="Coul Street EVSE",
        )
