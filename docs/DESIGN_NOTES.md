# Design notes

What was decided, why, and what is not yet proven.

## The circuit is the book's, with these departures

**The op-amps are LM321 singles, not '411s.**  The lab says "not 411" for the
motor driver (the 411's output cannot drive the push-pull's bases) and uses
411s elsewhere.  One type everywhere keeps the BOM short; the LM321 is a
single 358-class amplifier in SOT-23-5, slow (1 MHz, 0.4 V/µs) but the loop
lives below 100 Hz, and its output reaches within 1.5 V of the rails.  Being a
single, each triangle on the board is its own chip, so the silkscreen can draw
the schematic with one op-amp symbol round each package.  Its + input is pin 1,
at the top of the package, which is why every triangle is drawn + on top.

**The push-pull is a DPAK pair (MJD44H11 / MJD45H11), not TO-220s.**  Surface
mount, so the assembler places them; 8 A parts, so a stall is nothing to them
thermally for the seconds the fuse allows.  Each tab sits on a copper pour.

**Emitter resistors, 1 Ω each.**  Not in the book.  They share the current
between the two transistors across the crossover region, and across either one
a scope reads the motor current at 1 V per ampere.

**A 0.35 A resettable fuse in the MOTOR line, with red lamps across it.**  Not in
the book.  A stalled fader at full drive (the slider held against a big error,
or run into its end stop with the loop open and the gain up) draws about
0.63 A at 8.9 V in the simulation, 3.4 W in one transistor.  The PTC holds
0.35 A and trips at about twice that, so that stall opens it in seconds and it
recloses when the drive stops; the antiparallel red LEDs light on the voltage
across the open fuse.  A stall at a lower drive is not covered: see "A stall
at a few volts" below.  An earlier draft had an active
current limit (a small transistor across each 1 Ω); it was dropped because the
fuse covers the real case (a stall) and the limiter made the push-pull hard to
draw.  What the fuse does not cover is a dead short of MOTOR to ground: the
simulation puts 2.0 A and 29 W into one transistor until the PTC opens, which
is under a second at that current.  The transistors should live; it is on the
list below.

**Clamp diodes from DRIVE to both rails (SS34).**  Not in the book.  The motor's
inductive kick when the drive reverses stays inside the rails.

**The D capacitor is switchable, 22 nF or 100 nF.**  The book's 100 nF suits
its slow rotary-pot plant.  This fader's natural frequency with P gain at the
top is about 31 Hz in the simulation (the ringing right after a step, before
friction stops it), so the lab's rule RC = 1 / 2πf asks for
5 ms, which with 22 nF puts the D GAIN trimmer at 234k, a quarter of its
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

**Loop switch.**  The book has you lift a wire.  LOOP open puts ground where
POSITION was, so the pseudo op-amp sees TARGET alone and the student can drive
the plant open loop from the knob.

**Buffered POSITION OUT.**  U7 is a follower on the wiper feeding a BNC through
1k, so a scope cable loads the 10k track by nothing.  DRIVE OUT is the raw push-
pull output through 1k.

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

170 x 120 mm, two layers, every part on the top, the back a ground plane.  200
SMT and 27 through-hole joints, 66 vias.  Every wire in `scripts/layout.py` is
laid as copper on the front and drawn as a silkscreen line, so the picture is
the netlist; `check_circuit.py` makes 249 assertions on the netlist the
schematic exports, and `gen_pcb.py` refuses to lay a wire on a pad of another
net.

Two things could not be drawn on the front:

- **−15 V.**  The SOT-23-5 puts V− (pin 2) between the two inputs, where no
  front copper can leave the triangle.  So each op-amp's V− dives to the back
  inside its triangle and surfaces just under the triangle's bottom edge as a
  "−15 V" flag with its 100 nF bypass, the way the sheet draws a power symbol
  at each op-amp; a back-layer trunk under the +15 V rail joins the flags.  The
  +15 V rail is a real line along the top, and the lower stages' +15 V come
  up from the push-pull's pour on the back, as flags too.
- **POSITION.**  The fader's wiper is at the bottom right and the LOOP switch
  at the top left; a front wire between them would cross every stage.  It runs
  on the back and is printed as a dashed line, a net label with a route.

The pours under the DPAK tabs sit just outside each transistor's symbol
circle, fed through a 2 mm copper lead; the symbol's legs leave the base bar at
33 degrees rather than 45 because a 45-degree emitter leg cannot pass between
the tab and the base pad.

**170 x 120 mm, on purpose.**  The op-amp board is 100 x 100 mm and gets
JLCPCB's small-board price; this one is past it.  Jason's call (2026-10-25):
the circuit is much bigger, not every student needs one of these where every
student needs an op-amp board, and the probe loops and the room to read the
silkscreen are worth more than the few dollars.

## The simulation

`sim/pid_sim.py` builds a SPICE deck from `out/motorpid.net` (so it simulates
what the board is, not what was meant) with behavioural models of the LM321
(gain, slew, output clamp), the DPAKs, and the fader: a 14 Ω motor with back
EMF, a 15 ms mechanical time constant, friction of 0.15 A while sliding that
rises to 0.18 A to break loose below 5 mm/s, end stops 10 mm past the ends of
the track's linear part.  The motor's resistance and friction are Jason's
bench measurements (below); the speed is his "end to end in under a second at
5 V" taken as 0.8 s; the inertia and the speed below which the friction rises
are guesses, the second set so that a slow triangle sticks and slips as the
bench fader does.  It gives:

