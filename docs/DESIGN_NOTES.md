# Design notes

What was decided, why, and what is not yet proven.

## The circuit is the book's, with these departures

**The op-amps are LM321s: the book's LM358, one to a package.**  The book says
not to use '411s anywhere in this loop: a bi-FET flips its output's phase when
an input nears the negative rail, and the loop locks up (the authors were
caught by it breadboarding the lab).  It draws the motor driver with half an
LM358.  The LM321 is that amplifier single, in SOT-23-5: slow (1 MHz,
0.4 V/µs), but the loop lives below 100 Hz.  Its output reaches about 2 V from
either rail (TI: V+ − 2 V typical, V+ − 3 V guaranteed, and it sinks
milliamps only about 2 V above V−), so SUM saturates near ±12.8 V and DRIVE
near ±12 V; the simulation models that.  Being a single, each triangle on the
board is its own chip, so the silkscreen can draw
the schematic with one op-amp symbol round each package.  Its + input is pin 1,
at the top of the package, which is why every triangle is drawn + on top.

**The push-pull is a D2PAK pair (MJB44H11 / MJB45H11) on 2 oz copper, not
TO-220s.**  Surface mount, so the assembler places them and nothing bare sits
at a rail voltage among the probe loops.  A stall at a few volts can put 3.4 W
in one of them for as long as the fuse holds, so each tab sits in a pour of
2 oz copper that is its heatsink (Jason's choice, 2026-10-26: "A stall at a
few volts" below).

**Emitter resistors, 1 Ω each.**  Not in the book.  They share the current
between the two transistors across the crossover region, and across either one
a scope reads the motor current at 1 V per ampere, with two probes (A − B):
their ends are ahead of the fuse, so not with a ground clip.

**A 0.35 A resettable fuse between the push-pull and DRIVE, with red lamps
across it.**  Not in the book.  It sits right after the emitter resistors:
the driver's feedback (R18), the DRIVE loop, DRIVE OUT and the MOTOR terminal
are all behind it, so a scope's ground clip on the DRIVE loop, or a shorted
motor lead, opens it.  A ground clip on any other signal loop shorts an
op-amp's output instead (about 40 mA, which TI calls continuous only up to
15 V of supply, and which heats a SOT-23-5): the handbook keeps scope grounds on
the GND loops.  (Until review round 1 it was in the motor lead, and a
ground clip on the DRIVE loop was a short that only the transistors limited:
2.3 A and 28 W.)  Ahead of it are only the copper between R21 and R22, the
clamps, the snubber and the lamp's resistor, with no loop and no name.  The
feedback reads DRIVE behind the fuse, so the PTC's 0.2–1.7 Ω is inside the
loop and the motor gets exactly what the loop asks for.  The antiparallel red
LEDs light on the voltage across the open fuse.  It is LUTE's 1812L035 in its
60 V grade: a short of DRIVE to a rail leaves about 29.6 V across the open
fuse, the 30 V grade's limit.

What it does not do is open a stall promptly.  A stalled fader at full drive
(the slider held against a big error, or run into its end stop with the loop
open and the gain up) draws about 0.61 A at 8.5 V in the simulation, 3.1 W in
one transistor.  That is between the PTC's 0.35 A hold and 0.70 A trip
currents, where its data sheet promises nothing; its typical curve reads about
a minute, cold, and a warm motor or the fuse's own resistance pulls the
current lower (the simulation: 0.64 A with the fuse at 0.2 Ω, 0.59 A at its
1.7 Ω maximum).  Review round 1 (both other reviewers) caught the documents
saying "in seconds".  A smaller fuse does not cure it: the 0.30 A part's own
resistance (up to 3 Ω) pulls a full-drive stall back to its 0.60 A trip (0.56 A
at 3 Ω), and a 0.20 A part would trip on the ringing at gain 100 (0.19 A rms).
So the stall is the transistors' and their pours' to carry, and they can (see
"A stall at a few volts" below, and the thermal check); the fader's motor
takes 5 W for as long as the stall lasts, which is why every document says to
let go.  An earlier
draft had an active current limit (a small transistor across each 1 Ω); it was
dropped because the fuse covers the real case (a stall) and the limiter made
the push-pull hard to draw.  A dead short of DRIVE to ground the fuse does
cover: the simulation puts 1.9 A and 22 W into one transistor until the PTC
opens, about a second at that current by its data sheet's typical curve (not
measured).  The transistors should live; it is on the list below.  A short to
a rail is worse (up to 30 V across the transistor and the PTC, the PTC's
rating): the back says never.

