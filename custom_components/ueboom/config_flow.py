"""Config flow for UE BOOM."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from pyueboom import UEBoomAdvertisement

from .const import DOMAIN

DEFAULT_NAME = "UE BOOM"


def _is_ueboom(info: BluetoothServiceInfoBleak) -> bool:
    return UEBoomAdvertisement.from_manufacturer_data(info.manufacturer_data) is not None


def _title(info: BluetoothServiceInfoBleak) -> str:
    name = info.name
    return name if name and name.replace("-", ":").upper() != info.address.upper() else DEFAULT_NAME


class UEBoomConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UE BOOM."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._discovered: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a speaker found by Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if not _is_ueboom(discovery_info):
            return self.async_abort(reason="not_supported")
        self._discovery = discovery_info
        self.context["title_placeholders"] = {"name": _title(discovery_info)}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm adding a discovered speaker."""
        assert self._discovery is not None
        title = _title(self._discovery)
        if user_input is not None:
            return self.async_create_entry(
                title=title, data={CONF_ADDRESS: self._discovery.address}
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders={"name": title}
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Pick a speaker from those currently advertising."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=_title(self._discovered[address]), data={CONF_ADDRESS: address}
            )

        configured = self._async_current_ids(include_ignore=False)
        for info in async_discovered_service_info(self.hass, connectable=True):
            if info.address not in configured and _is_ueboom(info):
                self._discovered[info.address] = info
        if not self._discovered:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            addr: f"{_title(info)} ({addr})"
                            for addr, info in self._discovered.items()
                        }
                    )
                }
            ),
        )
