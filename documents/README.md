# Manufacturers' documents

The manufacturers' documents the GO was designed from, so that a person or an AI reviewing the design has everything in one repository and reads the revision the design was made from. The page numbers cited in the spec sheets, and on branch `v3-reroute` in `CHANGES-v3.md` and `design/requirements.md`, are those of the revisions kept here.

This folder is the same on branch `main` and on branch `v3-reroute`. Some notes below name files that only `v3-reroute` has: `CHANGES-v3.md` and everything under `design/`.

Two kinds of document are here:
- **Section 1:** documents a search does not find, or finds wrong: the display, the battery, the Senseair S12, the GNSS antenna and module.
- **Section 2:** datasheets of the main parts: the ESP32-C5 module, the charger, the fuel gauge, the power parts, the sensors, the peripherals.

The documents apply to v2 (tag `v2`) and to v3 (branch `v3-reroute`), except where a note says otherwise. References (`U5`, `CN1`) are those of v2 and v3; v1 numbers its parts differently. v1 (tag `v1.0`) shares most of these parts; the two datasheets that only v1 needs are marked "v1 only".

## 1. Parts a search does not find

| Part | Ref | Document | Revision | Pages | File |
|---|---|---|---|---|---|
| E-paper display, Good Display GDEY0213B74 | `FPC1` | product specification | 2021/03/17 | 37 | [display/GDEY0213B74_GoodDisplay_2021-03-17.pdf](display/GDEY0213B74_GoodDisplay_2021-03-17.pdf) |
| | | datasheet of its controller, Solomon Systech SSD1680 (product preview) | Rev 0.14, June 2019 | 46 | [display/SolomonSystech_SSD1680_controller_Rev0.14.pdf](display/SolomonSystech_SSD1680_controller_Rev0.14.pdf) |
| Battery, Cowon 18500 cell, 2600 mAh | `BT1` | cell specification, model INR18490NP | A0, 2025-06-13 | 9 | [battery/Cowon_INR18490NP_2600mAh_cell-spec_A0.pdf](battery/Cowon_INR18490NP_2600mAh_cell-spec_A0.pdf) |
| | | material safety data sheet, model INR18500 26N | 2026-10-15 | 11 | [battery/Cowon_INR18500-26N_MSDS_2026-10-15.pdf](battery/Cowon_INR18500-26N_MSDS_2026-10-15.pdf) |
| CO2 sensor, Senseair S12 (article 012-0-0001) | `U16` | product specification PSP15871 (preliminary) | Rev 4, July 2026 | 12 | [co2-s12/Senseair_S12_product-spec_PSP15871_Rev4.pdf](co2-s12/Senseair_S12_product-spec_PSP15871_Rev4.pdf) |
| | | "I2C on S12 CO2", TDE15933: registers and bus timing | Rev 4, 2026-06-23 | 27 | [co2-s12/Senseair_S12_I2C_TDE15933_Rev4.pdf](co2-s12/Senseair_S12_I2C_TDE15933_Rev4.pdf) |
| | | product change notification PCN16844 | 2026-10-07 | 3 | [co2-s12/Senseair_S12_change-notice_PCN16844_2026-10-07.pdf](co2-s12/Senseair_S12_change-notice_PCN16844_2026-10-07.pdf) |
| GNSS antenna, CrossAir CA-G01 | `AE1` | application manual, in Chinese | V01, 2021-07 | 8 | [gnss/CrossAir_CA-G01_antenna_application-manual_V01_CN.pdf](gnss/CrossAir_CA-G01_antenna_application-manual_V01_CN.pdf) |
| GNSS module, TAU1113-1010A00E | `U18` | module datasheet, the online version published by Tuya | 2025-02-24 | 33 | [gnss/TAU1113_module-datasheet_Tuya_2025-02-24.pdf](gnss/TAU1113_module-datasheet_Tuya_2025-02-24.pdf) |

`SPEC-SHEET.md` at the repository root gives the values taken from these documents, with the page of each.

### Read this before you use them

**Display.** The fitted panel is the GDEY0213B74: 250 × 122 pixels. The GDEY0213B74H has the same outline and nearly the same name, but 144 × 296 pixels. A search for the name returns both.

