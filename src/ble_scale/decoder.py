"""Decoder for Renpho ES-24M BLE advertisement data.

This scale broadcasts weight in BLE manufacturer data (company ID 0xFFFF).
No GATT connection is needed — just passively listen for advertisements.

Data format (24 bytes):
  Bytes 0-1:   AA BB (magic header)
  Bytes 2-7:   Device MAC address
  Bytes 17-18: Weight as uint16 LE / 100.0 = kg
"""

import struct
from datetime import datetime
from typing import Optional

from .models import WeightReading, WeightUnit, StabilityStatus

MANUFACTURER_ID = 0xFFFF
MAGIC = bytes([0xAA, 0xBB])
WEIGHT_OFFSET = 17
WEIGHT_DIVISOR = 100.0


def decode_weight(data: bytes | bytearray) -> Optional[WeightReading]:
    """Decode weight from Renpho advertisement manufacturer data.

    Args:
        data: Raw manufacturer data bytes (from company ID 0xFFFF).

    Returns:
        WeightReading if valid weight found, None otherwise.
    """
    if len(data) < WEIGHT_OFFSET + 2:
        return None

    if data[0:2] != MAGIC:
        return None

    weight_raw = struct.unpack_from("<H", data, WEIGHT_OFFSET)[0]

    if weight_raw == 0:
        return None

    weight_kg = weight_raw / WEIGHT_DIVISOR

    if weight_kg < 0.1 or weight_kg > 180.0:
        return None

    return WeightReading(
        weight=weight_kg,
        unit=WeightUnit.KG,
        timestamp=datetime.now(),
        raw_bytes=bytes(data),
    )


def is_renpho_scale(manufacturer_data: dict[int, bytes]) -> bool:
    """Check if BLE manufacturer data matches a Renpho advertisement scale."""
    if MANUFACTURER_ID not in manufacturer_data:
        return False
    data = manufacturer_data[MANUFACTURER_ID]
    return len(data) >= WEIGHT_OFFSET + 2 and data[0:2] == MAGIC