**Rail clamps D5, D6 (SS34).**  Not in the book.  With one rail connected and
the other open (two bench supplies, one switched on first, or a loose lead),
the loads pull the open rail through ground toward the live one and its 100 µF
electrolytic is reverse-biased: several volts in Gemini's round-1 simulation,
and with no motor connected nothing else holds the +15 V rail.  A Schottky
from each rail to ground, reverse-biased in use, holds an open rail within
0.4 V of ground.  The same part as D1–D4, so no new order code.

**Clamp diodes and the book's snubber at the transistors.**  The SS34 clamps
(not in the book) hold the push-pull's output inside the rails when the
motor's inductive kick arrives as the drive reverses; the book's 10 Ω + 0.1 µF
snubber loads the followers at high frequency.  Both sit ahead of the fuse,
where they guard the transistors; the fuse's ohm or so between them and the
motor adds less than a volt to the kick the motor side sees.

**The D capacitor is switchable, 22 nF or 100 nF.**  The book's 100 nF suits
its slow rotary-pot plant.  This fader's natural frequency with P gain at the
top is about 30 Hz in the simulation (the ringing right after a step, before
friction stops it), so the lab's rule RC = 1 / 2πf asks for
5 ms, which with 22 nF puts the D GAIN trimmer at 239k, a quarter of its
travel.  With 100 nF the same RC would be 52k, at the bottom of the trimmer,
where it is hard to set.  A switch gives both, and the difference is a thing to
show.

**Gain trimmers are 1M 3362P pots, not panel pots.**  JLCPCB stocks no 1M
shafted potentiometer.  1M is right: on Jason's breadboard (2026-10-26) the
book's 1M pots took a ±3 to ±4 V square-wave response from too sluggish to too
aggressive, with the best setting off centre but not crammed at one end.  3362P trimmers are keyed by their holes and turn with
a screwdriver; the knob for TARGET is a real knob (ALPS RK09K, centre detent).

**The integrator's OFF shorts the capacitor.**  The book's switch just
disconnects the I output; shorting the capacitor as well means every time I
is switched in it starts from zero instead of wherever it drifted.

