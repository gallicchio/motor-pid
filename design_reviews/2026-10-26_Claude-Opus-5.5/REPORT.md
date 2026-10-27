# Design review: PID motor control board (Lab 10L), rev A

Reviewer: Claude Opus 5.5 (claude-opus-5-5), the author, 2026-10-26, written
before reading any other review. The board reviewed is commit `52b99ea`
(D2PAKs on 2 oz copper, the review brief). Everything I made is in this
directory: `sims/` (three ngspice and thermal scripts and their outputs),
crops of the board (`q_*.png`, `z_*.png`), and `patch_round1.diff`.

## 1. Verdict

**Order after named fixes.** The circuit is the book's Fig. 10L.10 with every
departure stated and checked. The signs close the loop through P, D and I, the
driver is stable in a 10 ns simulation, and the low-drive stall found earlier on
2026-10-26 is now inside the D2PAKs' rating. Two things must change before ordering:

- **The five slide switches have no "1" or "3" at their ends**, while every
  legend, the back's START line and the handbook's first table set them by
  number (finding 1).
- **The DRIVE probe loop sits ahead of the fuse**, so a scope's ground clip on it
  puts 2.3 A and 28 W into Q1 (and 5 W into a 1 W resistor) with nothing to stop
  it (finding 2).

The rest are minor: a thermal margin that needs the board on standoffs, an
integrator capacitor that loses much of its value at high integrator output, one via
carrying Q2's whole current, a mislabelled overshoot, and several document lines
that disagree with the board. I am confident of findings 1 and 2 (read off the
artwork; simulated and calculated), fairly confident of the rest, and I
checked the lab against the book itself (`datasheets_not_in_git/`).

## 2. Findings

