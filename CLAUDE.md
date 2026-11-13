# AirGradient GO hardware: instructions for AI agents

KiCad 10 design files of the AirGradient GO, a portable battery-powered air quality monitor. Firmware and enclosure live in other repositories.

## Name the design first

Three designs of the main board are in this repository. Before you read the design or answer a question about it, establish which one you have. Quote the ref and the commit (`git rev-parse --short HEAD`) with everything you find.

| Design | Ref | Main board revision | State |
|---|---|---|---|
| v1 | tag `v1.0` | 1.0 | the first product |
| v2 | tag `v2` | 2.1 | the produced boards |
| v3 | branch `v3-reroute` | 3.0 | prototype; it gets a tag when the design is final |

- Branch `main` is tag `v2` plus documents added later.
- Branches `v2.0`, `v2.1`, `v2.1-no-display` and `v2.1-xtal32k` are working states on the way to v2 and v3, not the produced design: "the v2 board" is tag `v2`.
- The files named below are on `v3-reroute`. If one is missing, you are on another ref.

## Which document answers which question

| Question | Read |
|---|---|
| What the repository holds: boards, key parts, toolchain | `README.md` |
| How v1, v2 and v3 differ; the pin maps of all three; why v1 → v2 changed | `VERSIONS.md` |
| What changed from v2 to v3 and why; what it means for firmware; open points | `CHANGES-v3.md` |
| Why one v3 change was made, with its numbers and datasheet pages (IDs `R-V3-01` to `R-V3-35`) | `design/requirements.md` |
| How a changed block is meant to be connected, pin by pin | `design/airgradient-go-main/connections/*.csv` |
| Product-level specifications; the display, the battery and the cables, which the BOM does not define | `SPEC-SHEET.md` |
| The manufacturer's document for the display, the battery, the Senseair S12 or the GNSS antenna | `documents/README.md`, then the PDF it names |
| A part's value, part number or LCSC number | `PCB/airgradient-go-main/BOM.csv` (schematic) and `production/*_bom.csv` (what is assembled) |

## Reading the design

The schematic (`.kicad_sch`, 1.2 MB) and the board (`.kicad_pcb`, 3.7 MB) are S-expression text, too large to read whole.

- **Connections:** export a netlist and read that. **The drawing:** export a PDF. Both commands are in `CHANGES-v3.md`, section 7.
- **One part or one net:** search the file for its reference or net name.
- **Two versions:** export a netlist from each ref and compare the netlists.

## Traps

- **Manufacturers' documents.** For the display, the battery, the S12 and the GNSS antenna, use the PDFs in `documents/`, not a web search. `documents/README.md` names the look-alike part a search returns for the display, and the S12 document that overrides another one on pin 6.
- **Module, not chip.** U4 is the module ESP32-C5-MINI-1-N4. Take pad numbers, limits and strapping pins from the module datasheet. Label any value that only the ESP32-C5 chip datasheet gives.
- **Not fitted.** A symbol with `(dnp yes)` is not assembled. In v3 that is 42 parts, among them the whole CO read-out (U11, U22, U23, U24 and their passives), U2, TF1, R35 and R46. Check the flag before you report a fault in a circuit.
- **Test points.** The 16 test points (TP1 to TP17) are in the schematic only. The board has none.
- **Reference designators** were renumbered between v1 and v2 (the charger is U3 in v1, U5 afterwards). Across versions, match parts by part number and by net.
- **Rail name.** The system rail's net is `+3.1V` in v2 and `+3.3V` in v3: the same rail, renamed when its voltage was raised.
- **Known and deliberate.** `CHANGES-v3.md`, section 6, lists the open points and the choices made against a reviewer's advice (the 100 kΩ I2C pull-ups are one). Look there and in `design/requirements.md` first; report as new only what neither has.

## Changing the design

Read `design/requirements.md`, section "PCB constraints", before you move a footprint: the parts it lists are fixed by the enclosure and stay where they are.

A change is done when all of these hold:

1. `kicad-cli sch erc` and `kicad-cli pcb drc --schematic-parity`, run before and after, differ only by messages you can explain; 0 unconnected items; schematic and board agree.
2. The change has its row `R-V3-nn` in `design/requirements.md`: what changed, why, and the source of every number (document, revision, page).
3. `CHANGES-v3.md` says the same, and `VERSIONS.md` and `SPEC-SHEET.md` do where the change touches them.
4. `BOM.csv` (exported from the schematic) and `production/` (made by Fabrication Toolkit) are regenerated: they are outputs of the design, so a fix goes into the design and they are made again.

The scripts in `design/airgradient-go-main/eco/` and `layout/` are the record of changes already in the board. Read one to see exactly what a change did. They run under KiCad's Python (`pcbnew`), and some need tools from outside this repository.
