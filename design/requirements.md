# GO main v3 (from v2.1-xtal32k): change requirements

Status: v3 requirements approved by Tanapat 2026-11-03 (EXP_INT on an LP GPIO 0–6: IO1, not IO26; R61 100K pull-up added). Schematic drawn and checked, not committed; layout next. Everything below the v3 section is the v2.1-xtal32k history (layout done 2026-10-21); where a v3 item supersedes it, the v3 item wins.

Scope: an engineering change on top of v2.1-xtal32k (branch `v3`, from f1cdbac). The rest of the GO main board is hand-drawn and out of scope; only the items below change.

## v3 changes (Tanapat, 2026-11-03)
Why: touch (CAP1203 `INT` on expander P4) and motion (LIS2DH12 INT1 = `ACC_INT` on P5) must be able to tell the ESP32 that something happened, including from deep sleep, while both stay on the expander. Sam asked for the NAND CS on a native GPIO so the NAND/SDSPI drivers need no fork (AGFW-867, meeting 2026-11-02). The 32 kHz crystal is no longer needed.

| ID | Requirement | Number |
|---|---|---|
| R-V3-01 | Remove the 32 kHz crystal: Y1, C76, C77 and nets `XTAL_32K_P/N`. Supersedes R-XT-01. Firmware goes back to `CONFIG_RTC_CLK_SRC_INT_RC=y` | — |
| R-V3-02 | `EXP_INT` (U17 TCA6408A `~INT`, open drain) moves from U4 IO7 (pad 19) to U4 IO1 (pad 17, LP_GPIO1). Touch and ACC_INT stay on P4/P5 of the expander. IO1 can wake the chip from deep sleep; IO7 could not. Supersedes the IO7 half of R-INT-01 and R-INT-04 | deep-sleep GPIO wake = GPIO0–6 (ESP-IDF v5.5.2 `soc/esp32c5/include/soc/soc_caps.h:231`); IO1 = GPIO1/LP_GPIO1 (MINI-1 v1.3 Table 3-1, pad 17) |
| R-V3-03 | `NAND CS` (U1 `/CS`, U2 `DATA3`, R3 100K pull-up) moves from U17 P2 to U4 IO7 (pad 19). U17 P2 gets an NC flag. Not IO26 (the 2026-11-02 pin plan): on B.Cu, pads 31–34 are walled by the QON, ePaper BUSY, ePaper D/C and MISO runs, while pad 19 sits 2 mm south of the existing NAND CS trunk | IO7 = JTAG-source strap, floating by default and ignored while EFUSE_JTAG_SEL_ENABLE = 0 (MINI-1 v1.3 Table 4-1 p16, Table 4-7 p20); R3 holds CS high at reset, so the NAND stays deselected during boot |
| R-V3-04 | U4 IO0 (pad 16) is left unused (label `IO0`, house style for spare pins): the one spare LP GPIO, e.g. for `CHG_INT` later if USB plug-in should wake the chip from deep sleep | GPIO0/LP_GPIO0 (MINI-1 v1.3 Table 3-1, pad 16) |
| R-V3-05 | Unchanged: `CHG_INT` on IO15 (internal pull-up, R-INT-03 still holds for it), ePaper CS on IO6, LP I²C on IO2/IO3, WD_RST on IO4, ePaper D/C and RES where they are | — |
| R-V3-06 | R61 100K pull-up from `EXP_INT` to +3.1V, placed next to U4 pad 17 with one via to the In2 +3.1V plane (the freed crystal area). Supersedes R-INT-03 for EXP_INT. Why: EXP_INT is now the deep-sleep wake source, and an internal pull-up only exists while firmware keeps it (RTC_PERIPH on, or HOLD); the expander's INT is open drain. 100K like R3/R39/R60 (Tanapat, 2026-11-03) | TCA6408A SCPS192E Table 5-1 p3 ("Connect to VCCI through a pull-up resistor"), §8.3.3 p20; ESP-IDF v5.5.4 `esp_sleep.h`, `esp_sleep_enable_ext1_wakeup_io` note ("Internal pullups and pulldowns don't work when RTC peripherals are shut down… external resistors need to be added"); 3.1 V / 100K = 31 µA only while INT is low; rise ≈ 100K × 20 pF = 2 µs |

