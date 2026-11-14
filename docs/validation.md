# Pi and Home Assistant validation

Validated November 14, 2026 against Stillframe Pi OS 0.2.44 with the LAN API
development patch and Home Assistant Core 2026.9.1. Daydream and Windows have
not been changed or validated.

## Confirmed live

- Avahi advertised `_stillframe._tcp.local.` and Home Assistant created a
  discovery flow with source `zeroconf`.
- Authenticated setup created one loaded Stillframe device integration and 13 entities.
- `switch.turn_off` and `switch.turn_on` changed display power; the renderer
  reported the requested off/on states. Renderer confirmation took approximately
  4 seconds for off and 8 seconds for on in the final checks, after service acknowledgment.
- Both `time.set_value` controls persisted the requested daily hours.
- `select.select_option` selected a cached Google album, disabled album
  periods for manual playback and reached the renderer.
- `stillframe.set_album_periods` persisted and enabled a daily album period.
- The resume button restored automatic power scheduling.
- The integration's options wizard displayed its album selector and saved an
  album period. A duplicate manual setup was rejected by the stable device ID.
- The integration remained loaded with the same entities after a Home Assistant restart.
- The cache retained its downloaded photo count throughout these control checks.
- Original power policy, daily hours, album selection and periods were restored.

The final API serves controls from current settings and cache metrics from an
asynchronous snapshot. State reads measured approximately 12–39 ms during the
final command checks. Initial synchronous statistics had intermittently exceeded
client timeouts on the large catalog; controls no longer wait for those scans.
Intermittent LAN/save delays were also observed during setup. The client uses
fresh connections and a 45-second request deadline, and unchanged settings do
not cause additional SD-card writes. This is initial functional validation,
not a completed long-term reliability or performance soak test.

## Automated checks

- Pi suite: **159 passed, 7 skipped** on Windows with SDL's dummy video driver.
  Skips cover platform-dependent tests; they are not claims of hardware validation.
- Home Assistant client suite: **8 passed**, using a real local HTTP test server.
- Ruff passed in both projects, and `git diff --check` found no whitespace errors.
- Editable installation of this project and its test dependencies succeeded.

Coverage includes authentication, CSRF separation, partial settings updates,
overnight and timezone-aware periods, overlap rejection, strict playback album
isolation, shared-album cache counts, and nonblocking cache collection.

## Deployment and recovery

Initial Pi vetting installed the integration manually in Home Assistant's
`/config/custom_components/stillframe` (exposed as `/homeassistant` in its File
editor app). Public HACS distribution uses
`https://github.com/jmez11/stillframe-homeassistant` as a custom repository with
category **Integration**. HACS installs the same component directory and retains
the configured device and its entity IDs.

The Pi vetting deployment patches `/opt/stillframe/releases/0.2.44/stillframe`;
it is not a signed application release. The original modified app files are
backed up at `/var/backups/stillframe-ha-20261114T202129Z/stillframe`.
To roll back, restore the original `web.py`, `catalog.py` and `display.py` from
that backup and restart `stillframe-web` and `stillframe-display`. New helper
modules are unused by the original app. Remove the Stillframe Avahi service if
also reverting discovery. Photo databases, Google authorization and cached
files were not replaced.

Before normal signed app distribution, commit/release the companion Pi changes.
An older app update can otherwise
overwrite this development patch.
