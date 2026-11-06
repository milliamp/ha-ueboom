"""Audio-connection sensor for UE BOOM speakers."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UEBoomConfigEntry
from .entity import UEBoomEntity

PARALLEL_UPDATES = 0

AUDIO_CONNECTED = BinarySensorEntityDescription(
    key="audio_connected",
    translation_key="audio_connected",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UEBoomConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the audio-connected sensor."""
    async_add_entities([UEBoomAudioConnected(entry.runtime_data, AUDIO_CONNECTED)])


class UEBoomAudioConnected(UEBoomEntity, BinarySensorEntity):
    """On while the speaker has an audio (A2DP) connection to some host."""

    @property
    def is_on(self) -> bool | None:
        """Return True if audio is connected."""
        return self.coordinator.boom.audio_connected
