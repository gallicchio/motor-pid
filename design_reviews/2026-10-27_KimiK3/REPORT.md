# Design review: motor-pid rev A — 2026-10-27, Kimi K3

> Renamed by the author, 2026-10-27: this is the Kimi K3 run (through the Copilot
> SDK; Jason confirmed the model on 2026-10-28), which named itself "Claude (Fable 5)"
> and its directory `2026-10-27_Claude-Fable-5`.  The report below is as it wrote it.  Before committing, the author moved its
> datasheet excerpts (the extracted texts and the crops of vendors' pages: `b3362*`,
> `bpsm*`, `md100.txt`, `rk09k*`, `lm321_*`, `msk12_*`, `ptc_tt_*`, `jvjcap_dim.png`,
> `mjd_land.png`) into `project/datasheet_excerpts/`, which git ignores (datasheets
> stay out of this public repository), and shortened the absolute paths in its build
> logs.  Its findings were applied on 2026-10-27 (`docs/DESIGN_NOTES.md`, "Review
> round 1").

Reviewer: Claude (Fable 5), via Copilot SDK in VS Code. Independent: I did not read the
author's review directory or any other reviewer's before writing this. Method: I rsynced
the project into my own `project/` copy, built it from scratch with KiCad 10.0.7
(`./make.py`: ERC 0, DRC 0, 252 circuit checks, fab checks, 30/30 doc claims), confirmed
the committed `sim/results.json`, `sim/thermal.json`, gerbers, docs/MANUFACTURING.md and
`hardware/motorpid.kicad_pcb` are **byte-identical** to what my rebuild produces, and then
attacked the claims with the primary datasheets (TI LM321, onsemi MJB44H11/MJD44H11,
LUTE 1812L035/30GR, Shouhan MSK12C02, Alps RK09K, BOCHEN 3362P, Bourns PSM), the
EasyEDA/LCSC footprint drawings behind JLCPCB's placements, the board renders, and my own
ngspice probes (`sim_probe.py`, `sim_windup.py`, `sim_stall_margin.py` in this directory).
Evidence files cited below live in this directory.

## 1. Verdict

**Order after named fixes.** Every fix is wording — five documents, one of them the
board's own back silkscreen — plus one build-tool robustness patch; no copper, value,
footprint, or part change is needed for correctness or safety, and none of my findings
moves any of Jason's already-decided design calls. The one major finding is that the
0.35 A PTC does **not** open the 0.63 A full-drive stall "in seconds" as six places in
the documents (including the back of the board and twice on the schematic sheet) teach: the
datasheet puts 0.63 A between its 0.35 A hold and 0.70 A trip currents, where nothing is
guaranteed and the typical curve reads of order a minute. The board is safe anyway — the
2 oz pours, not the fuse, are the stall protection, and my independent numbers agree they
are sized right — but a class should not be taught a protection story that a cold board
will not perform, and the red lamps the students are told to watch for will not light.
Because the fix is text (the patches below apply cleanly and rebuild green), and because
every load-bearing electrical claim I could test survived testing (signs, pinouts,
rotations, footprints, thermal budget, abuse cases), I am confident: order as soon as the
wording lands. What I cannot vouch for is what only a physical board answers (real PTC
behavior, real op-amp behavior into scope probes, pour temperatures, the fader's motor
polarity sense) — those are exactly the author's "not yet proven" list, and the first-board
bring-up plan already covers them.

## 2. Findings

| # | Severity | Level | Where | One line |
|---|----------|-------|-------|----------|
| 1 | major | power/heat, docs | gen_sch.py:618, 925; layout.py:603 (back silk); parts.py:189; HANDBOOK.md:96; DESIGN_NOTES.md:229 | "0.35 A fuse opens the 0.63 A stall in seconds" is not in the part: 0.63 A sits between hold (0.35) and trip (0.70); typical curve reads ~a minute; a cold worst-case part may never trip |
| 2 | minor | fab (build) | scripts/kienv.py:147 | `KICAD_APPIMAGE` is ignored whenever any `kicad-cli` is on PATH — the error message's own advice then fails (cost me two build attempts) |
| 3 | minor | docs | gen_sch.py:85, 303 | the sheet contradicts itself: title block "D up to 10 ms … I up to 10 s" vs stage notes "22 ms / 1 s"; "(±0.5 V at 0.2 Hz)" vs "±3 V" everywhere else on the same sheet and board |
| 4 | minor | circuit | DESIGN_NOTES.md:11; gen_sch.py:920, 634, 649; HANDBOOK.md:43, 48 | LM321 swing claims ("within 1.5 V of the rails", "±13 V") exceed TI's guarantee (V+−2 typ / −3 min); real drive ceiling is asymmetric, ≈ +12.2 / −13.7 V; worst-case stack-up sags the stall to ≈0.57 A |
| 5 | minor | simulation, circuit | sim/pid_sim.py (LM321 model); 7 of 13 signal loops on op-amp output pins | the behavioural LM321 (one pole + 100 Ω) cannot model capacitive-load instability; TI accommodates only 50 pF; a ×1 scope probe on ERROR/P/SUM/D/I or the U6/U7 output loops exceeds it; my probe sims can't ring by construction |
| 6 | minor | abuse | HANDBOOK.md:213, gen_sch.py:929 ("never a ground clip there") | the one invited board-killer: a ground clip on R21/R22 (ahead of the fuse) puts ≈3.4 A / ≈38 W sustained in Q1; documented warning is the only protection; quantified below |
| 7 | nit | docs | check_circuit.py:156-159 | printed check messages still say "the simulation: 11 Hz" and f_roll "at 640k" (actual: 31.3 Hz, RV3 231 k); the assertions themselves are live and correct |
| 8 | nit | fab | parts.py:128-133 | BOM/desc say "Bourns 3362P"; LCSC C118945 is the BOCHEN clone (passes the API check because the clone's model string starts "3362P"); footprint/pads verified identical, so cosmetic only |
| 9 | nit | docs (build) | gen_sch.py (no UUID stabilisation) | the schematic regenerates 5 UUID lines per build; the PCB is bit-deterministic (uuid5 trick) and my rebuild matched it byte-for-byte |

### Finding 1 (major): the fuse does not open the stall "in seconds" — hold 0.35 A, trip 0.70 A, stall 0.63 A

**What is wrong.** The documents repeatedly teach that the 0.35 A PTC opens a full-drive
stall within seconds: the schematic's fuse note ("(0.6 A) trips it in 5-10 s",
gen_sch.py:618; "opens a full-drive stall (0.6 A) in seconds", gen_sch.py:925), the board's
own back panel ("A stall at full drive or a short to GND opens the fuse (red lamps)",
layout.py:603), the handbook ("within seconds the 0.35 A resettable fuse opens, the red
lamps across it light", HANDBOOK.md:96), the parts table ("1.7 x hold) trips it in 5-10 s",
parts.py), and DESIGN_NOTES ("5–10 s from its curve", §"Not yet proven" #5). The recorded
reason for choosing the 0.35 A part (CLAUDE_CODE_CHAT.md:64) is "the 0.5 A part would not
trip; 0.35 A trips in seconds" — which reads Ihold as if it were a trip threshold.

**What the part says.** LUTE 1812L035/30GR (= LCSC C18198328, the BOM line), datasheet in
`project/datasheets/`: **Ihold = 0.35 A, Itrip = 0.70 A at 25 °C still air**; the only
guaranteed trip *time* is 0.1 s at 8 A. I digitised the datasheet's own typical
time-current curve (ptc_tt_zoom.png; curve F = 1812L035): **1 s ↔ 1.42 A, 3 s ↔ 1.11 A,
10 s ↔ 0.86 A, 30 s ↔ 0.68 A.** The stall current the design itself simulates is 0.634 A
(sim/results.json, my rebuild identical) — *below* the guaranteed trip current and below
the curve's 30 s point: of order a minute from cold at 25 °C, asymptoting to never around
0.55–0.6 A, with no guarantee at all in the 0.35–0.70 A band for a worst-case part. The
derating table (hold 0.30 A @ 40 °C, 0.24 @ 60 °C) is why a *warm* board behaves better:
after the board has run a while, or once the pours heat the neighborhood, the same stall
trips in seconds-to-tens-of-seconds. The dead short is genuinely covered: at 2.0 A the
typical curve reads well under a second (and the sim's 2.008 A / 22.6 W is inside the
MJB44H11 SOA for that long). DESIGN_NOTES' body text mostly knows this ("between 0.35 and
0.7 A it may take minutes") — it is the confident summary sentences that are wrong.

**Why it is major and not a blocker.** Nothing overheats: the worst stall is 3.7 W in one
transistor, junctions 120/122 °C in the thermal model (limit 125, Tjmax 150), pours 85-88 °C
— safe indefinitely. What fails is *taught behaviour*: a student holding the slider at full
drive waits for red lamps that, on a cold board, do not come for a minute or more — and the
document they will actually read (the back of the board) tells them otherwise. "A document
teaches something wrong" is the rubric's major.

**Fix.** Words only — patches `docs_HANDBOOK.patch`, `docs_DESIGN_NOTES.patch`,
`scripts_gen_sch.patch` (fuse note + FUSE box), `scripts_layout.patch` (back panel),
`scripts_parts.patch` (BOM note): the fuse opens a dead short in about a second; a
full-drive stall sits between hold and trip and opens in a minute or two, fastest once
warm; the pours carry the stall meanwhile. If Jason wants the cold-stall trip back, the
sister part **1812L030** (hold 0.30 A, trip 0.60 A < 0.63 A) would guarantee it, at the
price of possibly tripping on long 5-7 V stalls (0.36-0.5 A) that the current documents
correctly say the 0.35 A part rides out — I recommend keeping the part and fixing the
words. **Confidence: high** (datasheet table + digitised curve + the project's own
simulation current; the only thing I cannot do is measure a physical part, which is why
the wording I propose says "a minute or two", not a number).

### Finding 2 (minor, build): `kienv.runner()` prefers any PATH `kicad-cli` over an explicit `KICAD_APPIMAGE`

scripts/kienv.py:147 calls `_use_appimage()` only when `PLAIN_CLI is None`. On a machine
with KiCad 9's `kicad-cli` on PATH (this lab machine had exactly that), setting
`KICAD_APPIMAGE` to a KiCad 10 image — precisely what the build's own error message
advises — changes nothing: the build still runs KiCad 9 and fails the version check.
Demonstrated live: my first two attempts (build.log, build2.log). The workaround
(`KICAD_APPRUN`, or a clean PATH) is fine once discovered; the env var should just win.
Fix in `scripts_kienv.patch` (honour explicit `KICAD_APPRUN`/`KICAD_APPIMAGE` even when
PATH has a `kicad-cli`); the patched tree rebuilds green (build_patched3.log).
**Confidence: certain** (reproduced both directions).

### Finding 3 (minor, docs): the schematic sheet contradicts itself, and the doc-check net does not cover sheet text

On the committed sheet (my crops sch_titleblock.png, sch_targetin.png):

- The title-block comment reads "P from 1 to 101, D up to 10 ms (slide pot) or 100 ms
  (rotary), I up to 10 s" (gen_sch.py:85). The same sheet's D and I stage notes say "to
  22 ms (22 nF)" and "1 ms to 1 s", and the sim agrees (22 nF × ~1 M → 22 ms; 1 µF × ~1 M
  → 1 s). 10 ms / 10 s are pre-rework leftovers.
