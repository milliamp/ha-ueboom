"""Battery sensor for UE BOOM speakers."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UEBoomConfigEntry
from .entity import UEBoomEntity

PARALLEL_UPDATES = 0

BATTERY = SensorEntityDescription(
    key="battery",
    device_class=SensorDeviceClass.BATTERY,
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UEBoomConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the battery sensor."""
    async_add_entities([UEBoomBatterySensor(entry.runtime_data, BATTERY)])


class UEBoomBatterySensor(UEBoomEntity, SensorEntity):
    """Battery level from the speaker's advertisements."""

    @property
    def native_value(self) -> int | None:
        """Return the battery percentage."""
        return self.coordinator.boom.battery_level
