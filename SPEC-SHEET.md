# AirGradient GO v2: hardware spec sheet

AirGradient GO is a portable, battery-powered air quality monitor. This sheet describes the hardware of **GO v2**: what it measures, the parts it is built from, how it is powered, and the parts that the KiCad BOMs do not define (display, battery, internal cables).

GO v2 is the produced unit: main board PCB revision 2.1 with touch pad revision 2.1 (tag `v2`, branch `main`).

The other versions have their own sheets:
- v1, the first product: [SPEC-SHEET-v1.md](SPEC-SHEET-v1.md);
- v3, the prototype: [SPEC-SHEET.md on branch `v3-reroute`](https://github.com/Open-Air-Foundation/pcb-go/blob/v3-reroute/SPEC-SHEET.md).

Sensor values come from each sensor's own datasheet (named in every row). They describe the sensor, not a tested accuracy of the finished device: inside the enclosure the device's own heat, the airflow and the firmware's compensation all change what a reading means.

## 1. At a glance

| | |
|---|---|
| Measures | PM1.0, PM2.5, PM4, PM10 (mass and particle count), CO2, temperature, relative humidity, VOC Index, NOx Index, barometric pressure |
| Location and motion | GNSS receiver, GPS L1 and BeiDou B1; 3-axis accelerometer |
| Display | 2.13″ e-paper, 250 × 122 pixels, black and white |
| Indicators | 4 RGB LEDs, buzzer |
| Controls | 3 capacitive touch pads, 2 push buttons (power, ESP32 boot) |
| Processor and radio | ESP32-C5 (RISC-V, up to 240 MHz): Wi-Fi 6 at 2.4 and 5 GHz, Bluetooth LE, IEEE 802.15.4 |
| Storage | 512 Mbit (64 MB) NAND flash |
| Battery | replaceable 18500 Li-ion cell, 2600 mAh, 3.7 V |
| Charging | USB-C |
| Size | about 68.7 × 102.5 × 26.5 mm |

## 2. Sensors

| Measures | Sensor | Range | Datasheet accuracy | Source |
|---|---|---|---|---|
| PM1.0, PM2.5, PM4, PM10 mass; PM0.5 to PM10 particle count | Sensirion **SPS30**, laser scattering | 0 to 1000 µg/m³; 0 to 3000 #/cm³; particles 0.3 to 10 µm | PM1.0 and PM2.5: ±(5 µg/m³ + 5 %) from 0 to 100 µg/m³, ±10 % from 100 to 1000 µg/m³. PM4 and PM10: ±25 µg/m³ / ±25 % | SPS30 datasheet v2.0 (June 2023), p2 |
| CO2 | Senseair **S12** (article 012-0-0001), NDIR | 400 to 5000 ppm (extended range to 10 000 ppm) | ±(50 ppm + 3 % of reading) from 0 to 5000 ppm, at 25 °C, 1013 mbar, 50 %RH; response T63 < 30 s | S12 product specification PSP15871 Rev 4 (preliminary), p2 |
| Temperature and relative humidity | Sensirion **SHT40** (SHT40-AD1B-R2) | −40 to 125 °C; 0 to 100 %RH | ±0.2 °C typical (±0.4 °C max from 0 to 65 °C); ±1.8 %RH typical (±3.5 %RH max from 10 to 90 %RH) | SHT4x datasheet v7.3, p4 to p7 |
| VOC Index, NOx Index | Sensirion **SGP41** (SGP41-D-R4), metal oxide | VOC Index 1 to 500; NOx Index 1 to 500 | an index, not a concentration: firmware computes it from the raw signals with Sensirion's Gas Index Algorithm. Valid after < 1.5 h (VOC) and < 6 h (NOx) | SGP41 datasheet v1.0, p3, p4, p10 |
| Barometric pressure | Goermicro **SPL07-003** | 300 to 1100 hPa | ±0.3 hPa absolute, ±3 Pa relative (typical) | SPL07-003 datasheet v1.0, p6 |

Notes:
- **SPS30.** Sensirion gives these figures as precision, meaning the spread from device to device; it gives no absolute accuracy. PM4 and PM10 are calculated from the particle size distribution, not measured directly. Lifetime is more than 10 years at 24 h a day, from an MTTF calculation.
- **SHT40.** The maximum values are read from the datasheet's graphs. The SHT40 sits on the main board, so the electronics warm it; the firmware compensates for that.
- **CO sensor.** The board has a place for a CO sensor. It is not fitted and not connected.

## 3. Location and motion

**GNSS: TAU1113 module** (ordering number TAU1113-1010A00E in its datasheet).
- Receives **GPS L1 C/A and BeiDou B1I** (single band).
- The module can also receive GLONASS G1, Galileo E1, QZSS and SBAS. Which systems it tracks is set by a mode stored in its flash.
- 88 channels, up to 5 Hz updates.
- From the module datasheet, open sky: position 1.5 m CEP (< 1.0 m with SBAS); cold start 26 to 28 s, hot start 1 to 2 s; tracking sensitivity −163 dBm (measured with a good external LNA). Source: TAU1113 datasheet V1.4 (preliminary), p9, p10.
- Antenna: a CA-G01 chip antenna on the main board, 8 × 3 mm. No matching network is fitted: its places hold a 0 Ω link and two unfitted capacitors.
- How well it receives inside the enclosure has not been specified.

**Accelerometer: LIS2DH12.** 3-axis, full scale ±2, ±4, ±8 or ±16 g, with programmable motion and wake-up interrupts (LIS2DH12 datasheet Rev 6, p1). Its interrupt line goes to the I/O expander, whose own interrupt output is not connected, so the firmware polls it.

## 4. Processor, radio, storage

| | |
|---|---|
| Module | Espressif **ESP32-C5-MINI-1-N4** |
| CPU | 32-bit RISC-V, single core, up to 240 MHz |
| Flash / PSRAM | 4 MB / none |
| Wi-Fi | IEEE 802.11ax (Wi-Fi 6), 20 MHz, 1T1R, dual band: 2412 to 2484 MHz and 5180 to 5885 MHz |
| Bluetooth | Bluetooth LE |
| IEEE 802.15.4 | Thread 1.4, Zigbee 3.0, 2.4 GHz |
| Antenna | PCB antenna on the module |
| Source | ESP32-C5-MINI-1 datasheet v1.4, p2, p3 |
| Data storage | Winbond W25N512GV, 512 Mbit (64 MB) SPI NAND. The board has a place for a microSD socket, not fitted |
| Watchdog | TPL5010 hardware watchdog timer |
| USB | USB-C data lines go to the ESP32-C5's native USB, used to load firmware and read logs. There is no ESD protection part on them |

These are what the hardware can do. Which radios are used, and how, is set by the firmware.

## 5. User interface

| | |
|---|---|
| Display | 2.13″ e-paper, 250 × 122: see section 8 |
| LEDs | 4 RGB LEDs (TJ-S1608SW6TDSLCCYRGB-A5) along the top edge of the main board, driven by an LP5036 |
| Buzzer | HYG-8503A, 8.5 mm, transistor-driven |
| Touch | 3 capacitive pads on the touch pad board, CAP1203 controller, connected to the main board by cable 2 (section 10). The controller's alert line goes to the I/O expander, so the firmware polls it |
| Power button (SW1) | on the charger's QON input: held low for about 0.8 s it takes the device out of ship mode; held for about 12.5 s on battery it forces a full power reset (BQ25628 datasheet SLUSEG4C, p6 and p16: tSM_EXIT, tQON_RST) |
| Boot button (SW2) | on ESP32-C5 GPIO28, a strapping pin. Held down while the chip resets or powers up, it puts the chip in download boot mode, so firmware can be loaded over USB (ESP32-C5 datasheet v1.5, section 3.1, Table 3-3) |

## 6. Power

| | |
|---|---|
| Battery | replaceable 18500 Li-ion cell, 2600 mAh, 3.7 V, in a moulded holder: see section 9 |
| Charging input | USB-C, 5 V, through a 0.75 A resettable fuse. The charger's input current limit resistor (2.49 kΩ) sets 1.0 A (BQ25628 datasheet, p6 and p11: IINREG = KILIM / RILIM, KILIM 2500 AΩ typical) |
| Charger | TI **BQ25628**: NVDC power path; charge current 0.04 to 2.00 A and charge voltage 3.50 to 4.80 V, both set by firmware; JEITA charging by temperature, from an NTC (NCP15XH103) at the cell (BQ25628 datasheet SLUSEG4C, p1, p9) |
| Fuel gauge and protection | TI **BQ27742-G1**: Impedance Track gauge reporting state of charge, remaining capacity, time to empty, voltage, current and temperature. It also protects the cell against over-voltage, under-voltage, over-current in charge and discharge, and short circuit, through a CSD83325L FET pair and a 5 mΩ sense resistor (BQ27742-G1 datasheet SLUSBV9D, p1) |
| Reversed cell | no protection on the board: a cell put in backwards reaches the gauge and the charger. The cell must go in the right way round |
| System rail | TPS63802 buck-boost converter, 3.11 V. Its input comes through an LM66200 ideal-diode switch, from USB or from the charger's system output |
| SPS30 supply | 5 V from the charger's PMID output, through a FET switch that closes when the charger reports PMID good. PMID carries the USB voltage while USB is connected and the charger's boost output on battery (3.84 to 5.2 V, set by firmware; BQ25628 datasheet, p1, p6). The SPS30's I2C lines are disconnected by a TMUX121 switch while it is off |

Battery life depends on the mode and the firmware, and is not specified in this sheet.

## 7. Mechanical

| | |
|---|---|
| Enclosure | about 68.7 × 102.5 × 26.5 mm: the outline of the top and bottom parts in the industrial design's assembly GO v2.12 of 2026-08-27 |
| Main board | 62.90 × 88.29 mm, 4 layers, 0.8 mm thick, with a 51.0 × 26.4 mm cut-out for the cell |
| Touch pad board | 2 layers (`PCB/touch-pad`), carried by the battery holder on the display side of the main board |
| Battery holder | moulded part. It holds the cell, carries the touch pad, and screws to the main board |

## 8. E-paper display

| Item | Spec |
|---|---|
| Part | Good Display **GDEY0213B74** |
| Size | 2.13″ |
| Resolution | 250 × 122 pixels, black and white |
| Controller | SSD1680 (SSD1680Z8) |
| Active area | 23.70 × 48.55 mm |
| Outline | 29.2 × 59.2 × 1.0 mm |
| Connection | its 24-pin, 0.5 mm FPC into main board `FPC1` |
| Interface | 4-wire SPI: BS1 (pin 8) tied to GND |
| Pins not connected | NC 1 and 4; TSCL 6 and TSDA 7 (external temperature sensor); VPP 19 |

The firmware addresses the panel as 128 × 250, because the controller's RAM rows are whole bytes.

Not the **GDEY0213B74H**: that panel has the same outline and nearly the same name, but 144 × 296 pixels.

Source: Good Display product specification GDEY0213B74, 2021/03/17 (values p6, pin table p8, BS1 p9).

## 9. Battery

| Item | Spec |
|---|---|
| Type | Li-ion, cylindrical, sold as 18500, replaceable by the user |
| Capacity | 2600 mAh minimum, 2620 mAh typical, at 0.2C |
| Nominal voltage / energy | 3.7 V / 9.62 Wh |
| Charge | CC/CV to 4.20 ± 0.05 V, cut-off 0.02C |
| Maximum continuous charge current | 2600 mA (1C) |
| Maximum continuous discharge current | 7800 mA (3C) |
| End of discharge | 2.50 V |
| Size | Ø18.6 mm (−0.3, with the PVC sleeve) × 49.2 mm (−0.6) |
| Weight | 34 ± 1 g |
| Temperature | charge 0 to 45 °C; discharge −20 to 60 °C |
| Cycle life | at least 300 cycles to 80 % of capacity |
| Holder | moulded battery holder; its contacts sit on the main board (`BT1`) |
| Supplier | Cowon (Shenzhen Cowon Technology) |

The cell is bought as an "18500", but by its drawing it is physically an 18490.

Cowon's documents name the model in two ways: INR18490NP in the cell spec (revision A0, 2025-06-13) and INR18500 26N in the MSDS (2026-10-15). Both give 2600 mAh and 3.7 V. Neither says whether the cell has its own protection circuit; the board protects it in any case (section 6).

## 10. Internal cables

Two cables. Each has 5 wires and is 35 mm long, and each runs pin 1 to pin 1, through pin 5 to pin 5.

| | Cable 1 | Cable 2 |
|---|---|---|
| From | main board `CN1` | main board `CN2` |
| To | SPS30 PM sensor | touch pad `CN1` (`PCB/touch-pad`) |
| Plug at the main board | 5-pin, 1.0 mm pitch, JST SH type (SHR-05V-S-B or equivalent) | 5-pin, 1.0 mm pitch, JST SH type (SHR-05V-S-B or equivalent) |
| Plug at the other end | 5-pin, 1.5 mm pitch, JST ZHR-5 | 5-pin, 1.0 mm pitch, JST SH type (SHR-05V-S-B or equivalent) |
| Length | 35 mm | 35 mm |

The headers on both boards are Hong Cheng HCZZ0032-5 (LCSC C7433426): right-angle SMD headers that take a JST SH-type plug. Main board `CN3` is a spare I2C header with no cable in the product.

### Cable 1: main board CN1 to SPS30

| Wire | CN1 pin | Main-board net | SPS30 pin | SPS30 signal |
|---|---|---|---|---|
| 1 | 1 | +5V | 1 | VDD, 5 V ± 10 % |
| 2 | 2 | PM_SDA | 2 | SDA |
| 3 | 3 | PM_SCL | 3 | SCL |
| 4 | 4 | GND | 4 | SEL: GND selects I2C |
| 5 | 5 | GND | 5 | GND |

The SPS30 selects I2C only if SEL is at GND before or at power-up (SPS30 datasheet v2.0, p16). The cable ties SEL to GND.

### Cable 2: main board CN2 to touch pad CN1

| Wire | CN2 pin | Main-board net | Touch pad CN1 pin | Touch-pad net |
|---|---|---|---|---|
| 1 | 1 | +3.1V | 1 | VCC |
| 2 | 2 | SDA | 2 | SDA |
| 3 | 3 | SCL | 3 | SCL |
| 4 | 4 | INT | 4 | INT (CAP1203 alert) |
| 5 | 5 | GND | 5 | GND |

The pins and nets in both tables come from the board files of tag `v2`.

### Length check against the enclosure

The industrial design's enclosure assembly (GO v2.12, 2026-08-27; not in this repository) models both cables. Each wire end sits 1 mm inside its plug.

| | Cable 1 (SPS30) | Cable 2 (touch pad) |
|---|---|---|
| Modelled wire, end to end | about 23 mm | about 30 mm |
| Free wire between the plugs | about 21 mm | about 28 mm |
| Route | from `CN1` on the main board's F.Cu side, folded through the notch at the bottom of the battery cut-out, to the SPS30 on the B.Cu side | from `CN2` on the F.Cu side, through the battery cut-out, to the touch pad, which the battery holder carries on the B.Cu side |

A 35 mm cable therefore leaves some slack on both routes. The main board in that assembly is revision 2.0; `CN1` and `CN2` moved by at most 0.16 mm in revision 2.1, so the check holds for the produced boards.

The production cables were bought as "ZH1.5 → SH1.0, 5P, 35 mm" and "SH1.0 → SH1.0, 5P, 35 mm", both as the vendor's 反向 ("reverse") type. Vendors do not all use 同向 / 反向 ("same" / "reverse") the same way. Before ordering from another vendor, check a sample end to end against the pin tables.

## 11. Not specified yet

A complete product spec sheet would also give the following. They need a measurement or a decision, so they are not given here:
- weight of the finished device;
- battery life in each mode;
- operating and storage temperature and humidity range of the device;
- measured accuracy of the finished device after compensation, for each quantity;
- GNSS reception inside the enclosure;
- ingress protection and drop rating;
- radio and safety certifications.

For the operating range, the narrowest part limits are:
- charging: 0 to 45 °C (cell);
- SGP41: −10 to 50 °C, 0 to 90 %RH, non-condensing;
- SPS30: 10 to 40 °C and 20 to 80 %RH recommended (−10 to 60 °C absolute);
- S12: calibrated for 15 to 35 °C, works from −10 to 60 °C.