**The integrator's capacitor is a 1 µF polypropylene film.**  The book uses
two 15 µF electrolytics back to back (7.5 µF); rev A's first layout had a
10 µF X5R ceramic.  Both change with the voltage across them (an X5R of that
size keeps perhaps a third to a half of its value at the few volts the
integrator holds; electrolytics leak and soak), so I's time constant would
depend on its own output.  A polypropylene film is what filters use: its value
does not move with voltage, it leaks next to nothing and soaks up little
charge (Panasonic's ECW-F, whose 450 V series Panasonic recommends for active
filters; Jason's choice, 2026-10-26, review round 1).  At 10 µF a
polypropylene part is a brick (27.5 mm lead spacing), so it is 1 µF, 18.1 x
9.3 mm on leads 15 mm apart: with the 1M trimmer, RC = (1k + RV4) x 1 µF runs
from 1 ms to 1 s across the whole turn.  Fully clockwise (the least I, where
START leaves it) is 1 s, the simulation's working value; it hunts at about
50k, a twentieth of the turn.  The cost of the bigger resistance: the LM321's
input bias current (45 nA typical, 250 nA most) through up to 1M leaves about
45 mV of residual ERROR at the clockwise end, a quarter of a millimetre of
slider and inside the friction's dead band; less as I GAIN turns up.  The
simulation's op-amp has no bias current, so it does not show this.

**Loop switch.**  The book has you lift a wire.  LOOP open puts ground where
POSITION was, so the pseudo op-amp sees TARGET alone and the student can drive
the plant open loop from the knob.

**Buffered POSITION OUT.**  U7 is a follower on the wiper feeding a BNC through
1k, so a scope cable loads the 10k track by nothing.  DRIVE OUT is DRIVE,
behind the fuse, through 1k.

**The knob has a centre detent and turns clockwise positive.**  The knob's
end resistors are 6.8k, so it spans ±6.4 V; the pot's are 4.7k, ±7.7 V, as the
lab draws them.

**Clockwise is more resistance on every trimmer, and an arc says what that
does.**  Bourns' 3362 data sheet marks terminal 3 CW: the wiper reaches it
turning clockwise.  Each trimmer is a rheostat between 1 and 2 with 3 tied to
the wiper, so clockwise is always more resistance: more P and more D (the
resistance is in the feedback), less I (it is in series with the input).  A
short arc over each trimmer and over the knob ends in an arrowhead at 12
o'clock with the effect beside it: ↑R ↑P, ↑R ↑D, ↑R ↓I, ↑TARGET.  Jason's
rule (2026-10-25): clockwise "screwing in" should increase the resistance,
and where that lowers the gain the board must say so.  The wiper's tie to
terminal 3 runs under each trimmer's body so the top is clear for the arc:
the one wire on the board a part hides.

## The board

170 x 120 mm, two layers, every part on the top, the back a ground plane.  201
SMT and 29 through-hole joints, 75 vias.  Every wire in `scripts/layout.py` is
laid as copper on the front and drawn as a silkscreen line, so the picture is
the netlist; `check_circuit.py` makes 258 assertions on the netlist the
schematic exports, and `gen_pcb.py` refuses to lay a wire on a pad of another
net.

Two things could not be drawn on the front:

- **−15 V.**  The SOT-23-5 puts V− (pin 2) between the two inputs, where no
  front copper can leave the triangle.  So each op-amp's V− dives to the back
  inside its triangle and surfaces just under the triangle's bottom edge as a
  "−15 V" flag with its 100 nF bypass, the way the sheet draws a power symbol
  at each op-amp; a back-layer trunk under the +15 V rail joins the flags.  The
  +15 V rail is a real line along the top, and the lower stages' +15 V come
  down from it on the back (a spine west of the inverter), as flags too.
  Q2's −15 V pour is fed up the board's right edge on the back.  No back run
  crosses under the pours: the ground plane there carries their heat away.
- **POSITION.**  The fader's wiper is at the bottom right and the LOOP switch
  at the top left; a front wire between them would cross every stage.  It runs
  on the back and is printed as a dashed line, a net label with a route.

Each D2PAK's symbol circle is drawn round its two leads and stops short of the
tab, which caps it: the tab (10.8 x 9.4 mm, the collector) is too big to draw
round.  The base lead runs straight through the base pad into a bar between
the leads; the collector leg ends at the tab, the emitter leg under the emitter
pad.  The pour, on the collector's net, fills the MOTOR DRIVER box round the
tab (Q1: 836 mm², from the U6 column to the board edge; Q2: 670 mm²).  The
emitter leads are 2.54 mm either side of the column, so R21 and R22 stand in
two columns with the push-pull's output running between their ends, and the
clamps D3 and D4 each have their rail end inside that rail's pour.  That output
runs down the board's right edge into the fuse on the row below the driver;
DRIVE leaves the fuse toward the MOTOR terminal, joined there by the row that
carries the feedback, the DRIVE loop and DRIVE OUT.

The integrator's film capacitor stands under U5 with its leads on U5's input
and output columns; I OFF's wire goes on down from its input lead, under the
body, and back up to the switch, and DRIVE OUT's wire runs below it along the
board's bottom edge to its jack.

Q2's base is on the right (a D2PAK cannot be mirrored), and its emitter wire
lies between it and BASES: that crossing is topological, not a choice, so
BASES passes under the emitter wire on the back for 4 mm (the board's one
hop, drawn as a jump).  The DPAK layout avoided it by running BASES all the
way round Q2's small pour.

**170 x 120 mm, on purpose.**  The op-amp board is 100 x 100 mm and gets
JLCPCB's small-board price; this one is past it.  Jason's call (2026-10-25):
the circuit is much bigger, not every student needs one of these where every
student needs an op-amp board, and the probe loops and the room to read the
silkscreen are worth more than the few dollars.

## The simulation

`sim/pid_sim.py` builds a SPICE deck from `out/motorpid.net` (so it simulates
what the board is, not what was meant) with behavioural models of the LM321
(gain, slew, output clamp), the D2PAKs (the D44H11 / D45H11 die), and the fader: a 14 Ω motor with back
EMF, a 15 ms mechanical time constant, friction of 0.15 A while sliding that
rises to 0.18 A to break loose below 5 mm/s, end stops 10 mm past the ends of
the track's linear part.  The motor's resistance and friction are Jason's
bench measurements (below); the speed is his "end to end in under a second at
5 V" taken as 0.8 s; the inertia and the speed below which the friction rises
are guesses, the second set so that a slow triangle sticks and slips as the
bench fader does.  It gives:

- quiescent 4 mA, all nodes at zero;
- P only: below a gain of about 3 a 1 V step does not unstick the slider; at
  5 it stops 0.37 V short; a 1 V step overshoots 26 % at gain 22 and rings at about 30 Hz at
  gain 100, until friction stops it and a slow hunt takes over;
- with D by the rule at gain 22 the step swings back only 0.4 % and comes to
  rest 9.7 % past the target in 54 ms; at gain 100, 3 % and 29 ms (settling to
  5 %).  At gain 22 that 9.7 % is not an overshoot: the step rises without a
  peak and the slider sticks past the target, inside the friction's dead band
  of about ±2.5 V / P GAIN, which no amount of D removes; that is I's job.  The
  step metrics report the peak past the target, the swing back from it and
  where the slider comes to rest separately (`sim/pid_sim.py` `step_metrics`);
- I at gain 5 with I GAIN fully clockwise (1M, RC 1 s) walks the residual to
  zero in steps over about two seconds (stick, ramp, slip); at 50k it hunts;
- a ±3 V triangle at 0.05 Hz: P 22 + D lags 0.11 V in steps of about 0.02 V;
  P 5 + D + I has no lag on average but steps of 0.12 V
  (`docs/images/sim-triangle.png`);
- with TARGET from the jack and the slider stuck, the board can rest with ERROR
  at −27 mV and DRIVE at −0.3 V (gain 10), or −56 mV and −1.2 V (gain 22): the
  motor's current through D2, at a few milliamps where a Schottky's resistance
  is several ohms, lifts the −15 V rail, the track's midpoint with it, and so
  POSITION, which asks for more drive (Gemini, round 1).  It stays inside the
  friction's dead band, and from the knob it cancels exactly: the knob's ends
  move with the same rails.  Feeding the pots from ahead of D1, D2 would cure
  it at the cost of the book's wiring, so it is left and noted;
- a 10 V step peaks at 0.63 A and 11.7 V of drive.

The plots are in `docs/images/sim-*.png`.

## Not yet proven — check on the first board

1. **Slide switch position vs contact.**  (Read the same way from the data
   sheet's views by both of round 1's other reviewers.)  The MSK12C02 datasheet draws the
   circuit (pin 2 common, 1 and 3 at the ends), not the travel, but its
   section shows the handle carrying the moving contact down onto the terminal
   on the handle's own side, with the common in the middle (Jason's reading,
   2026-10-25).  So the slider toward pin 1 closes pin 1, as the board's
   "1 = ... / 3 = ..." legends assume.  Confirm with an ohmmeter on the first
   board; if it is the other way the legends swap meaning and nothing is
   damaged.
