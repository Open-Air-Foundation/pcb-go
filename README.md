# AirGradient GO — Hardware

> KiCad hardware design files for the AirGradient GO, a portable battery-powered air quality monitor.

<!-- ![AirGradient GO](graphics/airgradient Final-02.png) -->

**This checkout is v2:** main board PCB revision 2.1, the boards in the GO v2 production units (tag `v2`, branch `main`).

## Overview

AirGradient GO is a handheld air quality monitor. It measures:
- particulate matter (Sensirion SPS30);
- CO₂ (Senseair S12);
- VOC/NOx (Sensirion SGP41);
- temperature and humidity (Sensirion SHT40);
- barometric pressure (Goermicro SPL07-003).

It also has an accelerometer (LIS2DH12) for motion detection and a GNSS receiver (TAU1113, GPS L1 and BeiDou B1) for location.

Readings are shown on a 2.13″ black-and-white e-paper display, with four RGB LEDs and capacitive touch controls. The device runs on a replaceable 18500 Li-ion cell (2600 mAh), charged over USB-C.

This repository contains the complete electronics design: schematics, PCB layouts, shared component libraries, and production outputs.

## Versions

| Version | Where | Main board revision | State |
|---|---|---|---|
| v1 | tag `v1.0` | 1.0 | the first product: pouch cell, separate LED + touch board |
| v2 | tag `v2`, branch `main` | 2.1 | **the produced boards** (this checkout) |
| v3 | branch `v3-reroute` | 3.0 | prototype |

[VERSIONS.md](https://github.com/Open-Air-Foundation/pcb-go/blob/v3-reroute/VERSIONS.md) (on branch `v3-reroute`) compares the three side by side, with pin maps and the reasons for each change. [SPEC-SHEET.md](https://github.com/Open-Air-Foundation/pcb-go/blob/v3-reroute/SPEC-SHEET.md) describes the hardware of v2 and v3, including the parts the KiCad BOM does not define: the display, the battery and the internal cables.

## Boards in this repository

| Board | Directory | Production set | Layers | Used by | Description |
|---|---|---|---|---|---|
| Main board | `PCB/airgradient-go-main/` | `Airgradient-GO_2.1` | 4 | v2 | MCU, power and charging, cell protection and fuel gauge, sensors, LEDs, storage. `Airgradient-GO_2.0` is the prototype revision |
| Touch pad | `PCB/touch-pad/` | `Touch_sensor_v2.1` | 2 | v2 | Three capacitive pads with the CAP1203 controller; 5-pin cable to the main board |
| LED + touch controller | `PCB/led-touch/` | `AG-GO-LED_1.0` | 2 | v1 only | RGB LEDs, LED driver and touch controller of v1 |
| SCD4x module | `PCB/scd4x-module/` | `SCD4x_module_0.1` | 2 | optional | CO₂ daughterboard. The standard configuration uses the on-board Senseair S12 |

## Key components (main board 2.1)

| Function | Part | Ref |
|---|---|---|
| MCU / Wi-Fi 6 + Bluetooth LE | ESP32-C5-MINI-1 (N4) | U4 |
| Battery charger | BQ25628 | U5 |
| Fuel gauge and cell protection | BQ27742-G1, with the CSD83325L FET pair | U3, Q3 |
| Input power switch | LM66200 ideal-diode switch | U19 |
| Buck-boost converter (3.1 V rail) | TPS63802 | U8 |
| LDO, GNSS backup supply | TPS7A0228 | U9 |
| Hardware watchdog | TPL5010 | U7 |
| NAND flash (512 Mb) | W25N512GVEIG | U1 |
| NAND flash, alternative footprint (not fitted) | ZDSD512MLGEAG | U2 |
| microSD socket (not fitted) | TF-CARD XG8P | TF1 |
| CO₂ sensor module | Senseair S12 | U16 |
| VOC/NOx sensor | SGP41 | U10 |
| Temperature/humidity sensor | SHT40 | U12 |
| Pressure sensor | SPL07-003 | U13 |
| Accelerometer | LIS2DH12 | U14 |
| GNSS receiver | TAU1113 | U18 |
| GNSS antenna | CA-G01 chip antenna | AE1 |
| I²C switch for the SPS30 | TMUX121 | U15 |
| I/O expander | TCA6408A | U17 |
| LED driver, 4 RGB LEDs | LP5036 | U20, LED1–LED4 |
| Buzzer | HYG-8503A | U6 |
| USB-C connector | GT-USB-7010ASV | USB1 |
| CO sensor place (not fitted) | — | U11 |

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
libraries/                   # Shared KiCad symbols, footprints, 3D models
graphics/                    # Logos and artwork
```

## Fabrication

Each board's `production/` directory holds a ready-to-order set: Gerber zip, BOM, designators, and pick-and-place positions in JLCPCB-compatible format (generated with Fabrication Toolkit). For v2 the sets are `Airgradient-GO_2.1` (main board) and `Touch_sensor_v2.1` (touch pad).

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

The display, the battery and the two internal cables are not in the KiCad BOM: see SPEC-SHEET.md.

## Versioning & releases

Hardware versions are tagged on this repository: `v1.0`, `v2`. Per-version release notes, with chip-level changes, design history and the matching production file set, are published on the [GitHub Releases](../../releases) page.

## Related repositories

<!-- TODO: add links to the firmware and enclosure repositories -->

## License

This is open-source hardware. The design files in this repository are licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/) license — see [LICENSE](LICENSE).

You are free to use, modify, and manufacture these designs, including commercially, provided you credit AirGradient and share derivative designs under the same license.

## Maintainers

AirGradient hardware team.