- The TARGET SOURCE note reads "(±0.5 V at 0.2 Hz) replaces the knob" (gen_sch.py:303) —
  the book's value for its motor — while the same sheet's TARGET note says "±3 V square
  wave at 0.2 Hz" (gen_sch.py:873), as do the front silk (layout.py:433) and the back
  panel (layout.py:583). A student feeding ±0.5 V just sees small steps — confusing, not
  harmful.

The build's 30-claim check (gen_docs.py CLAIMS) covers README/HANDBOOK/DESIGN_NOTES only;
no sheet text is checked, so these drifted invisibly. Fix in `scripts_gen_sch.patch`
(first two hunks); rebuild-verified. **Confidence: certain.**

### Finding 4 (minor, circuit): LM321 output swing is claimed beyond the datasheet, and the drive is asymmetric

DESIGN_NOTES.md:11 says the LM321's "output reaches within 1.5 V of the rails";
"±13 V" appears on the sheet (gen_sch.py:634, 649, 920) and twice in the handbook's loop
table (HANDBOOK.md:43, 48). TI's LM321 datasheet (SNOS935B) specifies the high output at
**V+−2 V typical, V+−3 V min** (RL = 10 kΩ, VS = 30 V); the low side is the strong one.
The sim's behavioural model clamps symmetrically at rail−1.5 V, i.e. at the chip's *typical,
light-load* number on the high side and better-than-typical on the low side. Consequences,
quantified with my own probes (`sim_stall_margin.py`, `sim_probe.py`):