Pin budget (only the pins that change):

| Pin | v2.1-xtal32k | v3 |
|---|---|---|
| U4 pad 16, IO0 (LP) | `XTAL_32K_P` | `IO0`, unused (spare LP GPIO) |
| U4 pad 17, IO1 (LP) | `XTAL_32K_N` | `EXP_INT` |
| U4 pad 19, IO7 | `EXP_INT` | `NAND CS` |
| U17 pin 4, P2 | `NAND CS` | NC |
| R61 (new) | — | 100K, `EXP_INT` → +3.1V |

Checked on the ESP32-C5 (2026-11-03, ESP-IDF v5.5.4 73550728): deep-sleep GPIO wake is GPIO0–6 (`soc_caps.h:231`, 7 LP IOs at `:248`); EXT1 is supported with a per-pin level (`:639–640`); `esp_sleep_is_valid_wakeup_gpio` checks `RTC_GPIO_IS_VALID_GPIO` (`sleep_modes.c:1885`); GPIO1 is a plain GPIO unless `RTC_CLK_SRC_EXT_CRYS` is chosen, and the default is `INT_RC` (`esp_hw_support/port/esp32c5/Kconfig.rtc:3`). GO firmware already wakes from deep sleep through EXT1 ANY_LOW on GPIO5, the power button (`go_power.cpp:839–850`, `board_config.h:110`); the boot button on GPIO28 is left out because it is not an LP pin.

Interrupt sources behind the expander (2026-11-03):

| Source | Output | Held or pulse | Pull-up |
|---|---|---|---|
| CAP1203 `ALERT#` → P4 | open drain, active low (DS00001572B Table 1-1 p4) | Held until the host clears the INT bit in Main Control (§4.8 p17, p22). Fires on touch and, by default, on release (`INT_REL_n = 0`, Config 2 44h, p27) | R38 100K to VCC on the touch board |
| LIS2DH12 `INT1` → P5 | push-pull, active high by default (DocID025056 Rev 6 p21; `INT_POLARITY`, CTRL_REG6, p38) | Pulse by default: high only while the condition holds. Held when `LIR_INT1 = 1` (CTRL_REG5 24h bit 3, §8.10 p38) until `INT1_SRC` (31h) is read (§8.20 p42). Click has its own latch, `LIR_Click` (CLICK_THS 3Ah bit 7, §8.29 p47), cleared by reading `CLICK_SRC` (39h) | not needed |

The TCA6408A clears `~INT` when the port is read or when an input returns to its old level (SCPS192E §8.3.3 p20). A pulse that ends before the ESP32 reads the port therefore leaves no trace, which is why every source must be latched.