**Battery.** Both documents are Cowon's and both describe the 2600 mAh cell, but they name the model differently: INR18490NP in the cell specification, INR18500 26N in the safety data sheet. The cell is bought as an "18500"; by the drawing in its specification it is an 18490.

**S12: the change notification overrides the product specification.** The product specification (Rev 4, July 2026) is older than the change notification (October 2026), and Senseair has not reissued it yet:

| | Product specification Rev 4 | Change notification PCN16844 |
|---|---|---|
| Pin 6 | `DE`: high while the sensor transmits | `EEPA`: tells that an EEPROM write is in progress |
| Solder pads | 0.8 mm | 1.5 mm ("increased by 0.7 mm"; the drawings on its pages 2 and 3 show where) |

- v3 follows the change notification: footprint `S12_rev2`, and pin 6 as net `EEPA` to ESP32 IO9.
- v2 has the earlier footprint, with pin 6 not connected.
- The change notification does not give the polarity or the timing of `EEPA`. That is an open point in `CHANGES-v3.md`, section 6.

**GNSS antenna.** The manual gives the pad pattern, the clear area round the antenna and the matching network that v3 fits (`CHANGES-v3.md`, row R-V3-31).

**GNSS module.** The datasheet here is the public copy that Tuya publishes for the same module. It gives the same performance values as `SPEC-SHEET.md` section 3, but that section's page numbers are those of Allystar's own datasheet V1.4, which is not in this folder (see section 3).

## 2. Datasheets of the main parts

### Processor: `mcu/`

| Part | Ref | Document, revision | Pages | File |
|---|---|---|---|---|
| Espressif ESP32-C5-MINI-1 module | `U4` | module datasheet v1.4, 2026-09-14 | 64 | [Espressif_ESP32-C5-MINI-1_datasheet_v1.4.pdf](mcu/Espressif_ESP32-C5-MINI-1_datasheet_v1.4.pdf) |
| | | module datasheet v1.3, 2026-08-12 | 62 | [Espressif_ESP32-C5-MINI-1_datasheet_v1.3.pdf](mcu/Espressif_ESP32-C5-MINI-1_datasheet_v1.3.pdf) |
| Espressif ESP32-C5, the chip inside the module | | chip datasheet v1.5, 2026-09-03 | 96 | [Espressif_ESP32-C5_chip-datasheet_v1.5.pdf](mcu/Espressif_ESP32-C5_chip-datasheet_v1.5.pdf) |
| | | ESP32-C5 Hardware Design Guidelines, release of 2026-10-12 | 32 | [Espressif_ESP32-C5_hardware-design-guidelines_2026-10-12.pdf](mcu/Espressif_ESP32-C5_hardware-design-guidelines_2026-10-12.pdf) |

The board carries the module. Take pad numbers and limits from the module datasheet, and use the chip datasheet only for what the module datasheet does not give. Two revisions of the module datasheet are here because both are cited: `design/requirements.md` gives pages of v1.3, the spec sheets pages of v1.4.

### Charging, battery and power: `power/`

