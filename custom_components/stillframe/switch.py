"""On-demand power and album schedule control."""
from homeassistant.components.switch import SwitchEntity

from .entity import StillframeEntity


async def async_setup_entry(hass, entry, async_add_entities):
    entities = [StillframeSwitch(entry.runtime_data, "power", "Display"),
                StillframeSwitch(entry.runtime_data, "album_schedule_enabled", "Album schedule")]
    if "mode_schedule_enabled" in entry.runtime_data.data["controls"]:
        entities.append(StillframeSwitch(entry.runtime_data, "mode_schedule_enabled", "Display mode schedule"))
    async_add_entities(entities)


class StillframeSwitch(StillframeEntity, SwitchEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.key = key

    @property
    def is_on(self):
        if self.key == "power":
            return self.coordinator.data["display"]["requested_on"]
        return self.coordinator.data["controls"][self.key]

    async def async_turn_on(self, **kwargs):
        await self.coordinator.control(**{self.key: "on" if self.key == "power" else True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.control(**{self.key: "off" if self.key == "power" else False})
