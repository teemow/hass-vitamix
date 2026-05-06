# Vitamix integration for Home Assistant

Adds a [Vitamix](https://www.vitamix.com/) Self-Detect blender (Ascent / Venturist
series) to Home Assistant over Bluetooth Low Energy. Discovery is automatic if
the blender is in range of any HA-registered Bluetooth scanner — the laptop
running HA, a USB BT dongle, or any [Bluetooth Proxy](https://esphome.io/projects/?type=bluetooth-proxy)
or BLE-capable Shelly device.

Exposes the live state of the blender (motor running / armed, attached
Self-Detect container, recipe slot, rated power, max RPM) as Home Assistant
sensors. Read-only at this stage — physical "Start" press is still required
to actually spin the blade.

Powered by [vitamix-ble](https://github.com/teemow/vitamix-ble).
