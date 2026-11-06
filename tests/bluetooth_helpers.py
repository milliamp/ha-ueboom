"""Bluetooth test helpers (mirrors of core's tests/components/bluetooth helpers).

pytest-homeassistant-custom-component ships the bluetooth fixtures but not these.
"""

from __future__ import annotations

from typing import Any

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from habluetooth import get_manager

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant


def generate_ble_device(address: str, name: str | None, details: Any = None) -> BLEDevice:
    """Return a BLEDevice."""
    return BLEDevice(address, name, details if details is not None else {})


def generate_advertisement_data(**kwargs: Any) -> AdvertisementData:
    """Return AdvertisementData with defaults for anything not given."""
    defaults: dict[str, Any] = {
        "local_name": None,
        "manufacturer_data": {},
        "service_data": {},
        "service_uuids": [],
        "tx_power": -127,
        "rssi": -127,
        "platform_data": (),
    }
    return AdvertisementData(**(defaults | kwargs))


def inject_bluetooth_service_info(hass: HomeAssistant, info: BluetoothServiceInfoBleak) -> None:
    """Feed a service info to the bluetooth manager as if a scanner saw it."""
    get_manager().scanner_adv_received(info)