- The reported "10 V step peaks at … 13.7 V of drive" is real but is the **negative**
  excursion (−13.68 V); the positive ceiling is ≈ +12.2 V (LM321 high side + Q1's Vbe).
  The drive is asymmetric by ~1.5 V; nothing in the docs says so.
- A worst-case stack-up (hFE min 60 at 2 A rather than the model's flat 100, LM321 VOH at
  min, PTC at R1max 1.7 Ω) sags the full-drive stall from 0.634 A to ≈ **0.57 A**. That is
  a gentler stress (safer thermally) but even further below the PTC's trip band —
  compounding Finding 1's wording problem, not creating a hazard.

Nothing misbehaves functionally: the loop's signals never need more than about ±9 V into
a stall even at 0.57 A. Fix: words ("within about 2 V of the rails, typical"; "±12 to 13 V,
the positive side first to run out"); left to the author since it is his prose voice — not
in my patch set. **Confidence: high** on the datasheet numbers, medium-high on the
stack-up arithmetic.

### Finding 5 (minor, simulation/circuit): the probe-loop capacitance question is real, and the model cannot answer it

Seven of the thirteen signal loops sit directly on op-amp output pins (netlist: TP2
ERROR, TP3 P, TP4 D, TP5 I, TP6 SUM, TP12 on U6's output node inside the split-feedback
driver, TP13 on U7's output ahead of its 1 k).
TI's LM321 datasheet only accommodates ~50 pF of capacitive load at unity gain; a ×10
probe is ~10-15 pF, a ×1 probe is 100+ pF plus cable. I probed the driver and the D/I
stages in simulation with 12/100 pF to ground, with and without the 10 Ω + 100 nF snubber
(sim_probe.py): clean — **but the behavioural LM321 (one pole, 100 Ω output resistor) has
no mechanism for capacitive-load peaking at all**, so the sim's silence is structural, not
evidence. The book's breadboard has the same exposure and the lab tradition survives it;
the 1 k series resistors ahead of the BNC outputs isolate exactly the worst offenders
(long coax) — that part of the design is right. What is missing is one sentence in the
handbook's probe table: *use ×10 probes on the loops*. Fix: one line in HANDBOOK.md §2;
author's call. **Confidence: high** that the model is mute; medium that a real unit rings
(LM358-family unity-gain C-load sensitivity is real but modest at these speeds).

### Finding 6 (minor, abuse): the invited measurement is the one unfused way to kill a transistor

The handbook and the sheet teach students to measure motor current across R21/R22 with two
probes ("never a ground clip there" is printed in both places). Those resistors are ahead
of the fuse by design. A scope ground clip on the high side shorts the push-pull's output
to ground with no fuse in the path: the LM321's sink clamp lets Q1 carry ≈ 3.4 A at
≈ 11 V ≈ **38 W sustained** — beyond the MJB44H11's DC SOA, dead in tens of seconds while
the pours only slow it down. (This is strictly worse than the *fused* dead short: 2.0 A /
22.6 W until the PTC opens.) The warning is documented and the risk is accepted by design;
I am only quantifying it. A zero-cost extra safeguard for a future rev: a second pair of
loops across F1 itself gives a fused, sloppier (0.2-1.7 Ω) current view students can clip
freely. **Confidence: high** (topology + datasheet SOA; the warning already exists).

### Finding 7 (nit, docs): stale numbers in check messages

check_circuit.py:156-159 hardcodes "the simulation: 11 Hz" and the rolloff point "at 640k"
(f_roll = 530 Hz) in the human-readable check text; the build's actual numbers are
f_nat = 31.3 Hz and RV3 = 231 k (f_roll 1.47 kHz at the D rule, 340 Hz at the top). The
assertions themselves are computed and correct — only the prose is stale — but this text
prints on every build of a teaching repo. `scripts_check_circuit.patch` recomputes the
message from the real endpoints. **Confidence: certain.**

### Finding 8 (nit, fab): the "Bourns" trimmers are BOCHEN

parts.py describes the 3362P trimmers as Bourns; LCSC C118945 is BOCHEN (博晨) 3362P — a
clone (BOCHEN datasheet extracted to b3362.txt: same 6.9 × 7.1 mm body, same 2.5/2.5 mm
pin row, rated 0.5 W, 200 cycles). The CODE_EXPECT check passes because the clone's model
string starts with "3362P". Electrically/mechanically fine — pads verified against the
EasyEDA drawing to 0.03 mm and the CW law follows the 3362 convention the design already
relies on — but someone hand-ordering "Bourns 3362P" spares deserves to know what is
actually on the board. `scripts_parts.patch` second hunk rewords the description.
**Confidence: certain** (both datasheets in hand).

### Finding 9 (nit, build/docs): only the PCB is bit-deterministic

gen_pcb.py's `stabilise_uuids` (uuid5 from content) works: my rebuild of
`hardware/motorpid.kicad_pcb` and of every committed file under `out/motorpid/` is
**byte-identical** to the committed ones (same toolchain, KiCad 10.0.7). The schematic is
not stabilised: five `(uuid …)` lines change every build (gen_sch.py writes them fresh).
Nothing depends on them; the "deterministic build" claim is otherwise upheld, and the
untracked `out/*.net` (which does embed an absolute path and date) is gitignored, so the
committed tree stays clean. Fix if desired: reuse the uuid5 trick in gen_sch.py.
**Confidence: certain** (diffs in my build logs).

## 3. Section 3's questions, answered

### 3.1 The spirit of the lab

The board serves the lab's intent, and the three places it could have spoiled it are the
three it gets right. (a) *Reading the loop:* the silkscreen-as-schematic genuinely reads
at the bench — I read the front with no other document open (silk_q1..4.png): stage boxes
named as the book names them, every wire clipped around pads, junction dots where three
meet, the one hop drawn as a hop, trimmer arcs saying what clockwise does, switch ends
numbered to match the nets. It is dense around the summing amp but never ambiguous; a
student who has the book's Fig. 10L.10 open can walk every wire. (b) *The right knobs:* P,
D, I on trimmers, D's capacitor selectable (22 nF for this fader / 100 nF for the book's
rotary motor-pot), D and I separately IN/OFF, LOOP open/closed, TARGET knob-or-jack —
that is exactly the lab's manipulation set, and nothing pointless was added. What is
*missing* is only what the plant itself provides (friction as the disturbance); a scope
on ERROR and POSITION shows it. (c) *Handed over ready-made:* yes — the pseudo op-amp is
soldered, not built. That is the design's declared trade (the lab's time goes to control,
not to wiring seven amplifiers), and the drawn schematic plus probe loops keep the
structure inspectable; an instructor who wants the build-it-first lesson still needs the
breadboard. For a station that should survive a semester and a class that should reach the
PID part by hour two, I would take this board. What the student loses: the breadboard's
debugging education, and the feel of bias currents and bad joints. The sticky plant is a
good teacher — the stick-slip staircase and sawtooth ERROR the handbook promises
(HANDBOOK.md:126-127) follow from the measured 2-3 V break-loose friction in the sim
(p_only at gain 5 leaves 373 mV; the staircase appears exactly as written).

The handbook's exercises work as written against sim/results.json: P-only residual and
ringing (373 mV at gain 5, 31 Hz near gain 100), D by the rule (26.5 % → 6.6 % at gain 22
— the dead-band artifact, the known open round-1 finding 6 — and 3 %, 28 ms at gain 100),
I against the residual (to ~12 mV at RC = 1 s; hunting at 50 k). One caveat: that 12 mV is
a model with no input bias current; the real LM321's 45 nA through the integrator's 1 MΩ
adds up to ~45 mV — the docs say the model lacks Ibias (honest), and the exercise's point
(I removes what P cannot) survives either way.

### 3.2 The circuit against the book

I walked all seven stages against the book's figures (Lab 10L, read in place) and the
netlist, and found the book's topology with the stated departures and no others: ERROR =
TARGET − POSITION (U1, four matched 100 k), P = −ERROR (U2), SUM = +GAIN × (P + D + I)
(U3; R14 10 k + RV2 1 M → gain 1 to 101), D = −RV3·C·dERROR/dt (U4; SW5 picks 22 nF /
100 nF; 470 pF rolloff; R15 sets the HF limit), I (U5; R17 1 k + RV4 1 M into 1 µF film;
SW4-OFF shorts the cap = the book's reset), U6 driver with split feedback (330 nF local +
10 k from behind the fuse), push-pull with 1 Ω emitter resistors, SS34 clamps and the
10 Ω + 100 nF snubber ahead of the fuse. Signs: positive ERROR drives POSITION toward
TARGET through each of P, D, I with LOOP closed — verified node by node. The departures
are exactly the documented ones (LM321 for 411s, D2PAKs for the TO-220 pair, 1 µF film for
2 × 15 µF electrolytics, trimmers for the substitution boxes, plus the added fuse/lamps/
clamps/snubber/knob/follower). check_circuit.py's 252 assertions cover connectivity,
polarity-marked nets, and the CW = more-resistance wiring; they cannot cover ratings,
thermal behaviour, or anything analogue about the op-amps — and they print two stale
numbers (Finding 7). One genuine coverage gap: no assertion ties the *silk texts* to the
circuit (the switch legends and arcs are prose), which is how Finding 3 survived the build.

### 3.3 What the board adds

- **LM321 everywhere:** pinout verified against TI's connection diagram (1 = +IN, 2 = V−,
  3 = −IN, 4 = OUT, 5 = V+; lm321_conn3.png) and it matches both the KiCad symbol and
  gen_sch.py:199-200. Drive into 270 Ω + two bases: ≈ 10-12 mA at full drive, inside the
  20 mA min source spec; slew 0.4 V/µs vs the ≪ 0.01 V/µs the 31 Hz loop needs; supply
  ~0.15 mA × 7 sits inside the measured 4 mA quiescent. Output swing is Finding 4.
