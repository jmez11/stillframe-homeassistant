# Stillframe for Home Assistant

<img src="custom_components/stillframe/brand/icon.png" alt="Stillframe" width="96" height="96">

A HACS custom integration for local control of Stillframe photo frames. Each frame
is a Home Assistant device. The integration communicates with its LAN API rather
than reading another project's files or accessing Google Photos directly.

Supports **Stillframe Pi OS** and **Stillframe Daydream** through the shared
[LAN API](docs/lan-api-v1.md). Stillframe Windows still needs the LAN API integration.

## Features

- Automatic mDNS discovery (`_stillframe._tcp.local.`), with manual URL setup as a fallback.
- Playback selector for daily hours or persistent Keep playing / Keep stopped choices.
- Daily on/off times, including overnight hours, in the frame's timezone.
- Album selection and daily periods containing one or several already synced albums.
- Scheduled display modes with independent periods for Fullscreen, Side by side, Mosaic, Collage and Photo pile.
- Cached/discovered photo counts, cache size, playback buffer, sync status and per-album progress.
- Stable device and entity IDs across address changes and reboots.

**Playback control** offers **Follow daily hours**, **Keep playing**, and
**Keep stopped**. The two Keep choices ignore daily hours until you select
**Follow daily hours** again. This controls photos and Pi display standby;
Android controls TV panel sleep. Equal start/stop times allow playback all day.
The old display switch has been removed. Update automations targeting that switch
to use the Playback control selector (`auto`, `on`, or `off`).

Album selection affects playback only. Every selected Google source continues to
sync and retain its cache. Google album authorization/selection remains on the
frame's existing Google setup page. Home Assistant does not manage Google credentials.

Playback control has three choices: Follow daily hours, Keep playing, and
Keep stopped. Keep playing/stopped takes priority until Follow daily hours is
selected. Use daily hours only applies the saved start/stop times; turning it
off removes the time restriction and does not stop photos. Saved times remain.
The separate Daily hours status shows whether the hours are in use, off, or
paused by an override. Photos showing reports actual playback separately.

Daily hours are one shared setting: edit the same saved times and enabled state
in the app or Home Assistant. Turning daily hours off keeps the saved times.
Keep playing/stopped is an explicit override until Follow daily hours is selected.
Album and display mode schedules are configured only in Home Assistant, saved
on the frame, and continue while HA is offline. Status shows what is controlling
each setting; Resume actions restore paused schedules. Google Photos controls
which sources are available. Photos showing is reported separately from the
requested playback state; it does not confirm TV panel power.

## Install

Requires Home Assistant 2026.9 or newer and a frame running the LAN API v1 changes
in `stillframe-pi-os`. The Pi image also installs the Avahi service advertisement;
an existing appliance must install `os/avahi/stillframe.service` into
`/etc/avahi/services/` to advertise discovery.

For local testing, copy `custom_components/stillframe` into Home Assistant's
`/config/custom_components/stillframe`, then restart Home Assistant.

In **HACS → Custom repositories**, add
`https://github.com/jmez11/stillframe-homeassistant` with category **Integration**.
Download **Stillframe** and restart Home Assistant.

[Open this repository in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=jmez11&repository=stillframe-homeassistant&category=integration)

Go to **Settings → Devices & services**. Configure the discovered Stillframe and
enter its device password, or choose **Add integration → Stillframe** and enter
its base URL, username (normally `admin`) and password. The frame password is
different from the Home Assistant password. Leave the password empty when
**Require password** is off on the frame. This also applies when reauthenticating.
Frames with password protection enabled still require the correct password.

Discovery requires mDNS between Home Assistant and the frame. Separate VLANs
need an mDNS reflector; manual setup works when discovery traffic is blocked.
Discovery never bypasses authentication. The discovered service is verified
against the authenticated device ID before updating a configured frame's address.

## Album schedules

