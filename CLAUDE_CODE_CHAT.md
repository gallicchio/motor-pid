# Claude Code Chat Log — Motor PID Educational PCB (Lab 10L)

Every prompt, verbatim (minor typos fixed), followed by the response as it was given, with the
renders as they were at the time (kept under `docs/history/`).  Model: Claude Fable 5.1.

## Prompt 1

> Similar in spirit to the project in `../op-amp-pcb`, I want you to design a schematic and PCB for Lab 10L.
>
> The motor+potentiometer combination that we have was from Sparkfun, item COM-10976, "Slide Pot - Motorized (10k Linear Taper)". I don't know if they sell these any longer, but they seemed commonly available.

## Prompt 2

Sent while the first response was being built:

> As usual, log all prompts and response in CLAUDE_CODE_CHAT and to look at CLAUDE_PCB.md and add anything relevant that you learn there.

## Response 1

*2026-10-24 17:42 PDT through the early hours of 2026-10-25 PDT.*  Prompt 2 arrived while
this was being built and is folded in: this log, and the lessons added to `CLAUDE_PCB.md`.

### What was built

A complete, script-generated KiCad 10 project in the style of `../op-amp-pcb`:

- `scripts/parts.py` — the parts table (JLCPCB codes, prices, stock on 2026-10-24,
  footprints, the per-code JLCPCB rotation **and datum shift** table).
- `scripts/gen_sch.py` — the A2 sheet: TARGET, the pseudo op-amp (difference amplifier,
  inverter, summing amplifier), the differentiator, the integrator, the motor driver, the
  plant's terminals, power.  ERC 0, no text overlaps.
- `scripts/check_circuit.py` — 243 assertions on the exported netlist (every stage's
  wiring and values, switch poles, diode polarities, the D rule's reach, no shorted part,
  no one-pin net).
- `sim/pid_sim.py` — ngspice on the exported netlist with behavioural LM321, DPAK and
  fader models: P sweep, the natural frequency, D by the lab's rule, I, stall, short, a 10 V
  step.  `sim/results.json`, `docs/images/sim-*.png`.
- `scripts/layout.py` + `scripts/gen_pcb.py` — the 170 x 120 mm board, every wire laid as
  copper and drawn as silkscreen, DRC 0 with schematic parity.
- `scripts/gen_outputs.py`, `check_outputs.py`, `gen_docs.py` — gerbers, BOM, CPL (native
  and JLCPCB-corrected, with datum shifts), prints, renders, STEP; the fab checks; the
  generated `docs/MANUFACTURING.md`, order form and `PLACEMENT_CHECKS.txt`; the claims check
  on the hand-written documents.
- `README.md`, `docs/HANDBOOK.md`, `docs/DESIGN_NOTES.md`.

![the board](docs/history/r1-render-top.png)

![the schematic](docs/history/r1-schematic.png)

### The fader

SparkFun COM-10976 is the TOP-UP MD100AM2B-D (datasheet in `datasheets/`): 100 mm travel,
two 10k linear tracks and a touch track, a 10 V motor (6–11 V, 400–800 mA stall,
200 mm/s).  Its side tabs do not fit a board; it hangs off two 3-way screw terminals (MOTOR
+, GND, shield; POT +, wiper, −) on flying leads, so any 100 mm fader with a 10k track works.

### Decisions, and why

| decision | why |
|---|---|
| LM321 singles (SOT-23-5) for all seven op-amps | the lab says "not 411" for the driver; one type; a single per triangle lets the silkscreen draw each op-amp as its symbol.  Its + input is pin 1, so every triangle is drawn + on top |
| MJD44H11 / MJD45H11 DPAK push-pull on pours | surface-mount so JLCPCB places them; 8 A parts shrug off a stall for the seconds the fuse allows |
| 1 Ω emitter resistors (2512) | current sharing, and 1 V/A for a scope.  An output current limiter (Q3/Q4 + steering diodes) was designed, simulated (0.65 A) and then **removed**: the fuse covers the stall, and the limiter made the push-pull impossible to draw cleanly |
| 0.35 A PTC in the MOTOR line, red LEDs across it | a stall is 0.60 A at 9.1 V (3.1 W in one DPAK); the 0.5 A part would not trip; 0.35 A trips in seconds and resets.  A dead short is 2.0 A / 29 W until it trips: listed as a risk |
| D capacitor switchable 22 nF / 100 nF | the loop rings near 12 Hz at full P; the lab's RC = 1/2πf is 13 ms, which with 22 nF puts the trimmer two thirds up (611k) and with the book's 100 nF at the bottom.  Started at 10 nF; moved to 22 nF so the rule lands mid-dial |
| 1M 3362P trimmers for P, D, I | JLCPCB stocks no 1M shafted pot; trimmers are keyed by their holes |
| ALPS RK09K centre-detent knob for TARGET, pin 3 at the + end | clockwise = positive; the pin order was flipped on the sheet once the ALPS drawing was read |
| D IN/OFF and I IN/OFF: pole 3 = into the sum, pole 1 = off; the D capacitor switch sits *before* its two capacitors | the MSK12C02 has all three pins on one edge; the common pin in the middle is trapped unless its two neighbours leave in opposite directions.  Putting the sum on the top pole and the short on the bottom one, and the ERROR into the capacitor switch's common, lets every switch wire leave straight |
| −15 V as a per-op-amp flag on the back | V− is pin 2, between the two inputs; no front copper can leave the triangle there.  A via inside each triangle, a back trunk under the +15 V rail, a flag and a bypass under each triangle, as the sheet's power symbols |
| POSITION back to the LOOP switch on the back, drawn dashed | the only wire that would otherwise cross every stage |
| 170 x 120 mm | the first floorplan at 160 x 110 could not stack the D and I stages' feedback rows above the bottom-edge terminals |

