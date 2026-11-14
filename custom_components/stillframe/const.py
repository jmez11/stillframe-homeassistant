"""Shared integration constants."""
from homeassistant.const import Platform

DOMAIN = "stillframe"
DISPLAY_MODES = {"auto": "Frame settings", "fullscreen": "Fullscreen", "side_by_side": "Side by side",
                 "mosaic": "Mosaic", "collage": "Collage", "pile": "Photo pile"}
PLATFORMS = [Platform.SWITCH, Platform.SELECT, Platform.TIME, Platform.SENSOR, Platform.BUTTON]
