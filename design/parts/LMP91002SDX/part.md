# LMP91002SDX/NOPB — potentiostat AFE for the CO sensor (U22, R-V3-17)

TI SNIS163B (Oct 2015), local copy read 2026-11-10. LCSC C2651581.

| Item | Value | Page |
|---|---|---|
| Use | Unbiased 3-lead amperometric sensors only (ES1-CO-100-01 is 0 mV) | 1 |
| Supply | 2.7–3.6 V | 4 |
| Supply current | 3-lead mode 10 µA typ, 13.5 µA max; deep sleep listed | 5 |
| TIA gain | TIACN[4:2]: external, 2.75k, 3.5k, 7k, 14k, 35k, **120k**, 350k | 6, 15 |
| Load resistor | **10 Ω fixed**, ±5 % (no RLOAD select, TIACN[1:0] reserved) | 6, 15 |
| Internal zero | REFCN[6:5] 20 / 50 / 67 % of the source; REFCN[7] source internal (VDD) or VREF pin | 15 |
| External VREF | 1.5 V to VDD, 10 MΩ input | 6 |
| Shorting FET | MODECN[7] FET_SHORT, off by default | 16 |
| Modes | deep sleep (default), standby, 3-lead | 16 |
| I2C | fixed 7-bit 0x48 (1001 000), 10–100 kHz, MENB low for the whole transfer | 7, 12 |
| Package | WSON-14 4×4 mm, 0.5 mm pitch, DAP 3.0×2.6 mm to GND; same pinout as LMP91000 | 3 |
| Not on this part | temperature sensor (LMP91000 has one) | 1 |

Lifecycle: LMP91002SDX/NOPB **Active** (orderable addendum, p26). SD and SDE orderables obsolete.
LCSC stock 2026-11-10: 92 (C2651581, US$5.83 at 1). LMP91000SDX (C2651584, pin-compatible) 0 in stock.
Enough for prototypes; a 1000-unit run needs another source.

Datasheet gaps: no decoupling values, no VREF-pin handling when the source is internal (tied to VDD here,
inside its 1.5 V–VDD range), no C1/C2 values.
