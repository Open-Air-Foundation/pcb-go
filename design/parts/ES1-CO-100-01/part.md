# ES1-CO-100-01 — 3-electrode CO sensor (U11, R-V3-17)

EC Sense datasheet V1.4 (2025-02-28), `~/Documents/Engineering/Datasheets/Sensors/`.
Amperometric, bias 0 mV, 30 ± 15 nA/ppm, 0–100 ppm, zero ±100 nA, load resistor 100 Ω recommended,
T90 < 30 s (p1). Pins C, S, R in a row, 2.54 mm pitch, ø0.4 mm; body 11.5 mm, 12.5 mm over the tabs (p2).
Sensitivity about 11 / 17.5 / 25 nA/ppm at 0 / 20 / 50 °C (p3).

Footprint: kept U11's PS1-CO-SMOKE-10k (locked on the board). Its pads R-S-C at 2.54 mm, 0.5 mm drill, the row
1.55 mm in from an 11.6 mm body (12.6 over tabs) match the ES1 top view R-S-C. Not confirmed: the ES1 drawing
does not dimension the row's offset from the body edge or centre; check with a sample before fab.
Not stocked at LCSC (only ES1-CO-1000-01, C528674). Stays DNP for JLCPCB (through-hole, fitted by hand, no wash).
