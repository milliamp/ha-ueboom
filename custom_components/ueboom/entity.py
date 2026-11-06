"""Base entity for UE BOOM."""

from __future__ import annotations

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import MANUFACTURER
from .coordinator import UEBoomCoordinator


class UEBoomEntity(PassiveBluetoothCoordinatorEntity[UEBoomCoordinator]):
    """A UE BOOM entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: UEBoomCoordinator, description: EntityDescription) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        address = coordinator.boom.address
        state = coordinator.gatt_state
        self._attr_unique_id = f"{address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            name=coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model="BOOM",
            sw_version=state.firmware_version if state else None,
            serial_number=state.serial_number if state else None,
        )
