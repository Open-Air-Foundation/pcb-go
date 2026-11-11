# AirGradient GO main board: v1, v2 and v3 side by side

Three designs of the main board (`PCB/airgradient-go-main`) in https://github.com/Open-Air-Foundation/pcb-go:

| | Where | PCB revision | State |
|---|---|---|---|
| v1 | tag `v1.0` (commit 96f6503) | 1.0 | the first product |
| v2 | tag `v2` (commit e806931, also the head of `main`) | 2.1 | the boards that were produced |
| v3 | branch `v3-reroute` | 3.0 | prototype, not ordered yet, not tagged yet |

The tables are read from the KiCad files of the three designs: a netlist exported from each schematic, and the three board files. Reference designators were renumbered between v1 and v2 (the charger is U3 in v1 and U5 afterwards), so parts are named here by what they do and by part number. The reasons in section 3 are the designer's.

v2 → v3 is written out in full, with the reason and the source of every number, in `CHANGES-v3.md`. This document adds v1 and puts the three next to each other.

## 1. At a glance

| | v1 | v2 | v3 |
|---|---|---|---|
| Battery | LiPo pouch cell on a 2-pin connector | replaceable 18500 cell in a moulded holder, in a cut-out of the board | as v2 |
| Cell protection, fuel gauge | BQ27427 gauge; protection is in the cell's pack | BQ27742-G1 gauge and protector on the board, CSD83325L FET pair, 5 mΩ sense resistor | as v2, plus a second CSD83325L against a reversed cell |
| Charger | BQ25628, input limit resistor 2.49K, input fuse 0.75 A | the same | BQ25628, 1.1K, fuse 2.6 A: a 2 A charge is possible |
| Charger NTC | KNTC0805 10K (B 3950), divider 4.12K / 17.33K | NCP15XH103F03RC at the cell, divider 5.23k / 30.1k | as v2 |
| System rail | TPS63802, 3.11 V (475K / 91K) | the same | TPS63802, 3.31 V (511K / 91K) |
| Input of that converter | two Schottky diodes: USB or the charger's SYS | LM66200 ideal-diode mux: USB through 0.47 Ω, or SYS; then a 50 mΩ shunt | LM66200 passes SYS only (the USB leg is not fitted) |
| GNSS backup supply | 2.8 V LDO or the 3.1 V rail, through two diodes | 2.8 V LDO alone, fed from the pack | as v2 |
| Microcontroller | ESP32-C5-MINI-1, top right, back side | ESP32-C5-MINI-1, left edge, front side | as v2 |
| I/O expander | TCA9536, 4 ports, one used | TCA6408A, 8 ports, seven used, its interrupt output not connected | TCA6408A, all eight used, interrupt output on IO1 |
| What can interrupt the ESP32 | touch (IO1), accelerometer (IO3) | nothing | touch, accelerometer and charger, through the expander, on IO1 |
| I2C (SDA / SCL) | IO7 / IO6, 10K pull-ups | IO7 / IO6, 10K | IO2 / IO3 (the low-power I2C pins), 100K |
| LEDs | on a separate LED + touch board: LP5036, 10 RGB and 2 white | on the main board: LP5036, 4 RGB at the top edge | the same parts under the battery holder, half the current |
| Touch controller | CAP1203 on the LED + touch board | CAP1203 on the touch pad | as v2 |
| Pressure sensor | DPS368 | SPL07-003 | as v2 |
| GNSS | TAU1113 on UART0; antenna GPS1003 (10 × 3 mm), no matching fitted | TAU1113 on UART0; chip antenna CA-G01 (8 × 3 mm), no matching fitted | TAU1113 on UART0 through 499 Ω; CA-G01 with the matching network of its manual |
| Storage | W25N512 NAND | W25N512 NAND; microSD socket place, not fitted | as v2 |
| CO sensor | none | footprint only, not fitted | footprint and an unfitted read-out circuit |
| USB ESD protection | none | none | TPD2E2U06 |
| Board | 62.90 × 86.98 mm, no cut-out | 62.90 × 88.29 mm, cut-out 51.0 × 26.4 mm for the cell | as v2 |
| Where the parts are | 118 of 143 footprints on the back | 157 of 184 on the front | 182 of 212 on the front |
| Screw holes | 2 of 2.5 mm, and 3 of 3.2 mm for standoffs | 4 of 2.5 mm, and 2 of 2.04 mm for the holder | 4 of 1.82 mm, and the same 2 for the holder |
| Test pads on the board | 16 | none | none |
| Parts in the schematic, without test points | 139, of them 9 not fitted | 184, 27 not fitted | 212, 42 not fitted |

All three are 4-layer boards, 0.8 mm thick. Places are named as the board is seen from the front. Not changed in any version: ESP32-C5-MINI-1, BQ25628, TPS63802, the 2.8 V LDO TPS7A0228, the watchdog TPL5010 with its 51K resistor, the W25N512 NAND, the TMUX121 switch and the 5 V switch for the SPS30, SHT4x, SGP41, S12, LIS2DH12, TAU1113, the e-paper booster and its 24-pin connector, the buzzer, the USB-C connector and both buttons.