- quiescent 4 mA, all nodes at zero;
- P only: below a gain of about 3 a 1 V step does not unstick the slider; at
  5 it stops 0.38 V short; a 1 V step overshoots 28 % at gain 22 and rings at about 31 Hz at
  gain 100, until friction stops it and a slow hunt takes over;
- with D by the rule: 10.9 % overshoot at gain 22; at gain 100, 3 % and 28 ms
  (settling to 5 %: the friction leaves a few per cent of dead band);
- I at gain 5 with RV4 at 100k walks the residual to zero in steps over about
  two seconds (stick, ramp, slip); at 5k it hunts;
- a ±3 V triangle at 0.05 Hz: P 22 + D lags 0.11 V in steps of about 0.04 V;
  P 5 + D + I has no lag on average but steps of 0.15 V
  (`docs/images/sim-triangle.png`);
- a 10 V step peaks at 0.78 A and 13.7 V of drive.

The plots are in `docs/images/sim-*.png`.

## Not yet proven — check on the first board

1. **Slide switch position vs contact.**  The MSK12C02 datasheet draws the
   circuit (pin 2 common, 1 and 3 at the ends), not the travel, but its
   section shows the handle carrying the moving contact down onto the terminal
   on the handle's own side, with the common in the middle (Jason's reading,
   2026-10-25).  So the slider toward pin 1 closes pin 1, as the board's
   "1 = ... / 3 = ..." legends assume.  Confirm with an ohmmeter on the first
   board; if it is the other way the legends swap meaning and nothing is
   damaged.
2. **A dead short of MOTOR to ground**: 2 A for the fraction of a second the
   PTC takes.  The DPAK's 8 A rating and the 1 Ω resistor (2 W pulse in a 1 W
   2512) should cover it.  Try it once with a current-limited supply.
3. **The fader model.**  Resistance and friction are now measured (below);
   the speed, the inertia and the friction's fall with speed are not.  The
   gains at which the loop rings, and so the D rule's trimmer position, move
   with them: the D rule went from 611k to 234k when the measurements came in.
4. **JLCPCB rotations and datums** for the SOT-23-5, the DPAK, the slide
   switch, the knob and the trimmers are predicted from the land patterns, not
   yet seen in a preview; `out/motorpid/PLACEMENT_CHECKS.txt` lists them.
5. **The PTC's trip time at 0.6 A** (a stall at full drive) is 5–10 s from its
   curve; if it is much longer the DPAK gets hot (3.4 W, no heatsink beyond
   the pour).  A stall below full drive does not trip it at all: next section.
6. **The knob's turn direction**: pin 3 is assumed to be the end the wiper
   reaches turning clockwise, by the convention Bourns' 3362 sheet states
   for the trimmers (terminal 3 = CW) and ALPS follows; the RK09K sheet itself
   could not be fetched.  If it is the other way, the knob's arc and
   "clockwise +" read backwards; the loop is unaffected.

## A stall at a few volts (2026-10-26, open)

The measured motor is 14 Ω, so a stalled slider draws DRIVE / 14 Ω.  With the
loop open and P GAIN at 1 (DRIVE = TARGET, which the board invites), the
slider runs to its stop and stays; the simulation's sweep
(`sim/results.json`, `stall_sweep`) puts the NPN's dissipation
from 1.8 W at 2 V to 3.7 W at 7 V of DRIVE, at 0.14 to 0.49 A.
The fuse holds 0.35 A, so up to about 5 V it never trips, and between 0.35 and
0.7 A it may take minutes.  The DPAK sits on a 12 x 5.8 mm pour: about
70 °C/W from junction to air (the data sheet's minimum-pad figure), so 2 W is
already past 150 °C, reached in something like a minute.  The full-drive
stall the fuse was chosen for (0.63 A) is the easy case.

Holding the slider by hand at a low P gain does the same.  The board says so
on the back and in the handbook ("seconds, not minutes"); that is not
protection.  The fixes, for Jason to choose:

1. **TO-220 transistors on clip-on heatsinks** (D44H11 / D45H11 come in TO-220,
   as the book's push-pull is drawn).  With a 10–13 °C/W heatsink, 3.7 W is a
   50 °C rise: a stall can last all afternoon.  Through-hole, hand-fitted;
   the fuse stays for a short and for the motor.
2. **More copper under the DPAKs**, both layers, stitched with vias: perhaps
   30 °C/W from 20 cm², so 3.7 W is still a 110 °C rise and the board too hot
   to touch.  Not enough on its own.
3. **Leave it**, with the warnings: the DPAKs are 30 cents and the board is
   at a lab station, but a dead driver mid-lab is a lost afternoon.

A smaller fuse does not help: the motor needs 0.15 A just to slide, and a
stall at 2 V (0.14 A) already puts 1.8 W in the transistor.

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
