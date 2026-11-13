# AirGradient GO v1: hardware spec sheet

AirGradient GO is a portable, battery-powered air quality monitor. This sheet describes the hardware of **GO v1**, the first product: what it measures, the parts it is built from, how it is powered, and the parts that the KiCad BOMs do not define (display, battery, internal cables).

GO v1 is three boards: main board PCB revision 1.0, the LED + touch board 1.0 and the touch pad 1.0. Their files are in tag `v1.0`:

```
git checkout v1.0
```

The other versions have their own sheets:
- v2, the produced units: [SPEC-SHEET.md](SPEC-SHEET.md);
- v3, the prototype: [SPEC-SHEET.md on branch `v3-reroute`](https://github.com/Open-Air-Foundation/pcb-go/blob/v3-reroute/SPEC-SHEET.md).

Sensor values come from each sensor's own datasheet (named in every row). They describe the sensor, not a tested accuracy of the finished device: inside the enclosure the device's own heat, the airflow and the firmware's compensation all change what a reading means.

For v1 fewer records exist than for v2. Section 11 lists what this sheet cannot give: among them the enclosure's size, the cable lengths and the battery's own specification.

## 1. At a glance

| | |
|---|---|
| Measures | PM1.0, PM2.5, PM4, PM10 (mass and particle count), CO2, temperature, relative humidity, VOC Index, NOx Index, barometric pressure |
| Location and motion | GNSS receiver; 3-axis accelerometer |
| Display | 2.13″ e-paper, 250 × 122 pixels, black and white |
| Indicators | 10 RGB LEDs, 2 white LEDs, buzzer |
| Controls | 3 capacitive touch pads, 2 push buttons (power, ESP32 boot) |
| Processor and radio | ESP32-C5 (RISC-V, up to 240 MHz): Wi-Fi 6 at 2.4 and 5 GHz, Bluetooth LE, IEEE 802.15.4 |
| Storage | 512 Mbit (64 MB) NAND flash |
| Battery | Li-ion polymer pouch cell, size 505060, 2000 mAh, on a 2-pin plug |
| Charging | USB-C |
| Size | not given: see section 11 |

## 2. Sensors

| Measures | Sensor | Range | Datasheet accuracy | Source |
|---|---|---|---|---|
| PM1.0, PM2.5, PM4, PM10 mass; PM0.5 to PM10 particle count | Sensirion **SPS30**, laser scattering | 0 to 1000 µg/m³; 0 to 3000 #/cm³; particles 0.3 to 10 µm | PM1.0 and PM2.5: ±(5 µg/m³ + 5 %) from 0 to 100 µg/m³, ±10 % from 100 to 1000 µg/m³. PM4 and PM10: ±25 µg/m³ / ±25 % | SPS30 datasheet v2.0 (June 2023), p2 |
| CO2 | Senseair **S12**, NDIR | 400 to 5000 ppm (extended range to 10 000 ppm) | ±(50 ppm + 3 % of reading) from 0 to 5000 ppm, at 25 °C, 1013 mbar, 50 %RH; response T63 < 30 s | S12 product specification PSP15871 Rev 4 (preliminary), p2 |
| Temperature and relative humidity | Sensirion **SHT40** (SHT40-AD1B-R2) | −40 to 125 °C; 0 to 100 %RH | ±0.2 °C typical (±0.4 °C max from 0 to 65 °C); ±1.8 %RH typical (±3.5 %RH max from 10 to 90 %RH) | SHT4x datasheet v7.3, p4 to p7 |
| VOC Index, NOx Index | Sensirion **SGP41** (SGP41-D-R4), metal oxide | VOC Index 1 to 500; NOx Index 1 to 500 | an index, not a concentration: firmware computes it from the raw signals with Sensirion's Gas Index Algorithm. Valid after < 1.5 h (VOC) and < 6 h (NOx) | SGP41 datasheet v1.0, p3, p4, p10 |
| Barometric pressure | Infineon **DPS368** (DPS368XTSA1) | 300 to 1200 hPa | typical values: ±1 hPa absolute, from 300 to 1200 hPa and 0 to 65 °C, without the effect of soldering; ±0.06 hPa relative, for any 1 hPa change between 800 and 1200 hPa at a constant temperature from 20 to 60 °C | DPS368 datasheet v1.1 (2019-07-03), p1, p10 |

Notes:
- **SPS30.** Sensirion gives these figures as precision, meaning the spread from device to device; it gives no absolute accuracy. PM4 and PM10 are calculated from the particle size distribution, not measured directly. Lifetime is more than 10 years at 24 h a day, from an MTTF calculation.
- **SHT40.** The maximum values are read from the datasheet's graphs. The SHT40 sits on the main board, so the electronics warm it; the firmware compensates for that.
- **SCD4x module.** `PCB/scd4x-module` is an optional CO2 daughterboard. The standard product uses the S12 on the main board.

## 3. Location and motion

**GNSS: TAU1113 module** (ordering number TAU1113-1010A00E in its datasheet).
- The module receives GPS L1 C/A, BeiDou B1I, GLONASS G1, Galileo E1, QZSS and SBAS (single band). Which systems it tracks is set by a mode stored in its flash.
- 88 channels, up to 5 Hz updates.
- From the module datasheet, open sky: position 1.5 m CEP (< 1.0 m with SBAS); cold start 26 to 28 s, hot start 1 to 2 s; tracking sensitivity −163 dBm (measured with a good external LNA). Source: TAU1113 datasheet V1.4 (preliminary), p9, p10.
- Antenna: a Rainsun GPS1003 chip antenna on the main board, 10 × 3 mm. No matching network is fitted: its places hold a 0 Ω link and two unfitted capacitors.
- How well it receives inside the enclosure has not been specified.

**Accelerometer: LIS2DH12.** 3-axis, full scale ±2, ±4, ±8 or ±16 g, with programmable motion and wake-up interrupts (LIS2DH12 datasheet Rev 6, p1). Its interrupt line goes to ESP32-C5 GPIO3, so motion can interrupt the processor.

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
| Data storage | Winbond W25N512GV, 512 Mbit (64 MB) SPI NAND |
| Watchdog | TPL5010 hardware watchdog timer |
| USB | USB-C data lines go to the ESP32-C5's native USB, used to load firmware and read logs. There is no ESD protection part on them |

These are what the hardware can do. Which radios are used, and how, is set by the firmware.

## 5. User interface

| | |
|---|---|
| Display | 2.13″ e-paper, 250 × 122: see section 8 |
| LEDs | on the LED + touch board: 10 RGB LEDs (TJ-S1608SW6TDSLCCYRGB-A5) and 2 white LEDs (99-213UMC/3640661/TR8-T), driven by an LP5036 |
| Buzzer | HYG-8503A, 8.5 mm, transistor-driven |
| Touch | 3 capacitive pads on the touch pad board, which carries only the copper pads. The CAP1203 controller is on the LED + touch board. Its alert line goes to ESP32-C5 GPIO1, so a touch can interrupt the processor |
| Power button (SW1) | on the charger's QON input: held low for about 0.8 s it takes the device out of ship mode; held for about 12.5 s on battery it forces a full power reset (BQ25628 datasheet SLUSEG4C, p6 and p16: tSM_EXIT, tQON_RST) |
| Boot button (SW2) | on ESP32-C5 GPIO28, a strapping pin. Held down while the chip resets or powers up, it puts the chip in download boot mode, so firmware can be loaded over USB (ESP32-C5 datasheet v1.5, section 3.1, Table 3-3) |

The LED + touch board connects to the main board by cable 2 (section 10): power, I2C and the touch alert line.

## 6. Power

| | |
|---|---|
| Battery | Li-ion polymer pouch cell, size 505060, 2000 mAh, plugged into main board `CN1`: see section 9 |
| Charging input | USB-C, 5 V, through a 0.75 A resettable fuse. The charger's input current limit resistor (2.49 kΩ) sets 1.0 A (BQ25628 datasheet, p6 and p11: IINREG = KILIM / RILIM, KILIM 2500 AΩ typical) |
| Charger | TI **BQ25628**: NVDC power path; charge current 0.04 to 2.00 A and charge voltage 3.50 to 4.80 V, both set by firmware; JEITA charging by temperature, from an NTC on the main board (KNTC0805, 10 kΩ, B 3950) (BQ25628 datasheet SLUSEG4C, p1, p9) |
| Fuel gauge | TI **BQ27427**: Impedance Track gauge with a 7 mΩ sense resistor inside. It reports remaining capacity, state of charge and voltage (BQ27427 datasheet SLUSEB5B, p1) |
| Cell protection | the board has no protector part for the cell: the gauge only measures. v1 relies on the protection circuit in the cell's pack |
| System rail | TPS63802 buck-boost converter, 3.11 V. Its input comes through two Schottky diodes, from USB or from the charger's system output |
| SPS30 supply | 5 V from the charger's PMID output, through a FET switch that closes when the charger reports PMID good. PMID carries the USB voltage while USB is connected and the charger's boost output on battery (3.84 to 5.2 V, set by firmware; BQ25628 datasheet, p1, p6). The SPS30's I2C lines are disconnected by a TMUX121 switch while it is off |

Battery life depends on the mode and the firmware, and is not specified in this sheet.

## 7. Mechanical

| | |
|---|---|
| Main board | 62.90 × 86.98 mm, 4 layers, 0.8 mm thick; most parts on the back |
| LED + touch board | 59.13 × 47.79 mm, 2 layers, 1.0 mm thick (`PCB/led-touch`) |
| Touch pad board | 60.63 × 50.74 mm, 2 layers, 1.0 mm thick (`PCB/touch-pad`, revision 1.0) |
| Board stack | the main board has 3 holes of 3.2 mm for standoffs and 2 screw holes of 2.5 mm. The product's parts list has 2 SMD standoffs M2.5 × 12 mm, 1 nylon spacer M2.5 × 12 mm, 3 M2.5 screws and 1 nylon nut |
| Enclosure | two parts, closed by 2 screws of 1.8 × 15 mm. Its dimensions are not given here (section 11) |

Board sizes are measured from the outlines in the board files.

## 8. E-paper display

The same panel as in v2.

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

| Item | Spec | Where it comes from |
|---|---|---|
| Type | Li-ion polymer pouch cell, size code 505060 | the product's parts list |
| Size | the code stands for about 5.0 × 50 × 60 mm | the size code; not measured |
| Capacity | 2000 mAh | the design capacity that the firmware gives the fuel gauge |
| Connection | 2 wires with a 2-pin, 1.0 mm pitch JST SH-type plug, into main board `CN1` (SM02B-SRSS-TB) | board files |
| Polarity at `CN1` | pad 1: minus (GND). Pad 2: plus (PACK+) | board files |
| Protection circuit | expected in the pack: the board has no protector part (section 6) | board files |

No specification from the cell's maker is on record. Not known from the records: the maker and model, the charge and discharge current limits, the temperature limits, the cycle life, the weight, and the length of the lead.

Check the polarity of a pack against `CN1` before plugging it in. Packs sold with this plug do not all have the same polarity.

## 10. Internal cables

Two cables, each with 5 wires.

| | Cable 1 | Cable 2 |
|---|---|---|
| From | main board `CN3` | main board `CN2` |
| To | SPS30 PM sensor | LED + touch board `CN1` (`PCB/led-touch`) |
| Plug at the main board | 5-pin, 1.0 mm pitch, JST SH type (SHR-05V-S-B or equivalent) | 5-pin, 1.0 mm pitch, JST SH type (SHR-05V-S-B or equivalent) |
| Plug at the other end | 5-pin, 1.5 mm pitch, JST ZHR-5 | 5-pin, 1.0 mm pitch, JST SH type (SHR-05V-S-B or equivalent) |
| Name in the product's parts list | SPS30 cable, ZHR-5 to SH1.0-5P | JST SH1.0-5P direct cable |
| Length | not on record | not on record |

The headers are JST BM05B-SRSS-TB (top entry) on the main board and SM05B-SRSS-TB (side entry) on the LED + touch board.

The pad numbers below are those of the footprints in the board files. By those numbers, pad 1 at one end joins pad 5 at the other in both cables.

### Cable 1: main board CN3 to SPS30

| CN3 pad | Main-board net | SPS30 pin | SPS30 signal |
|---|---|---|---|
| 5 | +5V | 1 | VDD, 5 V ± 10 % |
| 4 | PM_SDA | 2 | SDA |
| 3 | PM_SCL | 3 | SCL |
| 2 | GND | 4 | SEL: GND selects I2C |
| 1 | GND | 5 | GND |

The SPS30 selects I2C only if SEL is at GND before or at power-up (SPS30 datasheet v2.0, p16). The cable ties SEL to GND.

### Cable 2: main board CN2 to LED + touch board CN1

| CN2 pad | Main-board net | LED + touch board CN1 pad | Net there |
|---|---|---|---|
| 1 | +3.1V | 5 | VCC |
| 2 | SDA | 4 | SDA |
| 3 | SCL | 3 | SCL |
| 4 | INT | 2 | INT (CAP1203 alert) |
| 5 | GND | 1 | GND |

The tables come from the schematics of tag `v1.0`: each row joins the two pads that carry the same signal. The parts list calls cable 2 a "direct" cable, which does not fit a cable that joins pad 1 to pad 5. A footprint's pad numbers need not match the numbers printed on the connector, so the signals are what counts: before ordering cables, check a sample end to end against the signal columns.

### Other connectors

- Main board `CN4` (HCZZ0039-4, 4 pins) is an I2C header: +3.1V, SDA, SCL, GND. The standard product has no cable on it.
- LED + touch board `FPC1` is a 6-pin, 0.5 mm FPC connector wired to the board's supply and to one LP5036 output. The design files do not say what plugs into it.

## 11. Not specified yet

This sheet cannot give the following for v1, because no record of them was found:
- the enclosure's dimensions, and the weight of the finished device;
- the lengths of the two cables;
- the battery's own specification (section 9).

A complete product spec sheet would also give these. They need a measurement or a decision:
- battery life in each mode;
- operating and storage temperature and humidity range of the device;
- measured accuracy of the finished device after compensation, for each quantity;
- GNSS reception inside the enclosure, and which GNSS systems the firmware turns on;
- ingress protection and drop rating;
- radio and safety certifications.

For the operating range, the narrowest part limits on record are:
- SGP41: −10 to 50 °C, 0 to 90 %RH, non-condensing;
- SPS30: 10 to 40 °C and 20 to 80 %RH recommended (−10 to 60 °C absolute);
- S12: calibrated for 15 to 35 °C, works from −10 to 60 °C.

The cell's charging temperature range is not on record.
