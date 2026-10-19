# GO main v2.1-xtal32k: change requirements

Status: phase 4 (draw). Requirements and part approved by Tanapat 2026-10-19.

Scope: an engineering change on top of v2.1 (branch `v2.1-xtal32k`, from 426c645). The rest of the GO main board is hand-drawn and out of scope; only the items below change.

## Why
Battery life. The ESP32-C5 currently runs its RTC from the internal RC (`CONFIG_RTC_CLK_SRC_INT_RC=y`). A 32.768 kHz crystal gives BLE modem sleep and light sleep an accurate sleep clock (Sam's power research, `go/feat/pm`, 2026-10-17).

## Requirements
| ID | Requirement | Number |
|---|---|---|
| R-XT-01 | 32.768 kHz crystal on U4 pin 16 (IO0 = XTAL_32K_P) and pin 17 (IO1 = XTAL_32K_N), load caps to PGND, no series or parallel resistors | ESR ≤ 70 kΩ (ESP32-C5-MINI-1 Fig 9-1 p49) |
| R-XT-02 | ePaper CS moves from U4 IO0 to TCA6408A U17 P7 (pin 10, unused). R39 100K pull-up stays, so the display is deselected while the expander pins are inputs after reset | — |
| R-XT-03 | Nothing else changes: I²C stays on IO6/IO7, IO4 and IO15 stay free | — |

## PCB constraints (Tanapat, 2026-10-19)
Do not move: all LEDs, FPC1, BT1, U16, U11, U10, NTCx, SPS30, SWx, U12, USB-C (USB1), CN1, CN2.

## Firmware impact (not in this repo)
- `PIN_DISPLAY_CS` becomes expander P7 on this board variant (manual CS through the TCA6408A, like NAND CS on P2).
- `CONFIG_RTC_CLK_SRC_EXT_CRYS=y` on boards with the crystal.

## Blocks
1. `rtc32k`: Y1 + C76 + C77, plus the ePaper CS label on U17 P7.
2. Hand edits (not generated): U4 pin 16 label `ePaper CS` → `XTAL_32K_P`; U4 pin 17 label `IO1` → `XTAL_32K_N`.