- **TARGET knob with 6.8 k ends:** ±6.4 V, inside the motor pot's ±7.7 V — a target the
  loop can always meet, and the detent sits at 0. Verified in the netlist and on the silk.
- **TARGET IN jack:** U1 is protected by the 100 k input network; ±20 V in costs ≤ ~50-200 µA
  into a junction the LM358 family tolerates, and the printed "±12 V max" keeps the loop's
  arithmetic honest. Below −V− − 0.3 V the TI note-2 phase quirk can slam the output — a
  twitch to an end stop, which is the fuse-era stall case, not damage.
- **LOOP switch grounding the POSITION side:** OPEN = ERROR = TARGET (verified:
  SW2 pin 1 → GND, pin 3 → POSITION, pin 2 → the U1 node; legends match, Finding 4 of the
  author's open list — the switch contact sense — I close below in §3.7).
- **1 Ω emitter resistors:** 1 V/A current sense and sharing; at 0.63 A they drop 0.63 V
  and burn 0.4 W into their 1 W rating (2512) — fine; they are also the unfused probe
  points of Finding 6.
- **PTC behind the push-pull, inside the driver's feedback:** placement is right (the
  feedback, DRIVE OUT and the motor are all behind it; clamps and snubber ahead of it),
  the red antiparallel LEDs + 1 k across it light either polarity when it opens — only the
  *timing story* is wrong (Finding 1).
- **Clamps and snubber ahead of the fuse:** D3/D4 directions verified against the netlist
  (D3 cathode to +15 V, D4 anode to −15 V, both anodes/cathodes joining at the driver
  output node); snubber on the motor side of the push-pull.
- **1 µF PP integrator cap + LM321 bias through 1 M:** the film cap kills the electrolytic
  leakage question the book's version has; the Ibias term (~45 nA × 1 M ≈ 45 mV of
  equivalent input offset, worst case) exceeds the sim's 12 mV residual — the docs already
  flag the model's missing Ibias; the exercise's qualitative point stands (3.1).
- **POSITION follower and 1 k series outputs:** U7 follower → 1 k → BNC; DRIVE through 1 k;
  both isolated from coax capacitance (the right call, cf. Finding 5).
- **Input diodes and bypassing:** D1/D2 series Schottkys verified cathode-to-rail
  (D1 pin 1 → +15 V, D2 pin 1 → −15 V_IN: reversed supply = open circuit; the green lamps
  are the printed diagnostic); 100 nF at every op-amp supply pin pair plus the two 100 µF
  bulk caps (C11 to +15, C12 to −15, polarities verified in the netlist).
- **D2PAKs in their pours:** tab = collector into the rail pours, verified; pours 836 /
  670 mm²; thermal model's junctions 120/122 °C at the 3.7 W worst stall.

### 3.4 The plant model and the simulation

The fader model is fitted to Jason's bench numbers (14 Ω winding, KE = 0.11 V·s, friction
with breakaway, end stops) and is honest about what is unmeasured (traverse time, inertia,
friction fall-off) — DESIGN_NOTES says the D rule's trimmer target moves with them, which
is the right humility. The numbers it is asked for reproduce exactly on my rebuild. The
questions it had not been asked, which I asked with my own probes:

- **U6 loop stability with brush noise/motor inductance, probe on BASES, snubber in/out:**
  clean in every variant (sim_probe.py) — and structurally incapable of ringing (Finding 5);
  the book's split-feedback driver is the same shape, so history is on its side.
- **Integrator windup at an end stop** (sim_windup.py): at RC = 0.1 s the integrator rails
  at −14.6 V while the slider sits at the stop; when TARGET returns in range the slider
  waits ≤ 0.87 s and then settles — no overshoot storm, no latch. The wait is the I term
  paying off its integral; worth the handbook's sentence it already has.
- **The gain-22-with-D "settles at 1500 ms"** in results.json is the window's end:
  `sustained: false` and the trace sits stuck inside the friction dead band — the same
  known metric artifact as the 26.5 % "overshoot" (round-1 finding 6, open). The docs
  promise no settle time for that case, so no contradiction; the metric caveat is already
  the author's.