| Part | Ref | Document, revision | Pages | File |
|---|---|---|---|---|
| TI BQ25628, battery charger | `U5` | datasheet SLUSEG4C, February 2025 | 89 | [TI_BQ25628_charger_SLUSEG4C.pdf](power/TI_BQ25628_charger_SLUSEG4C.pdf) |
| TI BQ27742-G1, fuel gauge and cell protector | `U3` | datasheet SLUSBV9D, January 2018 | 46 | [TI_BQ27742-G1_gauge-protector_SLUSBV9D.pdf](power/TI_BQ27742-G1_gauge-protector_SLUSBV9D.pdf) |
| | | technical reference manual SLUUAX0C, July 2015: commands and data flash | 125 | [TI_BQ27742-G1_technical-reference_SLUUAX0C.pdf](power/TI_BQ27742-G1_technical-reference_SLUUAX0C.pdf) |
| TI BQ27427, fuel gauge of v1 | v1 only | datasheet SLUSEB5B, September 2025 | 23 | [TI_BQ27427_gauge_SLUSEB5B.pdf](power/TI_BQ27427_gauge_SLUSEB5B.pdf) |
| TI CSD83325L, dual N-FET | `Q3`; `Q6` in v3 | datasheet SLPS494C, November 2023 | 14 | [TI_CSD83325L_dual-NMOS_SLPS494C.pdf](power/TI_CSD83325L_dual-NMOS_SLPS494C.pdf) |
| TI LM66200, ideal-diode switch | `U19` | datasheet SLVSG04, November 2021 | 21 | [TI_LM66200_ideal-diode_SLVSG04.pdf](power/TI_LM66200_ideal-diode_SLVSG04.pdf) |
| TI TPS63802, buck-boost converter | `U8` | datasheet SLVSEU9D, January 2021 | 38 | [TI_TPS63802_buck-boost_SLVSEU9D.pdf](power/TI_TPS63802_buck-boost_SLVSEU9D.pdf) |
| TI TPS7A02, LDO (fitted: TPS7A0228) | `U9` | datasheet SBVS277C, September 2022 | 48 | [TI_TPS7A02_LDO_SBVS277C.pdf](power/TI_TPS7A02_LDO_SBVS277C.pdf) |
| TI TPL5010, watchdog timer | `U7` | datasheet SNAS651A, September 2018 | 27 | [TI_TPL5010_watchdog-timer_SNAS651A.pdf](power/TI_TPL5010_watchdog-timer_SNAS651A.pdf) |
| Murata NCP15XH103F03RC, NTC thermistor | `NTC1`, `NTC2` | Murata's catalogue of the NCP series | 49 | [Murata_NTC-thermistors_NCP-series_catalog.pdf](power/Murata_NTC-thermistors_NCP-series_catalog.pdf) |

### Sensors: `sensors/`

| Part | Ref | Document, revision | Pages | File |
|---|---|---|---|---|
| Sensirion SPS30, particulate matter | on `CN1` | datasheet v2.0, June 2023 | 26 | [Sensirion_SPS30_datasheet_v2.0.pdf](sensors/Sensirion_SPS30_datasheet_v2.0.pdf) |
| Sensirion SHT40, temperature and humidity | `U12` | SHT4x datasheet v7.3, June 2026 | 25 | [Sensirion_SHT4x_datasheet_v7.3.pdf](sensors/Sensirion_SHT4x_datasheet_v7.3.pdf) |
| Sensirion SGP41, VOC and NOx | `U10` | datasheet v1.0, December 2021 | 22 | [Sensirion_SGP41_datasheet_v1.0.pdf](sensors/Sensirion_SGP41_datasheet_v1.0.pdf) |
| ST LIS2DH12, accelerometer | `U14` | datasheet DocID025056 Rev 6, May 2017 | 53 | [ST_LIS2DH12_datasheet_Rev6.pdf](sensors/ST_LIS2DH12_datasheet_Rev6.pdf) |
| EC Sense ES1-CO-100-01, CO sensor (not fitted) | `U11` in v3 | datasheet V1.4, 2025-02-28 | 5 | [ECSense_ES1-CO-100-01_datasheet_V1.4.pdf](sensors/ECSense_ES1-CO-100-01_datasheet_V1.4.pdf) |
| Infineon DPS368, pressure sensor of v1 | v1 only | datasheet v1.1, 2019-07-03 | 44 | [Infineon_DPS368_datasheet_v1.1.pdf](sensors/Infineon_DPS368_datasheet_v1.1.pdf) |

The Senseair S12 is in section 1.

### Peripherals: `peripherals/`

| Part | Ref | Document, revision | Pages | File |
|---|---|---|---|---|
| TI TCA6408A, I/O expander | `U17` | datasheet SCPS192E, January 2023 | 50 | [TI_TCA6408A_io-expander_SCPS192E.pdf](peripherals/TI_TCA6408A_io-expander_SCPS192E.pdf) |
| TI TMUX121, I2C switch for the SPS30 | `U15` | datasheet SCDS381, August 2023 | 18 | [TI_TMUX121_i2c-switch_SCDS381.pdf](peripherals/TI_TMUX121_i2c-switch_SCDS381.pdf) |
| TI LP5036, LED driver | `U20` | datasheet SLVSEH1B, January 2019 | 62 | [TI_LP5036_led-driver_SLVSEH1B.pdf](peripherals/TI_LP5036_led-driver_SLVSEH1B.pdf) |
| TI TPD2E2U06, USB ESD protection | `U21`, v3 only | datasheet SLLSEG9C, December 2019 | 23 | [TI_TPD2E2U06_usb-esd_SLLSEG9C.pdf](peripherals/TI_TPD2E2U06_usb-esd_SLLSEG9C.pdf) |
| Winbond W25N512GV, NAND flash | `U1` | datasheet Revision C, 2018-11-21 | 74 | [Winbond_W25N512GV_nand-flash_RevC.pdf](peripherals/Winbond_W25N512GV_nand-flash_RevC.pdf) |
| Microchip CAP1203, touch controller | on the touch pad board | datasheet DS00001572B | 60 | [Microchip_CAP1203_touch-controller_DS00001572B.pdf](peripherals/Microchip_CAP1203_touch-controller_DS00001572B.pdf) |

