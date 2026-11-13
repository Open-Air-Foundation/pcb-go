# AirGradient GO — Hardware

> KiCad hardware design files for the AirGradient GO, a portable battery-powered air quality monitor.

<!-- ![AirGradient GO](graphics/airgradient Final-02.png) -->

**This checkout is v3:** main board PCB revision 3.0, a prototype (branch `v3-reroute`, not tagged yet). The produced boards are v2, tag `v2`.

## Overview

AirGradient GO is a handheld air quality monitor. It measures:
- particulate matter (Sensirion SPS30);
- CO₂ (Senseair S12);
- VOC/NOx (Sensirion SGP41);
- temperature and humidity (Sensirion SHT40);
- barometric pressure (Goermicro SPL07-003).

It also has an accelerometer (LIS2DH12) for motion detection and a GNSS receiver (TAU1113, GPS L1 and BeiDou B1) for location.

Readings are shown on a 2.13″ black-and-white e-paper display, with four RGB LEDs and capacitive touch controls. The device runs on a replaceable 18500 Li-ion cell (2600 mAh), charged over USB-C.

v3 keeps the v2 outline, mounting holes, connectors, switches and sensor positions. It changes:
- which ESP32 pin does what;
- the interrupt lines, so touch, motion and the charger can wake the chip;
- the rail, raised from 3.11 V to 3.31 V;
- charging, so a 2 A charge is possible;
- protection: against a reversed cell, and ESD protection on USB;
- the LEDs, moved under the battery holder;
- the GNSS antenna, which gets its matching network.

It also adds an unfitted read-out circuit for a CO sensor.

This repository contains the complete electronics design: schematics, PCB layouts, shared component libraries, and production outputs.

## Versions

| Version | Where | Main board revision | State |
|---|---|---|---|
| v1 | tag `v1.0` | 1.0 | the first product: pouch cell, separate LED + touch board |
| v2 | tag `v2`, branch `main` | 2.1 | the produced boards |
| v3 | branch `v3-reroute` | 3.0 | **prototype** (this checkout) |

Documents in this checkout:

| File | Contents |
|---|---|
| `VERSIONS.md` | the three versions side by side, with pin maps and the reasons for each change |
| `CHANGES-v3.md` | every v2 → v3 change, with its reason and its source |
| `SPEC-SHEET.md` | the hardware, including the parts the KiCad BOM does not define: the display, the battery and the internal cables |

## Boards in this repository

| Board | Directory | Production set | Layers | Used by | Description |
|---|---|---|---|---|---|
| Main board | `PCB/airgradient-go-main/` | `Airgradient-GO_3.0` | 4 | v3 | MCU, power and charging, cell protection and fuel gauge, sensors, LEDs, storage |
| Touch pad | `PCB/touch-pad/` | `Touch_sensor_v2.1` | 2 | v2, v3 | Three capacitive pads with the CAP1203 controller; 5-pin cable to the main board |
| LED + touch controller | `PCB/led-touch/` | `AG-GO-LED_1.0` | 2 | v1 only | RGB LEDs, LED driver and touch controller of v1 |
| SCD4x module | `PCB/scd4x-module/` | `SCD4x_module_0.1` | 2 | optional | CO₂ daughterboard. The standard configuration uses the on-board Senseair S12 |

## Key components (main board 3.0)

