"""Setup, entity and service tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from pyueboom import UEBoomConnectionError

from .bluetooth_helpers import inject_bluetooth_service_info
from .conftest import ADAPTER, ADDRESS, ADV_STANDBY, make_service_info

SWITCH = "switch.my_boom_power"
BATTERY = "sensor.my_boom_battery"


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    inject_bluetooth_service_info(hass, make_service_info())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_and_entities(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """Entities reflect the advertisement and the device gets GATT info."""
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(SWITCH).state == STATE_ON
    assert hass.states.get(BATTERY).state == "100"

    device = dr.async_get(hass).async_get_device(connections={(dr.CONNECTION_BLUETOOTH, ADDRESS)})
    assert device is not None
    assert device.sw_version == "1.1.0.24"
    assert device.serial_number == "0000AB000XY0"
    assert device.manufacturer == "Ultimate Ears"

    # A standby advertisement flips the switch.
    inject_bluetooth_service_info(hass, make_service_info(manufacturer_data=ADV_STANDBY))
    await hass.async_block_till_done()
    assert hass.states.get(SWITCH).state == STATE_OFF

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_local_adapter_used_as_host(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """The adapter that sees the speaker becomes the audio host."""
    await _setup(hass, config_entry)
    boom = config_entry.runtime_data.boom
    assert boom.host_mac == ADAPTER
    assert boom.adapter_address == ADAPTER


async def test_not_ready_when_not_seen(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Setup retries until the speaker is seen."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_gatt_info_failure_is_not_fatal(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """Device info is optional."""
    mock_gatt["update"].side_effect = UEBoomConnectionError("nope")
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(SWITCH).state == STATE_ON


async def test_turn_off_and_on(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """Commands go to the speaker; state is optimistic until confirmed."""
    await _setup(hass, config_entry)

    await hass.services.async_call("switch", "turn_off", {ATTR_ENTITY_ID: SWITCH}, blocking=True)
    mock_gatt["power_off"].assert_awaited_once()
    assert hass.states.get(SWITCH).state == STATE_OFF

    await hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: SWITCH}, blocking=True)
    mock_gatt["power_on"].assert_awaited_once()
    assert hass.states.get(SWITCH).state == STATE_ON


async def test_power_failure_raises(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """A failed command surfaces a translated error."""
    await _setup(hass, config_entry)
    mock_gatt["power_off"].side_effect = UEBoomConnectionError("out of range")
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: SWITCH}, blocking=True
        )
    assert err.value.translation_key == "power_failed"
    assert hass.states.get(SWITCH).state == STATE_ON


AUDIO = "binary_sensor.my_boom_audio_connected"
ADV_ON_NOT_CONNECTED = bytes.fromhex("011064002002000000000000c0288d00112228")


async def test_audio_connected_sensor(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """The connectivity sensor follows the advertisement's audio bit."""
    await _setup(hass, config_entry)
    assert hass.states.get(AUDIO).state == STATE_ON

    inject_bluetooth_service_info(hass, make_service_info(manufacturer_data=ADV_ON_NOT_CONNECTED))
    await hass.async_block_till_done()
    assert hass.states.get(AUDIO).state == STATE_OFF
    assert hass.states.get(SWITCH).state == STATE_ON


async def test_turn_on_reconnects_audio_when_already_on(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """On but not connected: ask BlueZ to reconnect instead of a power-on."""
    await _setup(hass, config_entry)
    inject_bluetooth_service_info(hass, make_service_info(manufacturer_data=ADV_ON_NOT_CONNECTED))
    await hass.async_block_till_done()

    with patch("pyueboom.bluez.connect_audio", AsyncMock()) as connect:
        await hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: SWITCH}, blocking=True)
    connect.assert_awaited_once_with(ADDRESS, "hci0")
    mock_gatt["power_on"].assert_not_awaited()


async def test_turn_on_from_standby_powers_on(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_gatt: dict[str, AsyncMock]
) -> None:
    """From standby it's a BLE power-on."""
    await _setup(hass, config_entry)
    inject_bluetooth_service_info(hass, make_service_info(manufacturer_data=ADV_STANDBY))
    await hass.async_block_till_done()

    with patch("pyueboom.bluez.connect_audio", AsyncMock()) as connect:
        await hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: SWITCH}, blocking=True)
    mock_gatt["power_on"].assert_awaited_once()
    connect.assert_not_awaited()
