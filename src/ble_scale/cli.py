"""CLI tool for reading BLE scale weight from advertisements."""

import asyncio
from datetime import datetime
from typing import Optional

import click
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .decoder import MANUFACTURER_ID, decode_weight, is_renpho_scale
from .models import StabilityStatus

# Stability: require N consecutive similar readings
STABLE_THRESHOLD_KG = 0.05
STABLE_COUNT = 5


@click.group()
def main() -> None:
    """BLE Scale - read weight from Bluetooth advertisement-based scales."""


@main.command()
@click.option("--timeout", default=15, help="Scan timeout in seconds")
@click.option("--adapter", default="hci0", help="BLE adapter name")
def scan(timeout: int, adapter: str) -> None:
    """Scan for nearby Renpho BLE scales."""
    asyncio.run(_scan(timeout, adapter))


async def _scan(timeout: float, adapter: str) -> None:
    scales: dict[str, str] = {}

    def callback(device: BLEDevice, adv: AdvertisementData) -> None:
        mfr = dict(adv.manufacturer_data) if adv.manufacturer_data else {}
        if is_renpho_scale(mfr):
            name = adv.local_name or device.name or "Renpho Scale"
            if device.address not in scales:
                scales[device.address] = name
                reading = decode_weight(mfr[MANUFACTURER_ID])
                weight = f"{reading.weight:.2f} kg" if reading else "no weight"
                click.echo(f"  Found: {name} ({device.address}) - {weight}")

    click.echo(f"Scanning for scales ({timeout}s)... step on the scale!")
    scanner = BleakScanner(
        detection_callback=callback,
        bluez={"adapter": adapter},
        scanning_mode="active",
    )
    await scanner.start()
    await asyncio.sleep(timeout)
    await scanner.stop()

    if not scales:
        click.echo("No scales found. Make sure the scale is awake (tap it).")
    else:
        click.echo(f"\nFound {len(scales)} scale(s)")


@main.command()
@click.argument("address")
@click.option("--adapter", default="hci0", help="BLE adapter name")
def monitor(address: str, adapter: str) -> None:
    """Monitor weight readings from a scale.

    ADDRESS is the BLE MAC address (e.g., AA:BB:CC:DD:EE:FF).
    """
    asyncio.run(_monitor(address, adapter))


async def _monitor(address: str, adapter: str) -> None:
    target = address.upper()
    last_weight = 0.0
    stable_count = 0

    def callback(device: BLEDevice, adv: AdvertisementData) -> None:
        nonlocal last_weight, stable_count

        if device.address.upper() != target:
            return

        mfr = dict(adv.manufacturer_data) if adv.manufacturer_data else {}
        reading = decode_weight(mfr.get(MANUFACTURER_ID, b""))
        if reading is None:
            return

        # Stability detection
        if abs(reading.weight - last_weight) < STABLE_THRESHOLD_KG:
            stable_count += 1
        else:
            stable_count = 0
        last_weight = reading.weight

        stable = " *" if stable_count >= STABLE_COUNT else ""
        now = datetime.now().strftime("%H:%M:%S")
        click.echo(f"[{now}] {reading.weight:.2f} {reading.unit.value}{stable}")

    click.echo(f"Monitoring {address} - step on the scale!\n")

    scanner = BleakScanner(
        detection_callback=callback,
        bluez={"adapter": adapter},
        scanning_mode="active",
    )
    await scanner.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await scanner.stop()
