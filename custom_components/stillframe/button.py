"""Resume the saved daily power schedule after an override."""
from homeassistant.components.button import ButtonEntity

from .entity import StillframeEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ResumeButton(entry.runtime_data, "resume_schedule", "Resume power schedule")])


class ResumeButton(StillframeEntity, ButtonEntity):
    async def async_press(self):
        await self.coordinator.control(power="auto")
