"""Push coordinator for UE BOOM speakers, fed by Bluetooth advertisements."""

from __future__ import annotations

import logging
import time

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothDataUpdateCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from pyueboom import UEBoom, UEBoomError, UEBoomState

from .const import DOMAIN, PENDING_POWER_TIMEOUT

_LOGGER = logging.getLogger(__name__)

type UEBoomConfigEntry = ConfigEntry[UEBoomCoordinator]


class UEBoomCoordinator(PassiveBluetoothDataUpdateCoordinator):
    """Track a speaker's power state and battery from its advertisements."""

    def __init__(self, hass: HomeAssistant, entry: UEBoomConfigEntry, boom: UEBoom) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            boom.address,
            bluetooth.BluetoothScanningMode.PASSIVE,
            connectable=True,
        )
        self.entry = entry
        self.boom = boom
        self.gatt_state: UEBoomState | None = None
        self._pending_on: bool | None = None
        self._pending_since = 0.0

    @property
    def is_on(self) -> bool | None:
        """Return the power state, preferring a just-sent command until confirmed."""
        if self._pending_on is not None:
            if time.monotonic() - self._pending_since < PENDING_POWER_TIMEOUT:
                return self._pending_on
            self._pending_on = None
        return self.boom.is_on

    @callback
    def _async_handle_bluetooth_event(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Decode the advertisement, then notify entities."""
        self.boom.set_ble_device_and_advertisement_data(
            service_info.device, service_info.advertisement
        )
        if self._pending_on is not None and self.boom.is_on == self._pending_on:
            self._pending_on = None
        super()._async_handle_bluetooth_event(service_info, change)

    async def async_refresh_device_info(self) -> None:
        """Best-effort GATT read of name, firmware and serial number."""
        try:
            self.gatt_state = await self.boom.update()
        except UEBoomError as err:
            _LOGGER.debug("%s: could not read device info: %s", self.boom.address, err)

    async def async_set_power(self, on: bool) -> None:
        """Send a power command to the speaker."""
        try:
            if on:
                await self.boom.power_on()
            else:
                await self.boom.power_off()
        except UEBoomError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="power_failed",
                translation_placeholders={"name": self.entry.title, "error": str(err)},
            ) from err
        self._pending_on = on
        self._pending_since = time.monotonic()
        self.async_update_listeners()