Firmware impact (v3):
- **Pins.** `EXP_INT = GPIO1`, `NAND_CS = GPIO7` (native GPIO; the NAND/SDSPI drivers use their stock CS handling, no fork). `CHG_INT` stays GPIO15.
- **RTC clock.** Back to `CONFIG_RTC_CLK_SRC_INT_RC=y`; the v2.1-xtal32k setting `RTC_CLK_SRC_EXT_CRYS` must not be used on v3.
- **Deep-sleep wake.** Add GPIO1 to the EXT1 mask next to GPIO5: `wake_mask |= 1ULL << 1`, `ESP_EXT1_WAKEUP_ANY_LOW`. Check the return value of `esp_sleep_enable_ext1_wakeup`: a non-LP pin in the mask returns `ESP_ERR_INVALID_ARG` and arms nothing, the power button included. Find the source with `esp_sleep_get_ext1_wakeup_status()`.
- **Pull-up.** R61 is external, so the internal pull-up on GPIO1 can stay off (it would only add current while INT is low). GPIO15 keeps its internal pull-up.
- **LIS2DH12.** Set `LIR_INT1 = 1` (CTRL_REG5 bit 3) for motion wake through IA1; if click is used on INT1, set `LIR_Click = 1` (CLICK_THS bit 7). Keep the sensor in a low-power detect mode during deep sleep, or nothing can raise INT1.
- **CAP1203.** Leave the touch IC sampling in standby during deep sleep (it is the only thing that can raise `ALERT#`). Decide whether release events are wanted; `INT_REL_n = 1` turns them off and halves the wake-ups per touch.
- **Wake sequence.** (1) read the TCA6408A input port to see the source (P4 low = touch, P5 high = motion); (2) clear it at the source: write 0 to the CAP1203 INT bit, or read `INT1_SRC`/`CLICK_SRC`; (3) read the port again, because the source letting go is another input change that pulls `~INT` low; (4) only then enter sleep. If `~INT` is still low when sleep starts, EXT1 wakes the chip at once.
- **Touch and ACC_INT polling** can go; both arrive through `EXP_INT`.

Blocks (v3):
1. Remove block `rtc32k` with `sch_writer.py remove` (Y1, C76, C77, their wires and labels, the frame and its note, and the U17 P7 NC flag it created; that flag comes back as a hand edit).
2. Hand edits (intent `connections/v3_pins.csv`): U4 pin 16 label `XTAL_32K_P` → `IO0`; pin 17 `XTAL_32K_N` → `EXP_INT`; pin 19 `EXP_INT` → `NAND CS`; U17 pin 4 label `NAND CS` → NC flag; U17 pin 10 (P7) NC flag back.
3. `int_lines` frame note updated to the v3 pins.
4. Hand edit in CONTROLLER (Tanapat, 2026-11-03): R61 100K added to the pull-up row at (237.49, 36.83), 12.7 mm right of R38, same style (+3.1V on top, `EXP_INT` label below). The old RTC 32K frame area is empty.

Schematic checks (2026-11-03): `sch_lint` 0 error / 0 warning on the INT LINE block; `net_diff` 29 pins, 0 error; ERC 268 messages = baseline 267 + one `isolated_pin_label` for the spare `IO0` label (house style), errors 14 = baseline.

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

## Interrupt lines (approved by Tanapat 2026-10-20, split 2026-10-21)
Why: on v2.1 the charger `~INT` (U5 pin 11, NC flag) and the expander `~INT` (U17 pin 11, floating) reach nothing, so charger events, touch (`INT` on P4) and `ACC_INT` (P5) can only be polled. The free ESP32 pins are IO7 and IO15; LP GPIO0–6 are all taken.

| ID | Requirement | Number |
|---|---|---|
| R-INT-01 | U5 BQ25628 `~INT` → net `CHG_INT` → U4 IO15 (pad 26); U17 TCA6408A `~INT` → net `EXP_INT` → U4 IO7 (pad 19). Both are open drain. Touch (`INT` on P4) and `ACC_INT` (P5) stop being polled, and charger events interrupt the MCU. (2026-10-20 they shared one wired-OR net `I2C_INT` on IO7; Tanapat asked for separate lines on 2026-10-21, so each edge names its source.) | BQ25628 SLUSEG4C pin table, §8.3.8.3 p31; TCA6408A SCPS192E §8.3.3 |
| R-INT-02 | Firmware: on a falling edge of IO15, read `Charger_Flag_X` (latched until read); on a falling edge of IO7, read the TCA6408A input port, which releases the line | SLUSEG4C §8.3.8.1; SCPS192E §8.3.3 |
| R-INT-03 | No external pull-ups: firmware enables the internal pull-ups (~45 kΩ) on GPIO15 and GPIO7. Rise time ≈ 45 kΩ × ~20 pF ≈ 1 µs, far shorter than the charger's 256 µs pulse; the expander holds INT low until read. (TI suggests 10 kΩ; no 0402 spot with +3.1V nearby at either end) | SLUSEG4C §8.3.8.3; SCPS192E §8.3.3 |
| R-INT-04 | Neither IO15 nor IO7 wakes the chip from deep sleep (deep-sleep GPIO wake = GPIO0–6 only); light sleep and active only. IO7 is the JTAG-source strap, ignored while EFUSE_JTAG_SEL_ENABLE = 0 | ESP-IDF v5.5.2 `soc/esp32c5/include/soc/soc_caps.h:231`; MINI-1 v1.3 Table 4-7 p20 |

