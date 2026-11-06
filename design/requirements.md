# GO main v3 (from v2.1-xtal32k): change requirements

Status: v3 requirements approved by Tanapat 2026-11-03 (EXP_INT on an LP GPIO 0–6: IO1, not IO26; R61 100K pull-up added). Schematic f7d4295, layout a2e751b. 2026-11-04: R-V3-07 added (S12 EEPA on IO9, ePaper RES to expander P2) and R-V3-08 (CHG_INT to LP GPIO0 with R62 pull-up); R-V3-09 (C78 BAT-/GND bridge). 2026-11-05: R-V3-10 (SCLK series R). 2026-11-06: R-V3-13 (rail moved to 3.31 V and net renamed `+3.3V`; `+3.1V` in older text below is this same net). Layout: RES, CHG_INT, R62, GND return vias, C78 and R63/R64 done; EEPA open. Everything below the v3 section is the v2.1-xtal32k history (layout done 2026-10-21); where a v3 item supersedes it, the v3 item wins.

Scope: an engineering change on top of v2.1-xtal32k (branch `v3`, from f1cdbac). The rest of the GO main board is hand-drawn and out of scope; only the items below change.

## v3 changes (Tanapat, 2026-11-03)
Why: touch (CAP1203 `INT` on expander P4) and motion (LIS2DH12 INT1 = `ACC_INT` on P5) must be able to tell the ESP32 that something happened, including from deep sleep, while both stay on the expander. Sam asked for the NAND CS on a native GPIO so the NAND/SDSPI drivers need no fork (AGFW-867, meeting 2026-11-02). The 32 kHz crystal is no longer needed.

