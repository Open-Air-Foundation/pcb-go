# GO main v2.1-xtal32k: change requirements

Status: phase 4 (draw). Requirements and part approved by Tanapat 2026-10-19.

Scope: an engineering change on top of v2.1 (branch `v2.1-xtal32k`, from 426c645). The rest of the GO main board is hand-drawn and out of scope; only the items below change.

## Why
Battery life. The ESP32-C5 currently runs its RTC from the internal RC (`CONFIG_RTC_CLK_SRC_INT_RC=y`). A 32.768 kHz crystal gives BLE modem sleep and light sleep an accurate sleep clock (Sam's power research, `go/feat/pm`, 2026-10-17).

## Requirements
| ID | Requirement | Number |
|---|---|---|
| R-XT-01 | 32.768 kHz crystal on U4 pin 16 (IO0 = XTAL_32K_P) and pin 17 (IO1 = XTAL_32K_N), load caps to PGND, no series or parallel resistors | ESR ≤ 70 kΩ (ESP32-C5-MINI-1 Fig 9-1 p49) |
| R-XT-02 | ePaper CS moves from U4 IO0 to U4 IO4 (pad 8, unused on v2.1), next to the existing CS trunk. R39 100K pull-up stays. (First tried TCA6408A P7: the route from U17 needed 5 vias through EN_PM1/BUZZ/PRTRG; Tanapat switched to IO4 on 2026-10-19.) | — |
| R-XT-03 | Nothing else changes: I²C stays on IO6/IO7, IO15 stays free | — |

## PCB constraints (Tanapat, 2026-10-19)
Do not move: all LEDs, FPC1, BT1, U16, U11, U10, NTCx, SPS30, SWx, U12, USB-C (USB1), CN1, CN2.

## Firmware impact (not in this repo)
- `PIN_DISPLAY_CS` becomes GPIO4 on this board variant (V1 keeps GPIO0).
- `CONFIG_RTC_CLK_SRC_EXT_CRYS=y` on boards with the crystal.

## Blocks
1. `rtc32k`: Y1 + C76 + C77, plus an NC flag on U17 P7.
2. Hand edits (not generated): U4 pin 16 label `ePaper CS` → `XTAL_32K_P`; U4 pin 17 label `IO1` → `XTAL_32K_N`; U4 pin 8 label `IO4` → `ePaper CS`.

## Layout (pcb-design, 2026-10-19)
Status: layout done. DRC 230 = baseline (0 new), 0 unconnected, parity 0. Route groups in `design/airgradient-go-main/layout/route.json`, checks in `constraints.json`.

### Accepted
- **RF-22 (by analogy for the 32 kHz crystal):** the existing I²C on B.Cu runs under Y1 (SCL) and C77 (SCL, SDA). The solid GND plane (In1) lies between them and the crystal, and I²C edges are slow. Accepted by Tanapat 2026-10-19 instead of re-routing SDA/SCL under U4.
- **ePaper CS at 0.2 mm** (net class 0.25): the 0.25 route from IO4 under the module has no path; 0.2 is above the 0.15 floor (RT-09).
- MOSI passes 0.53 mm above C77 (centre-to-centre ≈ 0.76 mm ≥ 3W, HS-30).
