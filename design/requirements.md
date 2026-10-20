# GO main v2.1-xtal32k: change requirements

Status: layout done (crystal + LP I²C). Requirements and part approved by Tanapat 2026-10-19. Interrupt line (R-INT, expander only): schematic done, layout in progress 2026-10-20.

Scope: an engineering change on top of v2.1 (branch `v2.1-xtal32k`, from 426c645). The rest of the GO main board is hand-drawn and out of scope; only the items below change.

## Why
Battery life. The ESP32-C5 currently runs its RTC from the internal RC (`CONFIG_RTC_CLK_SRC_INT_RC=y`). A 32.768 kHz crystal gives BLE modem sleep and light sleep an accurate sleep clock (Sam's power research, `go/feat/pm`, 2026-10-17).

## Requirements
| ID | Requirement | Number |
|---|---|---|
| R-XT-01 | 32.768 kHz crystal on U4 pin 16 (IO0 = XTAL_32K_P) and pin 17 (IO1 = XTAL_32K_N), load caps to PGND, no series or parallel resistors | ESR ≤ 70 kΩ (ESP32-C5-MINI-1 Fig 9-1 p49) |
| R-XT-02 | ePaper CS moves from U4 IO0 to U4 IO6 (pad 10). R39 100K pull-up stays. (First tried TCA6408A P7: the route from U17 needed 5 vias through EN_PM1/BUZZ/PRTRG. Then IO4 (pad 8), until the LP I²C change gave IO4 to WD_RST; Tanapat chose the swap on 2026-10-19.) | — |
| R-XT-03 | Nothing else changes for the crystal; IO15 stays free. (I²C moves later, see R-LP-01.) | — |

## LP I²C (Sam's offline-mode proposal, approved by Tanapat 2026-10-19)
Why: in offline mode the LP core reads the sensors while the HP core stays in deep sleep, and wakes it only to flush a 16-sample RTC-memory cache. The C5 LP I²C sits on fixed LP IO MUX pads (ESP-IDF v5.5.2 `hal/esp32c5/include/hal/i2c_ll.h:88-89`; the C5 has no LP GPIO matrix), and v2.1 put the bus on IO6/IO7, where IO7 is not even an LP pin.

| ID | Requirement | Number |
|---|---|---|
| R-LP-01 | I²C SDA on U4 IO2 (pad 6), SCL on U4 IO3 (pad 7) | LP_I2C_SDA = GPIO2, LP_I2C_SCL = GPIO3 |
| R-LP-02 | TPL5010 DONE (`WD_RST`) on an LP GPIO, so the LP core can feed the watchdog while the HP core sleeps longer than the watchdog period: U4 IO4 (pad 8). IO6 would also be LP, but its route to U7 needed 5 vias; IO4 reuses the old CS path with 1 via | R25 = 51 kΩ, roughly 7–8 min (TPL5010 resistor table) |
| R-LP-03 | IO7 (pad 19) is left unconnected (superseded 2026-10-20 by R-INT-01: IO7 = EXP_INT) | JTAG-source strap, ignored while EFUSE_JTAG_SEL_ENABLE = 0 (MINI-1 v1.3 Table 4-7 p20) |

Straps after the move: GPIO2 = MTMS and GPIO3 = MTDI (MINI-1 v1.3 Table 4-1 p16) are both held high at reset by R26/R30 10K. MTDI only selects the SDIO edge (Table 4-4 p18), which this board does not use; MTMS has no strap function listed in the module datasheet.

## Interrupt lines (approved by Tanapat 2026-10-20)
Why: on v2.1 the charger `~INT` (U5 pin 11, NC flag) and the expander `~INT` (U17 pin 11, floating) reach nothing, so charger events, touch (`INT` on P4) and `ACC_INT` (P5) can only be polled. The free ESP32 pins are IO7 and IO15; LP GPIO0–6 are all taken.

| ID | Requirement | Number |
|---|---|---|
| R-INT-01 | U17 TCA6408A `~INT` → U4 IO7 (pad 19), net `EXP_INT`, so touch (`INT` on P4) and `ACC_INT` (P5) stop being polled | TCA6408A SCPS192E §8.3.3 |
| R-INT-02 | U5 BQ25628 `~INT` stays NC. At layout pin 11 was walled in: pad 12 SDA and its escape via, pad 10 STAT, L1's SYS pad at x ≥ 24.70 and the SYS pour on F.Cu, and the SW island on In2 under U5. Freeing it means re-doing the U5 I²C escape inside the charger's SW/SYS copper. Firmware reads the latched `Charger_Flag_X` registers on wake or on a timer instead. (Drawn first as two lines, CHG_INT → IO15 + EXP_INT → IO7, then as a wired-OR onto IO7; both dropped at layout, Tanapat 2026-10-20.) | BQ25628 SLUSEG4C §8.3.8.1 (flags latch until read) |
| R-INT-03 | No external pull-up: firmware enables the GPIO7 internal pull-up. The TCA6408A holds INT low until the input port is read, so the weak pull-up's rise time does not matter | SCPS192E §8.3.3 |
| R-INT-04 | IO7 does not wake the chip from deep sleep (deep-sleep GPIO wake = GPIO0–6 only); light sleep and active only. IO7 is the JTAG-source strap, ignored while EFUSE_JTAG_SEL_ENABLE = 0 | ESP-IDF v5.5.2 `soc/esp32c5/include/soc/soc_caps.h:231`; MINI-1 v1.3 Table 4-7 p20 |

## PCB constraints (Tanapat, 2026-10-19)
Do not move: all LEDs, FPC1, BT1, U16, U11, U10, NTCx, SPS30, SWx, U12, USB-C (USB1), CN1, CN2.

## Firmware impact (not in this repo)
- `PIN_DISPLAY_CS` becomes GPIO6 on this board variant (V1 keeps GPIO0).
- `CONFIG_RTC_CLK_SRC_EXT_CRYS=y` on boards with the crystal.
- `PIN_I2C_SDA = GPIO2`, `PIN_I2C_SCL = GPIO3`, `PIN_EXT_WDT = GPIO4` (was GPIO2). `PIN_ACCEL_INT = GPIO3` is a V1 pin and must be variant-guarded, or it collides with SCL.
- `EXP_INT = GPIO7`: input with the internal pull-up on (keep it in light sleep), falling edge, then read the TCA6408A input port (clears its INT). Touch and ACC_INT polling can go. Charger INT is not wired: read `Charger_Flag_X` on wake or on a timer. GPIO15 stays unconnected.

## Blocks
1. `rtc32k`: Y1 + C76 + C77, plus an NC flag on U17 P7.
2. Hand edits (not generated): U4 pin 16 label `ePaper CS` → `XTAL_32K_P`; U4 pin 17 label `IO1` → `XTAL_32K_N`.
3. LP I²C hand edits (intent `connections/lp_i2c.csv`): U4 pin 6 `WD_RST` → `SDA`, pin 7 `IO3` → `SCL`, pin 8 `IO4` → `WD_RST`, pin 10 `SCL` → `ePaper CS`, pin 19 `SDA` → `IO7`.
4. `int_lines`: notes-only frame (INT LINE). Hand edits (intent `connections/int_lines.csv`): U4 pin 19 label `IO7` → `EXP_INT`, `EXP_INT` label on U17 pin 11, C63 field text moved below the RESET wire. U5 pin 11 keeps its NC flag; U4 pin 26 keeps its `IO15` label.

## Layout (pcb-design, 2026-10-19)
Status: layout done. DRC 230 = baseline (0 new), 0 unconnected, parity 0. Route groups in `design/airgradient-go-main/layout/route.json`, checks in `constraints.json`.

LP I²C (same day): groups `lp-i2c-sda`, `lp-i2c-scl` (pads 6/7 into the pocket under U4, B.Cu under pads 7–9, F.Cu north of pads 10–15 to the bus vias at x 120.0; 2 vias each), `wd-rst-io4` (old CS path from pad 8, bend raised to y 121.2 to make room for the SDA/SCL vias, 1 via onto the old WD_RST trunk) and `cs-io6` (1 via under pad 10, B.Cu south of the pad row and up the west side; the old CS via at the trunk is gone). Net +4 vias. DRC still 230 = baseline, 0 unconnected, parity 0; no new bends, junctions, dangling ends or tiny segments; pcb_check same as before except RT-07 (19 → 18 nets under U4).

### Accepted
- **RF-22 (by analogy for the 32 kHz crystal):** the existing I²C on B.Cu runs under Y1 (SCL) and C77 (SCL, SDA). The solid GND plane (In1) lies between them and the crystal, and I²C edges are slow. Accepted by Tanapat 2026-10-19 instead of re-routing SDA/SCL under U4.
- **ePaper CS at 0.2 mm** (net class 0.25): first the route from IO4 under the module, now from IO6 between ePaper RES and D/C on B.Cu; neither has a 0.25 path. 0.2 is above the 0.15 floor (RT-09).
- MOSI passes 0.53 mm above C77 (centre-to-centre ≈ 0.76 mm ≥ 3W, HS-30).