### What the simulation says (fader model estimated, not measured)

| case | result |
|---|---|
| quiescent | 4 mA, every node at zero |
| P only, 1 V step | gain 1.5: 46 % short; gain 5: 89 mV residual; gain 22: 12 % overshoot; gain 100: rings at 11.8 Hz |
| P 22 + D by the rule (RV3 611k) | 3.8 % overshoot |
| P 100 + D | 1 % overshoot, settles in 90 ms |
| P 5 + I (RV4 100k) | the residual walks through zero in about a second, then hunts slowly; RV4 5k oscillates |
| stall (end stop, loop open) | 0.60 A, 9.1 V across the motor, 3.1 W in Q1 |
| MOTOR shorted to ground | 2.0 A, 29 W in Q1 until the PTC opens |
| 10 V step, P 22 + D | 1.15 A peak, 13.3 V drive peak |

### Things that went wrong on the way (and are now rules or checks)

- A BNC placed on the knob's wire column grounded the knob's bottom end through its
  shield: C2 ended up with both pins on ground.  Found by reading the nets; now
  `check_circuit.py` asserts no two-pin part is shorted and the knob's ends are their own
  nodes.
- ngspice's `limit(x, lo, hi)` is a Monte-Carlo *random* function, not a clamp; the
  op-amp model returned 0.  `min(max())` instead.
- "+15V" and "−15V" both sanitise to the same SPICE node name unless the sign is spelled.
- KiCad's symbol coordinates have y up: the SW_SPDT's pin 1 is the *upper* right pin, so
  "mirror x" was needed to put pole 3 on top as the board wants it.
- The DPAK: KiCad's TO-252 has the base and emitter pads 2 mm below the tab, so a
  45-degree emitter leg cannot pass between them; the symbol's legs leave at 33 degrees,
  and the circle is centred 1.5 mm toward the tab.  The 'silk clipped by solder mask'
  warning that pointed at the tab was the leg grazing the tab's corner, found by deleting
  symbol pieces one at a time.
- A closed loop of back-layer runs (−15 V branches plus the +15 V spine) isolated a patch
  of ground plane with a bypass via in it; `gen_pcb.py` now checks every ground via is
  inside the filled plane.
- The AppImage ships no 3D model for the MSK12C02, the RK09K or the 1812 fuse; stand-in
  bodies are generated and swapped in, so the render shows parts and the model check passes.

### Not yet proven (also in DESIGN_NOTES)

1. Which slider position of the MSK12C02 closes which contact (the datasheet draws the
   circuit, not the travel).  The legends assume the slider toward pin 1 connects pin 1.
2. A dead short of MOTOR to ground: 2 A for under a second.
3. The fader model's constants.
4. The predicted JLCPCB rotations and datums (SOT-23-5, DPAK, slide switch, knob, trimmers).
5. The PTC's trip time at a 0.6 A stall.
6. The knob's turn direction (pin 3 = clockwise end).

### Numbers

170 x 120 mm, 102 placements, 45 BOM lines, 12 Extended codes, $9.96 in parts per board,
197 SMT and 27 through-hole joints, 66 vias, 15 probe loops.  `./make.py` runs every stage
and check from scratch.

## Prompts 3 and 4

Sent while Response 1 was being built, after context resets:

> keep going

> Keep going, but keep this chat updated as to your progress.

## Prompt 5

> Explain more what you changed: "The D and I switches now put pole 3 into the sum and pole 1 off, and the D capacitor switch sits ahead of its two capacitors, so each slide switch's wires leave its one-sided pins without crossing."
>
> Then explicitly ask again the things you need my input on.

## Response 2

*2026-10-25 PDT.*

