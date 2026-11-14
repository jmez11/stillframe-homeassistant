"""Daily on/off hours, interpreted in the frame's timezone."""
from datetime import time
from homeassistant.components.time import TimeEntity

from .entity import StillframeEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([StillframeTime(entry.runtime_data, "active_start", "On time"),
                        StillframeTime(entry.runtime_data, "active_end", "Off time")])


class StillframeTime(StillframeEntity, TimeEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.key = key

    @property
    def native_value(self):
        return time.fromisoformat(self.coordinator.data["controls"][self.key])

    async def async_set_value(self, value):
        await self.coordinator.control(**{self.key: value.strftime("%H:%M")})