## 2. Firmware

### ESP32-C5-MINI-1 pins

Bold marks a change from the version before.

| GPIO | Pad | v1 | v2 | v3 |
|---|---|---|---|---|
| IO0 | 16 | ePaper CS | ePaper CS | **ePaper D/C** |
| IO1 | 17 | touch alert `INT`, from the LED + touch board | **not used** | **EXP_INT**, the expander's interrupt output |
| IO2 | 6 | WD_RST | WD_RST | **SDA** |
| IO3 | 7 | ACC_INT | **not used** | **SCL** |
| IO4 | 8 | NAND CS | **not used** | **WD_RST** |
| IO5 | 9 | QON | QON | QON |
| IO6 | 10 | SCL | SCL | **ePaper CS** |
| IO7 | 19 | SDA | SDA | **NAND CS** |
| IO8 | 20 | BUZZ | BUZZ | BUZZ |
| IO9 | 21 | ePaper RES | ePaper RES | **EEPA** (S12 rev 2, "EEPROM write in progress") |
| IO10 | 22 | ePaper BUSY | ePaper BUSY | ePaper BUSY |
| IO13, IO14 | 23, 24 | USB D-, D+ | USB D-, D+ | USB D-, D+ |
| IO15 | 26 | ePaper D/C | **not used** | not used |
| IO23 | 31 | SCLK | SCLK | SCLK, 33 Ω in each branch |
| IO24 | 32 | MISO | MISO | MISO, 33 Ω |
| IO25 | 33 | MOSI | MOSI | MOSI, 33 Ω in each branch |
| IO26 | 34 | EN_PM1 (I2C switch of the SPS30) | **not used** | not used |
| IO27 | 35 | pull-up only, 10K | pull-up only, **100K** | pull-up only, 100K |
| IO28 | 4 | SW2 | SW2 | SW2 |
| TXD0, RXD0 | 39, 40 | GNSS UART | GNSS UART | GNSS UART **through 499 Ω** |
| EN | 45 | reset from the watchdog | the same | the same |

### I/O expander

| | v1 | v2 | v3 |
|---|---|---|---|
| Part | TCA9536 (4 ports) | **TCA6408A** (8 ports) | TCA6408A |
| P0 | PRTRG (GNSS) | PRTRG | PRTRG |
| P1 | not connected | **EN_PM1** | EN_PM1 |
| P2 | not connected | **NAND CS** | **ePaper RES** |
| P3 | not connected | **ePaper D/C** | **CHG_INT** (charger interrupt, input) |
| P4 | | **INT** (touch alert) | INT (touch alert) |
| P5 | | **ACC_INT** | ACC_INT |
| P6 | | **SD_CS** | SD_CS |
| P7 | | not connected | **CO_MENB** |
| Interrupt output | not connected | not connected | **EXP_INT, to IO1** |

### What else differs for firmware

| | v1 | v2 | v3 |
|---|---|---|---|
| Fuel gauge | BQ27427 | BQ27742-G1, which is also the protector | as v2 |
| Pressure sensor | DPS368 | SPL07-003 | as v2 |
| LED driver | LP5036 on the LED + touch board, reached over its 5-pin cable | LP5036 on the main board; LED1 to LED4 on outputs 0 to 11 | the same outputs; full-scale current 7.35 mA instead of 14.4 mA |
| Touch alert | IO1, an interrupt | expander P4, polled | expander P4, interrupt through EXP_INT |
| Accelerometer INT1 | IO3, an interrupt | expander P5, polled | expander P5, interrupt through EXP_INT |
| Charger interrupt | not connected | not connected | expander P3; a 256 µs pulse that the expander does not hold |
| NAND chip select | IO4 | an I2C write to the expander | IO7 |
| Display D/C | IO15 | an I2C write to the expander | IO0 |
| Display reset | IO9 | IO9 | an I2C write to the expander |
| microSD | none | CS on expander P6, socket not fitted | as v2 |
| S12 | enable pin pulled with 10K | pulled with 100K | 100K; `EEPA` on IO9 |
| Rail | 3.11 V | 3.11 V | 3.31 V |

## 3. v1 → v2: what changed and why