### The switch and why it dictates the wiring

The MSK12C02 has its three terminals in a row along one edge of the body: pin 1, then
the common pin 2, then pin 3 (the common sits nearer pin 3).  On this board every slide
switch is turned so that row is a vertical column on its west face.  Copper follows the
drawn silkscreen on the front layer, with no second-layer escapes except the deliberate
back runs, so from a column of three pads the only crossing-free pattern is: top pad goes
up, middle pad goes straight out west, bottom pad goes down.  Whatever arrives from the
west must land on the common, and whatever has to head up toward the summing amplifier
(which sits on the row above the D and I stages) must be on the top pad.  The first draft
had the poles the other way round, so the "to the sum" wire left the bottom pad and had to
climb past the other two.

### SW3 and SW4 (D IN / OFF, I IN / OFF)

Before: pole 1 fed the 10 k into the sum; pole 3 shorted the stage (D: output to its
− input; I: across the 10 µF).  Now: pole 3 is the top pad and goes up through R12 (R13)
into the sum; pole 1 is the bottom pad and goes down to the feedback return row and back
to the − input; the op-amp's output comes in from the west straight into the common.
Electrically nothing changed: the same two states with the same parts, only which pin
number does which.  In the schematic KiCad's SW_SPDT symbol is drawn mirrored vertically
so pin 3 is the upper throw, matching the board.

### SW5 (D CAPACITOR)

Before: the 22 nF and the 100 nF sat between ERROR and the two poles, and the common went
on through R15 (1 k) into U4's − input.  That makes the common the one wire that must get
east past the switch body while both poles are fed from the west.  Now ERROR goes into the
common from the west, pole 3 goes up and east to the 100 nF, pole 1 goes down and east to
the 22 nF, and the two capacitors' far ends join and feed R15 together.  For the selected
capacitor the path ERROR → C → 1 k → virtual ground is identical.  The unselected capacitor
has one end on an open pole in both versions, and flipping the switch gives the same small
kick into the differentiator either way.

The "3: … / 1: …" legends beside each switch, the handbook's set-up table, the netlist
checks and the simulation's default switch states all follow the new assignment.  Which
physical slider end is "3" remains item 1 of the unverified list.

### Questions, each with the default I will take if unanswered

1. **Slide switch travel.**  Is there an MSK12C02 (or the Sparkfun switch you would use)
   on hand to check which slider end closes pin 1?  Default: leave the legends, verify on
   the first board; nothing is damaged if it is backwards, the words just swap.
2. **Protection.**  I removed the active current limiter; the board relies on the 0.35 A
   PTC with the 1 Ω emitter resistors as sense.  A dead short of MOTOR to ground is about
   2 A through one DPAK for the PTC's trip time.  Keep that, or put the limiter back
   (two small transistors, two diodes, some board)?  Default: keep the PTC only.
3. **Fader measurements.**  The model assumes 15 Ω winding, 0.67 A stall at 10 V, 50 mA
   free-running.  Three bench numbers would pin it and confirm the 0.35 A PTC: winding
   resistance, free-running current at 5 V, and traverse time at 5 V.  Can you measure, or
   keep the estimates and tune on the bench?  Default: estimates.
4. **Board size.**  170 x 120 mm, against the op-amp board's 100 x 100.  Five bare boards
   are $14, ten are $24; assembled, $28 each at five and $21 each at ten.  Fine, or should
   it shrink (tighter layout, fewer probe loops, smaller text)?  Default: keep it.
5. **Next step.**  A design-review round first, like the op-amp board's `design_reviews/`,
   or straight to ordering?  How many assembled?  Who does the JLCPCB upload: I can drive
   the browser and check the placement preview (unverified item 4), or you upload and send
   screenshots.  Default: wait for your answer.
6. **Minor.**  The knob's clockwise end is assumed from the ALPS drawing (pin 3 = +).  Say
   if you care which way is +.

## Prompt 6

With the MSK12C02 data sheet's section drawing attached (handle 3 on top, moving
contact 4 and spring 5 over the three terminals):

> 1. I do not have an MSK12C02 on hand, but from the diagram that I've attached from the data sheet, it looks like the position of the slider handle mechanically pushes down metal onto the pin on that same side. Presumably that metal is also attached to the middle.
>
> 2. If the fuse is re-settable after being off for some thermal delay, keep the fuse as the protection.
> 3. Remind me again and I can make the measurements tomorrow in lab.
> 4. Keep the big size for this much bigger circuit. I'd rather keep the ability to probe than save a few dollars. Not every student needs one of these boards, whereas every student needs an op-amp board.
> 5. I will look over the schematic and PCB today or tomorrow and comment. After you make those changes, we will do a design review.
> 6. I'm torn. I generally do want clockwise "screwing in" to increase the resistance. Sometimes that corresponds to decreasing the relevant gain, which might be counter-intuitive. It would be best to have a little arc over the top of the knob with an arrow on the increasing/clockwise side that is labeled "↑R ↓P" or whatever is appropriate for that particular knob.

