# R02 hardware document increment

The taskbook now has a nine-item [BOM](../../../hardware/bom.csv), a three-page
[wiring candidate](../../../hardware/wiring.pdf), and a source/version/hash
[catalog](../../../hardware/wiring_sources.json). These documents derive from
the already reviewed package map at commit127d1567; they do not add physical results.

Main and independent review checked all15digital signals,4ADC channels,
3external PWM/capture jumpers, the DAC A pre/post-gain signal branches and actual
source conflicts. All3rendered pages were visually checked. J3I2Ccontact numbering
remains unresolved between the official manual and schematic; fitted PCB, external
components, address, electrical levels and timing must be confirmed before wiring.

The first drawing was revised once to connect A3 explicitly to the same DAC A
node as the PGA input. Original files/renders and the exact generator are retained
in `.planning/deepeye-resume-20261018/r02-hardware-docs-20261021`. No old test group,
GPU check or384/384base-overlay test was repeated. No measurement was invented.
This is document acceptance only; physical calibration, custom bit/HWH, R02, R03,
G03 and all29formal cards remain open. H01-H15 and the pinned human contract remain.
