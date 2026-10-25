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
the book.  A stalled fader (the slider held, or run into its end stop with the
loop open) draws about 0.60 A at 9.1 V in the simulation, 3.1 W in one
transistor.  The PTC holds 0.35 A and trips at about twice that, so a stall
opens it in seconds and it recloses when the drive stops; the antiparallel red
LEDs light on the voltage across the open fuse.  An earlier draft had an active
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
top is about 12 Hz in the simulation, so the lab's rule RC = 1 / 2πf asks for
13 ms, which with 22 nF puts the D GAIN trimmer at 611k, two thirds of its
travel.  With 100 nF the same RC would be 134k, at the bottom of the trimmer,
where it is hard to set.  A switch gives both, and the difference is a thing to
show.

**Gain trimmers are 1M 3362P pots, not panel pots.**  JLCPCB stocks no 1M
shafted potentiometer.  3362P trimmers are keyed by their holes and turn with
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
(gain, slew, output clamp), the DPAKs, and the fader: a 15 Ω motor with back
EMF, 15 ms mechanical time constant, 50 mA of stiction, end stops at ±7.7 V on
the track.  The constants are estimates from the fader's datasheet (10 V,
200 mm/s, 400–800 mA stall) and are the first thing to correct from a real
board.  It gives:

- quiescent 4 mA, all nodes at zero;
- P only: a 1 V step overshoots 12 % at gain 22 and rings at about 12 Hz at
  gain 100;
- with D by the rule: 3.8 % overshoot at gain 22; at gain 100, 1 % and 90 ms;
- I at gain 5 with RV4 at 100k walks the residual to zero in about a second and
  then hunts slowly; at 5k it oscillates;
- a 10 V step peaks at 1.15 A and 13.3 V of drive.

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
3. **The fader model.**  Stall current, back EMF and stiction were estimated,
   not measured.  The gains at which the loop rings, and so the D rule's
   trimmer position, move with them.
4. **JLCPCB rotations and datums** for the SOT-23-5, the DPAK, the slide
   switch, the knob and the trimmers are predicted from the land patterns, not
   yet seen in a preview; `out/motorpid/PLACEMENT_CHECKS.txt` lists them.
5. **The PTC's trip time at 0.6 A** (a stall) is 5–10 s from its curve; if it
   is much longer the DPAK gets hot (3 W, no heatsink beyond the pour).
6. **The knob's turn direction**: pin 3 is assumed to be the end the wiper
   reaches turning clockwise, by the convention Bourns' 3362 sheet states
   for the trimmers (terminal 3 = CW) and ALPS follows; the RK09K sheet itself
   could not be fetched.  If it is the other way, the knob's arc and
   "clockwise +" read backwards; the loop is unaffected.

## Measurements to make on the fader (bench, 2026-10-26)

The simulation's plant constants were estimated (15 Ω winding, 0.67 A stall
at 10 V, 50 mA free-running, a guessed stiction).  Four bench numbers replace
them and settle whether the 0.35 A fuse is right:

1. **Winding resistance.**  Ohmmeter across the motor leads, at four or five
   slider positions (the brushes vary); take the lowest few.  Sets `R_MOTOR`.
2. **Free-running current and traverse time at 5 V.**  Bench supply at 5 V
   with its current readout; note the direction that moves the slider toward
   the + end of the track, the current while it runs, and the time end to
   end (a phone video is enough).  Sets `KE` (back EMF per speed) and the
   viscous term.
3. **Stall current at 5 V**, holding the slider for a second, and the lowest
   voltage at which the slider starts to move from rest.  Sets `I_STICK` and
   checks `R_MOTOR` (stall current × R should be about the voltage).
4. **The track**: end-to-end resistance, and a scope on the wiper while the
   slider is pushed slowly by hand with 10 V across the track, looking for
   dropouts.  Says whether POSITION needs the 100 nF it has and nothing more.

## The trimmers' ranges: log or linear (2026-10-25, open)

Jason wants each gain trimmer's good setting near the middle of its travel,
with "too far" reachable both ways and neither "too far" squeezed into less
than 10 % of the turn.  Today's linear 1M trimmers miss that: P's ringing
gain of 22 sits at 21 % of the turn and gain 5 at 4 %; I's useful 5k-100k is
the first 0.5-10 %.

Stock check, 2026-10-25: JLCPCB has no log (audio, "A") potentiometer in
stock in any value, and no shaft pot of any taper above 50k.  Log trimmers
are not made in the 3362 size.  Bourns' PTV09A (9 mm panel pot) is listed in
linear and audio tapers, 1k to 1M; it would be hand-soldered (or consigned),
and distributor stock for a 1M audio part was not confirmed.

With a linear trimmer Rp after a fixed Rs (R = Rs + turn × Rp), reaching k
times too far each way means Rs = Rg/k and Rp = Rg (k - 1/k), and the good
value Rg sits at 1/(k + 1) of the turn: 25 % for k = 3, 10 % for k = 9.  So
linear can meet the 10 % rule only for about k <= 3, and even then the "too
low" side is short.  An audio taper puts Rg near the middle for k up to ~10.

Jason will tune his breadboard and measure, for each of P, D and I, the
resistance at: sluggish / about right / too much (rings, hunts or buzzes).
From those: audio-taper PTV09A pots for P and I if he wants true log
(D's good point is already at 61 % on linear), or 3362 trimmers resized with
a series resistor if k <= 3 is enough.

Put them in `sim/pid_sim.py` (the constants at the top), rerun `./make.py`,
and the handbook's numbers (ringing gain, the D rule's trimmer position)
follow.