| ID | Requirement | Number |
|---|---|---|
| R-V3-01 | Remove the 32 kHz crystal: Y1, C76, C77 and nets `XTAL_32K_P/N`. Supersedes R-XT-01. Firmware goes back to `CONFIG_RTC_CLK_SRC_INT_RC=y` | — |
| R-V3-02 | `EXP_INT` (U17 TCA6408A `~INT`, open drain) moves from U4 IO7 (pad 19) to U4 IO1 (pad 17, LP_GPIO1). Touch and ACC_INT stay on P4/P5 of the expander. IO1 can wake the chip from deep sleep; IO7 could not. Supersedes the IO7 half of R-INT-01 and R-INT-04 | deep-sleep GPIO wake = GPIO0–6 (ESP-IDF v5.5.2 `soc/esp32c5/include/soc/soc_caps.h:231`); IO1 = GPIO1/LP_GPIO1 (MINI-1 v1.3 Table 3-1, pad 17) |
| R-V3-03 | `NAND CS` (U1 `/CS`, U2 `DATA3`, R3 100K pull-up) moves from U17 P2 to U4 IO7 (pad 19). U17 P2 gets an NC flag. Not IO26 (the 2026-11-02 pin plan): on B.Cu, pads 31–34 are walled by the QON, ePaper BUSY, ePaper D/C and MISO runs, while pad 19 sits 2 mm south of the existing NAND CS trunk | IO7 = JTAG-source strap, floating by default and ignored while EFUSE_JTAG_SEL_ENABLE = 0 (MINI-1 v1.3 Table 4-1 p16, Table 4-7 p20); R3 holds CS high at reset, so the NAND stays deselected during boot |
| R-V3-04 | ~~U4 IO0 (pad 16) is left unused~~ superseded by R-V3-08: IO0 now carries `CHG_INT`, so no LP GPIO is spare | GPIO0/LP_GPIO0 (MINI-1 v1.3 Table 3-1, pad 16) |
| R-V3-05 | Unchanged: ePaper CS on IO6, LP I²C on IO2/IO3, WD_RST on IO4, ePaper D/C and RES where they are | — |
| R-V3-06 | R61 100K pull-up from `EXP_INT` to +3.1V, placed next to U4 pad 17 with one via to the In2 +3.1V plane (the freed crystal area). Supersedes R-INT-03 for EXP_INT. Why: EXP_INT is now the deep-sleep wake source, and an internal pull-up only exists while firmware keeps it (RTC_PERIPH on, or HOLD); the expander's INT is open drain. 100K like R3/R39/R60 (Tanapat, 2026-11-03) | TCA6408A SCPS192E Table 5-1 p3 ("Connect to VCCI through a pull-up resistor"), §8.3.3 p20; ESP-IDF v5.5.4 `esp_sleep.h`, `esp_sleep_enable_ext1_wakeup_io` note ("Internal pullups and pulldowns don't work when RTC peripherals are shut down… external resistors need to be added"); 3.1 V / 100K = 31 µA only while INT is low; rise ≈ 100K × 20 pF = 2 µs |
| R-V3-07 | S12 rev 2 pin 6 `EEPA` (EEPROM write in progress, PCN16844) goes straight to U4 IO9 (pad 21) so firmware can hold off cutting S12 power during a write (AGFW-797). IO9 is freed by moving `ePaper RES` to expander U17 P2 (output; reset timing is not critical). Not on the expander: the TCA6408A has no interrupt mask, every input change pulls `~INT` = `EXP_INT` (the deep-sleep wake) low, and the S12 keeps running in power saving, so each EEPROM write would wake the chip. IO0 stays the spare LP GPIO (Tanapat, 2026-11-04; later the same day IO0 went to `CHG_INT`, R-V3-08) | PCN16844 item 1 (no electrical spec for EEPA: polarity and push-pull/open-drain unknown, ask Senseair); S12 datasheet PSP15871 pin table (pin 6 = DE output on rev 1, pin 7 RDYN open drain); TCA6408A SCPS192E Table 8-4 p25 (4 registers, no mask), §8.3.3 p20 (any input edge interrupts; outputs cannot); IO9 is not a C5 strap (straps: GPIO26/27/28, GPIO7) |
| R-V3-08 | `CHG_INT` (U5 BQ25628 `~INT`, open drain) moves from U4 IO15 (pad 26) to U4 IO0 (pad 16, LP_GPIO0), the last free LP GPIO, so a charger event (USB plugged in or pulled, charge done, fault) can wake the chip from deep sleep; on IO15 the chip slept through them. R62 100K pull-up to +3.1V next to pad 16, same reason and part as R61 (R-V3-06). IO15 becomes a spare non-LP GPIO (label `IO15`). Supersedes R-INT-01/03/04 for `CHG_INT` (Tanapat, 2026-11-04) | BQ25628 SLUSEG4C §8.3.8.3 p31 (INT = 256 µs low pulse, open drain), §8.3.8.1 (flags latch until read); GPIO0/LP_GPIO0 (MINI-1 v1.3 Table 3-1, pad 16); deep-sleep wake GPIO0–6 (`soc_caps.h:231`); ESP-IDF v5.5.4 `esp_sleep.h` note on internal pulls in deep sleep (as R-V3-06) |
| R-V3-09 | C78 0.1 µF 0402 (same part as C16) from `BAT-` to GND: an HF bridge across the In1 split between the gauge's BAT- island and the GND plane, where SCLK (10 MHz NAND / 4 MHz ePaper, shared bus) crosses it at local (8.8, 44.1). DC still joins only at NT1 (13.4 mm away), so the gauge ground stays single-point. **Placed 2026-11-05 (Tanapat):** abs (108.31, 101.85), BAT- via (108.68, 101.74), GND via (108.55, 103.13). Route group `c78-bundle` takes SCLK across the gap at abs x 109.108; SCLK, D/C and BUSY are 0.15 mm over the whole rebuilt run (Tanapat, 2026-11-05), with 0.1005 mm clearance between the BAT- via and R8.1. The In2 reroutes that cleared these vias split +3.1V on In2, so group `p31-bridge` joins the split-off part (LED1, LED2, CN2.1, R39, R40) to the main plane on F.Cu. Also found: In1 has no fill at all over x 6–19, y 24–32 and x 0.5–6, y 38–44 (inside the BAT- zone outline, its fill only keeps the connected part), so SCLK changes reference again further north (Tanapat, 2026-11-04) | Ott, EMC Engineering, ch. 16 (split-plane stitching capacitors); local coords = abs − (100.51, 58.79) |
| R-V3-10 | SCLK from U4 IO23 splits at the pad into two branches, so one 33 Ω series R per branch: R63 to `ePaper SCLK` (FPC1.13, 78.7 mm) and R64 to `NAND SCLK` (U1.6, U2.3, R51). 58 Ω branch Z0 less R_drv 33 Ω parallel with the other branch and its R gives 34 Ω. Part 0402WGF330JTCE (C25105). R63 sits about 4 mm and R64 about 5 mm of track from pad 31. In the ngspice model 33/33 Ω gave no overshoot at R_drv 17 or 33 Ω and t_r 0.5–2 ns; without R the peak was 3.94 V at t_r 1 ns. t_r and R_drv are estimates, so check on the prototype and fit 0 Ω if the edge is slow enough (Tanapat, 2026-11-05) | Simulation in session 2026-11-04/05; ESP32-C5-MINI-1 datasheet v1.4 Table 6-3 (16.5 Ω at PAD_DRIVER = 3); default 20 mA drive from the chip datasheet |
| R-V3-11 | Branch `v3-reroute`: placement unchanged, every track, via, zone and board keepout deleted and redrawn. In1 is solid GND with no signal on it; the 17 x 22 mm In1 BAT- island becomes a 4.5 x 4 mm gauge island plus a strip to NT1, and battery return moves to In2. ePaper SCLK runs R63 to FPC1 on F.Cu over In1 with one via at the FPC. Power clusters, NAND SPI and UART keep the v3 geometry; `reroute_build.py` holds the plan, `reroute_fixes.py` the review fixes | Return-path review 2026-11-05; RT rules; PWR-52 (two vias into R8.1) |
| R-V3-12 | MOSI from U4 IO25 gets one 33 Ω series R per branch, as SCLK: R65 to `ePaper MOSI` (FPC1.14) and R66 to `NAND MOSI` (U1.5, U2.5, R52). MISO gets R67 33 Ω between `NAND MISO` (U1.2, U2.6, R50) and `MISO` (U4 IO24). Part 0402WGF330JTCE (C25105). R65 and R66 sit on B.Cu at (119.2, 105.2) and (121.2, 106.06), 6.3 and 4.9 mm of track from pad 33, R66.1 and R65.1 in a chain; R67 on F.Cu at (124.03, 108.65), 7.1 mm from U1.2 because U1's courtyard covers the run nearer to it. ngspice on the routed copper at R_drv 33 Ω, t_r 1 ns: MOSI at FPC1.14 +0.36 V without R, none with 33 Ω; at R_drv 17 Ω +0.85 V, none with 33 Ω. MISO at U4.32 at most +0.10 V with or without R, so R67 is by request (Tanapat, 2026-11-06), about 1.4 dB in the emission estimate. R_drv, t_r, the 10 pF ePaper load and W25N drive are estimates, W25N datasheet not read; check on the prototype and fit 0 Ω if the edge is slow enough | Simulation files in `Reports/GO-v3-layout-2026-11-04/spi-sim-2026-11-06/`; ESP32-C5-MINI-1 datasheet v1.4 Table 6-3, C_IN 2 pF |
| R-V3-13 | U8 output moves from 3.11 V to 3.31 V: R22 475K to 511K (0402 1 %, FOJAN FRC0402F5113TS, C5126239, same family as before), R24 stays 91K. Net `+3.1V` renamed `+3.3V` in the schematic, board and layout files. Why: at 3.11 V, tolerance and the Wi-Fi TX dip take U4 and S12 under their minimum in the worst case (power path check below). Cost: about 6.4 % more power on loads that draw a fixed current. No track, zone shape or footprint changes (Tanapat, 2026-11-06) | Vout = 0.5 × (1 + 511/91) = 3.308 V, the pair in TPS63802 SLVSEU9D Table 10-5; R2 ≤ 100 kΩ, §10.2.2.5. Worst case with FB ±1 % (datasheet), R ±1 % (assumed), line and load 0.4 % (assumed): low 3.21 V, giving U4 3.16 V at TX (min 3.0, MINI-1 Table 6-2) and S12 3.17 V (min 3.05, PSP15871); high 3.41 V, or 3.46 V with I_FB at its 100 nA maximum. Rail limits: 3.6 V for U4, W25N512, SHT4x, SPL07, LIS2DH12 and TMUX121, 3.6 V absolute maximum for SGP41, 3.63 V for TAU1113. U2 ZDSD and e-paper panel datasheets not read. Not measured on hardware |

