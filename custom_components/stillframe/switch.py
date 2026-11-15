"""Daily hours and advanced schedule controls."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .entity import StillframeEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers import entity_registry as er
from .policy import control_summary


async def async_setup_entry(hass, entry, async_add_entities):
    registry = er.async_get(hass)
    power_id = f"{entry.runtime_data.data['device']['id']}_power"
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id == power_id and entity.domain == "switch":
            registry.async_remove(entity.entity_id)
    entities = [StillframeSwitch(entry.runtime_data, "album_schedule_enabled", "Album schedule (HA)")]
    if "mode_schedule_enabled" in entry.runtime_data.data["controls"]:
        entities.append(StillframeSwitch(entry.runtime_data, "mode_schedule_enabled", "Display mode schedule (HA)"))
    if "daily_hours_enabled" in entry.runtime_data.data["controls"]:
        entities.append(StillframeSwitch(entry.runtime_data, "daily_hours_enabled", "Use daily hours"))
    async_add_entities(entities)


class StillframeSwitch(StillframeEntity, SwitchEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.key = key
        self._attr_entity_category = EntityCategory.CONFIG

    def schedule_configured(self):
        if self.key == "daily_hours_enabled":
            return True
        periods = "album_periods" if self.key.startswith("album") else "mode_periods"
        return bool(self.coordinator.data["controls"].get(periods))

    @property
    def is_on(self):
        return self.schedule_configured() and self.coordinator.data["controls"][self.key]

    async def async_turn_on(self, **kwargs):
        if not self.schedule_configured():
            kind = "album" if self.key.startswith("album") else "display mode"
            raise HomeAssistantError(f"Add a {kind} period first: Settings > Devices & services > Stillframe > Configure")
        await self.coordinator.control(**{self.key: True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.control(**{self.key: False})

    @property
    def extra_state_attributes(self):
        if self.key == "daily_hours_enabled":
            return {"current_status": control_summary(self.coordinator.data)["daily_hours"],
                    "effect": "On uses saved times. Off removes the time restriction; it does not stop photos.",
                    "priority": "Keep playing or Keep stopped takes priority until Follow daily hours is selected",
                    "saved_times": "Start and stop times are retained when switched off", "shared_with": "Frame app"}
        return {"status": "Configured" if self.schedule_configured() else "Not configured; add periods in Home Assistant",
                "setup": "Settings > Devices & services > Stillframe > Configure",
                "configured_in": "App or Home Assistant" if self.key == "daily_hours_enabled" else "Home Assistant",
                "runs_on": "Frame; continues while Home Assistant is offline"}
