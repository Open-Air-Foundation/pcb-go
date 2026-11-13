# AirGradient GO main board: what changed from v2 to v3

This compares two designs of the main board (`PCB/airgradient-go-main`) in https://github.com/Open-Air-Foundation/pcb-go:

| | Where | PCB revision | State |
|---|---|---|---|
| Old | tag `v2` (commit 58b90d4, also the head of `main`) | 2.1 | the boards that were produced |
| New | branch `v3-reroute` | 3.0 | prototype, not ordered yet, not tagged yet |

v3 is not tagged yet: it gets its tag when the design is final. Until then the branch is the design. Section 7 says how to get both designs and which files to give a reviewer or an AI.

The other boards (touch pad, LED + touch, SCD4x module) are the same in both.

For v1 as well, with the three versions next to each other, see `VERSIONS.md`.

In short: v3 keeps the outline, the mounting holes and every connector, switch and sensor where v2 has them; the four screw holes at the bottom corners are drilled smaller. It changes which ESP32 pin does what (eight pins), wires the interrupt lines so touch, motion and the charger can wake the chip from deep sleep, raises the rail from 3.11 V to 3.31 V, makes a 2 A charge possible, adds protection against a reversed cell, moves the four LEDs under the battery holder, gives the GNSS antenna the matching network of its manual, and adds an unfitted read-out circuit for a CO sensor. All copper was redrawn.

The full record, with the reason and the source for every number, is `design/requirements.md` (rows R-V3-01 to R-V3-35). IDs in the tables below point there.

## 1. Firmware: pin map

### ESP32-C5-MINI-1 (U4)

| GPIO | Pad | v2 | v3 | Note |
|---|---|---|---|---|
| IO0 | 16 | ePaper CS | **ePaper D/C** | native now, no I2C write per transfer (R-V3-30) |
| IO1 | 17 | not used | **EXP_INT** | expander `~INT`, open drain, 100K pull-up R61. LP GPIO, so it can wake from deep sleep (R-V3-02, 06) |
| IO2 | 6 | WD_RST | **SDA** | LP_I2C_SDA |
| IO3 | 7 | not used | **SCL** | LP_I2C_SCL |
| IO4 | 8 | not used | **WD_RST** | TPL5010 DONE |
| IO5 | 9 | QON | QON | |
| IO6 | 10 | SCL | **ePaper CS** | |
| IO7 | 19 | SDA | **NAND CS** | was on the expander. 100K pull-up R3 keeps the NAND deselected at reset (R-V3-03) |
| IO8 | 20 | BUZZ | BUZZ | |
| IO9 | 21 | ePaper RES | **EEPA** | S12 rev 2 pin 6, "EEPROM write in progress". Input. Polarity not in the S12 documents yet (R-V3-07) |
| IO10 | 22 | ePaper BUSY | ePaper BUSY | |
| IO11 (TXD0) | 39 | MCU_TX | MCU_TX through 499 Ω | R74 (R-V3-25) |
| IO12 (RXD0) | 40 | MCU_RX | MCU_RX through 499 Ω | R75 |
| IO13, IO14 | 23, 24 | USB D-, D+ | USB D-, D+ | ESD array U21 added |
| IO15 | 26 | not used | not used | |
| IO23 | 31 | SCLK | SCLK | 33 Ω in each branch (R63 display, R64 NAND) |
| IO24 | 32 | MISO | MISO | 33 Ω (R67) |
| IO25 | 33 | MOSI | MOSI | 33 Ω in each branch (R65 display, R66 NAND) |
| IO26, IO27 | 34, 35 | strap resistors | strap resistors | |
| IO28 | 4 | SW2 | SW2 | |

### I/O expander TCA6408A (U17, I2C 0x20)

| Port | v2 | v3 | Direction in v3 |
|---|---|---|---|
| P0 | PRTRG (GNSS) | PRTRG | output |
| P1 | EN_PM1 | EN_PM1 | output |
| P2 | NAND CS | **ePaper RES** | output |
| P3 | ePaper D/C | **CHG_INT** | input, 100K pull-up R62 |
| P4 | INT (touch) | INT (touch) | input |
| P5 | ACC_INT | ACC_INT | input |
| P6 | SD_CS | SD_CS | output |
| P7 | not connected | **CO_MENB** | output, only used when the CO circuit is fitted |
| `~INT` | not connected | **EXP_INT** to IO1 | |

## 2. Firmware: what follows from it