## PCB constraints (Tanapat, 2026-10-19)
Do not move: all LEDs, FPC1, BT1, U16, U11, U10, NTCx, SPS30, SWx, U12, USB-C (USB1), CN1, CN2.

## Firmware impact (not in this repo)
- `PIN_DISPLAY_CS` becomes GPIO6 on this board variant (V1 keeps GPIO0).
- `CONFIG_RTC_CLK_SRC_EXT_CRYS=y` on boards with the crystal.
- `PIN_I2C_SDA = GPIO2`, `PIN_I2C_SCL = GPIO3`, `PIN_EXT_WDT = GPIO4` (was GPIO2). `PIN_ACCEL_INT = GPIO3` is a V1 pin and must be variant-guarded, or it collides with SCL.
- `CHG_INT = GPIO15`, `EXP_INT = GPIO7`: inputs with the internal pull-up on (keep it in light sleep), falling edge. On GPIO15 read `Charger_Flag_X`, on GPIO7 the TCA6408A input port; set the BQ25628 INT masks. Touch and ACC_INT polling can go.

## Blocks
1. `rtc32k`: Y1 + C76 + C77, plus an NC flag on U17 P7.
2. Hand edits (not generated): U4 pin 16 label `ePaper CS` → `XTAL_32K_P`; U4 pin 17 label `IO1` → `XTAL_32K_N`.
3. LP I²C hand edits (intent `connections/lp_i2c.csv`): U4 pin 6 `WD_RST` → `SDA`, pin 7 `IO3` → `SCL`, pin 8 `IO4` → `WD_RST`, pin 10 `SCL` → `ePaper CS`, pin 19 `SDA` → `IO7`.
4. `int_lines`: notes-only frame (INT LINE). Hand edits (intent `connections/int_lines.csv`): `CHG_INT` labels on U5 pin 11 (NC flag removed) and U4 pin 26 (was `IO15`); `EXP_INT` labels on U17 pin 11 and U4 pin 19 (was `IO7`); C63 field text moved below the RESET wire.

## Layout (pcb-design, 2026-10-19)
Status: layout done. DRC 230 = baseline (0 new), 0 unconnected, parity 0. Route groups in `design/airgradient-go-main/layout/route.json`, checks in `constraints.json`.

LP I²C (same day): groups `lp-i2c-sda`, `lp-i2c-scl` (pads 6/7 into the pocket under U4, B.Cu under pads 7–9, F.Cu north of pads 10–15 to the bus vias at x 120.0; 2 vias each), `wd-rst-io4` (old CS path from pad 8, bend raised to y 121.2 to make room for the SDA/SCL vias, 1 via onto the old WD_RST trunk) and `cs-io6` (1 via under pad 10, B.Cu south of the pad row and up the west side; the old CS via at the trunk is gone). Net +4 vias. DRC still 230 = baseline, 0 unconnected, parity 0; no new bends, junctions, dangling ends or tiny segments; pcb_check same as before except RT-07 (19 → 18 nets under U4).