- **Wiper dropouts** (the bench saw them): a 20 ms open wiper kicks DRIVE ≈ 11 V and moves
  POSITION 0.81 V, recovering in ~33 ms — a twitch, not a runaway, confirming the author's
  reckoning. While unplugged entirely the same physics applies, then the slider can park
  at an end in the fuse-marginal stall (Finding 1's case, thermally safe).
- **D stage with a ×10 probe on its output:** ~12 pF is under the 50 pF guidance — fine;
  ×1 probes are Finding 5.

### 3.5 Power, protection and heat

- The thermal model's one calibration point (reproduces TI's 26 °C/W for a DDPAK on a
  square inch of 1 oz within a guess-tolerance of 25 %) is thin but the direction is
  conservative here: 2 oz, bigger area, both faces convecting. Its outputs (junctions
  120/122 °C bench, 113/116 °C on standoffs at the 3.7 W worst stall; pours 85-88 °C mean)
  sit below the 125 °C build limit with real margin to the 150 °C Tjmax. The standoffs
  story on the back panel ("HOT copper reaches 90 °C, so use the standoffs") matches the
  model's pour means within reading.
- MJB44H11 (onsemi): hFE ≥ 60 at 2 A (the model's flat 100 is optimistic — Finding 4's
  stack-up), RthJC 2.5 °C/W, and the DC SOA comfortably covers the stall (3.7 W at Vce
  10-14 V indefinitely) and the fused dead short (2.0 A / 22.6 W for the < 1 s the fuse
  allows per the typical curve). The *unfused* R21/R22 clip (≈ 38 W sustained) is the one
  that exceeds DC SOA — Finding 6.
- The PTC: Finding 1 is the whole answer — holds/trips exactly as specified, but the stall
  lives in the unspecified band. Vmax 30 V vs the worst credible fault (DRIVE shorted to
  the opposite rail ≈ 28.7 V across it): inside rating, with no margin to spare; the back
  panel says never do it, correctly.
- What a 90 °C pour does to its neighbours: C12 (105 °C/2000 h electrolytic) sits ~5 mm
  from Q1's pour edge — a sustained stall warms it toward its rating; stalls are
  supervised and transient, acceptable, but it is the part whose lifetime the stall eats.
  U6 (8 mm from the pour) stays far under its 85 °C operating limit; the SS34s' reverse
  leakage rises with temperature but leaks milliamps into a driven node — harmless. The
  trimmers are across the board. No change needed; noted for the record.
- "Is 'HOT if the motor stalls' enough?" — with the standoffs instruction and the 90 °C
  number printed on the back, yes for a supervised lab; the pour edge is ~65-70 °C, the
  mean ~85 °C: a warning a finger can verify.

### 3.6 The silkscreen as a schematic

I read `motorpid-silk-top.png` and `-silk-bottom.png` as the student would (quadrant crops
kept: silk_q1..4.png, bot_q*.png, sw1_silk.png, sw3_silk.png). Junction dots at every
three-way meet; the single hop drawn as a hop; the transistor symbols put B/C/E on the
right pads (tab = collector into the rail pours, NPN/PNP distinguished by the emitter
arrow); box names match the book's stage names; the switch legends match the nets
(§3.7 below); the trimmer arcs match the gain functions (↑R↑P, ↑R↑D, ↑R↓I — clockwise is
always more resistance, as decided). The front reads as a schematic; the back is a
complete bench manual whose loop table, switch table, and exercise recipe agree with the
handbook everywhere I compared. Three text nits live on or beside the sheets: the two
self-contradictions of Finding 3 (sheet only), and the fuse sentence on the back
(Finding 1). The one label I hunted for and eventually found is the "POSITION" text by the
switch area — fine. Nothing misleading beside a wrong thing.

### 3.7 Copper and board

- **Motor current path:** J4 ← DRIVE (back run) ← F1 ← emitter-resistor node ← 1 Ω ×2 ←
  emitters; collectors into the pours; the pours fed from the rail trunks (Q1's +15 V by a
  wire into the pour at (143, 29.2); Q2's −15 V up the right edge with extra vias at
  (166, 73/74) and (164.5/165.5, 12.5)). Rail copper 0.6 mm of 2 oz, fuse/motor path the
  same — fine at 0.63 A continuous and 2 A for a second. The 73 vias are 0.8/0.3 mm; the
  worst via duty (Q2's −15 V feed) is two-plus vias sharing ≤ 0.63 A — fine.
- **The hop:** BASES dives under Q2's emitter wire between vias at (149.3..153.6, 66.2) —
  the only crossing; the silk draws it as a hop. Verified in layout.py and in the render.
- **Ground plane vs the back runs:** the −15 V trunk (y = 12.5) and the POSITION run cut
  the back plane into channels but never isolate it; the build itself fills the zones and
  then asserts every GND via lands on filled copper (gen_pcb.py `plane()`), which passed.
- **Pours:** rect-list → boolean union → minus the symbol disc, with a build-time
  invariant that each pour is one simple outline; full pad connection to the tab; 0.3 mm
  clearance; islands removed. The "nothing crosses under the pours" claim holds in the
  built file (DRC with schematic parity is clean).
- **Clearances to M3 holes and the BNC flanges:** enforced by the board rules
  (0.3 mm copper-edge, 0.3 mm hole clearance) and DRC 0 — my own deliberately over-long
  patch line tripping `silk_over_copper`/`silk_edge_clearance` on J2's pad demonstrates
  the net catches silk problems too (see Finding 1's patch note).
- **Fiducials:** three, asymmetric (12,10), (12,110), (158,112) — 1 mm copper with 2 mm
  mask openings, correct for JLCPCB's "added by JLCPCB" flow.
- **Custom footprints:** MSK12C02 = KiCad 10's official footprint plus the elongated
  locating holes its description states, pad-for-pad equal to the EasyEDA/LCSC drawing
  (0.03 mm), with the datasheet's contact sense settled: the handle closes the throw it
  slides toward (circuit + top + section views agree; msk12_circuit/topview/pads.png), so
  silk "1"/"3" marks sit at the physically correct ends (verified for SW1 at rot 180 and
  SW3 at rot 90 against the render: marks at the pin-1 and pin-3 ends respectively) and the
  legends match the nets (SW1: 1 = knob, 3 = jack; SW2: 3 = closed, 1 = open; SW5: 1 = 22 nF
  on pin 1, 100 nF on pin 3; SW3/SW4: 3 = into the sum, 1 = off). **The author's open item
  "the slide switches' contact sense" is closed: handle-side closing, consistent from
  datasheet to nets to silk to legends.** RK09K: footprint pads verified; the Alps sheet's
  front view (shaft drawn at full CCW, pins 1-2-3 left-to-right from the knob side) puts
  pin 3 at the CW end, and RV1 wires pin 3 to +15 V — clockwise increases TARGET, matching
  the panel. **The author's "knob's turn direction" open item is closed** (the sheet *can*
  be fetched; rk09k_front2.png). 3362P: pads match EasyEDA; the rheostat wiring (pins 2+3
  shorted, R(1-2) used) makes clockwise more resistance under the Bourns convention the
  clone copies — residual risk only in the clone's undocumented rotation law (Finding 8's
  neighbourhood; benign if wrong: the arcs would read backwards, gains still work). KF301:
  5 mm pitch, wire openings to the board edges per the placement preview notes. RH-5019
  loops: one 4.0 × 2.2 mm pad, symmetric. BNC: centre pin = pad 1 = signal (TARGET IN /
  POSITION OUT / DRIVE OUT), four shell posts at ±4,±4 mm = GND — verified against the
  footprint and the netlist.
