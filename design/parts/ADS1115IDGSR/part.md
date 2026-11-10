# ADS1115IDGSR — 16-bit I2C ADC for the CO AFE (U23, R-V3-17)

TI SBAS444E (Dec 2024), fetched 2026-11-10. LCSC C37593. KiCad symbol Analog_ADC:ADS1115IDGS.

| Item | Value | Page |
|---|---|---|
| Supply | 2.0–5.5 V | 4 |
| Analog inputs | GND–0.3 to VDD+0.3 abs max; GND to VDD operating | 4 |
| Digital pins | SDA, SCL, ADDR, ALERT/RDY –0.3 to 5.5 V, independent of VDD | 4 |
| Current | 150 µA operating, 0.5 µA power-down (single-shot) | 6 |
| Address | ADDR to GND 0x48, **VDD 0x49**, SDA 0x4A, SCL 0x4B | 20 |
| Unused pins | float or tie analog inputs to GND; ALERT/RDY open or weak pull-up | 29 |
| Package | VSSOP-10 (DGS) 3×3 mm, 0.5 mm pitch | 3 |

Lifecycle: ADS1115IDGSR **Active** (orderable addendum, p42). LCSC stock 2026-11-10: 5,449 (US$1.41 at 1).
Symbol pin 2 is typed output; the datasheet calls it open drain (left unconnected here).
