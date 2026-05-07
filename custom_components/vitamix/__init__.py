"""Vitamix BLE integration for Home Assistant."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .coordinator import VitamixCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

SERVICE_CANCEL = "cancel"
SERVICE_LOAD_PROGRAM = "load_program"
SERVICE_SET_MOTOR_SPEED = "set_motor_speed"

ATTR_SLOT = "slot"
ATTR_SPEED = "speed"
ATTR_DURATION = "duration"

# Saved-program slots are 1-indexed. Allow up to 16 to accommodate models
# with extended program tables; the firmware will reject out-of-range
# values via VitamixWriteRejectedError.
SCHEMA_LOAD_PROGRAM = vol.Schema(
    {
        vol.Required(ATTR_SLOT): vol.All(int, vol.Range(min=1, max=16)),
    },
    extra=vol.ALLOW_EXTRA,
)

# Speeds 0..10 (Vitamix variable-speed dial); duration in u16 seconds.
SCHEMA_SET_MOTOR_SPEED = vol.Schema(
    {
        vol.Required(ATTR_SPEED): vol.All(int, vol.Range(min=0, max=10)),
        vol.Optional(ATTR_DURATION, default=0xFFFF): vol.All(
            int, vol.Range(min=1, max=0xFFFF)
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

ALL_SERVICES = (
    SERVICE_CANCEL,
    SERVICE_LOAD_PROGRAM,
    SERVICE_SET_MOTOR_SPEED,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vitamix from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    coordinator = VitamixCoordinator(hass, entry, address)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data.get(DOMAIN):
        # Last entry gone — drop services so a future reinstall registers fresh.
        for svc in ALL_SERVICES:
            if hass.services.has_service(DOMAIN, svc):
                hass.services.async_remove(DOMAIN, svc)
    return unloaded


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the integration's services exactly once."""
    if hass.services.has_service(DOMAIN, SERVICE_CANCEL):
        return

    async def _resolve_coordinators(call: ServiceCall) -> list[VitamixCoordinator]:
        """Find the coordinators targeted by ``call`` (via target devices)."""
        device_ids: list[str] = call.data.get("device_id", []) or []
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        coordinators: list[VitamixCoordinator] = []
        device_reg = dr.async_get(hass)
        domain_data: dict[str, VitamixCoordinator] = hass.data.get(DOMAIN, {})

        if not device_ids:
            # No target — apply to every configured Vitamix.
            return list(domain_data.values())

        for device_id in device_ids:
            device = device_reg.async_get(device_id)
            if device is None:
                continue
            for entry_id in device.config_entries:
                coordinator = domain_data.get(entry_id)
                if coordinator is not None and coordinator not in coordinators:
                    coordinators.append(coordinator)

        if not coordinators:
            raise HomeAssistantError(
                f"no Vitamix device matched targets {device_ids}"
            )
        return coordinators

    async def _async_cancel(call: ServiceCall) -> None:
        for coordinator in await _resolve_coordinators(call):
            await coordinator.async_cancel_program()

    async def _async_load_program(call: ServiceCall) -> None:
        slot: int = call.data[ATTR_SLOT]
        for coordinator in await _resolve_coordinators(call):
            await coordinator.async_load_program(slot)

    async def _async_set_motor_speed(call: ServiceCall) -> None:
        speed: int = call.data[ATTR_SPEED]
        duration: int = call.data[ATTR_DURATION]
        for coordinator in await _resolve_coordinators(call):
            await coordinator.async_set_motor_speed(
                speed, duration_seconds=duration
            )

    # We use device targets, not entity targets, so the schemas only
    # validate our own field; HA injects target keys (device_id /
    # entity_id / area_id) into call.data which we tolerate via
    # extra=vol.ALLOW_EXTRA.
    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL,
        _async_cancel,
        schema=vol.Schema({}, extra=vol.ALLOW_EXTRA),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOAD_PROGRAM,
        _async_load_program,
        schema=SCHEMA_LOAD_PROGRAM,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MOTOR_SPEED,
        _async_set_motor_speed,
        schema=SCHEMA_SET_MOTOR_SPEED,
    )