Pin budget (only the pins that change):

| Pin | v2.1-xtal32k | v3 |
|---|---|---|
| U4 pad 16, IO0 (LP) | `XTAL_32K_P` | `CHG_INT` (R-V3-08; was spare under R-V3-04) |
| U4 pad 17, IO1 (LP) | `XTAL_32K_N` | `EXP_INT` |
| U4 pad 19, IO7 | `EXP_INT` | `NAND CS` |
| U17 pin 4, P2 | `NAND CS` | NC |
| R61 (new) | — | 100K, `EXP_INT` → +3.1V |
| U4 pad 21, IO9 | `ePaper RES` | `EEPA` (R-V3-07) |
| U17 pin 4, P2 | (NC after R-V3-03) | `ePaper RES` (R-V3-07) |
| U16 pin 6, EEPA | NC | `EEPA` (R-V3-07) |
| U4 pad 26, IO15 | `CHG_INT` | `IO15`, unused (R-V3-08) |
| R62 (new) | — | 100K, `CHG_INT` → +3.1V (R-V3-08) |
| C78 (new) | — | 0.1 µF, `BAT-` → GND bridge (R-V3-09) |
| R63, R64 (new) | — | 33 Ω SCLK series, one per branch (R-V3-10) |
| R65, R66, R67 (new) | — | 33 Ω MOSI series, one per branch; 33 Ω MISO series (R-V3-12) |
| R22 (value) | 475K, C5713272 | 511K, C5126239 (R-V3-13) |
| R52 (moved) | was beside TF1 | Now just south of U2.5, stub 1.3 mm instead of 10.8 mm; old stub copper is the TF1 side |

