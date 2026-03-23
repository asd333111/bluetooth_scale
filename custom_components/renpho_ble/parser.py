"""Parser for Renpho ES-24M BLE advertisement data.

The scale broadcasts weight in BLE manufacturer data (company ID 0xFFFF):
  Bytes 0-1:   AA BB (magic header)
  Bytes 2-7:   Device MAC address
  Bytes 17-18: Weight as uint16 LE / 100.0 = kg
"""

from __future__ import annotations

import struct
import logging
from dataclasses import dataclass, field
from datetime import datetime

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

_LOGGER = logging.getLogger(__name__)

MANUFACTURER_ID = 0xFFFF
MAGIC = bytes([0xAA, 0xBB])
WEIGHT_OFFSET = 17
WEIGHT_DIVISOR = 100.0
STABLE_THRESHOLD_KG = 0.05
STABLE_COUNT = 5


@dataclass
class RenphoScaleData:
    """Parses Renpho scale advertisement data."""

    device_name: str = "Renpho Scale"
    weight_kg: float | None = None
    stable: bool = False

    _last_weight: float = field(default=0.0, repr=False)
    _stable_count: int = field(default=0, repr=False)

    def update(
        self, service_info: BluetoothServiceInfoBleak
    ) -> RenphoScaleData | None:
        """Process a BLE advertisement. Returns self if valid, None otherwise."""
        if MANUFACTURER_ID not in service_info.manufacturer_data:
            return None

        data = service_info.manufacturer_data[MANUFACTURER_ID]

        if len(data) < WEIGHT_OFFSET + 2 or data[0:2] != MAGIC:
            return None

        weight_raw = struct.unpack_from("<H", data, WEIGHT_OFFSET)[0]
        if weight_raw == 0:
            return None

        weight_kg = weight_raw / WEIGHT_DIVISOR
        if weight_kg < 0.1 or weight_kg > 180.0:
            return None

        if abs(weight_kg - self._last_weight) < STABLE_THRESHOLD_KG:
            self._stable_count += 1
        else:
            self._stable_count = 0

        self._last_weight = weight_kg
        self.stable = self._stable_count >= STABLE_COUNT
        self.weight_kg = weight_kg
        self.device_name = service_info.name or "Renpho Scale"

        _LOGGER.debug("Renpho scale %s: %.2f kg (stable=%s)",
                       service_info.address, weight_kg, self.stable)
        return self