INT lines (2026-10-20 wired-OR, split 2026-10-21): nets `CHG_INT` (49.8 mm, 2 vias) and `EXP_INT` (15.6 mm, 4 vias), vias 0.5/0.3, all locked route groups.
- Expander, group `exp-int`: U17 pin 11 → U4 pad 19, 15.6 mm, 4 vias, `pcb_path --routed` at 0.12 mm with Y1 kept out (no path at 0.15). PRTRG (B.Cu) dips 0.24 mm under the first via, group `prtrg-dip` (two old segments deleted). B.Cu passes under C76 and along the module edge west of pads 16–18 (In1 GND between); the last F.Cu run enters pad 19 from the pocket under U4.
- U5 escape, groups `u5-i2c-escape` + `int-u5-escape`: the SDA escape via moved from (24.25,39.81) to (24.20,39.62), under the SCL via in the 0.95 mm column between U5's east pads and L1 (old F.Cu stub, via and In2 jog deleted). Pin 11 leaves at 0.15 mm width between pad 10's corner and the SDA via to a via at (24.20,40.28), 0.25 mm from L1's SYS pad; the via crosses the SYS pour and the In2 SW island as antipads only.
- Charger, group `int-chg-west`: every way south from U5 is walled in on all three routing layers (F.Cu SYS pour + C4/C11, In2 SW island + Pack+ V, B.Cu TS pair + BAT+); a zone-aware 3-layer search (scratch `pcb_path3.py`) found no crossing between x 16 and 34. B.Cu runs north-west round U5 (≈2.4 mm under the In2 SW island: ~0.09 pF, ~45 mV estimated spike) and south under the module body 3 mm east of the antenna keepout (x 6.3). L1 + 0.15/0.3 mm kept out (PWR-22).
- Split 2026-10-21: IO15's F.Cu pocket (ePaper D/C via, BUSY, pads 22–27) is closed on B.Cu by the UART loop, so the via sits under pads 23–25, where B.Cu is free between UART TX (y 55.71) and NAND CS (y 58.32). The charger B.Cu turns east under the module at y 55.48 (0.48 mm north of the pad-61 GND vias, south of the UART diagonals), passes under the UART TX run at y 56.23 to one via at (19.05,56.23), and F.Cu enters pad 26 from the west; `pcb_path3` found the same corridor at 0.15 mm. The 2026-10-20 tail into the expander via (F.Cu and In2 hops at y 61.9, 2.1 mm across +3.1V, 2 vias) is gone, so the INT lines total 65 mm and 6 vias instead of 68 mm and 7.
- Accepted by Tanapat 2026-10-20: 0.15 mm neck and 0.12 mm clearance at the U5 escape, via in the SYS pour, internal pull-ups instead of TI's 10 kΩ.
- Zones refilled and saved. DRC 230 = baseline, 0 unconnected, parity 0. `pcb_check` vs 84c3d4d: same FAIL/WARN counts; RT-05 lists CHG_INT 3.3× (50 mm), RT-07 19 nets under U4 (CHG_INT and EXP_INT in place of I2C_INT); RT-09 minimum width stays 0.15 (= DFM-01 floor). RT-03 not run: `pcb_check` aborts in `GetFilledPolysList(z.GetLayer())` on GO's multi-layer GND zone under KiCad 10.0.1, on 1d977c7 too. `pcb_import` re-adds the TPs (on_board yes, DNP in the schematic); deleted again, since this board has never carried them.

### Accepted
- **RF-22 (by analogy for the 32 kHz crystal):** the existing I²C on B.Cu runs under Y1 (SCL) and C77 (SCL, SDA). The solid GND plane (In1) lies between them and the crystal, and I²C edges are slow. Accepted by Tanapat 2026-10-19 instead of re-routing SDA/SCL under U4.
- **ePaper CS at 0.2 mm** (net class 0.25): first the route from IO4 under the module, now from IO6 between ePaper RES and D/C on B.Cu; neither has a 0.25 path. 0.2 is above the 0.15 floor (RT-09).
- MOSI passes 0.53 mm above C77 (centre-to-centre ≈ 0.76 mm ≥ 3W, HS-30).