| # | severity | level | where | one line |
|---|---|---|---|---|
| 1 | **major** | silkscreen, lab | SW1-SW5; `layout.py` TEXTS, BACK_TEXT; HANDBOOK §1 | no "1" / "3" at either end of any switch; every instruction is by number |
| 2 | **major** | abuse, circuit | TP7 (DRIVE), R21/R22, Q1/Q2 | DRIVE is probed ahead of the fuse: a ground clip there is an unfused short, 2.3 A, 28 W in Q1, 5 W in R21 |
| 3 | minor | power/heat | `sim/thermal.py --board`; HANDBOOK | 120/122 C assumes a breathing underside; flat on a bench 128/130 C, past the build's own 125 C limit |
| 4 | minor | circuit | C8 (`parts.py` "10uF", CL21A106KAYNNNE) | the integrator's 10 uF X5R 0805 25 V loses much of its capacitance under DC bias, so I's time constant changes with the integrator's output |
| 5 | minor | copper | `layout.py` BACK, -15 V edge run | all of Q2's current (0.63 A in a stall, 2 A in a short) goes through one 0.3 mm via at each end of the edge run |
| 6 | minor | simulation, docs | `sim/pid_sim.py` step metrics; DESIGN_NOTES, HANDBOOK | at gain 22 with D, "10.9 % overshoot" is the friction dead band (no peak), and "settles 1500 ms" means never |
| 7 | minor | silkscreen, docs | front, TARGET IN legend | the front says "±0.5 V at 0.2 Hz" (the book's value for the rotary pot); the back and handbook say ±3 V, and ±0.5 V does not move this fader at a low gain |
| 8 | minor | docs | HANDBOOK §1 table | SUM "from 0" (the minimum gain is 1); D "a kick when TARGET changes" with D switched off (it is shorted); "a ground loop beside each group" (none near the driver or the power) |
| 9 | minor | lab | HANDBOOK §3 | the trimmers have no scale; the book's procedure runs on known gains and RC; no open-loop recipe to measure them |
| 10 | minor | lab | HANDBOOK §3 "I." | the I exercise at gain 5 is 4 % of the P trimmer's rotation; the book's gain 10 is 9 % and still leaves a 118 mV residual |
| 11 | nit | lab | HANDBOOK | the pseudo op-amp's common-mode test (book §10L.2.4) cannot be done without a jumper; say so |
| 12 | nit | silkscreen | `parts.py` BOARD_DATE | front and back say "rev A 2026-10-24"; the board changed on 10-26 |
| 13 | nit | copper | `layout.py` BACK, R4's -15 V run | the back run at x = 144 crosses under the URL printed below the QR code |
| 14 | nit | docs | `gen_sch.py` derivative note | "rolled off above 500 Hz by the 470 pF": it is 1 / (2 pi RV3 470 pF), 1.45 kHz at the rule's 234k (the book: about 1.5 kHz), 340 Hz at 1 M |
| 15 | nit | docs | `gen_sch.py` driver note | "Output ±13 V": into the stalled 14 ohm motor the simulation gives 8.9 V, because 270 ohm limits the base current |

### 1. No "1" or "3" at the switches' ends (major; silkscreen, lab)

*Where.* SW1 TARGET SOURCE, SW2 LOOP, SW3 D IN / OFF, SW4 I IN / OFF,
SW5 D CAPACITOR. The legends are in `scripts/layout.py` TEXTS ("1 = knob",
"3 = closed loop", ...), the back's BACK_TEXT ("START: every switch on 1") and
HANDBOOK §1 ("Set every switch first: ... 1").

*What is wrong.* Nothing at either end of any switch says which end is 1 and
which is 3 (`z_sw12.png`, `q_bm.png`). For the three vertical switches the legend
lists 3 above 1, which matches the pin order and so hints at it. For SW1 and SW2,
which lie horizontally with pin 1 on the right (`layout.py`: "rot 180: pins along
the bottom, 1 on the right"), the legend is a vertical list that says nothing
about left or right. A student cannot carry out the first instruction on the
board without the schematic. Which end is "1" also rests on the MSK12C02's
contact sense (DESIGN_NOTES "Not yet proven" 1), so a mark at the end tells the
student, and the first board's ohmmeter check tells the author, at the same
place.

*Fix.* In `gen_pcb.py`, print "1" and "3" beside each switch body at the pin-1 and
pin-3 ends, from the pads' positions, outward along the pin row. Better still,
print the meaning at each end: "knob" / "jack", "open" / "closed", "off" / "in",
"22n" / "100n". `patch_round1.diff` does the numbers.

*Sure:* certain that the marks are missing; the fix is cheap.

### 2. An unfused short one ground clip away (major; abuse, circuit)

*Where.* The DRIVE node: TP7 (the DRIVE probe loop at 140, 91), R21 / R22, the
clamps, the snubber, R18 and DRIVE OUT's 1k all sit on the push-pull's output
ahead of F1. Only MOTOR (TP11, the terminal) is behind the fuse.

*What is wrong.* A scope's ground clip on the DRIVE loop, or a probe tip
slipping from TP7 to a ground post, shorts the push-pull with nothing but the
LM321's output current and the 270 ohm to limit it. `sims/drive_short.py` (the
project's own models) gives **2.27 A whatever SUM is: 28 W in Q1 and 5.2 W in
R21**, a 1 W 2512. The loop makes it worse: with R18 reading the shorted DRIVE,
U6 winds its output up to the limit whatever the command. On the pour, a D2PAK at
28 W passes 150 C within seconds (RthJC 2.5 C/W alone is 70 C), and R21 is
five times over its rating. The handbook's probe table lists DRIVE without a
word of warning, and "MOTOR shorted to ground" (2 A for under a second, through
the PTC) is the only short the documents consider.

*Fix.* For rev A at the least, print "no fuse: never ground" beside TP7, add it to
the handbook's probe table and the back's WARNINGS, and keep every ground post
away from TP7 (none is near it now: good). The better fix is in the circuit: move
F1 to between R21/R22's junction and the rest of DRIVE, so the probed DRIVE, the
clamps, the snubber, the feedback and DRIVE OUT are all behind the fuse. R18
then reads the far side of the PTC, so its 0.2 to 1.7 ohm sits inside the loop and
is corrected. The red lamps keep their place across F1. Only the short copper
between R21 and R22 stays unfused, with no loop on it. That is a change to the
book's drawing and Jason's to make.

*Sure:* the current is the model's (its LM321 limits at about 28 mA through its
100 ohm output; TI's LM321 is typically 40 mA, which makes it worse); the
conclusion is certain.

### 3. The thermal margin needs standoffs (minor; power/heat)

*Where.* `sim/thermal.py --board`, `sim/thermal.json`; HANDBOOK "Limits".

*What is wrong.* The as-built check (Q1 120 C, Q2 122 C, limit 125 C) uses
h = 10 W/m²K on top and 6 underneath, "a board lying on a bench". A board lying
flat on a wooden bench, its underside nearly blocked (h about 2), gives 128 C and
130 C from the same model on the same copper (run in my copy). That is past the
build's own 125 C limit, and within the model's 25 % of 150 C. The board has four
M3 holes, but nothing says to fit standoffs.

*Fix.* Make standoffs (or feet) part of the board: a line in the handbook's §1 and
on the back ("stand it on its four feet"). Q2's pour is the smaller (670 mm²
against 836): U6's feedback network (C9 at 134.7, 72 and the FBM row) takes the
space above it. If the margin matters more than the drawing's symmetry, moving
C9 and R18 left by 5 mm would give Q2 about 100 mm² more.

*Sure:* the model's own numbers; how the lab will stand its boards I do not
know.

### 4. The integrator's capacitor changes with its voltage (minor; circuit)

*Where.* C8, `parts.py` PASSIVES "10uF": Samsung CL21A106KAYNNNE, X5R, 25 V,
0805. C3, C4 (pot-end decoupling) use the same code, harmlessly.

*What is wrong.* A 10 uF 25 V X5R 0805 keeps only part of its capacitance under
DC bias. Samsung's DC-bias plot for the family is in the data sheet; I could not
read a figure for 10 V from what I fetched, but parts of this size and rating
commonly keep a third to a half of their value at 10 to 12 V. The integrator's
output, which is the voltage across C8, runs to several volts in the I exercise
(the I term has to supply the 2 to 3 V that breaks the slider loose). So I's
time constant (1k + RV4) x C8 falls as the integrator's output grows. The loop
still works; the student's sense of "how much I" depends on the output voltage,
and the simulation (a fixed 10 uF) does not show it. The book uses two
electrolytics back to back, 15 uF each, 7.5 uF in all.

*Fix.* A 1206 or 1210 10 uF X7R at 50 V (much less loss under bias), or two
22 uF electrolytics back to back as the book does (11 uF; check their leakage
against the integrator's drift), or say so in DESIGN_NOTES.

*Sure:* the mechanism is certain; the size of the effect at this part's bias I
did not measure.

### 5. One via for Q2's whole current (minor; copper)

*Where.* `layout.py` BACK, `("-15V", [(166.0, Q2Y - 5.0), (168.8, Q2Y - 5.0),
(168.8, VM_TOP), (165.5, VM_TOP)], W_RAIL, "both")`: one via at (166, 75) into
Q2's pour and one at (165.5, 12.5) onto the front -15 V run.

*What is wrong.* Every amp of Q2's collector current goes through those two
0.3 mm vias: 0.63 A in a full-drive stall for 5 to 10 s, 0.49 A in a low-drive
stall indefinitely, 2 A for the fraction of a second a MOTOR short lasts. A
0.3 mm via is good for about 1 A at a 10 C rise; there is no margin and no
redundancy. Q1's +15 V reaches its pour by a front track, which has neither
problem.

*Fix.* Three vias at each end (`patch_round1.diff` adds a `vias` count to the
BACK entries' ends).

*Sure:* fairly; the 1 A figure is the usual rule of thumb, not a measurement.

### 6. "Overshoot" that is the friction's dead band (minor; simulation, docs)

*Where.* `sim/pid_sim.py` step metrics; DESIGN_NOTES "with D by the rule: 10.9 %
overshoot at gain 22"; `docs/images/sim-pd.png`.

*What is wrong.* In `sim-pd.png` the green trace (gain 22, D by the rule) rises
without a peak and stops at 1.11 V, 11 % past a 1 V target: the slider sticks
there because 22 x 0.11 V = 2.4 V of drive does not break it loose. The metric
reports this as 10.9 % overshoot, and its settling time as 1500 ms, the end of
the window. The orange and blue traces stop long or short the same way. So
DESIGN_NOTES' "with D by the rule: 10.9 % overshoot at gain 22" reads as D
cutting the overshoot from 28 to 11 %, where the simulation shows D removing
the overshoot entirely and leaving the friction's dead band, about
±2.5 V / P GAIN. The handbook's square wave is ±3 V (6 V steps), on which the same
dead band would be 2 %, while the simulation steps by 1 V.

*Fix.* Run the step scenarios with 6 V steps, report the peak overshoot and the
final error separately ("lands 0.11 V from the target: the dead band"), and
quote both. The dead band is itself worth teaching: it is why I is needed.

*Sure:* certain from the plot.

### 7. The front's TARGET IN legend is the book's, for the other motor (minor)

*Where.* `layout.py` TEXTS, "±12 V max.  A square wave" / "±0.5 V at 0.2 Hz
replaces the knob".

*What is wrong.* ±0.5 V at 0.2 Hz is the book's suggestion for its rotary
motor-pot. This fader needs 2 to 3 V to break loose: the simulation says a 1 V
step does not unstick it below gain 3. The back ("Try +/-3 V") and the handbook
(±3 V at 0.2 Hz) say ±3 V. The front is the one a student reads with the
generator in hand.

*Fix.* "±3 V at 0.2 Hz replaces the knob" (`patch_round1.diff`).

### 8. Three lines of the handbook's first table (minor; docs)

*Where.* HANDBOOK §1.

- SUM "the trimmer turns it from 0 to about 100 x ERROR": the gain is
  (10k + RV2)/10k, 1 to 101, so "from 1 x to about 100 x".
- D "0 at rest; a kick when TARGET changes": the table is read with D IN / OFF at
  1, which shorts U4's output to its input, so D stays 0. "0 with D OFF; with D IN,
  a kick when TARGET changes."
- "a ground loop is beside each group": the four GND posts are at the left and
  middle (40, 92), (42, 99), (50, 99), (118, 70); none is near the driver or the
  power entry. Given finding 2 that is the right place for them; say "four ground
  loops, at the left and centre".

### 9. Nothing tells the student what the gains are (minor; lab)

*Where.* HANDBOOK §3.

*What is wrong.* The book's procedure runs on numbers: close the loop at a gain
of 1.5, see overshoot at 22, oscillation near 68 to 100, then set RC to a sixth
of the measured period. It gets them from substitution boxes ("Watching the
position of the rotator will let you estimate R to perhaps 20 %"). The board's
trimmers have arcs but no scale, and the handbook gives positions ("a fifth of
the way up", "a quarter of the way up"). The board can measure every gain, which
is better than the book, but the handbook never says how.

*Fix.* A short "measure your gains" paragraph, done with LOOP open:
- **P:** TARGET at 0.10 V; P GAIN is SUM / ERROR.
- **D:** a ±1 V, 10 Hz triangle on TARGET IN (a slope of 40 V/s); D's
  square-wave height over 40 V/s is RV3 x C.
- **I:** a 0.10 V TARGET with I IN; I ramps at 0.10 V / RC.

This also gives back a little of the measuring and debugging the board took out
of the lab (see §3, question 1).

### 10. The I exercise sits at the bottom 4 % of the P trimmer (minor; lab)

*Where.* HANDBOOK §3 "I." and §3 "P alone" ("at a gain of 5 the simulation
leaves 380 mV").

*What is wrong.* Gain 5 is RV2 = 40k: 4 % of a 1 M linear trimmer, about 10
degrees of its turn. The book's I exercise uses Rgain = 100k, gain 10 (9 %),
and the simulation still leaves 118 mV of residual at gain 10 (`results.json`
p_only["10"]), which is plenty to watch I remove. Jason's bench test of the 1 M
trimmers (sluggish to aggressive, best point off centre) stands; this is only
about where the handbook asks students to work.

*Fix.* Use gain 10 in the I exercise and quote the 118 mV.

### 11-15 (nits)

11. **Common-mode test.** The book (§10L.2.4) has students check the pseudo
    op-amp's common-mode gain by driving both inputs from the input pot. The board
    cannot do it without a clip lead from TARGET to the POT wiper. Say so in the
    handbook, or let it go: §1's open-loop test is the book's pseudo-differential
    test.
12. **The date.** "rev A 2026-10-24" on the front and back (`parts.BOARD_DATE`):
    the board changed on 10-26 and will change again after this round. Set it on
    the order day.
13. **A back run under the URL.** R4's -15 V back run goes down x = 144 from the
    via at (144, 89.6) and crosses the two lines of text under the QR code. Move it
    to x = 149.6, which is still in Q2's pour and clear of the text.
14. **The derivative's roll-off.** The schematic's note says "rolled off above
    500 Hz by the 470 pF". It is 1 / (2 pi RV3 x 470 pF): 1.45 kHz at the rule's
    234k (the book: "about 1.5 kHz") and 340 Hz at 1 M.
15. **"Output ±13 V".** Unloaded, yes. Into the stalled 14 ohm motor the
    simulation gives 8.9 V (`results.json` stall), because the 270 ohm limits the
    base current to about 15 mA. Say "±13 V unloaded, about ±9 V into a stalled
    motor".

## 3. Section 3's questions

1. **The spirit of the lab.** The board keeps what the book is for: P alone and
   its residual, ringing as P rises, D against the ringing with the book's
   RC = T/6 rule, I against the residual, too much of each. The book's tests are
   there too: the driver alone (LOOP open, gain 1) and the pseudo-differential
   gain (§1 of the handbook). The silkscreen as schematic is readable at 300 dpi
   with every block boxed and named as the book names it.

   What the board takes away is the building and the debugging, which the book
   calls "our most important product". That is Jason's trade for a station board,
   and the probe loops on every node partly pay it back. Finding 9's "measure your
   gains" would pay back more. The sticky Bourns fader is a good teacher: the dead
   band (finding 6) and the I staircase are exactly the lesson of the I term.
   Nothing the lab needs is missing except the switch marks (finding 1) and a
   scale on the gains (finding 9).
2. **The circuit against the book.** Read against the book's text (Lab 10L,
   pp. 421-432 of the scan in `datasheets_not_in_git/`):
   - The difference amplifier has unity gain with 100k ✓.
   - The inverter, then a summing stage with 10k per input ✓.
   - The P gain is Rgain/10k in the book and (10k + RV2)/10k here, a stated
     departure: the minimum is 1, not 0 ✓.
   - The differentiator has a series 1k and 470 pF across the feedback, rolled
     off near 1.5 kHz at the rule ✓, with a switch to kill D ✓.
   - The integrator is 1k + 1 M into 10 uF, against the book's two 15 uF in series
     (finding 4). The board adds a reset switch, where the book relies on the
     loop's DC feedback ✓.
   - The driver has split feedback, a snubber and the book's 270 ohm.
   - The input ends are 6.8k and the pot ends 4.7k ✓, with decoupling
     capacitors (10 uF against the book's 15 uF) ✓.
   - "Not 411" ✓ (LM321 everywhere).

   The sign goes TARGET − POSITION in U1, then is inverted by U2 and inverted
   back by U3, so SUM = +G (E + RC dE/dt + ∫E/RC) ✓. DRIVE = SUM, and A positive
   moves the lever toward terminal 1 = POT+ ✓. `check_circuit.py` asserts all of
   this. What it cannot assert: the switches' contact sense (finding 1), C8's
   dielectric (finding 4), and which side of the fuse the probe loops are on
   (finding 2).
3. **What the board adds.**
   - **TARGET IN** is self-protecting. R5 / R6 (100k / 100k) put ±6 V on U1's +
     input at ±12 V in; ±30 V in gives ±15 V there through 100k, 0.15 mA.
   - **The LOOP switch** grounds R7: the book's dotted line ✓.
   - **The fuse:** see finding 2 and question 5.
   - **The clamps** are the right way round, as asserted. In the worst stall they
     run at 75 C, where SS34 leakage is mA-level: harmless.
   - **The follower and the 1k outputs** ✓.
   - **D1 and D2** are the right way round: the cathode faces the supply on -15 ✓.
4. **The plant model and the simulation.**
   - **The driver alone, at a 10 ns step (`sims/driver_stability.py`,
     `sims/driver_step.png`).** No ringing and no parasitic oscillation: as built,
     with no snubber, with a 10 mH motor, with a 10x probe (15 pF) on BASES or
     U6 OUT, through the crossover, with a metre of coax on DRIVE OUT. The
     models are generic (1 MHz single-pole LM321, D44H11 at Bf 100), so the
     first board's scope has the last word.
   - **The 1500 ms "settle" (finding 6)** is the stick-slip dead band.
   - **The integrator** winds up against an end stop (TARGET beyond ±7.7 V on the
     jack). It then drives a full-drive stall, which the fuse ends in seconds,
     and unwinds at the error divided by RC. A student waits a few seconds; say
     so in the handbook.
   - **Not checked:** the brush noise, and the wiper dropouts beyond the author's
     reasoning.
5. **Power, protection and heat.**
   - **The worst stall:** the transistors are fine, and the margin needs standoffs
     (finding 3).
   - **The PTC (`datasheets/1812L050_60GR_C19078719.pdf`, 1812L035 row).** Hold
     0.35 A, trip 0.70 A at 25 C, and at most 0.1 s at 8 A. Its derating table
     gives 0.20 A hold at 70 C.
   - **The neighbours, from the model (`sims/neighbours.py`).** In a Q2 stall F1
     reaches 73 C, so its hold falls to about 0.20 A and a -7 V stall at 0.49 A
     trips it: the board protects itself on that side. In a Q1 stall F1 is at
     39 C (hold about 0.30 A), and 0.49 A sits between hold and trip.
   - **U6** peaks at 54 C (LM321 rated to 85 C), the -15 V electrolytic C12 at
     64 C, D3 / D4 at 75 C, R21 at 66 C: all fine.
   - **The MJB44H11:** 50 W, 2.5 C/W, 10 A. The stall at 8 V and 0.5 A is deep
     inside its DC SOA.
   - **A MOTOR short to ground** is 2 A through the PTC, under a second ✓. To a
     rail, the PTC still sits in series ✓.
   - **A DRIVE short:** finding 2.
   - **"HOT if the motor stalls"** is enough, with finding 3's standoffs.
6. **The silkscreen as a schematic.** I read it at 300 dpi, quadrant by quadrant:
   - Every junction has a dot ✓ and the one hop has its jump ✓.
   - The D2PAK symbols put B on the base lead and C on the tab, with the arrow on
     the emitter: out of the NPN on Q1, into the bar on the PNP Q2 ✓.
   - Grounds point down ✓ and the rails are lines ✓. The -15 V electrolytic's +
     is on the ground side ✓.
   - **J4's "shield" pin** is GND by the plane, with no ground symbol drawn on it
     (fine).
   - **Two of the four GND loops** carry no name; one name for the pair would do.
   - **Missing:** the switch ends (finding 1).
7. **Copper and board.**
   - DRC is 0 at 0.21 mm ✓.
   - The motor current's path: E wires and DRIVE at 0.6 mm in 2 oz ✓; the -15 V
     vias are finding 5.
   - The hop's vias clear R22's pad by 0.42 mm ✓.
   - The plane under both pours is uncut ✓. The remaining slits are at the board
     edge (x = 168.8), at U6's V− (x = 135-143.5, y 62-70), and the short BASES
     hop.
   - KiCad's TO-263-2 is the JEDEC pattern (pads 4.6 x 1.1 at 2.54 mm, tab
     9.4 x 10.8) ✓.
   - The stackup in the board file now says 0.07 mm copper, and the job file
     agrees ✓.
   - The custom footprints were reviewed in earlier rounds; I did not re-measure
     them.
8. **The JLCPCB package.**
   - **The D2PAK rotation:** I re-derived it from `easyeda.py C233689` (their
     pins at +x, tab at -x). +180 and 2.45 mm toward the leads put their pins on
     ours within 0.05 mm, and the CPL rows check out (Q1 270 deg, Q2 90 deg,
     y moved 2.45 mm toward each part's leads).
   - **Not checked:** whether Economic PCBA takes 2 oz copper and through-hole
     parts together (§5).
9. **The documents.**
   - Findings 6-8 and 14-15.
   - The build checks 30 numbers. It does not check the handbook's table rows
     (finding 8), the front's legends (finding 7), the schematic's notes (14,
     15) or the date (12).
   - The "Not yet proven" list should gain finding 2's DRIVE short and finding
     3's standoffs.
10. **What a student will do to it.**
    - **A reversed supply:** blocked ✓.
    - **+15 and -15 swapped:** both diodes block ✓.
    - **One rail only:** the op-amps run off one rail with the other near ground;
      I see nothing that this damages, but did not simulate it.
    - **20 V peak into TARGET IN:** ±10 V on U1 ✓.
    - **A ground clip on a probe loop:**
      - An op-amp output (ERROR, P, SUM, D, I, U6 OUT, U7 OUT): the LM321 takes a
        continuous short to ground at 15 V ✓.
      - BASES: U6 into 270 ohm ✓.
      - A rail: the bench supply's limit ✓.
      - POSITION: the loop runs to an end stall and the fuse trips ✓.
      - **DRIVE: finding 2.**
    - **MOTOR to ground:** the PTC ✓.
    - **Motor wires swapped:** a runaway to an end, a stall at whatever drive the
      gain gives; the D2PAKs live, and the handbook says to swap them.
    - **LOOP open for a whole session at a few volts:** finding 3 decides whether
      that is comfortable.
    - **The fader replugged live:** the terminal block makes contact in no fixed
      order. Any order is a stall or a runaway that the fuse or the copper
      absorbs.
    - **A SparkFun fader** (800 mA stall): the PTC trips it at full drive, as
      designed.
    - **Every trimmer at an end:** P 101 oscillates (the lesson); I at 0
      (1k x 10 uF = 10 ms) hunts hard; neither is damage.
    - **A switch half way:** if the MSK12C02 breaks before it makes (I did not
      check its data sheet for this), the node floats and the output wanders;
      harmless either way.

## 4. Checked and found right

- **The book's Lab 10L text** against the board, stage by stage (question 2).
- **The loop's sign** through all three terms, and the fader's polarity.
- **The D rule's numbers:** 31 Hz gives 5.15 ms, so 234k with 22 nF and 51k with
  100 nF. The book's slider period of "about 40 ms" agrees with 31 Hz in shape.
- **The driver's stability** with the project's models, at 10 ns, in six cases.
- **TARGET IN's over-voltage tolerance;** the op-amp outputs' short-circuit
  tolerance.
- **The thermal check:** the pours, the plane and its cuts come out of the
  board file as built (`sims/thermal_masks.png`: Q1's pour red, Q2's green,
  tabs yellow, the plane blue, the back runs' cuts black).
- **The neighbours' temperatures,** and the PTC's derating helping on Q2's side.
- **The D2PAK's JLCPCB datum,** from their land pattern.
- **The 2 oz stackup** in the board and the job file; 0.21 mm rules; DRC 0;
  ERC 0; 249 assertions; 30 claims.

## 5. Could not check

- Whether JLCPCB's **Economic PCBA accepts 2 oz copper** with through-hole
  parts. No public statement found; JLCPCB's help page gives only the 2 oz
  8 mil rule. Check on the order form; if it forces Standard PCBA, the cost
  model's $8 setup is wrong.
- **C8's DC-bias curve** at 10 V (Samsung's plot; finding 4).
- **The real LM321's** output drive into 270 ohm plus a base at 80 C.
- **The MSK12C02's contact sense** and **the RK09K's turn direction**; both are
  on the first-board list.
- **The motor's inductance, brush noise and 5 V speed** (assumed 1 mH, none,
  0.8 s).

## 6. Publishing

Nothing in the repository should not be public. `datasheets_not_in_git/` (the
book) and `datasheets/` are gitignored. I quoted the book only as figure numbers
and a few words. No absolute paths, keys or personal data in the committed
files; the author names on the board are Jason's and Claude's by intent.

## 7. Patches

`patch_round1.diff`, against commit `52b99ea` (`patch -p1` from the
repository's root; it applies cleanly). Built in my copy (`project/`): ERC 0,
249 checks, DRC 0, thermal 120 / 122 C, fab checks, 30 of 30 claims (the via
count in DESIGN_NOTES goes from 69 to 73). Renders: `z_patch_sw12.png`,
`z_patch_sw345.png`, `z_patch_tp7.png`. It covers:
- switch end numbers (finding 1);
- the DRIVE warning under its loop, on the back (replacing the line about
  MOTOR shorts, which the fuse covers) and in the handbook (finding 2's
  minimum);
- the standoffs line in the handbook (finding 3);
- three vias at each end of Q2's -15 V run (finding 5);
- the front's TARGET IN legend (7);
- the handbook's table (8), the I exercise at gain 10 (10) and a "measure your
  gains" paragraph (9);
- the R4 back run moved off the URL (13);
- the schematic's roll-off and output notes (14, 15).

It does not touch finding 2's circuit change, finding 4's capacitor or finding
6's simulation: those are Jason's call or need more work.
