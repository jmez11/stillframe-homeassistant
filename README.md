# Stillframe for Home Assistant

A HACS custom integration for local control of Stillframe photo frames. Each frame
is a Home Assistant device. The integration communicates with its LAN API rather
than reading another project's files or accessing Google Photos directly.

The initial implementation targets **Stillframe Pi OS**. Stillframe Daydream and
Stillframe Windows can implement the same [LAN API](docs/lan-api-v1.md) later;
they are not yet supported or modified by this project.

## Features

- Automatic mDNS discovery (`_stillframe._tcp.local.`), with manual URL setup as a fallback.
- Display switch for on-demand control from dashboards, actions and automation triggers.
- Daily on/off times, including overnight hours, in the frame's timezone.
- Album selection and daily periods containing one or several already synced albums.
- Cached/discovered photo counts, cache size, playback buffer, sync status and per-album progress.
- Stable device and entity IDs across address changes and reboots.

Power commands control display standby, leaving the Pi and photo synchronization
running. On/off commands persist as overrides. Select `auto` in **Power mode** or
press **Resume power schedule** to return to daily hours. Equal on/off times mean
the display is active all day.

Album selection affects playback only. Every selected Google source continues to
sync and retain its cache. Google album authorization/selection remains on the
frame's existing Google setup page. Home Assistant does not manage Google credentials.

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
different from the Home Assistant password.

Discovery requires mDNS between Home Assistant and the frame. Separate VLANs
need an mDNS reflector; manual setup works when discovery traffic is blocked.
Discovery never bypasses authentication. The discovered service is verified
against the authenticated device ID before updating a configured frame's address.

## Album schedules

Open **Configure** on the Stillframe integration, choose **Add album period**,
select start/end times and choose one or several albums. Overnight periods work.
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

Choosing **Album** manually disables **Album schedule** until you enable it again.
Outside configured periods the frame uses the last manual album selection;
initially this is all enabled sources. Album periods and power hours run on the
frame and continue through Home Assistant outages. The display's existing
Google/local enable settings still apply.

## Automation examples

Use your frame's actual entity IDs from its device page:

```yaml
alias: Wake the frame on motion
triggers:
  - trigger: state
    entity_id: binary_sensor.living_room_motion
    to: "on"
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.stillframe_display
```

Set album periods from **Developer tools → Actions**:

```yaml
action: stillframe.set_album_periods
target:
  entity_id: switch.stillframe_display
data:
  periods:
    - start: "08:00"
      end: "17:00"
      album_ids: ["local"]
```

Settings persist on the appliance. Unloading/removing the integration leaves the
saved frame schedule in effect. Entity state refreshes every 30 seconds; commands
refresh immediately from the frame's response. The display switch represents
requested power. The **Album cache** attributes include the renderer's reported
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
