# AirGradient GO — Hardware

> KiCad hardware design files for the AirGradient GO, a portable battery-powered air quality monitor.

<!-- ![AirGradient GO](graphics/airgradient Final-02.png) -->

## Overview

AirGradient GO is a handheld air quality monitor. It measures particulate matter (Sensirion SPS30), CO₂ (Senseair S12), VOC/NOx (SGP41), temperature and humidity (SHT4x), and barometric pressure (DPS368), with an accelerometer (LIS2DH12) for motion detection and a GPS receiver (TAU1113) for location. Readings are shown on a 2.13″ black-and-white e-paper display with RGB LED indicators and capacitive touch controls. The device runs on a 505060 Li-Po pouch cell charged over USB-C.

This repository contains the complete electronics design: schematics, PCB layouts, shared component libraries, and production outputs for all four boards.

## Boards in this repository

| Board | Directory | Latest production set | Layers | Description |
|---|---|---|---|---|
| Main board | `PCB/airgradient-go-main/` | v1.0 | 4 | MCU, power/charging, sensors, storage |
| LED + touch controller | `PCB/led-touch/` | AG-GO-LED v1.0 | 2 | RGB LEDs, LED driver, and capacitive-touch controller; mates with the touch-pad board and mechanically holds the e-paper display (the display connector and control circuitry are on the main board) |
| Touch pad | `PCB/touch-pad/` | Touch_sensor v1.0 | 2 | Capacitive touch input board |
| SCD4x module | `PCB/scd4x-module/` | v0.1 | 2 | Optional CO₂ daughterboard (the standard configuration uses the on-board Senseair S12) |

> **Note:** v2.0 of the main board, touch pad, and LED + touch boards is currently in development.

## Key components (main board)

| Function | Part | Ref |
|---|---|---|
| MCU / Wi-Fi | ESP32-C5-MINI-1 | U4 |
| Battery charger | BQ25628 | U3 |
| Fuel gauge | BQ27427 | U8 |
| Buck-boost converter | TPS63802 | U2 |
| LDO | TPS7A0228 | U7 |
| Hardware watchdog | TPL5010 | U5 |
| NAND flash (512 Mb) | W25N512GVEIG | U1 |
| NAND flash (alternative footprint for U1) | ZDSD512MLGEAG | U14 |
| CO₂ sensor module | Senseair S12 | U17 |
| VOC/NOx sensor | SGP41 | U9 |
| Temperature/humidity sensor | SHT4x | U13 |
| Pressure sensor | DPS368 | U15 |
| Accelerometer | LIS2DH12 | U11 |
| GPS receiver | TAU1113 | U16 |
| I²C bus isolator | TMUX121 | U10 |
| I/O expander | TCA9536 | U18 |
| Buzzer | HYG-8503A | U12 |
| GPS antenna | GPS1003 | ANT1 |
| USB-C connector | GT-USB-7010ASV | USB1 |

PM sensing uses a Sensirion SPS30 module connected to the main board. CO₂ sensing is handled by the on-board Senseair S12; the SCD4x daughterboard is an optional alternative.

## Toolchain

- **KiCad 10** (file format 2026-03). All symbol, footprint, and 3D model libraries are bundled in `libraries/` and referenced project-relative through each board's `fp-lib-table` / `sym-lib-table` — the projects open without any extra library setup.
- **[Fabrication Toolkit](https://github.com/bennymeg/Fabrication-Toolkit)** plugin — generates the Gerber/BOM/CPL production sets (`fabrication-toolkit-options.json` per board).

## Repository structure

```
PCB/
├── airgradient-go-main/     # Main PCB (schematic, layout, production/)
├── led-touch/               # LED + touch-controller PCB (also holds the e-paper display)
├── touch-pad/               # Capacitive touch PCB
└── scd4x-module/            # Optional SCD4x CO₂ daughterboard
libraries/                   # Shared KiCad symbols, footprints, 3D models
graphics/                    # Logos and artwork
```

## Fabrication

Each board's `production/` directory holds the ready-to-order set for its latest released version: Gerber zip, BOM, designators, and pick-and-place positions in JLCPCB-compatible format (generated with Fabrication Toolkit). The main board is a 4-layer design; the display, touch, and SCD4x boards are 2-layer.

## BOM & sourcing

BOMs are exported alongside each production set (`production/*_bom.csv`) with LCSC part numbers for assembly at JLCPCB.

## Versioning & releases

Hardware revisions are tagged on this repository. Per-version release notes — chip-level changes, design history, and the matching production file set — are published on the [GitHub Releases](../../releases) page.

## Related repositories

<!-- TODO: add links to the firmware and enclosure repositories -->

## License

This is open-source hardware. The design files in this repository are licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/) license — see [LICENSE](LICENSE).

You are free to use, modify, and manufacture these designs, including commercially, provided you credit AirGradient and share derivative designs under the same license.

## Maintainers

AirGradient hardware team.
