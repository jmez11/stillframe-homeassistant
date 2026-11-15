"""Power policy and immediate playback-album selection."""
from homeassistant.components.select import SelectEntity

from .entity import StillframeEntity
from .const import DISPLAY_MODES
from .policy import control_summary


async def async_setup_entry(hass, entry, async_add_entities):
    entities = [PowerSelect(entry.runtime_data, "power_mode", "Playback control"),
                AlbumSelect(entry.runtime_data, "album", "Album override")]
    if "display_mode" in entry.runtime_data.data["controls"]:
        entities.append(DisplayModeSelect(entry.runtime_data, "display_mode", "Display mode override"))
    async_add_entities(entities)


class DisplayModeSelect(StillframeEntity, SelectEntity):
    _attr_options = list(DISPLAY_MODES.values())

    @property
    def current_option(self):
        return DISPLAY_MODES.get(self.coordinator.data["display"].get("display_mode", "auto"))

    @property
    def extra_state_attributes(self):
        return {"currently_controlled_by": control_summary(self.coordinator.data)["display_mode"],
                "effect": "Choosing a mode pauses the HA display mode schedule; Resume restores it"}

    async def async_select_option(self, option):
        mode = next(key for key, label in DISPLAY_MODES.items() if label == option)
        await self.coordinator.control(display_mode=mode, mode_schedule_enabled=False)


class PowerSelect(StillframeEntity, SelectEntity):
    _attr_translation_key = "playback_control"
    _attr_options = ["auto", "on", "off"]

    @property
    def current_option(self):
        return self.coordinator.data["controls"]["power"]

    async def async_select_option(self, option):
        await self.coordinator.control(power=option)


class AlbumSelect(StillframeEntity, SelectEntity):
    @property
    def extra_state_attributes(self):
        return {"currently_controlled_by": control_summary(self.coordinator.data)["albums"],
                "effect": "Choosing albums pauses the HA album schedule; Google Photos source selection is unchanged"}

    def album_options(self):
        # IDs disambiguate duplicate names and keep automation choices explicit.
        return {f"{a['name']} [{a['id']}]": a["id"] for a in self.coordinator.data["albums"]}

    @property
    def options(self):
        return ["All synced albums", "Multiple albums"] + list(self.album_options())

    @property
    def current_option(self):
        ids = self.coordinator.data["display"]["active_album_ids"]
        if not ids:
            return "All synced albums"
        if len(ids) == 1:
            return next((name for name, key in self.album_options().items() if key == ids[0]), "Multiple albums")
        return "Multiple albums"

    async def async_select_option(self, option):
        if option == "Multiple albums":
            from homeassistant.exceptions import HomeAssistantError
            raise HomeAssistantError("Use set_album_periods for a selection containing multiple albums")
        ids = [] if option == "All synced albums" else [self.album_options()[option]]
        await self.coordinator.control(album_ids=ids, album_schedule_enabled=False)