- **I2C** moves from IO7/IO6 to IO2/IO3. The pull-ups R26 and R30 go from 10K to 100K. With an estimated 150 to 200 pF on the bus the rise time is 13 to 17 µs, so expect to need a clock near 10 kHz. If that is too slow, 2.2K to 4.7K fits the same pads (R-V3-22).
- **Interrupts.** In v2 neither the expander's nor the charger's interrupt was connected. In v3 touch (P4), the accelerometer (P5) and the charger (P3) all arrive on `EXP_INT` (IO1), which is an EXT1 wake pin.
  - Touch and accelerometer hold the line until the port is read.
  - The charger does not: the BQ25628 pulls `~INT` low for 256 µs and the expander passes the pulse on without holding it. When `EXP_INT` fires and neither P4 nor P5 changed, read the charger's flag registers (they latch until read). Whether a 256 µs pulse wakes the chip from deep sleep has to be tried on the first boards.
  - P3 is an input now: read the port once after setting its direction.
- **Display.** D/C is on IO0 (direct), CS on IO6, RES on expander P2, BUSY unchanged.
- **NAND.** CS is on IO7 (direct), so the NAND and SD drivers need no expander call in the chip-select path.
- **Watchdog.** TPL5010 DONE is on IO4.
- **S12.** `EEPA` on IO9 tells when the sensor writes its EEPROM, so power is not cut during a write.
- **UART0** keeps its pins. The 499 Ω resistors do not matter at GNSS baud rates.
- **Rail.** The system rail is 3.31 V (3.11 V in v2).
- **LEDs.** Full-scale current is 7.35 mA (14.4 mA in v2), so the same brightness value gives about half the light. The LEDs stay on the same LP5036 outputs.
- **Charging.** The input current limit set by the ILIM pin is 2.05 to 2.50 A (about 1.0 A in v2) and the input fuse holds 2.6 A, so a 2 A charge is possible. What the charger actually draws is still what firmware writes to IINDPM and ICHG. With USB plugged in, the 3.3 V system now always runs through the charger (VBUS, U5, SYS); there is no direct VBUS path any more.
- **CO circuit** (not fitted): LMP91002 at 0x48, answering only while `CO_MENB` (P7) is low; ADS1115 at 0x49, read AIN1 - AIN3.

## 3. Hardware changes and why

| Area | v2 | v3 | Why | ID |
|---|---|---|---|---|
| Deep-sleep wake | expander and charger interrupts not connected | `EXP_INT` on IO1 with R61; charger `~INT` on expander P3 with R62 | touch, motion and charger events must wake the chip | R-V3-02, 06, 08, 30 |
| Pin map | see section 1 | see section 1 | NAND CS and display D/C off the expander (each change was an I2C write); I2C on the LP pins | R-V3-03, 07, 30 |
| System rail | 3.11 V (R22 475K) | 3.31 V (R22 511K), net `+3.1V` renamed `+3.3V` | at 3.11 V, tolerance plus the Wi-Fi transmit dip took the module and the S12 under their minimum | R-V3-13 |
| Reverse battery | none | Q6 (CSD83325L) in the cell's minus lead, R68 10K | a cell put in backwards reached the gauge and the charger | R-V3-15 |
| Charge input | F1 0.75 A hold, R21 2.49K | F1 2.6 A hold (same 1206 footprint), R21 1.1K | F1 heated and cut a 2 A charge down to 1.5 A | R-V3-16 |
| Power mux input | U19 VIN1 on VBUS through R35 | R35 and R46 not fitted: U19 passes SYS only | VIN1 saw raw VBUS with nothing to clamp it (6 V absolute maximum) | R-V3-19 |
| Cell capacitor | C75 alone across the cell | C75 and C82 in series | one shorted capacitor must not short the cell | R-V3-20 |
| USB | no ESD part | U21 TPD2E2U06 on D+ and D- | | R-V3-14 |
| SPI | direct | 33 Ω per branch on SCLK and MOSI, 33 Ω on MISO | the clock splits into two long branches; without them it overshot in simulation | R-V3-10, 12 |
| UART0 | direct | 499 Ω in each line | Espressif asks for it on U0TXD; it also lets a tool drive RXD0 against the GNSS | R-V3-25 |
| I2C pull-ups | 10K | 100K | lower current while a line is low; see the note in section 2 | R-V3-22 |
| LED current | R49 5.1K, 14.4 mA | R49 10K, 7.35 mA | green and blue could not get 14.4 mA from the rail, so colour moved with the rail voltage | R-V3-23 |
| LED positions | along the top edge | under the battery holder (section 5) | they glared at the top edge | R-V3-28, 32 |
| GNSS antenna | series 0 Ω, two unfitted capacitors, no matching | T network of the antenna's manual: L4 6.2 nH, L5 6.2 nH, C86 100 pF; pads and clear area as the manual draws them | the antenna was never matched | R-V3-31 |
| GNSS module | | U18 moved 1.0 mm west | its ground pad sat under the battery holder's flange | R-V3-18 |
| S12 | pin 6 not connected | `EEPA` to IO9; lands for S12 rev 2, pads 5 to 8 end inside the board | new S12 revision | R-V3-07, 21 |
| CO sensor | footprint only | read-out circuit: U22 LMP91002, U23 ADS1115, U24 3.0 V LDO, all not fitted | to be tested apart from the board first | R-V3-17, 24, 26 |
| Charger NTC divider | R18, R19 part numbers of other values | part numbers match the values (5.23k, 30.1k) | the assembly BOM is built from that field; values did not change | R-V3-27 |
| Accelerometer | address pin on ground through pour slivers only | track from U14 pad 3 to ground | if the sliver broke, the address would move from 0x18 to 0x19 | R-V3-33 |
| Screw holes | four plated holes at the bottom corners, drilled 2.5 mm in a 2.6 mm pad | drilled 1.82 mm, same pad | under the upper two the enclosure has a boss with a 1.5 mm pilot bore, so only a screw passes the board there. The 2.5 mm drill left a 0.05 mm ring | R-V3-35 |
| Routing | | every track and zone redrawn; layer 2 is ground without any track | return paths | R-V3-11 |