| Area | v1 | v2 | Why |
|---|---|---|---|
| Battery | LiPo pouch cell, 2-pin connector | 18500 cell in a moulded holder with contacts on the board; the top of the board is cut out for it | the cell can be replaced by the user |
| Protection and gauge | BQ27427 gauge only | BQ27742-G1 gauge and protector, CSD83325L FET pair, 5 mΩ sense resistor, its own NTC | a bare cell has no protection board. The protector that was chosen has a gauge in it, so the v1 gauge went |
| Charger NTC | KNTC0805 10K (B 3950), divider 4.12K / 17.33K | NCP15XH103F03RC, divider 5.23k / 30.1k, placed at the cell | one NTC part for the charger and the protector |
| Converter input | Schottky OR of USB and the charger's SYS | LM66200 ideal-diode mux, then a 50 mΩ shunt | no leak from the battery through the diode path while the device is off |
| GNSS backup | 2.8 V LDO or the 3.1 V rail, through two diodes | the 2.8 V LDO alone, fed from the pack | the same. The backup now lasts only while a cell is in |
| I/O expander | TCA9536; touch alert, accelerometer interrupt, NAND CS, display D/C and the SPS30 switch on ESP32 pins | TCA6408A carries those five; IO1, IO3, IO4, IO15 and IO26 are left free | to keep ESP32 pins free for later use. The expander's interrupt output was not connected, so touch and motion could not interrupt the ESP32, and NAND CS and display D/C cost an I2C write each. v3 undoes most of this (section 4) |
| LEDs | on the LED + touch board: LP5036, 10 RGB and 2 white | LP5036 and 4 RGB LEDs on the main board | the LED + touch board was dropped; the main board has room for four |
| Touch | CAP1203 on the LED + touch board, above a bare touch pad | CAP1203 on the touch pad itself | one touch board instead of two stacked ones |
| Pressure sensor | DPS368 | SPL07-003 | lower cost |
| GNSS antenna | GPS1003, top left corner, back side | CA-G01 chip antenna, top right corner, front side | a new antenna part with its own footprint. In both, the matching places hold a 0 Ω link and two unfitted capacitors |
| microSD | none | socket place on the SPI bus, not fitted | an option for more storage |
| CO sensor | none | footprint, not fitted and not connected | room for a later variant |
| Connectors | battery (2 pins); LED + touch board and SPS30 on top-entry 5-pin BM05B; I2C on a 4-pin HCZZ0039-4 | three right-angle 5-pin HCZZ0032-5: SPS30, touch pad, I2C | the cables run differently in the new enclosure |
| Pull-ups | 10K on NAND CS, EN_PM1, IO27 and the S12 enable | 100K | lower current |
| Board | 62.90 × 86.98 mm; most parts on the back; ESP32 top right; 16 test pads | 62.90 × 88.29 mm with the cut-out; most parts on the front; ESP32 on the left edge; no test pads | the cut-out takes the top of the board, so the board was laid out again |
| Mounting | 2 screw holes; 3 holes for standoffs | 4 screw holes; 2 holes for the holder's screws | the moulded battery holder replaces the standoffs and carries the touch board |

Where things stayed: the USB-C connector and both buttons are at the same coordinates in all three versions. The S12 (turned half a turn), the SGP41, the SHT4x (now on the front) and the buzzer stay in the same areas, within 3 mm.

PCB revision 2.0 (branch `v2.0`) was the prototype of v2. Revision 2.1, the tag `v2`, added the NTC change above, a capacitor at the cell's plus contact, a pull-up on the expander's reset pin and the HCZZ0032-5 connectors, and left the microSD socket unfitted.

## 4. v2 → v3 in short

The outline, the holder and every connector, switch and sensor stay where v2 has them. `CHANGES-v3.md` has each item with its reason.

- Pins: I2C on IO2 / IO3; NAND CS and display D/C back on ESP32 pins; the expander's interrupt output on IO1, with touch, accelerometer and charger behind it; watchdog on IO4; `EEPA` from the S12 on IO9.
- Power: rail 3.11 V → 3.31 V; a 2 A charge made possible on the input side; protection against a reversed cell; the converter no longer sees raw USB voltage.
- Signals: series resistors on SPI and UART0; an ESD part on USB; I2C pull-ups 100K; LED current halved.
- GNSS antenna: matching network, pads and clear area as its manual draws them.
- LEDs moved under the battery holder.
- CO sensor: an unfitted read-out circuit.
- The four screw holes at the bottom corners: 1.82 mm instead of 2.5 mm.
- All copper redrawn, with one inner layer as unbroken ground.

## 5. The other boards

| Board | With v1 | With v2 and v3 |
|---|---|---|
| LED + touch (`PCB/led-touch`, AG-GO-LED 1.0) | LP5036, 10 RGB and 2 white LEDs, CAP1203; 5-pin cable to the main board | not used; its files are unchanged |
| Touch pad (`PCB/touch-pad`) | 1.0: three pads | 2.1: three pads, CAP1203 and a 5-pin connector |
| SCD4x module (`PCB/scd4x-module`) | 0.1 | 0.1 |

## 6. Getting the three designs

```
git clone https://github.com/Open-Air-Foundation/pcb-go.git
cd pcb-go
git checkout v1.0           # v1
git checkout v2             # v2
git checkout v3-reroute     # v3
git rev-parse --short HEAD  # the commit you have: quote it with anything you find
```

Open `PCB/airgradient-go-main/airgradient-go-main.kicad_pro` in KiCad 10; all three open in it. For a comparison by a script or an AI, export a netlist from each checkout and compare by part number and net name, not by reference:

```
kicad-cli sch export netlist --format kicadxml -o netlist.xml PCB/airgradient-go-main/airgradient-go-main.kicad_sch
kicad-cli sch export pdf -o schematic.pdf PCB/airgradient-go-main/airgradient-go-main.kicad_sch
```