### Connectors, LEDs, buzzer: `misc/`

| Part | Ref | Document | Pages | File |
|---|---|---|---|---|
| Hong Cheng HCZZ0032-5, 5-pin 1.0 mm header (LCSC C7433426) | `CN1` to `CN3`; touch pad `CN1` | drawing | 1 | [HongCheng_HCZZ0032-5_header_C7433426.pdf](misc/HongCheng_HCZZ0032-5_header_C7433426.pdf) |
| GT-USB-7010ASV, USB-C connector (LCSC C2988369) | `USB1` | drawing | 1 | [GT-USB-7010ASV_usb-c-connector_C2988369.pdf](misc/GT-USB-7010ASV_usb-c-connector_C2988369.pdf) |
| TJ-S1608SW6TDSLCCYRGB-A5, RGB LED (LCSC C5356078) | `LED1` to `LED4` | Tongjia specification for approval | 11 | [Tongjia_TJ-S1608SW6TDSLCCYRGB-A5_rgb-led_C5356078.pdf](misc/Tongjia_TJ-S1608SW6TDSLCCYRGB-A5_rgb-led_C5356078.pdf) |
| HYG-8503A, buzzer (LCSC C7544813) | `U6` | specification, 2021-08-22 | 7 | [HYG-8503A_buzzer_C7544813.pdf](misc/HYG-8503A_buzzer_C7544813.pdf) |

## 3. Not in this folder

| Part | Document | Why it is not here | Where to get it |
|---|---|---|---|
| GNSS module TAU1113 (`U18`) | Allystar "TAU1113 Datasheet" V1.4 (preliminary), whose pages `SPEC-SHEET.md` cites | every page is marked "Confidential", and its notice forbids passing copies on | www.allystar.com, named in the document itself. Section 1 has the public datasheet of the same module |
| Pressure sensor SPL07-003 (`U13`) | Goermicro datasheet v1.0 | every page is marked "Confidential" | the part's page at LCSC, C3253727 |
| S12 | "Modbus on S12 CO2" (TDE15927) and the reflow soldering instructions (TDE16239), both named by the S12 documents in section 1 | not in hand | Senseair |
| ESP32-C5 | technical reference manual v1.1 | 1746 pages, 15 MB | www.espressif.com |
| CO read-out, not fitted: LMP91002 (`U22`), ADS1115 (`U23`), TPS7A2030 (`U24`) | their TI datasheets | not fitted on any board | www.ti.com. `design/parts/` has extracts for the LMP91002 and the ADS1115 |
| The two internal cables, the battery holder, the enclosure | none: the manufacturer has no document for them | | `SPEC-SHEET.md`, sections 7 and 10 |
| The other parts only v1 has: the KNTC0805 thermistor, the GPS1003 antenna, the pouch cell | public datasheets for the first two; no specification is on record for the cell | | `SPEC-SHEET-v1.md` on branch `main` |
| Every other part: resistors, capacitors, inductors, the fuse, the switches, the display's FPC socket, the unfitted microSD socket and second flash | its public datasheet | a search finds it | `PCB/airgradient-go-main/BOM.csv` gives the part number and the LCSC number |

## Licence

These PDFs are their manufacturers' documents, copied here unchanged, for the development and review of this design. Each stays under its manufacturer's copyright and under the notice printed in it. This repository's CC BY-SA licence does not cover them.

The display specification is the copy on Seeed Studio's file server (files.seeedstudio.com/wiki/Other_Display/213-epaper/GDEY0213B74.pdf).
