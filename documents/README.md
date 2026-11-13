# Manufacturers' documents

Most parts of the GO have a public datasheet: a search for the part number in the BOM finds it. For the parts below a search finds nothing, or finds the wrong document. Their documents are kept here, so that a person or an AI reviewing the design has everything in one repository and reads the revision the design was made from.

The documents apply to v2 (tag `v2`) and to v3 (branch `v3-reroute`), except where a note says otherwise.

| Part | Ref | Document | Revision | Pages | File |
|---|---|---|---|---|---|
| E-paper display, Good Display GDEY0213B74 | `FPC1` | product specification | 2021/03/17 | 37 | [display/GDEY0213B74_GoodDisplay_2021-03-17.pdf](display/GDEY0213B74_GoodDisplay_2021-03-17.pdf) |
| Battery, Cowon 18500 cell, 2600 mAh | `BT1` | cell specification, model INR18490NP | A0, 2025-06-13 | 9 | [battery/Cowon_INR18490NP_2600mAh_cell-spec_A0.pdf](battery/Cowon_INR18490NP_2600mAh_cell-spec_A0.pdf) |
| | | material safety data sheet, model INR18500 26N | 2026-10-15 | 11 | [battery/Cowon_INR18500-26N_MSDS_2026-10-15.pdf](battery/Cowon_INR18500-26N_MSDS_2026-10-15.pdf) |
| CO2 sensor, Senseair S12 (article 012-0-0001) | `U16` | product specification PSP15871 (preliminary) | Rev 4, July 2026 | 12 | [co2-s12/Senseair_S12_product-spec_PSP15871_Rev4.pdf](co2-s12/Senseair_S12_product-spec_PSP15871_Rev4.pdf) |
| | | "I2C on S12 CO2", TDE15933: registers and bus timing | Rev 4, 2026-06-23 | 27 | [co2-s12/Senseair_S12_I2C_TDE15933_Rev4.pdf](co2-s12/Senseair_S12_I2C_TDE15933_Rev4.pdf) |
| | | product change notification PCN16844 | 2026-10-07 | 3 | [co2-s12/Senseair_S12_change-notice_PCN16844_2026-10-07.pdf](co2-s12/Senseair_S12_change-notice_PCN16844_2026-10-07.pdf) |
| GNSS antenna, CrossAir CA-G01 | `AE1` | application manual, in Chinese | V01, 2021-07 | 8 | [gnss/CrossAir_CA-G01_antenna_application-manual_V01_CN.pdf](gnss/CrossAir_CA-G01_antenna_application-manual_V01_CN.pdf) |

`SPEC-SHEET.md` at the repository root gives the values taken from these documents, with the page of each.

## Read this before you use them

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

**Antenna.** The manual gives the pad pattern, the clear area round the antenna and the matching network that v3 fits (`CHANGES-v3.md`, row R-V3-31).

## Not in this folder

| Part | Document | Why it is not here | Where to get it |
|---|---|---|---|
| GNSS module TAU1113 (`U18`) | Allystar "TAU1113 Datasheet" V1.4 (preliminary), the one `SPEC-SHEET.md` cites | every page is marked "Confidential", and its notice forbids passing copies on | www.allystar.com, named in the document itself |
| Pressure sensor SPL07-003 (`U13`) | Goermicro datasheet v1.0 | every page is marked "Confidential" | the part's page at LCSC, C3253727 |
| S12 | "Modbus on S12 CO2" (TDE15927) and the reflow soldering instructions (TDE16239), both named by the documents above | not in hand | Senseair |
| The two internal cables, the battery holder, the enclosure | none: the manufacturer has no document for them | | `SPEC-SHEET.md`, sections 7 and 10 |
| Every other part | its public datasheet | a search finds it | `PCB/airgradient-go-main/BOM.csv` gives the part number and the LCSC number |

## Licence

These PDFs are their manufacturers' documents, copied here unchanged for reference. Each stays under its manufacturer's copyright. This repository's CC BY-SA licence does not cover them.

The display specification is the copy on Seeed Studio's file server (files.seeedstudio.com/wiki/Other_Display/213-epaper/GDEY0213B74.pdf).