## 4. Parts

Fitted, new in v3: C82, C86, L4, L5, Q6, R61 to R68, R74, R75, U21.

Not fitted, new in v3 (CO circuit): C76, C77, C79, C80, C81, C84, C85, R69 to R73, U22, U23, U24.

Removed: R45, C61, C62 (the old antenna network).

Changed:

| Ref | v2 | v3 |
|---|---|---|
| F1 | BSMD1206-075-6V (C883127) | BSMD1206-260-6V (C976306) |
| R21 | 2.49K (C25884) | 1.1K (C2845203) |
| R22 | 475K (C5713272) | 511K (C5126239) |
| R26, R30 | 10K (C327797) | 100K (C60491) |
| R49 | 5.1K (C105872) | 10K (C327797) |
| R18 | 5.23k (C25907) | 5.23k (C2933105) |
| R35, R46 | fitted | not fitted |
| U11 | PS1-CO-SMOKE-10k | ES1-CO-100-01, same footprint, not fitted |
| U16 | S12 footprint | S12 rev 2 footprint |
| AE1 | pads 1.1 x 3.2 mm, 7.5 mm apart | pads 1.2 x 3.0 mm, 8.0 mm apart |

U4's symbol had two pins numbered 12 and none numbered 11 (both not connected): pad 11 has its own pin now. The 3.3 V net is named `+3.3V` (`+3.1V` in v2).

Files: `PCB/airgradient-go-main/BOM.csv` (schematic BOM) and `PCB/airgradient-go-main/production/Airgradient-GO_3.0*` (gerbers, drill, assembly BOM, positions).

## 5. Layout

The outline is identical. These parts moved; everything else is where v2 has it.

| Part | v2 (x, y) | v3 (x, y) | |
|---|---|---|---|
| LED1 | 111.11, 60.92 | 106.20, 71.90 | bottom side |
| LED2 | 124.67, 60.92 | 119.40, 60.92 | bottom side |
| LED3 | 139.63, 60.92 | 144.50, 60.92 | bottom side |
| LED4 | 152.80, 61.25 | 158.80, 71.90 | bottom side |
| U18 (GNSS) | 147.35, 65.70 | 146.35, 65.70 | |
| AE1 (antenna) | | 0.16 mm towards its feed pad | |
| C65 | 140.58, 70.06 top | 141.75, 68.75 bottom | |
| R43 | 126.94, 69.50 | 139.30, 69.50 | |
| R52 | 133.01, 122.52 | 127.42, 127.90 | |
| C45, L3 | | 0.25 mm and 0.4 mm | |

The four screw holes at the bottom corners keep their places and their 2.6 mm pads: (102.71, 126.88), (161.21, 126.88), (102.71, 132.38) and (161.21, 132.38). Their drill is 1.82 mm (2.5 mm in v2).

Coordinates are KiCad's, in mm. The board's top edge is at y 58.79 and its centre line at x 131.96, so the LEDs sit:

| | From the centre line | Below the top edge |
|---|---|---|
| LED1 | 25.76 mm left | 13.11 mm |
| LED2 | 12.56 mm left | 2.13 mm |
| LED3 | 12.54 mm right | 2.13 mm |
| LED4 | 26.84 mm right | 13.11 mm |

(seen from the top side; LED1 and LED4 lie in the pockets of the battery holder, LED4 with 0.14 mm between its pads and the holder on each side.)