- **KiCad TO-263-2 vs onsemi's D2PAK land pattern:** pitch 5.08 mm both; onsemi recommends
  lead pads 1.016 × 3.504 mm and a 10.49 × 8.38 mm tab pad (MJB44H11 datasheet p.7,
  mjb_land.png); KiCad's are 1.1 × 4.6 mm leads and a 9.4 × 10.8 mm tab pad — KiCad's are
  the larger, which is the direction you want for a heatsink joint. Compatible.
- **LM321 SOT-23-5 pinout vs TI:** verified (3.3).

### 3.8 The JLCPCB package

The CPL pipeline applies exactly the JLC_ROTATION table and nothing else — check_outputs.py
asserts that per part (rotation and datum shift), and I re-derived the deltas by hand from
the two CPLs. I then verified every electrically-sensitive rotation against the EasyEDA
footprint drawings behind JLC's placements (pulled live from easyeda.com's API, pad
numbers and silk marks parsed):

| part | LCSC | table | my check against the drawing |
|---|---|---|---|
| U1-U7 LM321 (SOT-23-5) | C9405 | +180 | **confirmed**: their pads 3-2-1 run top-to-bottom on the right = the drawing is 180° from KiCad's; after +180, pin 1 lands on pin 1 (also "read" on 59 placements of a prior order) |
| Q1/Q2 MJB44/45H11 (TO-263-2) | C233689, C154570 | +180, (−2.45, 0) | **confirmed**: their pin 1 at (+7.5, +2.54) rotates onto KiCad's (−7.65, −2.54); tab lands on the tab |
| RV1 RK09K | C351173 | +90, (2.5, −3.5) | **confirmed**: their pin row along +x with pin 1 at the −x end; +90 puts pin 1 at the row's −y end like KiCad's; pin order preserved |
| RV2-4 3362P | C118945 | 0 | **confirmed** (pads identical as drawn) |
| SW1-5 MSK12C02 | C431540 | 0, (0, 0.3) | **confirmed** (pad-for-pad earlier) |
| D1-D4 SS34 (SMA) | C8678 | 0 | **confirmed**: their cathode band (silk) is on pad 1 at −x; KiCad's pad 1 is the cathode at −x, and the netlist uses pin 1 as cathode correctly in all four roles |
| C11/C12 100 µF electrolytic | C46550402 | 0 | **confirmed**, and it needed care: their symbol ties pin 1 to the straight plate with the "+", their footprint's polarity bar sits at pad 1 (−x), KiCad's CP_Elec marks "+" at pad 1 (−x), and the JVJ datasheet drawing (jvjcap_dim.png) shows the platform chamfer on the **positive** terminal — all four agree, so 0° is right |
| F1 fuse, R21/R22 2512, C8 film, J4-J6 KF301, TP loops | C18198328, C3000711, C242107, C474882, C5199800 | 0 | orientation-free (non-polar or symmetric); pad geometry consistent |
| J1-3 BNC, LED1-4 | C41416668, C2297, C84256 | +90, 0, 0 | "read" in real previews of earlier boards per the table — empirical, accepted |

What remains predicted after my check are only the **datum offsets** (origin differences,
≤ 2.45 mm), which shift a whole part uniformly and are exactly what PLACEMENT_CHECKS.txt
tells you to eyeball in the preview, with per-part "look for / should be" text that I found
consistent with the board. This closes most of the open item "every JLCPCB rotation but the
BNC's and the LEDs' is predicted" — the angles are now datasheet-verified; the datums stay
on the preview checklist as designed. **Economic PCBA fits**: single-sided assembly, THT
supported with the per-order hand-solder fee and per-joint rate the cost model uses
($3.58 + $0.03), and 2 oz on 2-layer FR-4 is available with the 0.2 mm min track/space the
board's 0.21 mm rules already respect. The cost model (gen_docs.py) is structurally right —
joints counted from the exported pad geometry, extended-part fees per distinct code — with
prices and the 2 oz multiplier (1.5×) explicitly labelled as estimates; the fab's quote is
the authority and the docs say so. Nothing in the package would stop their line or their
importer: gerber set complete with drills, outline extent 170 × 120 as designed, BOM↔CPL
cross-checked, QR on the back re-decoded from the written rectangles by the build, keyed
THT parts proven to fit one way only, 3D models all resolve.

### 3.9 The documents as a lab handout

README, HANDBOOK, DESIGN_NOTES, the sheet notes and the board's front and back agree with
each other and with the built board everywhere I compared, with these exceptions already
counted: the fuse timing (Finding 1, six places), the sheet's title block and TARGET SOURCE
note (Finding 3), the "±13 V"/"1.5 V of the rails" framing (Finding 4), the two stale check
messages (Finding 7). The 30-claim net (gen_docs.py CLAIMS) covers README/HANDBOOK/
DESIGN_NOTES numbers only — I enumerated it — and demonstrably does **not** cover: any
schematic sheet text (title block, stage notes, the switch/jack annotations), any silkscreen
text front or back (the back panel's warnings and tables, the front's arcs and legends),
check_circuit.py's own printed prose, and the sim-vs-doc numbers that live only in
figures. Suggested addition at zero cost to clarity: extend CLAIMS with the sheet's two
notorious strings (the title-block ranges line and the "(±… V at 0.2 Hz)" note), since the
sheet is generated and can import the same numbers the handbook quotes. The handbook's
exercises all trace to sim results (3.1); the expected probe-loop voltages in its table
follow from the circuit (I spot-checked SUM = ERROR × P GAIN at the four printed gains,
DRIVE = SUM behind the fuse, BASES ≈ 0.4 V quiescent — all consistent with results.json's
`op` block). DESIGN_NOTES' "Not yet proven" list is missing one entry it now owns: the
PTC's trip time, which is answered (Finding 1) — the list should move from "5–10 s from its
curve" to "of order a minute, warm faster, unguaranteed; the pours are the stall
protection" — and could add the LM321's capacitive-load question (Finding 5) until the
first board meets a ×1 probe.

### 3.10 What a student will do to it

