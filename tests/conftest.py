"""Fixtures for UE BOOM tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Import before HA mounts its testing config dir, so `custom_components`
# resolves to this repo's package.
from custom_components.ueboom.const import DOMAIN
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS
from pyueboom import UEBoomState

from .bluetooth_helpers import generate_advertisement_data, generate_ble_device

ADDRESS = "C0:28:8D:00:11:22"
ADAPTER = "00:1A:7D:00:33:44"
ADV_ON = bytes.fromhex("011064004002000000000000c0288d00112228")
ADV_STANDBY = bytes.fromhex("011064000002001a7d003344c0288d00112228")


def make_service_info(
    manufacturer_data: bytes = ADV_ON, name: str = "My BOOM", address: str = ADDRESS
) -> BluetoothServiceInfoBleak:
    """Return a service info as a local BlueZ adapter would report it."""
    adv = generate_advertisement_data(
        local_name=name, manufacturer_data={3: manufacturer_data}, rssi=-60
    )
    device = generate_ble_device(
        address, name, details={"path": f"/org/bluez/hci0/dev_{address.replace(':', '_')}"}
    )
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=-60,
        manufacturer_data={3: manufacturer_data},
        service_data={},
        service_uuids=[],
        source=ADAPTER,
        device=device,
        advertisement=adv,
        connectable=True,
        time=0,
        tx_power=None,
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth: None) -> None:
    """Auto mock bluetooth."""


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A config entry for the test speaker."""
    return MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, title="My BOOM", data={CONF_ADDRESS: ADDRESS}
    )


@pytest.fixture
def mock_gatt() -> Generator[dict[str, AsyncMock]]:
    """Patch the GATT operations of pyueboom.UEBoom."""
    state = UEBoomState(
        power_state=0x40,
        battery_level=100,
        name="My BOOM",
        serial_number="0000AB000XY0",
        firmware=bytes.fromhex("01010018"),
    )
    with (
        patch("pyueboom.UEBoom.update", AsyncMock(return_value=state)) as update,
        patch("pyueboom.UEBoom.power_on", AsyncMock()) as power_on,
        patch("pyueboom.UEBoom.power_off", AsyncMock()) as power_off,
    ):
        yield {"update": update, "power_on": power_on, "power_off": power_off}
