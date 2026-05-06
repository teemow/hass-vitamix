"""Coordinator that polls the Vitamix over BLE.

We re-resolve the :class:`BLEDevice` from Home Assistant's Bluetooth
integration on every poll so any registered scanner (USB adapter,
ESPHome Bluetooth Proxy, Shelly BLE Gateway, …) can be the one that
delivers the device to us. Vitamix blenders advertise sparingly while
idle, so we keep the connection short and rely on whichever proxy is
closest to wake the radio.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from bleak.exc import BleakError
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from vitamix_ble import VitamixClient, VitamixState
from vitamix_ble.client import VitamixError

from .const import DOMAIN, SCAN_INTERVAL_IDLE_S, SCAN_INTERVAL_RUNNING_S

_LOGGER = logging.getLogger(__name__)


class VitamixCoordinator(DataUpdateCoordinator[VitamixState]):
    """Poll a single Vitamix blender."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        address: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {address}",
            update_interval=timedelta(seconds=SCAN_INTERVAL_IDLE_S),
        )
        self.entry = entry
        self.address = address.upper()

    async def _async_update_data(self) -> VitamixState:
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise UpdateFailed(
                f"no Bluetooth scanner has seen {self.address} recently"
            )
        client = VitamixClient(ble_device)
        try:
            async with client as vmx:
                state = await vmx.read_state()
        except (VitamixError, BleakError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"vitamix poll failed: {err}") from err

        # Speed up polling once the motor is running so live attributes
        # (motor on/off, recipe slot) update with low latency.
        new_interval = (
            SCAN_INTERVAL_RUNNING_S if state.motor_running else SCAN_INTERVAL_IDLE_S
        )
        new_td = timedelta(seconds=new_interval)
        if self.update_interval != new_td:
            self.update_interval = new_td

        return state