Checked on the ESP32-C5 (2026-11-03, ESP-IDF v5.5.4 73550728): deep-sleep GPIO wake is GPIO0–6 (`soc_caps.h:231`, 7 LP IOs at `:248`); EXT1 is supported with a per-pin level (`:639–640`); `esp_sleep_is_valid_wakeup_gpio` checks `RTC_GPIO_IS_VALID_GPIO` (`sleep_modes.c:1885`); GPIO1 is a plain GPIO unless `RTC_CLK_SRC_EXT_CRYS` is chosen, and the default is `INT_RC` (`esp_hw_support/port/esp32c5/Kconfig.rtc:3`). GO firmware already wakes from deep sleep through EXT1 ANY_LOW on GPIO5, the power button (`go_power.cpp:839–850`, `board_config.h:110`); the boot button on GPIO28 is left out because it is not an LP pin.

Interrupt sources behind the expander (2026-11-03):

| Source | Output | Held or pulse | Pull-up |
|---|---|---|---|
| CAP1203 `ALERT#` → P4 | open drain, active low (DS00001572B Table 1-1 p4) | Held until the host clears the INT bit in Main Control (§4.8 p17, p22). Fires on touch and, by default, on release (`INT_REL_n = 0`, Config 2 44h, p27) | R38 100K to VCC on the touch board |
| LIS2DH12 `INT1` → P5 | push-pull, active high by default (DocID025056 Rev 6 p21; `INT_POLARITY`, CTRL_REG6, p38) | Pulse by default: high only while the condition holds. Held when `LIR_INT1 = 1` (CTRL_REG5 24h bit 3, §8.10 p38) until `INT1_SRC` (31h) is read (§8.20 p42). Click has its own latch, `LIR_Click` (CLICK_THS 3Ah bit 7, §8.29 p47), cleared by reading `CLICK_SRC` (39h) | not needed |