Open **Configure** on the Stillframe integration, choose **Add album period**,
select start/end times and choose one or several albums. Overnight periods work.
This works on Android and Pi. Until periods are added, the schedule switch is
Off with a Not configured status; Unavailable means the frame cannot be reached.
An empty album selection means all enabled sources, including local uploads.
Periods cannot overlap. **Edit periods and timezone** exposes the complete JSON
list for editing/removing periods and the frame's IANA timezone.

Example periods:

```json
[
  {"start": "08:00", "end": "17:00", "album_ids": ["ALBUM_ID_FROM_FRAME"]},
  {"start": "17:00", "end": "22:00", "album_ids": ["local"]}
]
```

The **Album cache** sensor's `albums` attribute lists IDs, names, downloaded
counts, discovered totals, percentages and discovery state. Totals describe the
media discovered so far, not a guaranteed Google library total. A 100% cache
percentage does not establish that discovery is complete.

Albums are checked separately. With Highlights selected, Google also sends a mix of your selections. Photos not yet matched to an album may be Highlights or album photos. With Highlights alone, all returned photos are Highlights.

Choosing **Album** manually disables **Album schedule** until you enable it again.
Outside configured periods the frame uses the last manual album selection;
initially this is all enabled sources. Album periods and power hours run on the
frame and continue through Home Assistant outages. The display's existing
Google/local enable settings still apply.

## Display mode schedules

In **Configure**, choose **Add display mode period**, set start/end times, choose
a mode and save. Repeat for more periods. **Edit display mode periods** lets you
edit or remove the complete list. Mode schedules use the same frame timezone as
album schedules, support overnight periods and continue when HA is offline.
Periods cannot overlap within the mode schedule, but mode and album periods
can overlap freely.

Use **Display mode** on the device page for an immediate change. That disables
the **Display mode schedule** switch; enable it again to resume scheduled modes.
**Frame settings** uses the frame's existing layout and automatic mode rotation.
Outside mode periods, the frame uses the last manual mode selection, initially
**Frame settings**. Your native frame preferences are preserved.

Example mode periods:

```json
[
  {"start": "08:00", "end": "17:00", "display_mode": "mosaic"},
  {"start": "17:00", "end": "22:00", "display_mode": "fullscreen"}
]
```

Mode scheduling requires the updated Pi LAN API with the `mode_schedules`
capability. On older frames the existing album/power controls remain available;
update the frame and reload the integration to expose mode controls.

## Automation examples

Use your frame's actual entity IDs from its device page:

```yaml
alias: Wake the frame on motion
triggers:
  - trigger: state
    entity_id: binary_sensor.living_room_motion
    to: "on"
actions:
  - action: select.select_option
    target:
      entity_id: select.stillframe_power_mode
    data:
      option: "on"
```

Set album periods from **Developer tools → Actions**:

```yaml
action: stillframe.set_album_periods
target:
  entity_id: select.stillframe_power_mode
data:
  periods:
    - start: "08:00"
      end: "17:00"
      album_ids: ["local"]
```

The `stillframe.set_mode_periods` action uses the same target and a `periods`
list with `start`, `end`, and `display_mode`. Supported mode IDs are `auto`,
`fullscreen`, `side_by_side`, `mosaic`, `collage`, and `pile`.

Settings persist on the appliance. Unloading/removing the integration leaves the
saved frame schedule in effect. Entity state refreshes every 30 seconds; commands
refresh immediately from the frame's response. Playback control represents the requested policy, while Photos showing reports actual playback. The **Album cache** attributes include the renderer's reported
power and timestamp for hardware troubleshooting.

Cache statistics refresh in a background snapshot on the frame so catalog scans
do not block controls. They may initially be unknown while the first scan runs.
The `cache_updated_at` attribute records when the last complete scan finished.

## Development

```sh
python -m pip install -e '.[test]'
python -m ruff check .
python -m pytest -q
```

No device credentials are stored in this repository. Home Assistant stores frame
credentials in its config entry. The LAN API uses the frame's existing HTTP Basic
authentication; use a trusted LAN or HTTPS reverse proxy.
