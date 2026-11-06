"""Power switch for UE BOOM speakers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UEBoomConfigEntry
from .entity import UEBoomEntity

PARALLEL_UPDATES = 1

POWER = SwitchEntityDescription(key="power", translation_key="power")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UEBoomConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the power switch."""
    async_add_entities([UEBoomPowerSwitch(entry.runtime_data, POWER)])


class UEBoomPowerSwitch(UEBoomEntity, SwitchEntity):
    """Turn the speaker on, or put it in standby."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the speaker is on."""
        return self.coordinator.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Wake the speaker."""
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Put the speaker in standby."""
        await self.coordinator.async_set_power(False)
