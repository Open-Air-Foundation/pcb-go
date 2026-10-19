# X1A0001410006 (Epson FC-135R, 32.768 kHz, CL 6 pF, ESR 50 kΩ max, 3215): RTC crystal for ESP32-C5 XTAL_32K_P/N

Datasheet: `FC-135R_epson_datasheet.pdf` (Document No FC-135R_E_Ver2.0, 8 pp, from https://download.epsondevice.com/td/pdf/app/FC-135R_en.pdf). Also `FC-135_brief_en.pdf` (FC-135R / FC-135 two-page brief, https://download.epsondevice.com/td/pdf/brief/FC-135_en.pdf). The extraction is reused from the pulse-oximeter part `XTAL-32K/part.md` (FC-135R, checked 2026-10-16) and re-verified below.

LCSC: C94673 (Seiko Epson X1A0001410006, SMD3215-2P), extended. JLCPCB stock 6,435, @500 = 0.1359 (checked 2026-10-19, `selectSmtComponentList`). Attributes per JLC: 32.768 kHz, CL 6 pF, ±20 ppm, -40 to +85 °C.

## CL = 6 pF is not verified against Epson
The FC-135R datasheet lists CL "7, 9, 12.5 pF, Please specify" (p2) and says the product-number suffix is "Please contact Epson for details" (p2). The 6 pF value for suffix 0006 comes from the LCSC/JLCPCB attribute only. LCSC's own datasheet PDF link returns an HTML bot wall. Bring-up check: measure the 32 kHz frequency against the 40 MHz XTAL (ESP-IDF `rtc_clk_cal`). A crystal that is really CL 7 or 9 pF runs about +30 to +90 ppm high with these 8.2 pF caps (pulling estimate below), still inside the 500 ppm BLE sleep-clock budget.

## Selection (user decision 2026-10-19, option B)
| Candidate | LCSC | ESR | CL | Verdict |
|---|---|---|---|---|
| **X1A0001410006 FC-135R** | C94673 | 50 kΩ max (p2) | 6 pF (LCSC) | **chosen**: lowest CL means the least oscillator drive; stock 6,435 |
| X1A0001410002 FC-135R | C1987155 | 50 kΩ max | 9 pF (LCSC) | used on the oximeter; stock 2,865 |
| Q13FC13500004 FC-135 | C32346 | 70 kΩ typ in the full datasheet | 12.5 pF | rejected: does not guarantee Espressif's ≤ 70 kΩ |
| X1A0000610006 FC-12M 2012 | C99009 | 90 kΩ | 7 pF | rejected: above 70 kΩ |

Second source (same 3215 footprint): C95361 Epson Q13FC13500049 (FC-135, 6 pF, ESR 70 kΩ per LCSC, stock 171,275), drop-in with the same caps but less ESR margin.

## Lifecycle
Active. FC-135R is listed as a current product on Epson's FC-135R page (https://www.epsondevice.com/crystal/en/products/crystal-unit/fc135r.html, checked 2026-10-16 for the oximeter; FC-135 page re-checked 2026-10-19, no NRND or discontinued marking). The datasheet has no status field.

## ESP32-C5 requirement
- ESP32-C5-MINI-1 datasheet v1.3 Table 3-1 p14: pin 16 = IO0 = XTAL_32K_P, pin 17 = IO1 = XTAL_32K_N.
- Same datasheet Fig 9-1 p49: X1 32.768 kHz with C5/C6 = 12 pF (NC), note "X1: ESR = Max. 70 KΩ".
- Espressif HW Design Guidelines, ESP32-C5 schematic checklist, "RTC Clock Source (Optional)": ESR ≤ 70 kΩ; load caps per the crystal's specification; the parallel bias resistor (5–10 MΩ) is normally not populated.

## Values (FC-135R_epson_datasheet.pdf p2)
- ESR R1 = 50 kΩ max. C1 (motional) = 3.4 fF typ. C0 (shunt) = 1.0 pF typ.
- Frequency tolerance ±20 ppm at +25 °C; aging ±3 ppm max first year; B = -0.04 ppm/°C² max, Ti = +25 ±5 °C.
- Drive level operating max 0.5 µW; not destroyed up to 1.0 µW. Espressif does not state the C5 oscillator drive level [gap].
- Operating -40 to +85 °C.

## Load capacitors
C = 2 × (CL − Cstray) = 2 × (6 − 2) = 8 pF → **8.2 pF C0G 0402, LCSC C1579 (FH 0402CG8R2C500NT, ±0.25 pF, 50 V)**. Cstray (module pin + pad + short trace) is assumed 2–3 pF [inferred; Espressif gives no value], so the effective CL is 6.1–7.1 pF.
Pulling sensitivity S ≈ C1 / (2 (C0 + CL)²) = 3.4 fF / (2 × (7 pF)²) ≈ 35 ppm per pF [inferred from p2 values], so the Cstray uncertainty moves the frequency by 0 to −35 ppm from nominal.

## Pins
2 pads, "X'tal" / "X'tal", non-polarised (p4). Symbol `Device:Crystal`, footprint `Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm` (pads 1.0 × 1.8 mm at ±1.25 mm). Matches Epson's recommended footprint (brief p1: 1.0 / 1.8 / 2.5 mm pitch).

## Layout (p4, p7)
- "Do not design any circuit patterns in the shaded area" (between the pads, under the body, p4).
- "Shortest line pattern on PCB is recommended. Too long line on PCB may causes abnormal oscillation." (p7 note 3).
- Place next to U4 pins 16/17 on F.Cu, no vias on XTAL_32K_P/N, keep MOSI/SCLK away (pcb-layout-rules RF-21, RF-22, HS-30, HS-32 applied by analogy).

## Verification (opened the PDF)
1. p2: "Motional resistance (ESR) R1 | 50 Max. | kΩ".
2. p2: "Shunt capacitance C0 | 1.0 Typ. | pF"; "Load capacitance CL | 7, 9, 12.5 | pF | Please specify".
3. p2: "Maximum level of drive ... 1.0 µW, Not destroyed".