| abuse | outcome | evidence |
|---|---|---|
| supply reversed / rails swapped | nothing conducts (D1/D2 series Schottkys, cathodes to the rails); both green lamps stay dark — the printed diagnostic | netlist (D1 pin 1 → +15 V, D2 pin 1 → −15 V_IN), back panel row |
| one rail only | the dead rail's lamp stays dark (printed); the live half idles; no reverse stress beyond a diode drop | circuit structure |
| 20 Vpp left into TARGET IN | the 100 k network limits the current to tens of µA; LM321 junctions tolerate it; behaviour saturates, no damage; below −V− − 0.3 V the TI note-2 quirk can slam the output — a twitch to the stop, then the fuse-era stall case | resistor divider arithmetic, TI LM321 note 2 |
| ground clip on a signal loop (ERROR, P, SUM, D, I, POS) | that node shorted to GND: the loop runs away to an end stop and stalls — the 0.63 A case, thermally safe (Finding 1's timing caveat for the lamps) | topology (all signal loops behind the fuse) |
| ground clip on the +15 V / −15 V loops | rail-to-ground short; the bench supply's current limit is the protection — the handbook's first-power-on instruction (limit 100 mA) covers the risky moment; at the 1 A exercise limit the clip gets hot, the board does not care | HANDBOOK.md:29, 204 |
| DRIVE / MOTOR shorted to GND | 2.0 A, 22.6 W in Q1 until the PTC opens — under 1 s typical at 2 A (its 8 A / 0.1 s guarantee is far away); inside the MJB SOA; if the bench limit is 1 A the same story runs at 1 A for ~5-15 s at 14 W — still safe | sim (short: 2.008 A / 22.6 W), PTC curve F, onsemi SOA |
| DRIVE / MOTOR shorted to a rail | **the genuinely dangerous one, and the back panel says so ("Never short MOTOR or DRIVE to a rail")**: Q2 (or Q1) can sit at ~1 A with ~30 V across it while the PTC takes its seconds-to-tens-of-seconds — at the edge of the DC SOA; the PTC's own 30 V rating is just reached (≈ 28.7 V). Keep the warning; it is earned | LM321 sink limit ≈ 10-20 mA → β-limited ~1 A; onsemi SOA; PTC Vmax |
| ground clip on R21/R22 (ahead of the fuse) | ≈ 3.4 A / ≈ 38 W sustained in Q1, unfused: beyond DC SOA in tens of seconds. Documented in both places students read ("never a ground clip there") — Finding 6 | topology, SOA |
| motor leads swapped | positive feedback, runaway to the end stop, stall; the back panel prints the remedy ("slider runs to an end and stays: swap the motor leads"); the fader is unhurt (drive is clamp-limited) | layout.py:579, sim stall numbers |
| LOOP open all session, TARGET a few volts | slider parked at the stop at P × TARGET volts; at 5 V: 0.36 A, 3.2 W, pours ≈ 85-90 °C, junctions ≤ ~120 °C — the "HOT" story, safe indefinitely | stall_sweep (5 V: 0.357 A / 3.24 W), thermal.json |
| fader unplugged / replugged live | POSITION floats through U1's 100 k: a twitch (0.81 V, 33 ms recovery per my dropout probe), possibly parking at an end in the safe stall; replugging hot has no ESD path of consequence (4.7 k ends, 100 k inputs) | sim_probe.py S5 |
| a different fader (SparkFun/ALPS motorized slide) | works if it is a 10 k track and a 6-11 V motor (the docs say so); the D rule's trimmer target moves with the plant — DESIGN_NOTES already warns | DESIGN_NOTES "The fader, measured" |
| every trimmer at an end | P = 0: nothing moves; P max: ringing/saturation; D = 0 or D cap either: ringing by degrees; I = 0: nothing; I max: hunting (the sim's 50 k hunt). All bounded by the clamp-limited drive — these *are* the lessons | results.json p_only/pd/pi rows |
| a switch half-way | MSK12C02 is break-before-make; mid-travel floats the common: SW1 mid floats TARGET (bias currents park it), SW2 mid ≈ OPEN, SW3/SW4 mid = D/I out of the sum, SW5 mid = no D cap. All benign, all self-correcting when the slider seats | switch topology + nets |

Nothing reachable damages the **fader**: its motor sees the clamp-limited drive and its
track sits behind the 4.7 k end resistors. The two board-killers are both printed on the
board (rail shorts, the R21/R22 clip). What would further reduce risk at no cost to
clarity: the F1-loop-pair idea of Finding 6, and the ×10-probe sentence of Finding 5.

## 4. Checked and found right

So the next round need not repeat it:

- **The build reproduces.** From a clean copy with KiCad 10.0.7 (AppImage auto-found by
  kienv): ERC 0, DRC 0 (with schematic parity), 252 circuit assertions, fab checks, 30/30
  doc claims. Committed `sim/results.json`, `sim/thermal.json`, `docs/MANUFACTURING.md`,
  every gerber in `out/motorpid/gerbers/`, and `hardware/motorpid.kicad_pcb` are
  **byte-identical** to my rebuild. The PCB is bit-deterministic (uuid5 stabilisation);
  the schematic differs only in five fresh UUID lines (Finding 9).
- **The sign chain and topology are the book's** (§3.2), including the awkward ones:
  P = −ERROR re-inverted at the summing amp, D's sign, I's sign, and the LOOP-open
  grounding that turns the driver into P GAIN × TARGET.
- **LM321 SOT-23-5 pinout** (1 = +IN … 5 = V+), verified against TI's connection diagram,
  the KiCad symbol, and the generator's pin map — a potential board-killer, dead right.
- **Every op-amp supply pin has its 100 nF**, the bulk caps' polarities are right in the
  netlist, and the series Schottkys point the protecting way (D1 pin 1 = cathode → +15 V).
- **The five slide switches end-to-end**: datasheet contact sense (handle-side closing),
  footprint = KiCad official = EasyEDA, netlist (commons and throws), silk "1"/"3" at the
  correct physical ends, legends matching the nets (incl. SW5: pin 1 = 22 nF, pin 3 = 100 nF;
  SW3/SW4 "off" = output shorted to its own virtual ground, which also discharges C8 —
  elegant and correct), and the D IN/OFF shorting scheme safe for the op-amp.
- **The TARGET knob direction** (Alps drawing: pin 3 = CW end; RV1 pin 3 → +15 V; panel
  "clockwise +") and the **trimmer directions** (rheostat on R(1-2), CW = more R; arcs
  match P↑/D↑/I↓).
- **The JLCPCB rotation table**: every polarised or asymmetric angle re-derived from the
  parts' actual EasyEDA drawings (table in §3.8); the CPLs apply exactly the table, and
  the build asserts that.
- **The back-panel QR**: the build re-decodes it from the written rectangles, mirrored
  correctly (check_outputs.py check_qr).
- **Keyed through-hole parts**: RV1-RV4 hole patterns proven by the build to fit only one
  way round.
- **TO-263-2 vs onsemi's D2PAK land pattern**: compatible, KiCad's pads larger in the
  heatsinking direction.
- **The fuse's placement** (everything the student touches behind it; clamps and snubber
  ahead) and the red lamp circuit across it.
- **The thermal budget**: stall sweep peaks 3.41 W at 7 V / 0.5 A; docs design to 3.7 W;
  junctions 120/122 °C bench, *lower* on standoffs (113/116 °C) — the printed "use the
  standoffs" has the model behind it; MJB SOA covers the stall and the fused short.
- **The sim's own numbers reproduce exactly** and its fader/plant parametrisation is the
  measured one, with unmeasured parameters flagged in the docs.
- **Wiper-dropout and windup behaviour** (my probes): twitch-not-runaway, and bounded
  recovery.
- **The front silk reads as the schematic** and the back is a self-consistent manual
  (bar the fuse sentence and the two sheet nits).
- **The DRC net catches silk overflow on the back text** — demonstrated when my first
  patch draft's 133-char line tripped `silk_over_copper` against J2's pad; the final
  patches rebuild green.

## 5. What I could not check, and why

- **The fader's motor polarity sense.** DESIGN_NOTES claims the Bourns drawing has the
  lever moving toward terminal 1 when A is positive. I read both Bourns PSM pages and the
  MD100AM2B motor sheet (bpsm_*.png, md100.txt): neither states a polarity-to-direction
  law. Benign if wrong (instant runaway to a stop at first power, and the back panel's own
  remedy is "swap the motor leads"), but the drawing claim should not be asserted as fact.
- **The PTC's real behaviour at 0.63 A** — datasheet-only by definition here; hence my
  proposed wording says "a minute or two", not a promise. First-board check: hold a
  full-drive stall cold and time the lamps.
- **Real LM321 capacitive-load behaviour** (Finding 5) and real input-bias residuals —
  silicon, not paper.
- **Contact bounce and brush noise** — bench phenomena; the snubber and split feedback are
  the right mitigations on paper.
- **The thermal model's absolute accuracy** (one calibration point, ±25 %) — the first
  board's thermocouple plan stands; my review agrees with its margins, not its decimals.
- **JLCPCB's datum offsets and live stock** — the preview-day items PLACEMENT_CHECKS.txt
  already exists for; prices and the 2 oz multiplier are labelled estimates.
- **The book's page numbers** — I verified against the Lab 10L text and figures, not a
  paginated printing.

## 6. Publishing

- The repository's own hygiene is right: `datasheets/` (vendor PDFs), the book, the JLC
  caches, and `out/*.net` (which embeds an absolute build path and date) are all
  gitignored; the committed tree (source, `out/motorpid/` package, docs, images) contains
  no absolute paths — proven by byte-identical rebuild from a different absolute path — no
  credentials, and no personal data beyond the authors' names and the public repo URL the
  board deliberately prints.
- **My own directory needs the same care before it is committed**: this review's working
  files include a book excerpt and vendor datasheets fetched for evidence. Per the repo's
  rule I have moved all of them under `project/` (which `/design_reviews/*/project/` in
  .gitignore excludes) or deleted them: `book_10L_excerpt.txt`, `ptc_full.txt`,
  `jvj_cap.pdf`, `mjb44h11.pdf` and the full-page datasheet renders live in
  `project/datasheets/review_work/`; the bulky KiCad 10.0.6
  AppImage and its extracted tree (`tools/`) are deleted. What remains in the review
  directory is REPORT.md, the patches, the probe scripts, the logs, and small evidence
  crops — brief datasheet figure excerpts used for verification comment, consistent with
  how the repo itself treats datasheets (fetch, don't commit; the crops are the evidence
  the findings cite).

## 7. Patches

All in `patches/`, generated against the repo root, applied to my `project/` copy and
**build-verified**: `./make.py` green — ERC 0, DRC 0, 252/252 assertions, all fab checks,
30/30 doc claims, sheet overlap check clean (build_patched3.log). The copy is left in the
patched state as evidence; diffing its `scripts/` and `docs/` against the repo root shows
exactly these changes (its `hardware/` and `out/` then differ by the regenerated sheet and
silk texts, which is the point).

| file | what it fixes |
|---|---|
| `patches/scripts_kienv.patch` | Finding 2: explicit KICAD_APPRUN/KICAD_APPIMAGE win over a PATH `kicad-cli` |
| `patches/scripts_gen_sch.patch` | Findings 3 + 1: title block "D up to 22 ms … I up to 1 s"; TARGET SOURCE note "±3 V"; the fuse note and FUSE box tell the hold/trip-band truth in the same space |
| `patches/scripts_layout.patch` | Finding 1: back-panel WARNING row — "A short opens the fuse in a second (red lamps); a stall takes a minute or two." (78 chars, fits the row's width budget the way the old line did) |
| `patches/scripts_parts.patch` | Finding 1 + 8: PTC description states the short/stall timing truth; the trimmer description says 3362P-pattern/BOCHEN |
| `patches/scripts_check_circuit.patch` | Finding 7: the rolloff message computed from the real endpoints (340 Hz at RV3 max, 1.47 kHz at the D rule) |
| `patches/docs_HANDBOOK.patch` | Finding 1: §2's stall sentence — between hold and trip, opens in a minute or two, fastest warm |
| `patches/docs_DESIGN_NOTES.patch` | Finding 1: "Not yet proven" #5 rewritten to the measured curve reading and the guarantee gap |

Deliberately not patched (author's prose call): the "±13 V"/"within 1.5 V of the rails"
framing (Finding 4), the ×10-probe sentence (Finding 5), and a CLAIMS extension covering
the sheet's two number strings (§3.9).

## Evidence index

Builds: `build.log`, `build2.log`, `build3.log` (KiCad 9 failure → 10.0.6 ERC failure →
clean 10.0.7 build), `build_patched.log`/`build_patched2.log` (my over-long back line
tripping DRC), `build_patched3.log` (patches green). Probe sims: `sim_probe.py`,
`sim_windup.py`, `sim_stall_margin.py`. Datasheet evidence crops: `lm321_conn3.png` (TI
pinout), `msk12_circuit/topview/pads/section.png` (contact sense), `rk09k_front2.png`
(knob law), `b3362_drawing.png` (clone drawing), `bpsm_*.png` (fader), `jvjcap_dim.png`
(electrolytic polarity), `mjd_land.png`/`mjb44h11` land pattern page (D2PAK footprint),
`ptc_tt_curve.png`/`ptc_tt_zoom.png` (the time-current chart I digitised). Renders read as
a student: `silk_q1..4.png`, `top_q*.png`, `bot_q*.png`, `sw1_silk.png`, `sw3_silk.png`,
`sch_titleblock.png`, `sch_targetin.png`. Full extracted texts (kept out of the commit
set): `project/datasheets/`.
