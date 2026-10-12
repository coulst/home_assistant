"""Sensor entities for the Coul Street EVSE integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CABLE_LOCK_STATE_NAMES,
    CHARGING_STATE_NAMES,
    CONTROL_STATE_NAMES,
    DOMAIN,
    LIMITING_SOURCE_NAMES,
    PILOT_STATE_NAMES,
)
from .coordinator import CoulstEvseCoordinator, EvseData
from .entity import CoulstEvseEntity


@dataclass(frozen=True, kw_only=True)
class EvseSensorDescription(SensorEntityDescription):
    """A sensor description plus how to pull its value out of EvseData."""

    value_fn: Callable[[EvseData], object] = lambda data: None


SENSOR_DESCRIPTIONS: tuple[EvseSensorDescription, ...] = (
    EvseSensorDescription(
        key="charging_state",
        translation_key="charging_state",
        value_fn=lambda d: CHARGING_STATE_NAMES.get(
            d.charging_state, f"Unrecognized ({d.charging_state})"
        ),
    ),
    EvseSensorDescription(
        key="pilot_state",
        translation_key="pilot_state",
        value_fn=lambda d: PILOT_STATE_NAMES.get(
            d.pilot_state, f"Unrecognized ({d.pilot_state})"
        ),
    ),
    EvseSensorDescription(
        key="cable_lock_state",
        translation_key="cable_lock_state",
        value_fn=lambda d: CABLE_LOCK_STATE_NAMES.get(
            d.cable_lock_state, f"Unrecognized ({d.cable_lock_state})"
        ),
    ),
    EvseSensorDescription(
        key="offered_current",
        translation_key="offered_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.offered_current_a,
    ),
    EvseSensorDescription(
        key="voltage",
        translation_key="voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.voltage_v,
    ),
    EvseSensorDescription(
        key="current",
        translation_key="current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.current_a,
    ),
    EvseSensorDescription(
        key="active_power",
        translation_key="active_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.active_power_w,
    ),
    EvseSensorDescription(
        key="session_energy",
        translation_key="session_energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        # total_increasing, not total: the session counter resets every session.
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.session_energy_wh,
    ),
    EvseSensorDescription(
        key="lifetime_energy",
        translation_key="lifetime_energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.lifetime_energy_wh,
    ),
    EvseSensorDescription(
        key="session_duration",
        translation_key="session_duration",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda d: d.session_duration_s,
    ),
    EvseSensorDescription(
        key="relay_temperature",
        translation_key="relay_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.relay_temp_c,
    ),
    EvseSensorDescription(
        key="board_temperature",
        translation_key="board_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.board_temp_c,
    ),
    EvseSensorDescription(
        key="socket_temperature",
        translation_key="socket_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.socket_temp_c,
    ),
    EvseSensorDescription(
        key="max_circuit_current",
        translation_key="max_circuit_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        value_fn=lambda d: d.max_circuit_a,
    ),
    EvseSensorDescription(
        key="max_user_set_current",
        translation_key="max_user_set_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        value_fn=lambda d: d.max_user_set_a,
    ),
    EvseSensorDescription(
        key="max_cable_current",
        translation_key="max_cable_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        value_fn=lambda d: d.max_cable_a,
    ),
    EvseSensorDescription(
        key="limiting_source",
        translation_key="limiting_source",
        value_fn=lambda d: LIMITING_SOURCE_NAMES.get(
            d.limiting_source, f"Unrecognized ({d.limiting_source})"
        ),
    ),
    EvseSensorDescription(
        key="applied_limit",
        translation_key="applied_limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        value_fn=lambda d: d.applied_limit_a,
    ),
    EvseSensorDescription(
        key="control_state",
        translation_key="control_state",
        value_fn=lambda d: CONTROL_STATE_NAMES.get(
            d.control_state, f"Unrecognized ({d.control_state})"
        ),
    ),
    EvseSensorDescription(
        key="since_modbus_write",
        translation_key="since_modbus_write",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda d: d.since_write_s,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CoulstEvseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EvseSensor(coordinator, entry.entry_id, description)
        for description in SENSOR_DESCRIPTIONS
    )


class EvseSensor(CoulstEvseEntity, SensorEntity):
    """A single telemetry value read from the EVSE's input register block."""

    entity_description: EvseSensorDescription

    def __init__(
        self,
        coordinator: CoulstEvseCoordinator,
        entry_id: str,
        description: EvseSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry_id, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)
