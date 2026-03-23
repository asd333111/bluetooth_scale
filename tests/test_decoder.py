"""Tests for Renpho advertisement decoder."""

import struct
import pytest

from ble_scale.decoder import decode_weight, is_renpho_scale, MANUFACTURER_ID
from ble_scale.models import WeightUnit


def _make_packet(weight_raw: int = 1935) -> bytes:
    """Build a Renpho advertisement packet with given raw weight."""
    data = bytearray(24)
    data[0:2] = b"\xaa\xbb"
    struct.pack_into("<H", data, 17, weight_raw)
    return bytes(data)


class TestDecodeWeight:
    def test_basic(self):
        reading = decode_weight(_make_packet(1935))
        assert reading is not None
        assert abs(reading.weight - 19.35) < 0.01
        assert reading.unit == WeightUnit.KG

    def test_heavy(self):
        reading = decode_weight(_make_packet(15000))  # 150.00 kg
        assert reading is not None
        assert abs(reading.weight - 150.00) < 0.01

    def test_light(self):
        reading = decode_weight(_make_packet(50))  # 0.50 kg
        assert reading is not None
        assert abs(reading.weight - 0.50) < 0.01

    def test_zero_returns_none(self):
        assert decode_weight(_make_packet(0)) is None

    def test_too_heavy_returns_none(self):
        assert decode_weight(_make_packet(18100)) is None  # 181 kg, over 180 kg limit

    def test_bad_magic_returns_none(self):
        data = bytearray(_make_packet(1935))
        data[0] = 0x00
        assert decode_weight(data) is None

    def test_too_short_returns_none(self):
        assert decode_weight(b"\xaa\xbb\x00") is None

    def test_raw_bytes_preserved(self):
        packet = _make_packet(1935)
        reading = decode_weight(packet)
        assert reading.raw_bytes == packet


class TestIsRenphoScale:
    def test_valid(self):
        assert is_renpho_scale({MANUFACTURER_ID: _make_packet()}) is True

    def test_wrong_id(self):
        assert is_renpho_scale({0x004C: _make_packet()}) is False

    def test_wrong_magic(self):
        bad = bytearray(_make_packet())
        bad[0] = 0x00
        assert is_renpho_scale({MANUFACTURER_ID: bytes(bad)}) is False

    def test_empty(self):
        assert is_renpho_scale({}) is False