| Function | Part | Ref |
|---|---|---|
| MCU / Wi-Fi 6 + Bluetooth LE | ESP32-C5-MINI-1 (N4) | U4 |
| Battery charger, up to 2 A | BQ25628 | U5 |
| Fuel gauge and cell protection | BQ27742-G1, with the CSD83325L FET pair | U3, Q3 |
| Reverse-cell protection | CSD83325L | Q6 |
| Input power switch | LM66200 ideal-diode switch | U19 |
| Buck-boost converter (3.3 V rail) | TPS63802 | U8 |
| LDO, GNSS backup supply | TPS7A0228 | U9 |
| Hardware watchdog | TPL5010 | U7 |
| NAND flash (512 Mb) | W25N512GVEIG | U1 |
| NAND flash, alternative footprint (not fitted) | ZDSD512MLGEAG | U2 |
| microSD socket (not fitted) | TF-CARD XG8P | TF1 |
| CO₂ sensor module | Senseair S12 (revision 2 footprint) | U16 |
| VOC/NOx sensor | SGP41 | U10 |
| Temperature/humidity sensor | SHT40 | U12 |
| Pressure sensor | SPL07-003 | U13 |
| Accelerometer | LIS2DH12 | U14 |
| GNSS receiver | TAU1113 | U18 |
| GNSS antenna, with matching network | CA-G01 chip antenna | AE1 |
| I²C switch for the SPS30 | TMUX121 | U15 |
| I/O expander, interrupt output to the ESP32 | TCA6408A | U17 |
| LED driver, 4 RGB LEDs under the battery holder | LP5036 | U20, LED1–LED4 |
| Buzzer | HYG-8503A | U6 |
| USB-C connector | GT-USB-7010ASV | USB1 |
| USB ESD protection | TPD2E2U06 | U21 |
| CO sensor read-out (not fitted): sensor, potentiostat, ADC, LDO | ES1-CO-100-01, LMP91002, ADS1115, TPS7A2030 | U11, U22, U23, U24 |

The cable connectors are HCZZ0032-5 (5-pin, 1.0 mm), referenced `CN1` to `CN3`:
- `CN1` takes the Sensirion SPS30 PM module.
- `CN2` takes the touch pad.
- `CN3` is a spare I²C header.

The cell sits in a moulded holder whose contacts are on the board (`BT1`), in a cut-out at the top of the board.

## Toolchain

- **KiCad 10** (file format 2026-03). All symbol, footprint, and 3D model libraries are bundled in `libraries/`. Each board's `fp-lib-table` / `sym-lib-table` references them project-relative, so the projects open without any extra library setup.
- **[Fabrication Toolkit](https://github.com/bennymeg/Fabrication-Toolkit)** plugin generates the Gerber/BOM/CPL production sets (`fabrication-toolkit-options.json` per board).

## Repository structure

```
PCB/
├── airgradient-go-main/     # Main PCB (schematic, layout, BOM.csv, production/)
├── touch-pad/               # Capacitive touch PCB
├── led-touch/               # LED + touch-controller PCB (v1 only)
└── scd4x-module/            # Optional SCD4x CO₂ daughterboard
design/                      # v3 design notes: per-part extracts, intended connections, layout tools
libraries/                   # Shared KiCad symbols, footprints, 3D models
graphics/                    # Logos and artwork
VERSIONS.md                  # v1, v2 and v3 side by side
CHANGES-v3.md                # v2 → v3 change record
SPEC-SHEET.md                # Hardware spec sheet
```

## Fabrication

Each board's `production/` directory holds a ready-to-order set: Gerber zip, BOM, designators, and pick-and-place positions in JLCPCB-compatible format (generated with Fabrication Toolkit). For v3 the sets are `Airgradient-GO_3.0` (main board) and `Touch_sensor_v2.1` (touch pad, unchanged from v2). The v2 sets are on tag `v2`.

The main board is 4 layers, 0.8 mm thick. The touch, LED and SCD4x boards are 2 layers.

## BOM & sourcing

The schematic BOM is `PCB/airgradient-go-main/BOM.csv`. The assembly BOMs (`production/*_bom.csv`) carry LCSC part numbers for assembly at JLCPCB.

These main-board parts have no LCSC number and are supplied separately for assembly:
- ESP32-C5-MINI-1 module
- Senseair S12
- SGP41
- SHT40
- TAU1113
- CA-G01 antenna

The display, the battery and the two internal cables are not in the KiCad BOM: see `SPEC-SHEET.md`.

## Versioning & releases

Hardware versions are tagged on this repository: `v1.0`, `v2`. v3 will be tagged when its design is final. Per-version release notes, with chip-level changes, design history and the matching production file set, are published on the [GitHub Releases](../../releases) page.

## Related repositories

<!-- TODO: add links to the firmware and enclosure repositories -->

## License

This is open-source hardware. The design files in this repository are licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/) license — see [LICENSE](LICENSE).

You are free to use, modify, and manufacture these designs, including commercially, provided you credit AirGradient and share derivative designs under the same license.

## Maintainers

AirGradient hardware team.