Around the antenna, nothing but the feed and L4 is nearer than 2.0 mm to the antenna's pads on any layer (0.49 mm in v2).

The battery holder has a foot on the top side round its screw at (155.47, 71.15), which bears on the board. C86 stands upright between the GNSS module and L5, 0.40 mm clear of it; the module's nearest pad is 0.45 mm clear (R-V3-34, R-V3-18).

## 6. Open points

### What the review meeting of 2026-11-11 asked for

| Asked | State in v3 |
|---|---|
| The GPIO differences in a table, and all changes from v2 in one document, on GitHub | this document |
| A tag for v3 | not yet (see the top) |
| LEDs about 1 cm in from the top edge, behind the battery holder | all four are under the holder now (section 5): LED1 and LED4 13 mm below the top edge, LED2 and LED3 still 2 mm below it, under the holder's bar. The places come from a sketch made after the meeting and are not confirmed yet |
| The antenna turned along the top edge | not done. Its feed pad would sit 0.8 mm from the GNSS module's pads, and its manual asks for 2 mm to ground (R-V3-28) |
| CO circuit: keep the footprint, do not fit it, give it its own low-noise LDO and a filter at VREF | footprints kept, nothing fitted, LDO U24 added. No separate RC at the LMP91002's VREF: there is no room for two more parts at that pin, so VREF shares the LDO's rail with VDD (R-V3-26) |
| F1: a footprint that takes a resettable fuse, a one-time fuse or 0 Ω | the 1206 footprint takes all three. A 2.6 A resettable fuse is fitted; the part for production is not chosen |
| 2 A charge as a user setting | firmware. The hardware allows it (section 2); a full charge with logged temperatures has not been run |
| A smaller LED driver | no change, the LP5036 stays |

The I2C pull-ups are 100K by choice, for the current while a line is low. The design review of the same day asked for 2.2 to 3.3 kΩ; see section 2.

### To check on the first boards

- I2C at 100K pull-ups: rise time on a scope, and the clock it allows.
- Does the charger's 256 µs pulse on `EXP_INT` wake the chip from deep sleep?
- GNSS: C/N0 against a v2 unit, then tune L4, L5 and C86 with a network analyzer on a complete unit. The fitted values are those of the antenna maker's test board.
- LED4 and C86 against a real battery holder.
- A full 2 A charge with temperatures.
- SPI clock edges at the display and at the NAND with the 33 Ω resistors.
- The accelerometer answers at 0x18.
- S12 `EEPA`: polarity and timing.

## 7. Getting the two designs for a review

```
git clone https://github.com/Open-Air-Foundation/pcb-go.git
cd pcb-go
git checkout v2             # the old design
git checkout v3-reroute     # the new design
git rev-parse --short HEAD  # the commit you have: quote it with anything you find
git diff v2 v3-reroute --stat -- PCB/airgradient-go-main
```

Open `PCB/airgradient-go-main/airgradient-go-main.kicad_pro` in KiCad 10. What each design holds:

| File | What it is | v2 | v3 |
|---|---|---|---|
| `PCB/airgradient-go-main/airgradient-go-main.kicad_sch` | schematic, one sheet | yes | yes |
| `PCB/airgradient-go-main/airgradient-go-main.kicad_pcb` | board, 4 layers | yes | yes |
| `PCB/airgradient-go-main/BOM.csv` | schematic BOM | yes | yes |
| `PCB/airgradient-go-main/production/` | gerbers, drill, assembly BOM, positions | `Airgradient-GO_2.1*` (and the 2.0 prototype set) | `Airgradient-GO_3.0*` |
| `CHANGES-v3.md` | this document | | yes |
| `design/requirements.md` | every v3 change with its reason, its numbers and the datasheet pages | | yes |
| `design/airgradient-go-main/connections/*.csv` | the intended connections of the changed blocks, pin by pin | | yes |

For an AI review, give it this document and the two schematics. A netlist is easier for it to compare than the schematic file, and a PDF is easier to read; in each checkout:

```
kicad-cli sch export netlist --format kicadxml -o netlist.xml PCB/airgradient-go-main/airgradient-go-main.kicad_sch
kicad-cli sch export pdf -o schematic.pdf PCB/airgradient-go-main/airgradient-go-main.kicad_sch
```

(`kicad-cli` comes with KiCad; on macOS it is `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.)

Design checks on the head of `v3-reroute`: electrical rule check 276 messages, none of them a wrong connection; layout check 0 unconnected, schematic and board agree; its errors are all in `v2` as well (the battery holder's outline drawing, the holes of the USB connector, one via under the fuel gauge, the battery contacts at the board edge, two pairs of part outlines that overlap).
