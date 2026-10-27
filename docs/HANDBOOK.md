# Handbook

How to bring the board up, wire the fader, and run Lab 10L on it.  The
voltages quoted come from the simulation (`sim/pid_sim.py`, which runs the
exported netlist through ngspice with a model of the lab's Bourns fader,
fitted to bench measurements); the first boards will say how close they are.

## 1. Before the fader: the electronics alone

Set every switch first:

| switch | set to | which is |
|---|---|---|
| TARGET SOURCE | 1 | the knob |
| LOOP | 1 | open: U1 compares TARGET with ground |
| D CAPACITOR | 1 | 22 nF |
| D IN / OFF | 1 | off (the differentiator's output shorted to its input) |
| I IN / OFF | 1 | off (the integrator's capacitor shorted: reset) |

Turn P GAIN and D GAIN fully anticlockwise and I GAIN fully clockwise: all
three gains at their lowest.  The arc over each trimmer says what clockwise
does: more resistance, which is more P and more D (the resistance is in the
feedback) but less I (it is in series with the input).
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
| U6 OUT | the driver op-amp's own output | = DRIVE plus a jump of about 1.2 V as DRIVE crosses zero |
| BASES | the two transistors' bases | = DRIVE + 0.6 V when the NPN conducts, − 0.6 V when the PNP does |
| DRIVE | the push-pull's output | = SUM (the driver's gain is 1), up to about ±13 V |
| MOTOR | past the fuse | = DRIVE |
| POSITION | the POT terminal's wiper | floating with nothing on the terminal |
| U7 OUT | the follower's output | = POSITION |

Turn P GAIN up a little, turn the knob: SUM and DRIVE follow TARGET, amplified.
That is the whole loop minus the plant.

## 2. The fader

The lab's faders are Bourns PSM01-082A-103B2 (100 mm of travel, a 10k track,
a 10 V motor); PSP01-082A-103B2 is the same in a metal-framed body.  The PSM
has two snap-in connectors at 2.5 mm pitch, a 2-pin one for the motor (B, A)
and a 7-pin one for the tracks (3', 2', 1', T, 1, 2, 3); the PSP has one 10-pin
connector (A, B, 3, 1, 2, T, 1', 2', 3').  Bring five leads from them to the
screw terminals:

| fader | terminal | pin |
|---|---|---|
| motor A | MOTOR | MOTOR |
| motor B | MOTOR | GND |
| track 1 | POT | 1 (+) |
| track 2, the wiper | POT | 2 (wiper) |
| track 3 | POT | 3 (−) |

The numbers match: fader 1, 2, 3 to POT 1, 2, 3.  Bourns' drawing has the lever
moving toward terminal 1 when A is positive, so with this wiring a positive
DRIVE moves the wiper toward the + end, as the loop needs.  The touch-sense
pin T and the second track (1', 2', 3') stay free.  If the fader's cable has a
shield, the MOTOR terminal's third pin is ground for it.

The track 1-2-3 has Bourns' taper B2: linear over the middle 80 mm and flat
for about the last 10 mm at each end, where POSITION stops changing.  The
knob's ±6.4 V never asks for those ends.  The second track (1', 2', 3', the
"servo track") is linear over all but 2 mm at each end; Bourns does not give
its resistance.  If it measures about 10k end to end, it is the better track:
wire 1', 2', 3' in place of 1, 2, 3.

Check the polarity anyway.  Power up with LOOP still open and move the slider
by hand: POSITION must read about +7.7 V at one end and −7.7 V at the other, 0
near the middle.  Now close the LOOP (switch to 3) with P GAIN low and the knob
at its detent.  The slider either goes to the middle and stays, or runs to an
end and sits there pushing: if it runs away, power down and swap the two motor
wires.  A positive DRIVE must move the wiper toward the + end.

The motor is rated 10 V; the driver can give it 13 V, but only during a step.
It sticks: it takes 2 to 3 V across the motor to break the slider loose, and
about 0.16 A to keep it sliding, so at a low P gain a small step does not move
it at all.  Holding the slider against a full drive stalls the motor at about
0.6 A; within seconds the 0.35 A resettable fuse opens, the red lamps across it
light, and it closes itself once you let go.  A stall at a few volts does not
open the fuse: the motor draws DRIVE / 14 Ω, 0.15 to 0.45 A, and the driver
transistor carries the rest of the 15 V at that current, 2 to 3.7 W.  Let go,
or move the knob back, within a few seconds.

## 3. The exercises, in the lab's order

**P alone.**  Loop closed, D and I off.  Turn the knob: the slider follows.
Turn P GAIN up.  At low gain the slider stops short of where it should and the
ERROR loop shows the leftover: the residual error that only I will remove (at a
gain of 5 the simulation leaves 380 mV of a 1 V step; below a gain of about 3 a
1 V step does not unstick the slider at all).  Keep raising the gain and the
slider overshoots, then rings: at the top of the trimmer each step rings near
31 Hz, the natural frequency of motor plus slider, until friction catches it,
and then the slider hunts slowly about the target.  Put a scope on POSITION
and DRIVE together and watch DRIVE swing rail to rail while POSITION wobbles:
the book's picture.

**The square wave.**  Switch TARGET SOURCE to 3 and feed the TARGET IN jack a
±3 V square wave at 0.2 Hz (±12 V is the jack's limit).  Trigger the scope on
it and look at POSITION: the step response at each gain.  POSITION OUT on the
left edge is the same signal buffered through 1k, for the scope or for a
second channel.

**The slow triangle.**  The same ±3 V as a triangle at 0.05 Hz, 3 mm/s: now the
slider sticks, the error grows until the drive breaks it loose, it jumps, and
sticks again.  POSITION climbs in a staircase and ERROR is a sawtooth
([docs/images/sim-triangle.png](images/sim-triangle.png)).  The best settings
for the square wave are not the best for the triangle: the friction, not the
electronics, is the hard part of this plant.

**D.**  Set a gain that rings (the trimmer a fifth of the way up, about 22 in
the simulation).  Switch D IN.  Turn D GAIN up from zero (clockwise): the
ringing dies, the step gets crisp, and too much D makes the slider buzz on the
brush noise.  The lab's rule for the time constant, RC = 1 / (2π f) with f the
ringing frequency, puts D GAIN a quarter of the way up with the 22 nF capacitor
(5 ms; 234k).  Watch the D loop on the scope: the spike at each step.  Now the
gain can go all the way up: at the top with D the simulated step settles (to
5 %) in 28 ms with 3 % overshoot.  The book's 100 nF (switch D CAPACITOR to 3)
is for a slower rotary pot: here it puts the rule at the bottom twentieth of
the trimmer.

**I.**  Back to a low P gain with its residual error.  Switch I IN and turn
I GAIN up from zero (anticlockwise: less resistance is more I): the residual
walks to zero over a couple of seconds, in steps: the slider sticks, I ramps
until the drive breaks it loose, it jumps, and sticks again.  Too much I, and
the loop hunts: a slow stick-slip oscillation that the D term cannot touch.  I OFF
shorts the capacitor, so switching back and forth restarts the integrator from
zero each time.

**Break the loop.**  The LOOP switch chooses what the difference amplifier U1
subtracts from TARGET.  Closed (3), it subtracts POSITION, the fader's wiper:
that is the feedback.  Open (1), it subtracts ground, so ERROR = TARGET and
nothing about the slider reaches the driver: DRIVE = P GAIN × TARGET, plus D
and I of TARGET if they are switched in.  With P GAIN fully anticlockwise
(gain 1) and D and I off, DRIVE = TARGET: the knob or a function generator
drives the motor driver directly.  Try it: the slider runs to an end and
stays there pushing, whatever the knob says (bring the knob back to the
detent soon: a few volts into a stalled motor heats the driver, see section 2),
and a slow triangle wave from the generator shows the driver's crossover on
U6 OUT and BASES.  The difference
between the loop and no loop is the point of the lab.

## 4. Probe loops

| loop | node |
|---|---|
| TARGET | after the source switch |
| ERROR | TARGET − POSITION |
| P | the inverted error |
| SUM | the summing amplifier's output, the loop's command |
| D, I | the differentiator and integrator outputs |
| U6 OUT | the driver op-amp's output: it jumps about 1.2 V as DRIVE crosses zero, from turning on the NPN to turning on the PNP |
| BASES | the two bases, after the 270 Ω: the same jump (little base current flows near zero) |
| DRIVE | the push-pull's output, before the fuse |
| MOTOR | after the fuse, what the motor sees |
| POSITION | the fader's wiper |
| U7 OUT | the follower's output, before the 1k to POSITION OUT |
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
- A stalled slider at a few volts of DRIVE: the fuse holds, the driver
  transistor dissipates 2 to 3.7 W.  Seconds, not minutes.
- The DRIVE OUT and POSITION OUT jacks are through 1k: scope inputs, not loads.