The TCA6408A clears `~INT` when the port is read or when an input returns to its old level (SCPS192E §8.3.3 p20). A pulse that ends before the ESP32 reads the port therefore leaves no trace, which is why every source must be latched.

Firmware impact (v3):
- **Pins.** `EXP_INT = GPIO1`, `NAND_CS = GPIO7` (native GPIO; the NAND/SDSPI drivers use their stock CS handling, no fork). `CHG_INT = GPIO0` (was GPIO15, R-V3-08).
- **RTC clock.** Back to `CONFIG_RTC_CLK_SRC_INT_RC=y`; the v2.1-xtal32k setting `RTC_CLK_SRC_EXT_CRYS` must not be used on v3.
- **Deep-sleep wake.** Add GPIO1 (`EXP_INT`) and GPIO0 (`CHG_INT`) to the EXT1 mask next to GPIO5: `wake_mask |= (1ULL << 1) | (1ULL << 0)`, `ESP_EXT1_WAKEUP_ANY_LOW`. Check the return value of `esp_sleep_enable_ext1_wakeup`: a non-LP pin in the mask returns `ESP_ERR_INVALID_ARG` and arms nothing, the power button included. Find the source with `esp_sleep_get_ext1_wakeup_status()`.
- **Pull-up.** R61 and R62 are external, so the internal pull-ups on GPIO1 and GPIO0 can stay off (they would only add current while INT is low).
- **CHG_INT (R-V3-08).** Every unmasked charger flag pulses `~INT` for 256 µs and now wakes the chip: set the BQ25628 INT masks so only the wanted events (VBUS in/out, charge done, faults) are left, and keep the charger watchdog off or fed so its expiry does not wake the chip. On wake, read the `Charger_Flag` registers (latched until read). EXT1 is level-triggered: check on the bench that the 256 µs pulse wakes the chip from deep sleep; if not, FW falls back to reading the flags at each timed wake.
- **LIS2DH12.** Set `LIR_INT1 = 1` (CTRL_REG5 bit 3) for motion wake through IA1; if click is used on INT1, set `LIR_Click = 1` (CLICK_THS bit 7). Keep the sensor in a low-power detect mode during deep sleep, or nothing can raise INT1.
- **CAP1203.** Leave the touch IC sampling in standby during deep sleep (it is the only thing that can raise `ALERT#`). Decide whether release events are wanted; `INT_REL_n = 1` turns them off and halves the wake-ups per touch.
- **Wake sequence.** (1) read the TCA6408A input port to see the source (P4 low = touch, P5 high = motion); (2) clear it at the source: write 0 to the CAP1203 INT bit, or read `INT1_SRC`/`CLICK_SRC`; (3) read the port again, because the source letting go is another input change that pulls `~INT` low; (4) only then enter sleep. If `~INT` is still low when sleep starts, EXT1 wakes the chip at once.
- **Touch and ACC_INT polling** can go; both arrive through `EXP_INT`.
- **EEPA (R-V3-07).** `EEPA = GPIO9`, input. Before anything that cuts S12 power (ship mode, deep sleep with the S12 rail off, low-battery shutdown) wait until EEPA shows no write in progress, with a timeout (Senseair quotes ~275 ms per write). Use the internal pull while reading, since the output type is unknown; ask Senseair for polarity and type. Rev 1 sensors (shipping until Q2-2027) drive DE on this pin, so only trust EEPA after reading the sensor revision.
- **ePaper RES (R-V3-07)** is now expander P2: set P2 as output (high) at init and give the display driver a reset hook that pulses it over I²C. Until the expander is configured after power-up, P2 is an input and RES floats.
- **Expander directions.** P0, P1, P2, P3, P6, P7 outputs; only P4 and P5 inputs. The TCA6408A has no internal pull-ups and no interrupt mask, so an unused or floating input wakes the chip. Read the input port once after setting the directions to clear the power-up interrupt.

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

