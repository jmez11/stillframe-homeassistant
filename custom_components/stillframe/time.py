"""Daily on/off hours, interpreted in the frame's timezone."""
from datetime import time
from homeassistant.components.time import TimeEntity

from .entity import StillframeEntity
from .policy import daily_hours_enabled
from homeassistant.helpers.entity import EntityCategory


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([StillframeTime(entry.runtime_data, "active_start", "Daily hours start"),
                        StillframeTime(entry.runtime_data, "active_end", "Daily hours end")])


class StillframeTime(StillframeEntity, TimeEntity):
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.key = key

    @property
    def native_value(self):
        return time.fromisoformat(self.coordinator.data["controls"][self.key])

    async def async_set_value(self, value):
        values = {self.key: value.strftime("%H:%M")}
        if "daily_hours_enabled" in self.coordinator.data["controls"]:
            values["daily_hours_enabled"] = daily_hours_enabled(self.coordinator.data)
        await self.coordinator.control(**values)

    @property
    def extra_state_attributes(self):
        p = self.coordinator.data["controls"]
        return {"managed_in": "Shared with the frame app", "timezone": p["timezone"],
                "in_effect": daily_hours_enabled(self.coordinator.data) and p["power"] == "auto",
                "note": "Saved times are kept while daily hours are disabled or overridden"}
