"""Shared base entity for the Vitamix integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import VitamixCoordinator


class VitamixEntity(CoordinatorEntity[VitamixCoordinator]):
    """Base class shared by all Vitamix entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: VitamixCoordinator) -> None:
        super().__init__(coordinator)
        self._address = coordinator.address

    @property
    def device_info(self) -> DeviceInfo:
        state = self.coordinator.data
        # Model can only be derived once we've read the firmware specs.
        model = None
        if state is not None:
            # We can't read a model name directly, but rated_power_w +
            # max_rpm uniquely identify the line (e.g. Ascent A3500 is
            # 1200 W / 12000 RPM). Surface them as an informational model
            # string so users can tell devices apart.
            model = f"{state.rated_power_w} W, max {state.max_rpm} RPM"
        return DeviceInfo(
            identifiers={(DOMAIN, self._address)},
            connections={(CONNECTION_BLUETOOTH, self._address)},
            manufacturer=MANUFACTURER,
            name=self.coordinator.entry.title,
            model=model,
        )
