# Manufacturing

One board, two layers, 170 x 120 mm, every part on the top side, a solid
ground plane on the back.  It passes ERC, DRC with schematic parity, the
258 circuit assertions and the fab-package checks with zero violations,
and `./make.py` rebuilds and rechecks everything from scratch in about a minute.

## What to upload

| file | where it goes |
|---|---|
| `out/motorpid/motorpid-gerbers.zip` | the *Add gerber file* box |
| `out/motorpid/motorpid_bom_jlcpcb_upload.csv` | the BOM box (JLCPCB's column layout) |
| **`out/motorpid/motorpid_cpl_jlcpcb_upload.csv`** | the CPL / pick-and-place box, at JLCPCB |
| `out/motorpid/motorpid_cpl_kicad_native.csv` | the CPL box at any other fab |
| `out/motorpid/motorpid-assembly-notes.txt` | paste into the assembly remark |

## The order form, field by field

The same list is in `out/motorpid/motorpid-fabrication-notes.txt` to keep open while
ordering.  The values that come from the board are computed, not typed.

| field | pick | why |
|---|---|---|
| **PCB** | | |
| Base Material | FR-4 | the default |
| Layers | 2 | what the gerber set contains |
| Dimensions | 170 x 120 mm | read from the board outline; past the 100 x 100 mm discount, so the bare boards cost a little more |
| PCB Qty | 5 | the minimum; 10 costs about $15 more |
| Product Type | Industrial/Consumer electronics | the default |
| **PCB Specifications** | | |
| Different Design | 1 | one board in the outline |
| Delivery Format | Single PCB | no panel |
| PCB Thickness | 1.6 mm | the BNC flanges, the knob and the terminal blocks expect it |
| PCB Color | Green | any; the white silkscreen reads best on green or black |
| Silkscreen | White | the default for green |
| Material Type | FR4-Standard TG 135-140 | the default; the worst stall holds the board round a transistor near 110 C, below the TG |
| Surface Finish | LeadFree HASL | students handle this board: lead-free.  ENIG is fine too |
| **High-spec Options** | | |
| Outer Copper Weight | 2 oz | NOT the default: the copper round Q1 and Q2 is their heatsink (DESIGN_NOTES, "A stall at a few volts"); the 0.21 mm rules assume it |
| Via Covering | Tented | or Plugged if the form upgrades it: either is fine, no via must stay open |
| Min via hole size/diameter | 0.3 mm / (0.4 / 0.45 mm) | the smallest via on the board is 0.30 mm drill, 0.80 mm pad |
| Board Outline Tolerance | +/-0.2 mm (Regular) | nothing mates with the edge |
| Confirm Production file | No | the gerbers are checked here |
| Mark on PCB | Remove Mark | the whole front is a drawing; nowhere for an order number |
| Electrical Test | Flying Probe Fully Test | the default |
| Gold Fingers | No |  |
| Castellated Holes | No |  |
| Edge Plating | No |  |
| **PCB Assembly** | | |
| PCBA Type | Economic | all parts on one side, nothing fine-pitch |
| Assembly Side | Top | every part is on the front |
| PCBA Qty | 2, or as many as the class needs | the per-order fees are the same for 2 or 20 |
| Edge Rails/Fiducials | Added by JLCPCB | the board carries three fiducials; rails do no harm, removed before delivery |
| Confirm Parts Placement | Yes | look at the preview against PLACEMENT_CHECKS.txt before paying |
| Parts Selection | By JLCPCB | every BOM line has an LCSC code |
| Through-hole parts | keep them: C8, J1, J2, J3, J4, J5, J6, RV1, RV2, RV3, RV4 | the form lists them separately; the BNCs, terminals, knob and trimmers are meant to be fitted |
| Bake Components | No | nothing moisture-sensitive |
| Stencil | none | JLCPCB keeps its own; nothing to order |

## Cost

The board has **201 SMT joints** and **29 through-hole joints** on
48 BOM lines; 13 distinct order codes are JLCPCB *Extended* parts
(the op-amps, the BNCs, the terminal blocks, the knob, the trimmers, the slide
switches, the test loops, the power transistors, the bulk capacitors, the integrator's
film capacitor, the fuse and the 1 ohm resistors),
each with a one-off $3.00 feeder fee.  Parts alone are
**$12.21 per board**, of which the three BNC jacks are
$3.88 and the 17 test loops $1.64.

**2 boards, fully assembled, through-hole parts included**

| line | cost |
|---|---|
| bare PCBs (5 made) | $21.00 |
| parts ($12.21 x 2) | $24.42 |
| assembly: setup $8.00 + stencil $1.50 + THT setup $3.58 + 13 extended codes + 402 SMT and 58 THT joints | $54.50 |
| shipping (DHL) | $22.00 |
| **total** | **$121.92**  ($60.96 each) |

**5 boards, fully assembled, through-hole parts included**

| line | cost |
|---|---|
| bare PCBs (5 made) | $21.00 |
| parts ($12.21 x 5) | $61.04 |
| assembly: setup $8.00 + stencil $1.50 + THT setup $3.58 + 13 extended codes + 1005 SMT and 145 THT joints | $58.14 |
| shipping (DHL) | $22.00 |
| **total** | **$162.18**  ($32.44 each) |

**10 boards, fully assembled, through-hole parts included**

| line | cost |
|---|---|
| bare PCBs (10 made) | $36.00 |
| parts ($12.21 x 10) | $122.08 |
| assembly: setup $8.00 + stencil $1.50 + THT setup $3.58 + 13 extended codes + 2010 SMT and 290 THT joints | $64.20 |
| shipping (DHL) | $22.00 |
| **total** | **$244.28**  ($24.43 each) |

**20 boards, fully assembled, through-hole parts included**

| line | cost |
|---|---|
| bare PCBs (20 made) | $64.80 |
| parts ($12.21 x 20) | $244.16 |
| assembly: setup $8.00 + stencil $1.50 + THT setup $3.58 + 13 extended codes + 4020 SMT and 580 THT joints | $76.31 |
| shipping (DHL) | $22.00 |
| **total** | **$407.27**  ($20.36 each) |

The fixed fees dominate a small order: a second board costs about
$13.42 more than the first, so order one per bench, not one per class.

## Rotations JLCPCB needs

JLCPCB places from its own drawing of each part, and for some parts that
drawing is turned from KiCad's footprint, so a placement file that is right
everywhere else is wrong there by a fixed angle.  The upload CPL has these
angles already applied, per LCSC code, from `scripts/parts.py`:

| parts | LCSC | turned by | datum shift | evidence |
|---|---|---|---|---|
| RV1 | C351173 | 270 deg | (+3.50, -2.50) mm | predicted: RK09K: their pins along +x at the body's bottom edge, pin 1 at -x, the posts above; turned 270, the pins land on KiCad's (overlay of easyeda C351173: 0.00 mm); their origin is the body's middle, 3.5 mm from the pins toward the posts.  Their posts are 10 mm apart, ALPS's slots 8.8: the preview shows each post 0.6 mm off its slot (review round 1) |
| Q2 | C154570 | 180 deg | (-2.45, +0.00) mm | predicted: D2PAK, the same drawing as the NPN |
| Q1 | C233689 | 180 deg | (-2.45, +0.00) mm | predicted: D2PAK: their pins at +x, KiCad's TO-263-2 at -x; turned, their pins land 2.45 mm from KiCad's origin toward the pins (the tabs differ) |
| J4, J5, J6 | C474882 | 180 deg | none | predicted: KF301-3P: pins along x at -5/0/+5 in both drawings; EasyEDA draws the wire-entry arrows on +y, the body 3.7 mm that way and 4.0 the other; ours face -y (the board edge): the pin row is symmetric, so +180 turns only the body (the op-amp board's review round 1) |
| U1, U2, U3, U4, U5, U6, U7 | C9405 | 180 deg | none | predicted: SOT-23-5: their pad 1 at (+1.3,+0.95), KiCad's at (-1.14,-0.95); +180 was read on 59 SOT-23-5 placements on the GPSDO board |
| J1, J2, J3 | C41416668 | 90 deg | none | read: BNC-KYWE-295-W4-N: Lorenz board rev A/B preview, built and working |
| RV2, RV3, RV4 | C118945 | 0 deg | none | predicted: 3362P: their pads 1/3 at y=+1.27 and 2 at y=-1.27, as drawn here; their 3D body 1.30 mm toward pins 1 and 3, as BOCHEN's drawing (rev A's preview, 2026-10-29: our first outline was centred on the pins) |
| F1 | C18198330 | 0 deg | none | predicted: 1812 fuse: two pads along x, not polarised |
| LED1, LED2 | C2297 | 0 deg | none | read: KT-0805G on KiCad's LED_0805: GPiBridge rev A preview, cathode at pad 1 |
| C8 | C242107 | 0 deg | none | predicted: ECWF2W105JA: two leads on 15 mm along x, origin the body's middle in both drawings (easyeda CAP-TH_L18.1-W9.3-P15.00-D0.8); not polarised |
| R21, R22 | C3000711 | 0 deg | none | predicted: 2512: pads along x, not polarised |
| SW1, SW2, SW3, SW4, SW5 | C431540 | 0 deg | (+0.00, +0.55) mm | predicted: MSK12C02: pins along x in both drawings, pin 1 at -x; their origin 0.55 mm from ours toward the terminals, so their posts (and their 3D body) sit on ours.  Their land pattern's terminals are 2.25 mm from the posts against Shouhan's 1.95, and a datum of 0.25 that fitted them left the body 0.3 mm short in rev A's preview (Jason nudged all five, 2026-10-29) |
| C11, C12 | C46550402 | 0 deg | none | predicted: SMD electrolytic: pads along x, pad 1 (+) at -x in both drawings |
| TP1, TP2, TP3, TP4, TP5, TP6, TP7, TP8, TP9, TP10, TP11, TP12, TP13, TP100, TP101, TP102, TP103 | C5199800 | 0 deg | none | predicted: RH-5019 test loop: one 4.0 x 2.2 pad, as drawn here; the loop lies along x |
| LED3, LED4 | C84256 | 0 deg | none | read: NCD0805R1 on KiCad's LED_0805: GPiBridge rev A preview, cathode at pad 1 |
| D1, D2, D3, D4, D5, D6 | C8678 | 0 deg | none | predicted: SS34 SMA: cathode (pad 1) at -x in both drawings |

*read* means seen in a JLCPCB preview on a real order of that part on that
footprint; *predicted* means derived by fitting JLCPCB's own land pattern
onto ours by pin number (`scripts/easyeda.py <code>`).  Every predicted part is
in `out/motorpid/PLACEMENT_CHECKS.txt`, the list to hold against the preview.
After adding or changing a part, run `scripts/check_rotations.py` (the fit, and
JLCPCB's drawing laid where the upload puts it) and `scripts/check_pinouts.py`
(our symbols' pin names against JLCPCB's); they need the network, so the build
does not run them.
`check_outputs.py` proves the two CPL files differ in nothing but those angles.

## Check these in the preview before you pay

| part | what to look for | should be |
|---|---|---|
| U1, U2, U3, U4, U5, U6, U7 | SOT-23-5: three pads on the left, two on the right | the three-pad side under the triangle's inputs (left); pin 1 top-left |
| Q1 | D2PAK tab | tab pointing UP into the copper pour, the two leads down inside the circle |
| Q2 | D2PAK tab | tab pointing DOWN into the copper pour, the two leads up inside the circle |
| SW1, SW2, SW3, SW4, SW5 | MSK12C02 slide switch: the three pins on one edge | SW1, SW2: pins along the bottom edge of the body; SW3, SW4, SW5: pins down the left edge |
| RV1 | RK09K knob, keyed by its two posts | fits one way; the shaft up, the pins toward the switch |
| RV2, RV3, RV4 | 3362P trimmer, keyed | fits one way; screw on top, wiper pin toward the top |
| J1, J2 | BNC barrel | pointing off the LEFT edge |
| J3 | BNC barrel | pointing off the BOTTOM edge |
| J4, J5 | screw terminal wire openings | facing the BOTTOM edge |
| J6 | screw terminal wire openings | facing the TOP edge |
| D1, D2 | SMA cathode band | D1 cathode on the LEFT (toward the rail); D2 cathode at the TOP (toward the terminal) |
| D3, D4 | SMA cathode band | both cathodes UP: D3's into the +15 V pour, D4's toward the push-pull's output row above it |
| D5, D6 | SMA cathode band | D5 cathode UP toward the +15 V rail; D6 cathode DOWN toward its ground (its anode up to the -15 V rail) |
| LED1, LED2 | 0805 LED cathode mark | LED1 cathode DOWN toward its ground via; LED2 cathode UP toward its 10k |
| LED3, LED4 | 0805 LED cathode mark | antiparallel across the fuse: LED3 cathode on the RIGHT, LED4 cathode on the LEFT |
| C11, C12 | electrolytic stripe (negative) | C11 negative DOWN toward its ground; C12 negative UP toward the -15 V rail (its + DOWN to ground) |
| TP1-TP13, TP100-TP103 | test loops | the loop lying along the pad's long side; not polarised |

The parts that cannot go in wrong are the knob and the three trimmers: their
hole patterns fit one way.  `check_outputs.py` re-derives that from the board
file on every build.  The BNCs are not keyed (four symmetric posts and a centre
pin), which is why their correction is read, not predicted, and worth a glance.

## The through-hole parts

11 parts are through-hole: **C8, J1, J2, J3, J4, J5, J6, RV1, RV2, RV3, RV4**, the three BNC
jacks, the three terminal blocks, the knob and the three trimmers.  They are in the BOM and the
CPL and JLCPCB fits them for a per-order fee plus pennies a joint; keep them
selected when the form lists them.  If you would rather solder them yourself
they are the 29 largest, easiest joints on the board.  Everything else is 0805,
1206, 2512, SMA or SOT-23-5 and is hand-workable with a fine iron; the two
D2PAKs' tabs sit in 2 oz pours and need hot air or a large iron to move.

## Parts, stock and alternates

Stock as JLCPCB's parts API reported it on 2026-10-24; the build re-reads
every code's description against the value and package here and stops if
one has changed.  JLCPCB's assembly stock is what counts and their BOM
upload shows it per line.

| ref | value | LCSC | JLC | unit | stock then | notes |
|---|---|---|---|---|---|---|
| C1,C2,C3,C4 | 10uF | C15850 | basic | $0.0426 | 9,137,411 | X5R 25V 0805: the pot's end decoupling |
| C5 | 22nF | C1729 | basic | $0.0084 | 478,982 | X7R 50V 0805: the D capacitor for the slide pot |
| C6,C10,C13,C14,C20,C21,C22,C23,C24,C25,C26,C27,C28,C29,C30,C31,C32,C33 | 100nF | C49678 | basic | $0.0205 | 22,485,395 | X7R 50V 0805 |
| C7 | 470pF | C1743 | basic | $0.0075 | 438,251 | X7R 50V 0805: rolls the differentiator off |
| C8 | 1uF | C242107 | extended | $0.3259 | 2,052 | 1 uF 5 % metallized polypropylene film, 450 V, Panasonic ECW-F, 18.1 x 9.3 mm, leads on 15 mm: the integrator's capacitor, C8 |
| C9 | 330nF | C1740 | preferred | $0.0207 | 103,724 | X7R 50V 0805: the driver's split feedback, the book's 0.33 uF |
| C11,C12 | 100uF | C46550402 | extended | $0.0423 | 200,110 | 100 uF 25 V aluminium electrolytic, SMD 6.3 x 5.4 mm, one per rail at the motor driver: the motor draws 0.8 A pulses through a metre of bench lead |
| D1,D2,D3,D4,D5,D6 | SS34 | C8678 | basic | $0.0351 | 3,642,483 | 3 A 40 V Schottky, SMA.  Two in series with the supplies (a reversed bench supply does nothing) and two clamping the motor node to the rails (the motor's inductive kick when a brush breaks contact) |
| F1 | 0.35A | C18198330 | extended | $0.0667 | 9,170 | LUTE resettable fuse between the push-pull and DRIVE: 0.35 A hold, 0.7 A trip, 60 V, 0.2-1.7 ohm.  Opens a short of DRIVE (2 A) in about a second and resets when the drive stops; a full-drive stall (about 0.6 A) sits between hold and trip and may take a minute or more.  The loop's running current is 50-190 mA rms even when it rings (sim/pid_sim.py) |
| J1,J2,J3 | BNC | C41416668 | extended | $1.2929 | 215 | 50 ohm BNC jack, right angle, 4 ground posts on 8x8 mm (the op-amp board's jack: JLCPCB rotation +90 read off a real preview) |
| J4 | MOTOR + - shield | C474882 | extended | $0.1396 | 28,051 | 3-way 5.0 mm screw terminal block, blue: MOTOR, POT and POWER all use the same block so one order code covers the three |
| J5 | POT 1 (+) 2 (wiper) 3 (-) | C474882 | extended | $0.1396 | 28,051 | 3-way 5.0 mm screw terminal block, blue: MOTOR, POT and POWER all use the same block so one order code covers the three |
| J6 | +15 / GND / -15 | C474882 | extended | $0.1396 | 28,051 | 3-way 5.0 mm screw terminal block, blue: MOTOR, POT and POWER all use the same block so one order code covers the three |
| LED1,LED2 | GREEN | C2297 | basic | $0.0164 | 2,420,908 | green 0805 LED, one per rail, 1.2 mA through 10k: rails at a glance (JLCPCB rotation 0 on KiCad's LED_0805, read in GPiBridge's preview) |
| LED3,LED4 | RED | C84256 | basic | $0.0135 | 3,082,781 | red 0805 LED, two anti-parallel across the fuse with 1k: lights only when the fuse has tripped (more than 2 V across it), either polarity |
| Q1 | MJB44H11 | C233689 | extended | $1.2244 | 1,458 | 10 A 80 V 50 W NPN, D2PAK (1 = B, 2 = C on the tab, 3 = E): the upper half of the motor driver's push-pull.  Its tab is the +15 V rail; the copper round it is its heatsink |
| Q2 | MJB45H11 | C154570 | extended | $1.1573 | 486 | 10 A 80 V 50 W PNP, D2PAK: the lower half of the push-pull, tab on the -15 V rail |
| R1,R2 | 6.8k | C17772 | basic | $0.0029 | 567,224 | the target knob's end resistors: +/-6.4 V |
| R3,R4 | 4.7k | C17673 | basic | $0.0051 | 4,750,437 | the motor pot's end resistors: +/-7.7 V |
| R5,R6,R7,R8 | 100k | C149504 | basic | $0.0059 | 3,369,385 | the error amplifier's four |
| R9,R10,R11,R12,R13,R14,R18,R26,R27 | 10k | C17414 | basic | $0.0034 | 54,265,030 |  |
| R15,R17,R23 | 1k | C17513 | basic | $0.0035 | 43,108,325 |  |
| R19 | 270R | C17590 | preferred | $0.0070 | 352,205 | the push-pull's base resistor, the book's 270 |
| R20 | 10R | C17415 | basic | $0.0040 | 5,960,192 | the motor snubber, the book's 10 ohm |
| R21,R22 | 1R | C3000711 | extended | $0.0313 | 73,941 | 2512, 1 W: the push-pull's emitter resistors; 1 V per ampere of motor current across either |
| R24,R25 | 1k | C4410 | basic | $0.0085 | 1,945,919 | 1206, 0.25 W: the series resistors to the BNC outputs |
| RV1 | 10k | C351173 | extended | $0.5335 | 6,351 | ALPS RK09K 9 mm vertical potentiometer, 10 k linear, 30 mm knurled knob shaft with a centre detent: TARGET.  The detent is 0 V |
| RV2,RV3,RV4 | 1M | C118945 | extended | $0.1585 | 1,113 | 3362P 1 M single-turn cermet trimmer (BOCHEN's, Bourns' pattern and pinout: the wiper reaches 3 turning clockwise), top adjust: P GAIN, D GAIN and I GAIN.  JLCPCB stocks no 1 M potentiometer with a shaft, so these take a screwdriver; the slot shows the setting |
| SW1 | TARGET SOURCE | C431540 | extended | $0.0544 | 194,273 | SPDT slide switch, SMD, 2 = common; the knob slides toward the pin it connects.  TARGET source, LOOP, D, I and the D capacitor |
| SW2 | LOOP | C431540 | extended | $0.0544 | 194,273 | SPDT slide switch, SMD, 2 = common; the knob slides toward the pin it connects.  TARGET source, LOOP, D, I and the D capacitor |
| SW3 | D IN / OFF | C431540 | extended | $0.0544 | 194,273 | SPDT slide switch, SMD, 2 = common; the knob slides toward the pin it connects.  TARGET source, LOOP, D, I and the D capacitor |
| SW4 | I IN / OFF | C431540 | extended | $0.0544 | 194,273 | SPDT slide switch, SMD, 2 = common; the knob slides toward the pin it connects.  TARGET source, LOOP, D, I and the D capacitor |
| SW5 | D CAPACITOR | C431540 | extended | $0.0544 | 194,273 | SPDT slide switch, SMD, 2 = common; the knob slides toward the pin it connects.  TARGET source, LOOP, D, I and the D capacitor |
| TP1 | TARGET | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP2 | ERROR | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP3 | P | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP4 | D | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP5 | I | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP6 | SUM | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP7 | DRIVE | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP8 | POSITION | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP9 | +15V | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP10 | -15V | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP11 | BASES | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP12 | U6 OUT | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP13 | U7 OUT | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP100,TP101,TP102,TP103 | GND | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| U1,U2,U3,U4,U5,U6,U7 | LM321 | C9405 | extended | $0.1578 | 193,397 | LM321 (TI): the single-amplifier LM358, SOT-23-5, 3-32 V, 1 MHz, 0.4 V/us, inputs to V- and to V+ - 1.5 V, no phase reversal (the book: 'not 411'). One package per triangle so the silkscreen is the schematic |

### If something is out of stock

**LM321MFX/NOPB** (C9405)
  - LM321DTR (XBLW) / C18723612 (398k, $0.03)
  - LM321MF (UTC) / C668208 (391k, $0.04)

**MJB44H11T4G** (C233689)
  - MJB44H11G / C80690 (355)
  - MJB44H11T4-A (ST) / C2802057 (708)

**MJB45H11T4G** (C154570)
  - MJB45H11G / C463327 (151)

**JVJ25V100M6x5** (C46550402)
  - RST100UF25V004 / C4747964 (196k)
  - RVT25V100M6X5 / C47023107 (141k)

**ECWF2W105JA** (C242107)
  - C352S105J62C000 (Faratronic) / C401331 (3757, $0.22, 15 mm)
  - ECWFE2W105J / C178481 (987, $0.58)

**RK09K1130A70** (C351173)
  - RK09K1130AAU / C202373 (20 mm flat shaft, no detent)
  - RK09K1130AP5 / C470295 (15 mm screwdriver shaft)

**3362P-1-105** (C118945)
  - 3362P-1-105LF (Bourns) / C111656 (1278 in stock, $0.41)

**MSK12C02** (C431540)
  - MSK12C02-HB / C431541 (78k, black knob)
  - MSK12C02-SZ / C2681568 (26k)

**BNC-KYWE-295-W4-N** (C41416668)
  - HL2-BNC-KYWE / C48606310 (107 in stock)
  - MLD-BNC-KYWE-L29.5 / C52766468 (12 in stock)

**RH-5019** (C5199800)
  - RH-5015 / C5199798 (276k): the smaller 2.7 x 1.0 mm loop, same idea

**SS34** (C8678)
  - SS34 / C115205 (67k)
  - SS34A / C211775 (100k)

**1812L035/60GR** (C18198330)
  - 1812L035/30GR / C18198328 (40k, 30 V: at its limit in a short to a rail)

The thinnest line is the BNC-KYWE-295-W4-N: 215 in stock and 3 per
board, about 71 boards' worth; next the 3362P-1-105 at about 371.
The BNC alternates share the 'BNC-KYWE' body (10 x 10 mm flange, four posts on
8 x 8 mm, centre pin), so the footprint takes any of them.  Any 100 mm motorized
fader with a 10k track and a 6-11 V motor is the plant; see the handbook.

## After the boards arrive

The bring-up order, the expected voltage at every loop and the student
exercises are in [HANDBOOK.md](HANDBOOK.md).  In one line: with the fader
unplugged and the LOOP switch open, power it at ±15 V, both green lamps light,
and the TARGET knob moves the P loop's output; then wire the fader and close
the loop at a P gain of a few.

