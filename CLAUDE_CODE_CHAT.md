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
