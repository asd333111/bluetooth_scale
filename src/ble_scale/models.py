"""Data models for BLE scale readings."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WeightUnit(Enum):
    KG = "kg"
    LBS = "lbs"


class StabilityStatus(Enum):
    STABLE = "stable"
    UNSTABLE = "unstable"


@dataclass
class WeightReading:
    weight: float
    unit: WeightUnit
    stable: StabilityStatus = StabilityStatus.UNSTABLE
    timestamp: datetime = field(default_factory=datetime.now)
    raw_bytes: bytes = b""
    device_address: str = ""
