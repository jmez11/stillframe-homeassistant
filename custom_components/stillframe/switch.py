"""On-demand power and album schedule control."""
from homeassistant.components.switch import SwitchEntity

from .entity import StillframeEntity
from homeassistant.helpers.entity import EntityCategory


async def async_setup_entry(hass, entry, async_add_entities):
    entities = [StillframeSwitch(entry.runtime_data, "power", "Playback override"),
                StillframeSwitch(entry.runtime_data, "album_schedule_enabled", "Album schedule (HA)")]
    if "mode_schedule_enabled" in entry.runtime_data.data["controls"]:
        entities.append(StillframeSwitch(entry.runtime_data, "mode_schedule_enabled", "Display mode schedule (HA)"))
    if "daily_hours_enabled" in entry.runtime_data.data["controls"]:
        entities.append(StillframeSwitch(entry.runtime_data, "daily_hours_enabled", "Daily hours enabled"))
    async_add_entities(entities)


class StillframeSwitch(StillframeEntity, SwitchEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.key = key
        if key != "power":
            self._attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self):
        if self.key in ("album_schedule_enabled", "mode_schedule_enabled"):
            periods = "album_periods" if self.key.startswith("album") else "mode_periods"
            return super().available and bool(self.coordinator.data["controls"].get(periods))
        return super().available

    @property
    def is_on(self):
        if self.key == "power":
            return self.coordinator.data["display"]["requested_on"]
        return self.coordinator.data["controls"][self.key]

    async def async_turn_on(self, **kwargs):
        await self.coordinator.control(**{self.key: "on" if self.key == "power" else True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.control(**{self.key: "off" if self.key == "power" else False})

    @property
    def extra_state_attributes(self):
        if self.key == "power":
            return {"effect": "Manual playback override until Resume daily hours is pressed",
                    "meaning": "Starts or stops photos; Android controls TV panel sleep" if "Daydream" in self.coordinator.data["device"]["model"] else "Controls photo playback and display standby"}
        return {"status": "Configured" if self.key == "daily_hours_enabled" or self.coordinator.data["controls"].get("album_periods" if self.key.startswith("album") else "mode_periods") else "Not configured; add periods in Home Assistant",
                "configured_in": "App or Home Assistant" if self.key == "daily_hours_enabled" else "Home Assistant",
                "runs_on": "Frame; continues while Home Assistant is offline"}
