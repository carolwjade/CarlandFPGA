# Reviewed R02 package and electrical candidate

Use the accepted `design.md`, `candidate-pinmap.json` and package-only `candidate.xdc` here. They describe 15 distinct PL package pins, four analog channels, three independent external PWM-to-capture jumper pairs, PGA SPI, DAC I2C and a 3.3 V RS485 transceiver for a future custom overlay. The clock proposal is PS FCLK0 at 100 MHz, distinct from the board's 125 MHz PHY-driven PL reference.

**J3 I2C cable positions remain unresolved.** TUL manual Table16 and schematic sheet4 interchange contacts9/10. The P15 SCL/P16 SDA package mapping is supported, but does not resolve physical header contact numbering. The revised design accounts for board R49/R50 2.2k pullups and gives the correct A0 divider/filter reference designators. Actual PCB revision, peripherals, wiring, clock implementation and measured signals remain unverified.

Main independently reviewed official schematic/manual pixels and source constraints, found three issues in the original candidate, and verified the successor correction. The new conflict check passed13/13; the old44-check suite and completed board384/384 baseline were not repeated. Raw original and revised designs, native terminal evidence, review findings and accepted derivatives are in `evidence.zip`. Main also corrected a PDF page/index notation and an inaccurate author label: the document review was by agents, not a new human review.

`sources.json` records the seven official URLs, revisions, full-file hashes and evidence locations. Full vendor documents/renderings remain in the pinned local source cache; they are not republished in this archive. Archive member hashes are separate from those retained-source hashes.

This is a static integration input. No custom bit/HWH, physical timing, wiring or full R02/R03 acceptance is claimed. H01-H15 and requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` remain unchanged; all29 formal cards remain open.
