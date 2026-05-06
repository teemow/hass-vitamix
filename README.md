# hass-vitamix

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Home Assistant custom component for [Vitamix](https://www.vitamix.com/) Self-Detect
blenders (Ascent A2300 / A2500 / A3300 / A3500 and Venturist 330 / 350) over
Bluetooth Low Energy.

> [!NOTE]
> This is an **unofficial** integration. It is not endorsed by, affiliated
> with, or supported by Vita-Mix Corporation.

Built on top of the [`vitamix-ble`](https://github.com/teemow/vitamix-ble)
library.

## Features

- **Auto-discovery** via Home Assistant's Bluetooth platform — works with
  the local BT adapter or any [Bluetooth Proxy](https://esphome.io/projects/?type=bluetooth-proxy)
  / BLE-capable Shelly device.
- **Sensors** showing the live state of the blender:
  - `binary_sensor.<device>_motor_running`
  - `binary_sensor.<device>_armed`
  - `binary_sensor.<device>_container_attached`
  - `sensor.<device>_container` — short id of the attached Self-Detect jar
  - `sensor.<device>_container_max_runtime` — safe runtime in seconds
  - `sensor.<device>_recipe_slot`
  - `sensor.<device>_rated_power` (W)
  - `sensor.<device>_max_rpm`, `sensor.<device>_rated_rpm` (diagnostic)
- Adaptive polling — slow while idle, fast while the motor is running.

## Limitations

- **Read-only at this stage.** The library can write the official
  cancel-program packet, but the integration does not yet expose
  program-load services because the program-write protocol is still
  being mapped.
- The blender's Bluetooth radio sleeps when idle, so the very first
  poll after a long idle period can take 30 s+ while a scanner wakes
  it up. Subsequent polls are fast.
- A physical Start press is still required to actually spin the blade.

## Install

### HACS (recommended)

1. In HACS, add this repository as a **Custom repository** of category
   "Integration":
   `https://github.com/teemow/hass-vitamix`
2. Install **Vitamix** from HACS and restart Home Assistant.
3. The blender should be auto-discovered. If not, *Settings → Devices →
   Add Integration → Vitamix*.

### Manual

Copy `custom_components/vitamix/` into your Home Assistant
`config/custom_components/` directory and restart.

## Hardware tested

- Vitamix Ascent A3500 (1200 W, 12000 RPM, C-panel / slave 0x67).

Other Self-Detect models speaking the same protocol should work out of
the box; please open an issue if yours doesn't.

## License

MIT — see [LICENSE](LICENSE).