## Full re-route (branch v3-reroute, 2026-11-05, reviewed once, not committed)
Status: DRC 254 (94 errors, same set as before the review: footprint library, BT1 and U16 pads at the edge, U3-BAT via; warnings +18 from silk and zone neck, 10 of them R65-R67 labels until the close-out silk pass), 0 unconnected, parity 0. `pcb_check --stage routing`: RT-01 2 bends (GND round U6.1 pad, a sliver on U5-TS; v3 had 5), RT-02 PASS (8 junctions, all perpendicular T), RT-09 FAIL on deliberate 0.15 mm tracks.

Review fixes (Tanapat, 2026-11-05) are in `reroute_fixes.py`, applied on the autorouted board; autorouted tracks exist only in the board file, so that script needs the pre-fix board. After it: `tools/fill_net.py` joins SCL (`/SCL --width 0.2 --viacost 4`), re-routes `/ACC_INT` and `/LED_4_B` (`--viacost 12`), then 25 GND vias were added on single-via pour pieces, U4 west pads and U18.1.
- USB D+/D- on In2 with In1 as return (USB 2.0 full speed, 12 Mbit/s, C5-MINI-1 datasheet). In2 GND strip deleted. Z0 falls to about 32 ohm where B.Cu pour is under the pair (estimate); 45 mm is electrically short at 4 ns edges.
- GNSS clearance grown south to y 70.4 with a chamfer: AE1.1 to ground 0.49 mm before, now 1.74 mm (In1), 1.9 mm (F.Cu), 2.08 mm (B.Cu). CA-G01 manual 5.4.2-5.4.3 asks 2-6 mm; the UART round the BT1 hole sets the corner. PRTRG out of the clearance: F.Cu to via (154.1,64.9), B.Cu outside SCL, via (159.15,73.3), 8 vias.
- RF feed straight on the centre of AE1.1 (y 67.73) from C62.1 through R45 and C61; those three parts moved 0.43-0.56 mm (Tanapat).
- Y junctions redrawn as perpendicular T (Tanapat): MOSI, BAT+ strap, SCL at U13, EN, QON, SDA at U14, +3.1V via at U14, U5-TS at R18. Three tracks into one pad stay at C27.1 and FPC1.16: the pad is the node, no wedge shows.
- Signal nets chained through their pads (Tanapat, 2026-11-06): `tools/route_chain.py` with `chain_plan.json`, run on the board before the GND stitching vias. Each link starts and ends on a named pad or via, and the net's other copper is an obstacle. MISO and GDR are free of branches; MOSI leaves U4.33 with two tracks, so its only split is at the driver pad. SDA 279 to 308 mm, 19 to 25 vias; SCL 290 to 304 mm, 18 to 27 vias; MOSI 105 to 115 mm, 7 to 10 vias. Branch nodes on SDA + SCL 20 to 9.
  - Branches kept, because the pad has one way out: U3.C3 0.4 mm and U3.E3 0.5 mm (WCSP ball), U20.41 8.1 mm and U20.42 9.0 mm (a +3.1V lane and C69 close the row), U15.1 2.5 mm, U13.2 1.6 mm, CN3.3 1.8 mm.
  - One real split stays on each I2C net beside U4 (SDA at via (114.28,125.37), SCL at U4.7): the bus has three dead ends (U12, U5, CN2) and a chain has two. U12 stays on one lane each because a return lane would add copper across the SHT4x tab neck.
  - Not chained: USB D+/D- (USB-C has two pads for each line), EN, QON, CHG_INT and strap or supply nets (Tanapat: no fast edges to reflect).
