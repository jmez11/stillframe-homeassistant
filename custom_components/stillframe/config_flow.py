"""Manual setup, automatic mDNS discovery, reauthentication and album periods."""
import json

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .api import StillframeAuthError, StillframeClient, StillframeError
from .const import DOMAIN, DISPLAY_MODES


class StillframeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    discovered = None

    @staticmethod
    def async_get_options_flow(config_entry):
        return StillframeOptionsFlow()

    async def async_step_zeroconf(self, discovery_info):
        await self.async_set_unique_id(discovery_info.name)
        host = discovery_info.host
        if ":" in host:
            host = f"[{host}]"
        url = f"http://{host}:{discovery_info.port}"
        self.discovered = {CONF_URL: url, "discovery_name": discovery_info.name}
        for entry in self._async_current_entries():
            if entry.data.get("discovery_name") == discovery_info.name or entry.data[CONF_URL] == url:
                # Verify the stable ID before following an address change.
                try:
                    state = await StillframeClient(async_get_clientsession(self.hass), url,
                                                   entry.data[CONF_USERNAME], entry.data.get(CONF_PASSWORD, "")).state()
                except StillframeError:
                    return self.async_abort(reason="already_configured")
                if state["device"]["id"] == entry.unique_id:
                    changed = entry.data[CONF_URL] != url
                    self.hass.config_entries.async_update_entry(entry, data=entry.data | self.discovered)
                    if changed:
                        await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="already_configured")
        self._async_abort_entries_match({CONF_URL: url})
        self.context["title_placeholders"] = {"name": discovery_info.name.split("._stillframe")[0]}
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        errors = {}
        defaults = self.discovered or {}
        if user_input is not None:
            try:
                client = StillframeClient(async_get_clientsession(self.hass), user_input[CONF_URL],
                                          user_input[CONF_USERNAME], user_input.get(CONF_PASSWORD, ""))
                state = await client.state()
            except StillframeAuthError:
                errors["base"] = "invalid_auth"
            except (StillframeError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(state["device"]["id"])
                self._abort_if_unique_id_configured(updates={CONF_URL: client.url})
                return self.async_create_entry(title=state["device"]["name"],
                    data=defaults | user_input | {CONF_URL: client.url,
                                                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, "")})
            defaults = defaults | user_input
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required(CONF_URL, default=defaults.get(CONF_URL, "http://stillframe.local:8080")): str,
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "admin")): str,
            vol.Optional(CONF_PASSWORD, default=""): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }), errors=errors)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                state = await StillframeClient(async_get_clientsession(self.hass), entry.data[CONF_URL],
                    entry.data[CONF_USERNAME], user_input.get(CONF_PASSWORD, "")).state()
                if state["device"]["id"] != entry.unique_id:
                    return self.async_abort(reason="wrong_device")
            except StillframeAuthError:
                errors["base"] = "invalid_auth"
            except StillframeError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input | {CONF_PASSWORD: user_input.get(CONF_PASSWORD, "")})
        return self.async_show_form(step_id="reauth_confirm", data_schema=vol.Schema({
            vol.Optional(CONF_PASSWORD, default=""): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }), errors=errors)


class StillframeOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        menu = ["add_period", "edit_periods"]
        if "mode_periods" in self.config_entry.runtime_data.data["controls"]:
            menu += ["add_mode_period", "edit_mode_periods"]
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_add_mode_period(self, user_input=None):
        coordinator = self.config_entry.runtime_data
        errors = {}
        if user_input is not None:
            from homeassistant.exceptions import HomeAssistantError
            period = {"start": user_input["start"][:5], "end": user_input["end"][:5],
                      "display_mode": user_input["display_mode"]}
            try:
                await coordinator.control(mode_periods=coordinator.data["controls"]["mode_periods"] + [period],
                                          mode_schedule_enabled=True)
            except HomeAssistantError:
                errors["base"] = "cannot_save"
            else:
                return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="add_mode_period", data_schema=vol.Schema({
            vol.Required("start", default="08:00:00"): selector.TimeSelector(),
            vol.Required("end", default="17:00:00"): selector.TimeSelector(),
            vol.Required("display_mode", default="fullscreen"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=[{"value": key, "label": label}
                    for key, label in DISPLAY_MODES.items()], mode=selector.SelectSelectorMode.DROPDOWN)),
        }), errors=errors)

    async def async_step_edit_mode_periods(self, user_input=None):
        coordinator = self.config_entry.runtime_data
        errors = {}
        if user_input is not None:
            try:
                periods = json.loads(user_input["periods"])
                if not isinstance(periods, list):
                    raise ValueError
                await coordinator.control(mode_periods=periods, mode_schedule_enabled=True)
            except (ValueError, TypeError):
                errors["base"] = "invalid_periods"
            except Exception as error:
                from homeassistant.exceptions import HomeAssistantError
                if not isinstance(error, HomeAssistantError):
                    raise
                errors["base"] = "cannot_save"
            else:
                return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="edit_mode_periods", data_schema=vol.Schema({
            vol.Required("periods", default=json.dumps(coordinator.data["controls"]["mode_periods"], indent=2)):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }), errors=errors)

    async def async_step_add_period(self, user_input=None):
        coordinator = self.config_entry.runtime_data
        errors = {}
        if user_input is not None:
            from homeassistant.exceptions import HomeAssistantError
            period = {"start": user_input["start"][:5], "end": user_input["end"][:5],
                      "album_ids": user_input["album_ids"]}
            try:
                await coordinator.control(album_periods=coordinator.data["controls"]["album_periods"] + [period],
                                          album_schedule_enabled=True)
            except HomeAssistantError:
                errors["base"] = "cannot_save"
            else:
                return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="add_period", data_schema=vol.Schema({
            vol.Required("start", default="08:00:00"): selector.TimeSelector(),
            vol.Required("end", default="17:00:00"): selector.TimeSelector(),
            vol.Required("album_ids", default=[]): selector.SelectSelector(selector.SelectSelectorConfig(
                options=[{"value": a["id"], "label": a["name"]} for a in coordinator.data["albums"]],
                multiple=True, mode=selector.SelectSelectorMode.DROPDOWN)),
        }), errors=errors)

    async def async_step_edit_periods(self, user_input=None):
        coordinator = self.config_entry.runtime_data
        errors = {}
        if user_input is not None:
            try:
                periods = json.loads(user_input["periods"])
                if not isinstance(periods, list):
                    raise ValueError
                await coordinator.control(album_periods=periods, album_schedule_enabled=True,
                                          timezone=user_input["timezone"])
            except (ValueError, TypeError):
                errors["base"] = "invalid_periods"
            except Exception as error:
                from homeassistant.exceptions import HomeAssistantError
                if not isinstance(error, HomeAssistantError):
                    raise
                errors["base"] = "cannot_save"
            else:
                return self.async_create_entry(title="", data={})
        controls = coordinator.data["controls"]
        return self.async_show_form(step_id="edit_periods", data_schema=vol.Schema({
            vol.Required("timezone", default=controls["timezone"] or self.hass.config.time_zone): str,
            vol.Required("periods", default=json.dumps(controls["album_periods"], indent=2)):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }), description_placeholders={"albums": "; ".join(
            f"{a['name']}: {a['id']}" for a in coordinator.data["albums"])}, errors=errors)
