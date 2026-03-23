# BLE Scale

> **Disclaimer:** The author is not an expert in BLE or Home Assistant. This project is a proof of concept for reading weight from an older Renpho scale that is not supported by [openScale](https://github.com/oliexdev/openScale). The entire codebase was written with [Claude Code](https://claude.ai/claude-code). Use at your own risk.

Read weight from Bluetooth Low Energy scales that broadcast data via advertisements — no pairing or connection needed.

## How It Works

The **Renpho ES-24M-B** (and likely similar models) broadcasts its weight reading in BLE advertisement packets using manufacturer-specific data. Any device can passively listen and decode the weight without establishing a connection.

```
Manufacturer Data (Company ID 0xFFFF), 24 bytes:
  Bytes 0-1:   AA BB (magic header)
  Bytes 2-7:   Device MAC address
  Bytes 17-18: Weight (uint16 LE / 100.0 = kg)
```

Multiple listeners can read simultaneously, there's no connection to drop, and no pairing is required.

## CLI Tool

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Scan for scales

```bash
ble-scale scan
```

### Monitor weight

```bash
ble-scale monitor AA:BB:CC:DD:EE:FF
```

```
Monitoring AA:BB:CC:DD:EE:FF - step on the scale!

[10:15:07] 18.20 kg
[10:15:08] 19.65 kg
[10:15:09] 20.35 kg
[10:15:10] 20.50 kg
[10:15:11] 20.50 kg *
[10:15:12] 20.50 kg *
```

Readings marked with `*` are stable (weight has settled).

## Home Assistant Integration

Copy `custom_components/renpho_ble/` to your Home Assistant `config/custom_components/` directory and restart. The scale auto-discovers when you step on it, or add manually via **Settings > Devices & Services > Add Integration > Renpho BLE Scale**.

### Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.renpho_scale_weight` | Weight (kg) | Current weight reading |
| `sensor.renpho_scale_stable` | Boolean | `True` when reading has settled |

## Supported Scales

- **Renpho ES-24M-B** — confirmed working

If your scale is supported by the [old Renpho app](https://apps.apple.com/us/app/renpho-outdated-version/id1219889310), it may use the same broadcast protocol and work with this tool.

## Project Structure

```
bluetooth_scale/
├── src/ble_scale/
│   ├── cli.py          # CLI commands (scan, monitor)
│   ├── decoder.py      # Advertisement data decoder
│   └── models.py       # WeightReading dataclass
├── custom_components/
│   └── renpho_ble/     # Home Assistant integration
├── tests/
│   └── test_decoder.py
└── pyproject.toml
```

## Requirements

- Python 3.11+
- Linux with BlueZ (tested on Raspberry Pi 5)
- BLE adapter

## License

MIT