## Response 3

*2026-10-25 PDT, afternoon.*  All six answers acted on; the build passes end to end
(ERC 0, 246 circuit checks, DRC 0, fab checks, 23 document claims).

![the clockwise arcs](docs/history/r3-clockwise-arcs.png)

### What changed on the board

- **Clockwise arcs.**  Each trimmer and the knob has a short arc over its top ending in an
  arrowhead at 12 o'clock, labelled with what clockwise does: "↑R ↑P", "↑R ↑D", "↑R ↓I"
  and "↑TARGET".  Bourns' 3362 data sheet marks terminal 3 as the clockwise end, and all
  three trimmers are rheostats between pins 1 and 2 with 3 tied to the wiper, so clockwise
  is always more resistance.  A new circuit check asserts that wiring; `gen_pcb.py` refuses
  an arc that comes within 0.5 mm of a drawn wire (DRC does not mind ink over ink).  KiCad's
  stroke font has ↑ and ↓, so the labels are ordinary silk text.
- **Room for the arcs.**  Each trimmer's wiper tie to pin 3 now runs under the part body
  (the one wire on the board a part hides) so the top of the trimmer is clear.  The P
  trimmer moved right 1 mm with its 10 k fed from the side on the pin row; the D stage's
  feedback row went up 1 mm and its return row down 0.5 mm, and the D trimmer moved down
  2 mm; the I stage's + input ground via moved 0.8 mm right.  The arcs are radius 5 from
  238°: a 10 o'clock start lands on the wire feeding terminal 1, and any lower start
  overlaps the trimmer's own silk box.
- **Handbook fix.**  The set-up table said to turn all three trimmers fully anticlockwise
  for lowest gain.  For I that is backwards: anticlockwise is least resistance and most I
  gain.  Now: P and D anticlockwise, I clockwise; the I exercise says "anticlockwise: less
  resistance is more I".  The schematic carries the same note beside each trimmer's formula.
- **Design notes.**  Jason's reading of the MSK12C02 section is item 1 (slider toward pin 1
  closes pin 1; still an ohmmeter check on the first board).  The fuse stays as the only
  protection.  The board size and the reason for it are recorded.  The knob's clockwise end
  is still the Bourns/industry convention; the ALPS sheet could not be fetched.

### For the lab on 2026-10-26 (also in DESIGN_NOTES, "Measurements to make on the fader")

1. Winding resistance: ohmmeter across the motor leads at several slider positions; take
   the lowest few.
2. At 5 V from a bench supply: the current while it runs freely, the time end to end, and
   which polarity moves the slider toward the + end of the track.
3. Stall current at 5 V holding the slider for a second, and the lowest voltage at which it
   starts to move from rest.
4. The track: end-to-end resistance, and a scope on the wiper while the slider is pushed
   slowly with 10 V across the track, looking for dropouts.

They go into the constants at the top of `sim/pid_sim.py`; the handbook's ringing gain and
D trimmer position follow from the rerun.

### Elsewhere

Lessons into `~/OpticsPCBs/CLAUDE_PCB.md` (committed as its own hunk; another session's
uncommitted section-17 edits left as they were).  Next: Jason's read of the schematic and
board, those changes, then the design-review round.

## Prompt 7

> The target should be able to be overridden with a function generator input on a BNC input. If the target potentiometer has reasonable resistors between each extreme and +-15V, a function generator should be able to be plugged in directly onto the center tap to "override" the potentiometer and input a square, triangle, sawtooth, or sine wave. If this is not already there, add it.

## Response 4

*2026-10-25 PDT.*  Already there, as a switch rather than a direct tap; no change made.
J1 (TARGET IN, BNC, shell grounded) goes to pole 3 of SW1 (TARGET SOURCE); the knob's
wiper goes to pole 1; the common is TARGET, which feeds U1's 100k input.  Silk beside
the jack: "±12 V max.  A square wave ±0.5 V at 0.2 Hz replaces the knob".  Handbook
section "The square wave" uses it.  The switch was kept over a direct tap because the
generator then sees only the 100k input, with no knob-position offset (a direct tap
would see the wiper's 2.5–5.9 kΩ, about 1–2 % loading and up to ~50 mV of offset
from the knob with a 50 Ω generator; workable, and Jason's call if he prefers it).

## Prompt 8

> No, your switch is great. Keep it. If you didn't already have it, I was suggesting something that would need fewer changes.

## Response 5

Kept as is.  No change.
