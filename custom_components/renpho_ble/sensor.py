"""Sensor platform for Renpho BLE Scale."""

from __future__ import annotations

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RenphoBLEConfigEntry
from .parser import RenphoScaleData

WEIGHT_KEY = PassiveBluetoothEntityKey("weight", None)
STABLE_KEY = PassiveBluetoothEntityKey("stable", None)

WEIGHT_DESCRIPTION = SensorEntityDescription(
    key="weight",
    device_class=SensorDeviceClass.WEIGHT,
    native_unit_of_measurement=UnitOfMass.KILOGRAMS,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=2,
)

STABLE_DESCRIPTION = SensorEntityDescription(
    key="stable",
    name="Measurement Stable",
    icon="mdi:check-circle-outline",
)


def _sensor_update_to_bluetooth_data_update(
    parsed_data: RenphoScaleData | None,
) -> PassiveBluetoothDataUpdate:
    """Convert parsed scale data to HA PassiveBluetoothDataUpdate."""
    entity_data: dict[PassiveBluetoothEntityKey, float | str | None] = {}
    entity_descriptions: dict[
        PassiveBluetoothEntityKey, SensorEntityDescription
    ] = {}
    entity_names: dict[PassiveBluetoothEntityKey, str | None] = {}

    if parsed_data is not None and parsed_data.weight_kg is not None:
        entity_data[WEIGHT_KEY] = parsed_data.weight_kg
        entity_descriptions[WEIGHT_KEY] = WEIGHT_DESCRIPTION
        entity_names[WEIGHT_KEY] = "Weight"

        entity_data[STABLE_KEY] = parsed_data.stable
        entity_descriptions[STABLE_KEY] = STABLE_DESCRIPTION
        entity_names[STABLE_KEY] = "Stable"

    return PassiveBluetoothDataUpdate(
        devices={
            None: {
                "name": (parsed_data.device_name if parsed_data else None) or "Renpho Scale",
                "manufacturer": "Renpho",
                "model": "ES-24M-B",
            }
        },
        entity_descriptions=entity_descriptions,
        entity_data=entity_data,
        entity_names=entity_names,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RenphoBLEConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Renpho BLE scale sensors."""
    coordinator = entry.runtime_data
    processor = PassiveBluetoothDataProcessor(
        _sensor_update_to_bluetooth_data_update
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            RenphoBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )


class RenphoBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[
        PassiveBluetoothDataProcessor[float | str | None, RenphoScaleData]
    ],
    SensorEntity,
):
    """Renpho BLE scale sensor entity."""

    @property
    def native_value(self) -> float | str | None:
        """Return the sensor value."""
        return self.processor.entity_data.get(self.entity_key)
