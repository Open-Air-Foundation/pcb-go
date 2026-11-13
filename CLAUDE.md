# AirGradient GO hardware: instructions for AI agents

KiCad 10 design files of the AirGradient GO, a portable battery-powered air quality monitor. Firmware and enclosure live in other repositories.

## Name the design first

Three designs of the main board are in this repository. Before you read the design or answer a question about it, establish which one you have. Quote the ref and the commit (`git rev-parse --short HEAD`) with everything you find.

| Design | Ref | Main board revision | State |
|---|---|---|---|
| v1 | tag `v1.0` | 1.0 | the first product |
| v2 | tag `v2` | 2.1 | the produced boards |
| v3 | branch `v3-reroute` | 3.0 | prototype; it gets a tag when the design is final |

- **This branch, `main`, holds v2:** tag `v2` plus documents added later.
- v3 is on branch `v3-reroute`, which has a `CLAUDE.md` of its own. For work on v3, check that branch out and read that file.
- Branches `v2.0`, `v2.1`, `v2.1-no-display` and `v2.1-xtal32k` are working states on the way to v2 and v3, not the produced design: "the v2 board" is tag `v2`.

## Which document answers which question

| Question | Read |
|---|---|
| What the repository holds: boards, key parts, toolchain | `README.md` |
| Product-level specifications of v2; its display, battery and cables, which the BOM does not define | `SPEC-SHEET.md` |
| The same for v1 | `SPEC-SHEET-v1.md` |
| A part's datasheet: the ESP32-C5 module, the charger, the fuel gauge, the sensors, the display, the battery, the Senseair S12 | `documents/README.md`, then the PDF it names |
| A part's value, part number or LCSC number | `PCB/airgradient-go-main/BOM.csv` (schematic) and `production/*_bom.csv` (what is assembled) |
| How v1, v2 and v3 differ; the pin maps of all three; why v1 → v2 changed | `VERSIONS.md`, on branch `v3-reroute` |
| What v3 changes in v2 and why: the known weaknesses of v2 | `CHANGES-v3.md`, on branch `v3-reroute` |

Read a file of another branch without leaving this one: `git show origin/v3-reroute:VERSIONS.md`.

## Reading the design

The schematic (`.kicad_sch`, 1.1 MB) and the board (`.kicad_pcb`, 3.2 MB) are S-expression text, too large to read whole.

- **Connections:** export a netlist and read that. **The drawing:** export a PDF.

  ```
  kicad-cli sch export netlist --format kicadxml -o netlist.xml PCB/airgradient-go-main/airgradient-go-main.kicad_sch
  kicad-cli sch export pdf -o schematic.pdf PCB/airgradient-go-main/airgradient-go-main.kicad_sch
  ```

  `kicad-cli` comes with KiCad; on macOS it is `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
- **One part or one net:** search the file for its reference or net name.
- **Two versions:** export a netlist from each ref and compare the netlists.

## Traps

- **Datasheets.** For a part that `documents/` holds, read its PDF there: it is the revision whose pages the spec sheets cite, and a web search returns other revisions and look-alike parts. `documents/README.md` names the traps: the look-alike display, the S12 notice that overrides the S12 specification on pin 6, and the documents that are not there.
- **Module, not chip.** U4 is the module ESP32-C5-MINI-1-N4. Take pad numbers, limits and strapping pins from the module datasheet (`documents/mcu/`). Label any value that only the ESP32-C5 chip datasheet gives.
- **Not fitted.** A symbol with `(dnp yes)` is not assembled. In v2 that is 27 parts, among them U2, TF1 and U11 (the place for a CO sensor). Check the flag before you report a fault in a circuit.
- **Test points.** The 16 test points (TP1 to TP17) are in the schematic only. The board has none.
- **Reference designators** were renumbered between v1 and v2 (the charger is U3 in v1, U5 afterwards). Across versions, match parts by part number and by net.
- **Rail name.** The system rail's net is `+3.1V` here (3.11 V). v3 raises it to 3.31 V and renames it `+3.3V`.
- **Known in v2.** v3 exists because of what was found in v2. Before you report a fault in v2 as new, look in `CHANGES-v3.md` on branch `v3-reroute`, section 3: it lists what v3 changes in v2, with the reason for each.

## Changing the design

`main` records the boards that were produced. New design work is on `v3-reroute`.

A change here is done when all of these hold:

1. `kicad-cli sch erc` and `kicad-cli pcb drc --schematic-parity`, run before and after, differ only by messages you can explain; 0 unconnected items; schematic and board agree.
2. `BOM.csv` (exported from the schematic) and `production/` (made by Fabrication Toolkit) are regenerated: they are outputs of the design, so a fix goes into the design and they are made again.
3. `README.md` and the spec sheet say the same as the design.
