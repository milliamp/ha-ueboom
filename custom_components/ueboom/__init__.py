"""The UE BOOM integration: power and battery for Ultimate Ears BOOM speakers."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pyueboom import UEBoom
from pyueboom.transport import bluez_adapter

from .const import DOMAIN
from .coordinator import UEBoomConfigEntry, UEBoomCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: UEBoomConfigEntry) -> bool:
    """Set up a UE BOOM speaker from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    service_info = bluetooth.async_last_service_info(hass, address.upper(), connectable=True)
    if service_info is None:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found",
            translation_placeholders={"address": address},
        )

    # When a local BlueZ adapter sees the speaker, connect from that adapter and
    # ask the speaker to connect its audio to it. Through a proxy, leave the MAC
    # as zeros so the speaker reconnects to whatever host it used last.
    local = bluez_adapter(service_info.device) is not None
    boom = UEBoom(
        service_info.device,
        host_mac=service_info.source if local else None,
        adapter_address=service_info.source if local else None,
    )
    boom.set_ble_device_and_advertisement_data(service_info.device, service_info.advertisement)

    coordinator = UEBoomCoordinator(hass, entry, boom)
    entry.runtime_data = coordinator
    await coordinator.async_refresh_device_info()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UEBoomConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