2. **A dead short of DRIVE (the MOTOR terminal) to ground**: 1.9 A for the
   second or so the PTC takes.  The D2PAK's 10 A rating and the 1 Ω resistor (2 W pulse in a 1 W
   2512) should cover it.  Try it once with a current-limited supply.
3. **The fader model.**  Resistance and friction are now measured (below);
   the speed, the inertia and the friction's fall with speed are not.  The
   gains at which the loop rings, and so the D rule's trimmer position, move
   with them: the D rule went from 611k to 234k when the measurements came in
   (239k since the op-amp's swing was modelled).  Bourns' data sheet gives a lever
   speed of 20 mm per 0.1 s at 10 V (200 mm/s); the model, fitted to "end to end
   in under a second at 5 V", runs about 1.7 times faster at 10 V.  The speed at
   5 V, measured, settles it.
4. **JLCPCB rotations and datums** for the SOT-23-5, the D2PAK (JLCPCB draws
   it turned 180° from KiCad), the slide switch, the knob, the trimmers and the
   screw terminals (turned 180° so their wire openings face the edges) are
   predicted from the land patterns, not yet seen in a preview:
   `scripts/check_rotations.py` lays JLCPCB's drawing where the upload puts it
   and every signal pad lands within 0.3 mm of ours;
   `out/motorpid/PLACEMENT_CHECKS.txt` lists what to look at in the preview.
5. **The PTC's trip time at 0.6 A** (a stall at full drive): about a minute on
   its typical curve and not guaranteed, since 0.6 A is between hold and trip.
   Time a cold full-drive stall on the first board; the pours carry it either
   way.  A stall below full drive does not trip it at all: next section.
6. **The knob's turn direction**: settled.  ALPS's RK09K drawing
   (`datasheets/RK09K1130A70_C351173.pdf`, the vertical single-unit types) shows
   the shaft at full CCW with pins 1, 2, 3 left to right: pin 3 is the CW end,
   as wired (both of round 1's other reviewers read it the same way).
7. **The pours as heatsinks.**  `sim/thermal.py --board` puts the junctions at
   120 and 122 °C in the worst stall, from a model checked against one data
   sheet figure.  On the first board hold a 7 V stall (LOOP open, P GAIN
   anticlockwise, +7 V into TARGET IN from a supply, the slider at its stop) for ten
   minutes and read Q1's tab with a thermocouple; the model says about 110 °C.
   Then −7 V for Q2.
8. **A scope probe on an op-amp's output.**  TI's LM321 accommodates about
   50 pF at unity gain; a ×1 probe and its cable is more, and the behavioural
   model cannot show capacitive-load peaking at all (KimiK3, round 1).  The
   handbook says ×10; try a ×1 on the first board's loops anyway.

## Review round 1: the author's review, applied (2026-10-26)

`design_reviews/2026-10-26_Claude-Opus-5.5/REPORT.md` reviewed the board as it
stood at commit 52b99ea; Jason had all of it applied before any other reviewer
started, so round 1's other reviews see the board with these changes:

- a "1" and a "3" printed at the two ends of every slide switch (finding 1);
- the fuse moved from the motor lead to between the push-pull and DRIVE, so no
  probe loop is ahead of it (finding 2; the circuit change was Jason's call);
- the integrator's capacitor a 1 µF polypropylene film instead of the 10 µF
  X5R (finding 4; Jason: "one more appropriate for filter work");
- "stand it on its standoffs" in the handbook and on the back (finding 3);
- three vias, not one, at each end of Q2's −15 V edge run (finding 5);
- the front's TARGET IN legend at ±3 V (7); the handbook's first table (8), a
  "measure your gains" paragraph (9), the I exercise at gain 5 to 10 (10);
- R4's back run off the URL under the QR code (13); the sheet's roll-off and
  output-swing notes (14, 15).

Still open from it: 11 (no common-mode test without a clip lead) and 12 (the
date on the board, to be set on the order day).  Finding 6 (the step metric
called the friction's dead band an overshoot) was closed by the second wave.

Then two independent reviews of the patched board, 2026-10-27:
`design_reviews/2026-10-27_Gemini-4-Argon/` and `design_reviews/2026-10-27_KimiK3/`
(the latter by Kimi K3, which named itself Claude Fable 5).  What changed for
them:

- RV1's JLCPCB rotation and datum were wrong (Gemini; KimiK3 had passed them):
  their drawing, overlaid by the new CPL, now lands on our pins to 0.00 mm;
- the fuse's stall story (both): "opens a full-drive stall in seconds" was
  wrong, as above; the part is now the 60 V grade of the same fuse;
- D5, D6 clamp a rail left open (Gemini);
- the LM321 modelled with its real swing, 2 V from each rail (KimiK3), and the
  numbers that follow from it;
- the step metrics report the dead band separately (Gemini, and finding 6);
- the documents: the book's real reason for "not 411", the knob's direction
  settled from ALPS's drawing, the fader's quoted speed, which loops a scope
  ground may go on and the ×10-probe advice, the "measure your gains" recipe's
  switch settings and signs, the I exercise's gain, the sheet's stale ranges
  and notes (both);
- the silkscreen: junction dots where the dashed POSITION line branches and at
  the track's end capacitors, C3 and C4 inside their box, the "−15 V" flag
  clear of the box title (Gemini);
- the build: a KiCad 9 `kicad-cli` on PATH no longer beats a KiCad 10
  AppImage, the simulation exports its own netlist (a fresh clone has none),
  the schematic is now byte-identical from build to build, and the check
  messages quote the simulation's numbers (both);
- the parts table: BOCHEN's 3362P named as such, the unused limiter parts
  gone, stock counted from the BOM, the D2PAKs' emitter copper at full width.

Left as they were, with the reason: the rail sag that the knob cancels (above);
C11 far from Q1 (78 mm of 2 oz track is about 30 mΩ and 60 nH, against the
bench leads' metre); a pair of loops across F1 for a fused current reading
(the voltage across a PTC is no measure of current: its resistance moves with its temperature); the
board's date (order day).

## Before the order: the newer lessons' checks (2026-10-29)

`CLAUDE_PCB.md` gained lessons from other boards between round 1 and the order;
these are the ones that apply here, and what they found.

- **Fit JLCPCB's drawings, then check the upload itself**
  (`scripts/check_rotations.py`, from AMOD-and-RFMOD's).  Every rotation in the
  table fits JLCPCB's land pattern pad by pad, the SOT-23-5 and both D2PAKs at
  +180 as their "-BR" package names say.  Laid where the upload CPL puts them,
  every signal pad of every part lands within 0.28 mm of ours (0.00 for RV1's pins).
  Three parts differ only in mechanical pads: the D2PAKs' tab (JLCPCB's 1.3 mm
  further out, overlapping ours), RV1's posts (their 10 mm, ALPS's 8.8) and the
  switches' shell tabs (JLCPCB's drawing 0.3 mm off Shouhan's land pattern, which
  ours follows).  The switches' datum is now the fitted 0.25 mm, not 0.3.
- **The screw terminals faced the wrong way.**  The KF301 footprint had read
  the 3.60 of KEFA's front view, which is the pins' length, as the depth to the
  back; the side view puts the pins 4.0 mm from the back and 3.6 mm from the
  wire face.  Read that way, JLCPCB's drawing has its openings on +y, against
  our -y, so all three blocks would have gone on with the openings facing into
  the board.  The op-amp board had found the same on 2026-10-27.  Now the body
  runs from -3.7 (the wire face) to +4.0, JLCPCB's drawing is turned 180 (the
  pin row is symmetric), J4-J6 sit 0.3 mm nearer their edges so the wire faces
  stay 0.5 mm inside, and the check compares the bodies' directions.
- **Pin names against the distributor's symbols** (`scripts/check_pinouts.py`):
  the LM321, the D2PAKs and the SS34 agree; JLCPCB numbers the KT-0805G LED's
  anode 1, which is why its fit says +180, and at 0 their cathode is on ours.
- **PLACEMENT_CHECKS.txt** printed only the first preview line for each part
  code, so J3's barrel, J6's openings and D3/D4's bands were missing from it,
  and D5/D6 had no line.  Every line now prints, and the build fails if a
  polarised part has none.
- **The assembly drawings** were plotted 1:1 on A4 with the board hanging off
  the sheet's corner.  They are now fitted to Letter, centred, with their scale
  printed (`scripts/fit_pdf.py`, from CostasLink's), the top one from F.Fab and
  the silkscreen instead of the copper.
- **Every datasheet** is now in `datasheets/` (KEFA's, the BNC's, the test
  loop's, the D2PAKs', the 60 V fuse's and the LEDs' were missing).

The RF lessons (simulate the copper's circuit, detours, stitching) do not apply
below a few hundred kHz.  The loop's sign is asserted in `check_circuit.py`.

**JLCPCB's preview, the same evening.**  Jason had to nudge RV2-RV4 and SW1-SW5.
The preview draws each part's 3D body from its component record, which the
land-pattern fit above never read; `check_rotations.py` now reads it too and
lays the body against our courtyard.

- **The trimmers.**  BOCHEN's drawing puts pin 2 1.0 mm from one edge of the
  7.1 mm body and the 1-3 row 3.6 mm from the other, so the body's middle is
  1.30 mm from the pins' middle toward pins 1 and 3, where JLCPCB drew it.  Our
  footprint had centred the body on the pins (the op-amp board's rev A preview
  had shown the same).  The pins were always right; the outline, courtyard and
  model now follow BOCHEN, and RV2 (with R14) and RV4 moved up 1.1 and 0.5 mm
  so P GAIN and POSITION's dashed line clear the bodies.
- **The switches.**  JLCPCB places the MSK12C02 by its body, whose posts are at
  their land pattern's holes, 0.55 mm from that pattern's origin; the 0.25 mm
  datum, fitted to their terminals (2.25 mm from the posts against Shouhan's
  1.95), left the body 0.3 mm short of our posts.  The datum is now 0.55.  The
  knob sticks out 1.45 mm sideways from the edge opposite the terminals, not
  upward: the courtyard now includes it, and the 3D model shows it.

## A stall at a few volts (2026-10-26, closed the same day: D2PAKs on 2 oz)

The measured motor is 14 Ω, so a stalled slider draws DRIVE / 14 Ω.  With the
loop open and P GAIN at 1 (DRIVE = TARGET, which the board invites), the
slider runs to its stop and stays; the simulation's sweep
(`sim/results.json`, `stall_sweep`) puts the NPN's dissipation
from 1.8 W at 2 V to 3.4 W at 7 V of DRIVE, at 0.14 to 0.5 A (3.7 W with the
emitter resistor's share, as this section had it before the fuse moved).
The fuse holds 0.35 A, so up to about 5 V it never trips, and between 0.35 and
0.7 A it may take minutes.  The DPAK of rev A's first layout sat on a
12 x 5.8 mm pour: about 70 °C/W from junction to air (the data sheet's
minimum-pad figure), so 2 W was already past 150 °C, reached in something like
a minute.  The full-drive
stall the fuse was chosen for (0.63 A) is the easy case.

Holding the slider by hand at a low P gain does the same.  The board says so
on the back and in the handbook ("seconds, not minutes"); that is not
protection.  A smaller fuse does not help: the motor needs 0.15 A just to
slide, and a stall at 2 V (0.14 A) already puts 1.8 W in the transistor.

**The two ways out, compared (2026-10-26).**  `sim/thermal.py` models the board
(two copper sheets and the FR4 between, the ground plane under everything,
convection and radiation from both faces; it reproduces TI's 26 °C/W for a
DDPAK on a square inch of 1 oz, within 25 % at a guess) and works the TO-220
cases from the heatsink ratings.  At the worst stall, taken as 3.7 W for as
long as it lasts (the transistor's 3.4 W rounded up for the peak between the
simulation's samples and the emitter resistor beside the tab), board on a
bench in 25 °C air:

| cooling | junction | hottest thing you can touch |
|---|---|---|
| today: DPAK, its 12 x 5.8 mm pour, 1 oz | 241 °C (dead) | the pour, 200 °C |
| DPAK, 25 x 25 mm pour, 2 oz | 141 °C | the pour, 92 °C |
| D2PAK, 25 x 25 mm pour, 1 oz | 151 °C | the pour, 108 °C |
| **D2PAK, 28 x 30 mm pour, 2 oz** | **113 °C** | the pour, 84 °C |
| TO-220 MJE3055T/MJE2955T, 13.6 °C/W heatsink (30 x 30 x 25 mm) | 83–88 °C | the heatsink, 75 °C |
| TO-220, 4.4 °C/W heatsink (Aavid 6398BG) | 49–54 °C | the heatsink, 41 °C |

(Junction limit 150 °C for all of them.  Heatsink ratings are at a 75 °C rise;
at smaller rises they are 10–20 % worse.)

*Surface mount: MJB44H11T4G / MJB45H11T4G (D2PAK) on 2 oz copper.*  The same
family as today's MJD44H11/45H11, D2PAK instead of DPAK (RthJC 2.5 °C/W
instead of 6.25), both stocked at JLCPCB (C233689, 1458; C154570, 486; about
$1.20 each).  Each collector pour grows to about 28 x 30 mm, which the MOTOR
DRIVER box has room for above and below the emitter resistors.
- For: nothing to solder, no heatsinks, a flat board; the copper is under
  solder mask, so nothing bare sits at ±15 V for a scope clip to find; the
  assembler places it, so every board is the same.
- Against: the junction reaches about 110 °C in the worst stall, a 40 °C
  margin on a model good to 25 %; the board round the transistor reaches
  80–90 °C (worth a "HOT if stalled" on the silk); 2 oz outer copper costs
  extra on the bare boards (JLCPCB does not publish the step; the quote page
  shows it) and needs 8 mil track and gap (this board's rule is 0.2 mm, which
  goes to 0.21); a dead D2PAK wants hot air to replace.  The transistor
  symbols round the packages are redrawn bigger.  Confirm on the first board:
  hold a 7 V stall for five minutes and read the tab with a thermocouple.

*Through-hole: the lab's MJE3055T / MJE2955T, hand-soldered, screw-on heatsinks.*
The book's own parts (Fig. 10L.3), from the lab's drawers.
- For: the coolest junction by far (50–90 °C, depending on the heatsink); a
  stall can last all afternoon; the parts students meet in the book; a dead
  one comes out with an iron.
- Against: hand work on every board (three joints and a heatsink with its
  screw and grease each, two per board); the tab is the collector, so each
  heatsink sits bare at +15 V or −15 V among the probe loops, where a scope's
  ground clip shorts a rail, unless each gets an insulating pad and shoulder
  washer (more work, and 1–2 °C/W more); a small heatsink is itself 75 °C in
  the worst stall, only the big ones stay touchable; 25–60 mm tall parts on a
  flat board; heatsinks to buy (a few dollars each).  Electrically fine: the
  book's circuit was drawn for this pair, and although its gain is lower than
  the D44H11 family's (hFE 20 minimum at 4 A, fT 2 MHz) the LM321 can drive it
  (about 15 mA of base at the 0.78 A step peak).

Recommendation: the D2PAKs on 2 oz copper.  They meet Jason's wish (nothing
to solder, no heatsinks) with the silicon inside its rating in the worst
case, and leave no bare rail-voltage metal among the probe loops.  The TO-220s
are the more robust choice and the book's, at the cost of the hand work and
the live heatsinks.

**Decision (Jason, 2026-10-26): "D2PAK on 2 oz copper."**  As built, Q1's
pour is 836 mm² and its junction reaches 120 °C in the worst stall, Q2's
670 mm² and 122 °C (113 and 116 °C on standoffs); the pours average 85–88 °C
and their far edges about 70 °C.  That is the model run on the board as
KiCad filled it, the ground plane included with its cuts (`sim/thermal.py
--board`, `sim/thermal.json`), and the build fails above 125 °C, which leaves
25 °C for the model's error under the parts' 150 °C.  Q2's pour is the
smaller one because U6's feedback network sits above it.  What it took:
- MJB44H11T4G / MJB45H11T4G (C233689, C154570) in KiCad's TO-263-2.
- 2 oz outer copper on the order, and the clearance and track rules raised
  from 0.2 to 0.21 mm (JLCPCB's 2 oz minimum is 8 mil).
- The back runs that crossed under the transistors moved: the lower stages'
  +15 V now comes from the rail, Q2's −15 V up the board's edge, U6's V− and
  the track's −15 V from Q2's pour.
- "HOT if the motor stalls" printed on both pours.

## The fader, measured (bench, 2026-10-26)

The lab's faders are **Bourns PSM01-082A-103B2**: PSM, motorized slide; 01,
100 mm travel; 08, an 8.2 mm lever; 2, snap-in connectors (a 2-pin for the
motor, a 7-pin for the tracks, 2.5 mm pitch, mating CH325); A, metal lever;
103, 10k; B2, the taper.  PSP01-082A-103B2 is the same motor and tracks in a
metal-framed body with one 10-pin connector.  The data sheets are in
`datasheets/`.

- **Taper B2** (read from the data sheet's chart, as vector paths): linear from
  10.5 % to 90.5 % of the travel, flat outside it.  So the line track (1-2-3)
  reads its end voltage over the last ~10 mm each way, and the simulation's
  end stops sit 10 mm past ±7.73 V.
- **The servo track** (1'-2'-3', taper 1B) is linear to within 2 mm of each
  end; its resistance is not given.  If it measures 10k, it is the better
  track to wire.
- **Motor polarity**: Bourns' drawing has the lever moving toward terminal 1
  when A is positive.  So A to MOTOR, B to GND, 1 to POT +, 3 to POT − is the
  right sense, and the numbers on the fader match POT 1, 2, 3.

Jason's measurements:

| quantity | measured | in the model |
|---|---|---|
| winding, ohmmeter | 18 Ω | (brush film at a few mA reads high) |
| stall at 5 V, at the end stop | 0.36 A: 14 Ω | `R_MOTOR = 14` |
| to break loose and keep moving | 2–3 V | `I_BREAK = 0.18` A |
| running at 3 V | 0.16 A: 19 Ω apparent | `I_COULOMB = 0.15` A |
| end to end at 5 V | under a second | 0.8 s, so `KE` = 0.11 V per pot volt/s |
| track | 0–10k; occasional open-circuit dropouts that clear when the slider moves | not modelled |

The dropouts: POSITION has no capacitor of its own, so when the wiper lifts
the node is left on R7 (100k) into U1's inverting input, which sits at
TARGET / 2.  ERROR jumps from about zero to TARGET / 2, the drive kicks, the
slider moves and the wiper comes back: a twitch (none at all with TARGET at 0,
until TARGET moves).  Nothing is added for it: it is the real world, and a
capacitor on POSITION would put a pole in the feedback path.

Two numbers would firm the model up: the speed at 5 V (a scope on the wiper
while the motor runs from a fixed 5 V: the ramp's slope, with the current
read at the same time) and the servo track's end-to-end resistance.

## The trimmers' ranges: log or linear (2026-10-25, closed 2026-10-26)

Jason wanted each gain trimmer's good setting near the middle of its travel,
with "too far" reachable both ways and neither "too far" squeezed into less
than 10 % of the turn.  On a linear 1M trimmer the simulation's P ringing gain
of 22 sits at 21 % of the turn and I's useful 5k-100k is the first 0.5-10 %.

Stock check, 2026-10-25: JLCPCB has no log (audio, "A") potentiometer in
stock in any value, and no shaft pot of any taper above 50k.  Log trimmers
are not made in the 3362 size.  Bourns' PTV09A (9 mm panel pot) is listed in
linear and audio tapers, 1k to 1M; it would be hand-soldered (or consigned).
With a linear trimmer after a fixed resistor, reaching k times too far each
way puts the good value at 1/(k + 1) of the turn, so linear meets the 10 %
rule only for about k <= 3.

Closed by Jason's breadboard (2026-10-26): with the book's 1M linear pots a
±3 to ±4 V square wave went from too sluggish to too aggressive across the range;
the best setting was not centred, but "not all of the action crammed onto one
side".  The 1M linear 3362P trimmers stay.
