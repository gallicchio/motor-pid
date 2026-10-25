# Handbook

How to bring the board up, wire the fader, and run Lab 10L on it.  The
voltages quoted come from the simulation (`sim/pid_sim.py`, which runs the
exported netlist through ngspice with a model of the SparkFun fader); the
first boards will say how close they are.

## 1. Before the fader: the electronics alone

Set every switch first:

| switch | set to | which is |
|---|---|---|
| TARGET SOURCE | 1 | the knob |
| LOOP | 1 | open: U1 compares TARGET with ground |
| D CAPACITOR | 1 | 22 nF |
| D IN / OFF | 1 | off (the differentiator's output shorted to its input) |
| I IN / OFF | 1 | off (the integrator's capacitor shorted: reset) |

Turn the three trimmers fully anticlockwise (P GAIN, D GAIN, I GAIN lowest).
Nothing on the MOTOR or POT terminals.

Power: +15 V, ground, −15 V into the POWER terminal (the pins are labelled),
from a supply that can give 1 A on each rail but set its current limit to 100 mA
for this first step.  Both green lamps light.  The board draws about 4 mA with
no motor.  The series diodes D1, D2 protect it from a reversed supply: swapped
rails light neither lamp and nothing is hurt.

Then with a meter or scope on the probe loops (a ground loop is beside each
group):

| loop | node | expect |
|---|---|---|
| +15 V, −15 V (on the rails) | the rails after the diodes | ±14.8 V |
| TARGET | the knob, through the switch | −6.4 V to +6.4 V as the knob turns, 0 at the detent |
| ERROR | U1's output | = TARGET with the loop open (ERROR = TARGET − 0) |
| P | U2's output | −ERROR |
| SUM | U3's output | ERROR × P GAIN; the trimmer turns it from 0 to about 100 × ERROR, so a small TARGET saturates it at ±13 V |
| D | U4's output | 0 at rest; a kick when TARGET changes |
| I | U5's output | 0 with I OFF |
| DRIVE | the push-pull's output | = SUM (the driver's gain is 1), up to about ±13 V |
| MOTOR | past the fuse | = DRIVE |
| POSITION | the POT terminal's wiper | floating with nothing on the terminal |

Turn P GAIN up a little, turn the knob: SUM and DRIVE follow TARGET, amplified.
That is the whole loop minus the plant.

## 2. The fader

The SparkFun COM-10976 (TOP-UP MD100AM2B-D) has solder tabs on its side: a
motor pair, and for each of two 10k tracks a pair of ends and a wiper, plus a
touch-sense pin.  Solder four flying leads to it, 10 cm or so:

| fader | terminal | pin |
|---|---|---|
| motor terminal A | MOTOR | MOTOR |
| motor terminal B | MOTOR | GND |
| one track's end | POT | 1 (+) |
| the same track's other end | POT | 3 (−) |
| that track's wiper | POT | 2 (wiper) |

The second track and the touch pin stay free.  If the fader's cable has a
shield, the MOTOR terminal's third pin is ground for it.

Which end is + decides which way the loop pushes.  Power up with LOOP still
open and move the slider by hand: POSITION must read about +7.7 V at one end
and −7.7 V at the other, 0 near the middle.  Now close the LOOP (switch to 3)
with P GAIN low and the knob at its detent.  The slider either goes to the
middle and stays, or runs to an end and sits there pushing: if it runs away,
power down and swap the two motor wires.  A positive DRIVE must move the wiper
toward the + end.

The motor is rated 10 V; the driver can give it 13 V, but only during a step,
and the loop runs it at a tenth of that most of the time.  Holding the slider
against the loop by hand stalls the motor at about 0.6 A; after a few seconds
the 0.35 A resettable fuse opens, the red lamps across it light, and it closes
itself once you let go.

## 3. The exercises, in the lab's order

**P alone.**  Loop closed, D and I off.  Turn the knob: the slider follows.
Turn P GAIN up.  At low gain the slider stops short of where it should and the
ERROR loop shows the leftover: the residual error that only I will remove (at a
gain of 5 the simulation leaves 89 mV of a 1 V step).  Keep raising the gain and
the slider overshoots, then rings, then at the top of the trimmer sustains an
oscillation near 12 Hz, the natural frequency of motor plus slider.  Put a
scope on POSITION and DRIVE together and watch DRIVE swing rail to rail while
POSITION wobbles: the book's picture.

**The square wave.**  Switch TARGET SOURCE to 3 and feed the TARGET IN jack
±0.5 V at 0.2 Hz (a square wave; ±12 V is the jack's limit, 1 V is plenty).
Trigger the scope on it and look at POSITION: the step response at each gain.
POSITION OUT on the left edge is the same signal buffered through 1k, for the
scope or for a second channel.

**D.**  Set a gain that rings (the trimmer two thirds up, about 22 in the
simulation).  Switch D IN.  Turn D GAIN up from zero: the ringing dies, the
step gets crisp, and too much D makes the slider buzz on the brush noise.  The
lab's rule for the time constant, RC = 1 / (2π f) with f the oscillation
frequency, puts D GAIN two thirds of the way up with the 22 nF capacitor (13 ms;
611k).  Watch the D loop on the scope: the spike at each step.  Now the gain can
go all the way up: at the top with D the simulated step settles in 90 ms with
1 % overshoot.  The book's 100 nF (switch D CAPACITOR to 3) is for a slower
rotary pot and is too much here.

**I.**  Back to a low P gain with its residual error.  Switch I IN and turn
I GAIN up from zero: the residual walks to zero over a second or two.  Too much
I, and the loop hunts: a slow oscillation that the D term cannot touch.  I OFF
shorts the capacitor, so switching back and forth restarts the integrator from
zero each time.

**Break the loop.**  Switch LOOP open at any point: the slider stops wherever
it is, the TARGET knob moves it in open loop (DRIVE = TARGET × gain, the
slider runs to an end), and the difference between the loop and no loop is the
point of the lab.

## 4. Probe loops

| loop | node |
|---|---|
| TARGET | after the source switch |
| ERROR | TARGET − POSITION |
| P | the inverted error |
| SUM | the summing amplifier's output, the loop's command |
| D, I | the differentiator and integrator outputs |
| DRIVE | the push-pull's output, before the fuse |
| MOTOR | after the fuse, what the motor sees |
| POSITION | the fader's wiper |
| +15 V, −15 V | the rails |
| GND x 4 | for the scope clip |

The 1 Ω resistors in the push-pull's emitters read the motor current: 1 V per
ampere across either one, differentially, at the DRIVE row.

## 5. Limits

- POWER: ±15 V, 1 A on each rail (the motor's stall current).  ±12 V works
  with a little less swing.
- TARGET IN: ±12 V.  The knob gives ±6.4 V.
- MOTOR terminal: a shorted terminal pulls about 2 A through the driver until
  the fuse opens; the transistors survive a moment of that, not a minute.  Do
  not short MOTOR to the rails.
- The DRIVE OUT and POSITION OUT jacks are through 1k: scope inputs, not loads.