- R65-R67 added after the chain step (`series_plan.json`, R-V3-12). MOSI 107 mm, 8 vias; MISO 48 mm, 4 vias. Return path on the routed SPI copper: SCLK 91 % and MOSI 74 % over In1 GND, most of the rest B.Cu over In2 +3.1V; the longest way round any plane gap is 2.9 mm. Each F.Cu to B.Cu change moves the return from In1 GND to In2 +3.1V with the nearest cap 6.8-11.6 mm away and a GND via within 0.7-2.9 mm; MOSI runs 3.7 mm over In2 PMID beside R65 and R66. Estimated margin to FCC Class B at 3 m, Ott differential-mode formula, +-10-20 dB: MOSI on the board 31.5 to 35.4 dB, with an assumed 40 mm FPC tail 11.1 to 21.4 dB; MISO 34.2 to 35.6 dB. Cable common mode is not in that number. A cap within 2 mm of every layer change is worth 1-4 dB on SCLK and MOSI, not added.
- Power path check (2026-11-06), files in `Reports/GO-v3-layout-2026-11-04/power-path-2026-11-06/`. Copper is enough: all-on 860 mA on +3.1V drops 17 mV at worst and 4 mV at U4, battery path copper about 74 mOhm with 0.5 oz inner layers. At 3.11 V the rail had no tolerance margin: with FB +-1 %, R22 and R24 +-1 % assumed and a 39 mV dip at a 426 mA step (fitted to TPS63802 Fig 10-21), U4 reached 2.97 V against 3.0 V and S12 3.01 V against 3.05 V in the worst case. R-V3-13 moves the rail to 3.31 V: U4 3.16 V and S12 3.17 V in the same case. Load rises to 892 mA (buzzer 132 mA from the HYG-8503A datasheet, was an assumed 100 mA) and the worst copper drop stays 17 mV. At a 3.0 V cell U8 draws 1.24 A and the cell 1.33 A, so the 0.2 mm Pack+ neck at U5.8 would reach IPC dT 37 C if sustained; it is short and sees bursts only. F1 holds 0.75 A; all-on while charging draws about 1.15 A. C21 is marked 22 uF but its description field is CL05A106MP5NUNC, a 10 uF part. Not measured on hardware.
- EEPA at x 158.1, over In1, no longer under U8's L1/L2 traces.
- I2C: both In2 wraps round the SW island deleted. U5 SDA joins U3 on B.Cu (U3-BAT B.Cu lane moved south of the SDA via, BAT- via to (116.75,101.62)). SCL east group joined by B.Cu from (122.62,125.34) to (137.12,117.69). SDA 320 to 279 mm, SCL to U13 128 to 73 mm.
- U5: U5.15 to C3.1 direct (0.15 mm), GND vias at C6, C30, C4, C11, C22, C8; SYS and Pack+ fan out at 0.35 / 0.3 mm. C3 keeps no via of its own (SCL/SDA on B.Cu below), its ground goes to U5.15 and the C6 vias on F.Cu.
- U8: two GND vias at C38.1. R8 BAT+ sense taken from the R8.1 pad, not from the battery via.
- R43 moved next to Q5 (139.3,69.5), so booster current no longer runs 14 mm on the In2 RESE lane. R18/R19 stay: U5-TS must reach the NTC on the west side, and by inspection (no route attempted) pins 5/6 have no clear way west, so moving them would not shorten the lanes.
- In2 SW island trimmed to the current path (14.1 to 10.0 mm2). In2 VBUS band gives 1.7 mm back to +3.1V.

Not improved: A* found no lower via count for QON (8), RES (5), EN_PM1 (4), BUZZ (4), CHG_INT (4), LED_3_G (2).

Build: `reroute_build.py` writes `planes.json` and `route.json` from the v3 board (commit 6b78484), `pcb_route.py` applies them, `reroute_autoroute.py` runs Freerouting on what is left, `tools/fill_net.py` joins the pieces it dropped. Freerouting is not deterministic, so the board file is the source for the autorouted tracks, not `route.json`.

Layers: F.Cu and B.Cu signals. In1 GND, gauge island. In2 +3.1V with power islands, plus USB, LED1/LED2, GDR, RESE, SDA, SCL (neck only), Pack+, CHG_INT and the U3 I2C hop. The neck at FPC1 has no plane left on In2, so `plane-bridges` joins the top-left +3.1V (0.2 mm B.Cu) and FPC1 +3.1V (0.15 mm B.Cu).

Open: C78 no longer spans a split (its BAT- side now lands on the In2 return, not across an In1 gap), so it can go. EMC analysis, fab set and silk pass not done. AE1 matching (C61, C62 DNP, R45 0R) still needs a network analyzer on the finished board.
