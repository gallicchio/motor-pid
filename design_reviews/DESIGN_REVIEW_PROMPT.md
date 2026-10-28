# Design review brief: PID motor control board (Lab 10L), rev A

**Nothing you say in the chat will be read or kept. Your review exists only if it is a
file in your directory.** Make a directory

    design_reviews/<YYYY-MM-DD>_<YourModel-Version>/

at the top of this repository, dated the day you start and named after yourself
(letters, digits, dots, hyphens and underscores only: `2026-10-27_GPT-5.2`,
`2026-10-27_Gemini-3.0-Pro`, `2026-10-26_Claude-Opus-5.5`), and write your report as
`REPORT.md` inside it. Creating that directory and writing into it is **required**; it
is not a change to the project. Write your verdict and your findings table into the
report first, then fill in the details, so a half-finished report survives an
interruption.

**What you are reviewing: rev A as it stands after review round 1.** The author
reviewed the board first and Jason had its fixes applied (the fuse now sits between
the push-pull and DRIVE; the integrator's capacitor is a 1 µF polypropylene film);
then two other reviewers' findings were applied (RV1's JLCPCB rotation, the fuse's
stall story and its 60 V grade, rail clamps D5 and D6, the op-amp's real swing in
the simulation, and more). `docs/DESIGN_NOTES.md`, "Review round 1", lists what
changed. Review the repository as it is now; do not read the earlier reviews until
your own report is written (section 0).

**Look for problems at every level**, from whether the board carries out the spirit of
the lab down to whether the copper will work. A finding that the board teaches the
wrong lesson, or would leave an instructor worse off than the book's breadboard, is
worth as much as a short circuit; so is a number in a document that the board does not
deliver. Nothing is out of scope because the author decided it: Jason's decisions are
listed in section 6 with their reasons, and a reasoned case against one is welcome.

## 0. Ground rules

Several reviewers work on this repository at the same time, and the author may have
the project open in KiCad. So:

- **Only ever create, edit or delete files inside your own directory.** Notes, scripts,
  logs, renders, simulations, copies, patches and the report all go there.
- **Do not change git**: no add, commit, rm, mv, checkout, switch, restore, reset,
  stash, branch, tag, clean, rebase, merge, pull or push. Reading commands (log, show,
  diff, blame, grep) are fine.
- **Do not run `./make.py` in place**, nor any `scripts/gen_*.py`, `sim/pid_sim.py`
  (it always rewrites `sim/results.json`), `sim/thermal.py --board`,
  `scripts/jlc_api.py`, `scripts/easyeda.py` or `scripts/jlc_datasheet.py` from the
  repository's root: they rewrite `hardware/`, `out/`, `build/`, `docs/images/`,
  `docs/MANUFACTURING.md`, `sim/results.json`, `sim/thermal.json` and the caches under
  `scripts/`, which the other reviewers are reading. To build, simulate or try a
  change, copy the project into your directory first, from the repository's root:

  ```bash
  D=design_reviews/<YYYY-MM-DD>_<YourModel-Version>
  mkdir -p "$D"
  rsync -a --exclude .git --exclude build/ --exclude datasheets/ \
        --exclude datasheets_not_in_git/ --exclude design_reviews/ ./ "$D/project/"
  cd "$D/project" && ./make.py          # a few minutes; needs KiCad 10 and ngspice, see README.md
  ```

  The copy is about 20 MB and builds into itself: every script finds its paths from
  its own location. `design_reviews/*/project/` is gitignored, so the copy is never
  committed; everything else in your directory is kept. Put any change you want to
  propose in your report as a patch (`diff -ru` against the original), so the author
  can apply it through the generators.
- **Everything the build makes is committed**, so nothing has to be built to review it:
  the schematic and board (`hardware/motorpid.kicad_sch`, `hardware/motorpid.kicad_pcb`),
  the fab package (`out/motorpid/`: gerbers, BOM, CPL, prints, `PLACEMENT_CHECKS.txt`),
  the simulation's numbers (`sim/results.json`, `sim/thermal.json`), the renders and
  plots (`docs/images/`, earlier rounds in `docs/history/`) and the documents.
- **Datasheets are not in git** (copyright): `datasheets/` is ignored. Fetch what you
  need yourself (`python3 scripts/jlc_datasheet.py <LCSC code>` in your copy writes
  into the copy's `datasheets/`) or read the vendors' pages. If you are working on the
  author's machine, `datasheets/` at the repository's root already holds most of them,
  including the fader's (`bourns_psm_slider_pot.pdf`), and `datasheets_not_in_git/`
  holds the book, *Learning the Art of Electronics* (Hayes and Horowitz, 2016): read
  Lab 10L there, in place, and do not copy it into your directory or quote more of it
  than a finding needs. Otherwise the book's circuit is quoted stage by stage in
  `scripts/gen_sch.py` and asserted part by part in `scripts/check_circuit.py`; if you
  know the book, check the quotation.
- **Settle disagreements with a datasheet, a calculation or a simulation**, not by
  memory or majority. A finding with a number and a source outranks a verdict.
- You share one machine with the other reviewers: no long background jobs, no
  `/tmp` files with common names (use your directory).
- Other reviewers' directories may already be there, the author's among them. Do not
  read them until your own report is written: the rounds are worth most when the
  reviews are independent.

## 1. What it is

Lab 10L of the book: a PID loop that holds a motorized fader (a slide potentiometer
driven by a small DC motor and a belt) where a TARGET voltage says. The board is the
book's Fig. 10L.10 laid out as its own schematic: the white silkscreen lines are the
copper, each of the seven op-amps (LM321, the single-amplifier LM358) sits at the
centre of a drawn triangle, the two power transistors of the motor driver sit inside
drawn transistor symbols, dashed boxes name the stages as the book names them
(difference amplifier, inverter and summing amplifier, together "the pseudo op-amp";
differentiator; integrator; motor driver; the fader's track; a follower), and 17 wire
loops take a scope probe. Five slide switches choose the TARGET source (knob or jack),
open or close the LOOP, switch D and I in or out, and pick the differentiator's
capacitor (22 nF for this fader, the book's 100 nF for its rotary motor-pot); a "1"
and a "3" mark each switch's ends. Three trimmers set P, D and I, each with a printed
arc saying what clockwise does. A 0.35 A resettable fuse sits between the push-pull and
DRIVE, so the feedback, the DRIVE loop, DRIVE OUT and the motor are behind it. TARGET
comes from a centre-detent knob or a BNC; POSITION and DRIVE go out on BNCs through
1 k; power, the motor and the fader's track are on screw terminals. The back of the
board is the students' bench reference: they read the back, not the README.

The fader is the lab's: a Bourns PSM01-082A-103B2 (10 k, taper B2, 10 V motor),
measured on Jason's bench (`docs/DESIGN_NOTES.md`, "The fader, measured"). The board is
170 x 120 mm, one per lab station, and JLCPCB assembles all of it, through-hole parts
included, from the files in `out/motorpid/` as they stand, on 2 oz copper.

Everything was generated by the Python under `scripts/` and `sim/` from a conversation
with Claude (`CLAUDE_CODE_CHAT.md`, fifteen prompts); nothing was drawn by hand. Read
the generators as well as their output.

| read | for |
|---|---|
| `README.md` | the one-page summary, the book's blocks against the board's, how to build |
| `docs/HANDBOOK.md` | the student and instructor guide: the electronics alone, the fader, the exercises in the lab's order, every probe loop, the limits |
| `docs/DESIGN_NOTES.md` | the departures from the book and why, the board, the simulation, what is not yet proven, the stall and its cooling, the fader's measurements, the trimmers' ranges |
| `docs/MANUFACTURING.md` | the order form field by field, the costs, the JLCPCB rotations, the parts and their stock |
| `CLAUDE_CODE_CHAT.md` | what was asked and why each thing is the way it is |
| `scripts/parts.py` | every part: value, footprint, LCSC code, stock, JLCPCB rotation |
| `scripts/layout.py` | the board: placements, wires, back runs, pours, the hop, texts, boxes, arcs, the back's text |
| `scripts/gen_sch.py`, `scripts/gen_pcb.py` | the schematic (with its notes) and the board (copper follows the silk wires) |
| `scripts/check_circuit.py` | the 258 netlist assertions |
| `sim/pid_sim.py` | the ngspice model of the board as built, the fader's plant model, every scenario |
| `sim/thermal.py` | the board's thermal model, the cooling comparison and the as-built check |
| `docs/images/motorpid-top.png`, `-silk-top.png`, `-silk-bottom.png`, `-render-*.png`, `schematic.png`, `sim-*.png` | the board, the bare silkscreen front and back, 3D renders, the sheet, the simulated responses |

## 2. The claim to break

"At a lab station, students can do Lab 10L on this board in the book's order (P alone
and its residual error, then D against the ringing, then I against the residual),
see on the scope why each term does what it does, and the board survives what they
will do to it; the lab's fader works with it as wired; JLCPCB builds it from
`out/motorpid/` as it stands; and nothing on the board or in its documents is wrong."
The board's own numbers, each of which the build checks:

- ERC 0; DRC 0 at every severity with schematic parity, at 0.21 mm track and gap
  (2 oz copper), 0.8 mm minimum text and 0.15 mm silk clearance;
- 258 circuit assertions pass against the exported netlist; the sheet has no text
  overlaps; the fab package passes its checks (gerber layers and extent, drill files,
  BOM against CPL, each LCSC code's JLCPCB description against the value and
  package, stock, the QR code decodes, the keyed parts);
- 31 numbers quoted in the documents and on the sheet match the build;
- the simulation (`sim/results.json`; behavioural LM321, generic D44H11 / D45H11
  transistors, the fader as a 14 ohm motor with back EMF, sliding and breakaway
  friction and end stops; the LM321's output 2 V from each rail): rails +/-14.8 V
  after the diodes; ringing near 30 Hz at high P gain, so the D rule (RC = T/6) asks
  for 5 ms, RV3 = 239 k with 22 nF; P gain 5 leaves 373 mV of residual error and does
  not overshoot, gain 22 overshoots 26 %, with D by the rule it swings back only
  0.4 % and comes to rest 9.7 % past the target (the friction's dead band) in 54 ms,
  gain 100 with D 3 % and settles in 29 ms; I (fully clockwise, RC 1 s) takes the
  residual to about 12 mV, and hunts at 50 k; a 10 V step peaks at 0.63 A and
  11.7 V of drive; a stall at full drive 0.61 A, 3.1 W in one transistor; a stall at
  a few volts up to 3.4 W in it (at 7 V of DRIVE, 0.5 A, which the 0.35 A fuse may
  hold); DRIVE (the MOTOR terminal) shorted to ground 1.9 A and 22 W in one
  transistor until the fuse opens; 4 mA of quiescent supply current. The model's
  LM321 has no input bias current;
- the thermal model on the board as built (`sim/thermal.json`): in the worst stall,
  taken as 3.7 W (the transistor's 3.4 W rounded up), board on a bench in 25 C air, junctions 120 C (Q1) and 122 C (Q2), pours
  85 to 88 C on average; the build fails above 125 C;
- 110 footprints, all on the front; 201 SMT and 29 through-hole joints; 75 vias;
  1 hop (a crossing on the back layer); 48 BOM lines, 13 JLCPCB Extended codes;
  parts $12.21 a board; 2 assembled about $122, 10 assembled about $244 (the 2 oz
  price is a guess: JLCPCB does not publish it).

## 3. What to attack

Each item names where to look. Disagreement is welcome; a numbered finding with a
file and line, or a reference designator and net, and a number with its source, is
the most useful form. The order runs from the lab's intent down to the copper; do not
stop at the top.

1. **The spirit of the lab.** Lab 10L is about a student feeling why P alone leaves an
   error and rings when pushed, why D damps it, why I removes the residual and what
   too much of each does, on a real, imperfect plant. Does this board serve that, or
   does it get in the way? Ask, among others:
   - Does the silkscreen-as-schematic help a student see the pseudo op-amp and the
     three terms, or is it too dense to read at the bench? Is anything the book makes
     the student build (and so understand) handed over ready-made in a way that loses
     the lesson?
   - Are the right things adjustable and switchable? The P, D and I trimmers (1 M
     linear, clockwise = more resistance, so clockwise is less I), the D CAPACITOR
     switch, D and I IN / OFF, the LOOP switch (open = DRIVE is P GAIN x TARGET) and
     the TARGET SOURCE switch. Is anything the lab needs missing (a disturbance, a
     view of the error, a way to compare the terms on one screen), or present but
     pointless?
   - The plant is sticky (2 to 3 V to break loose, stick-slip on a slow triangle). Is
     that a good teacher or a frustration? Do the exercises in `docs/HANDBOOK.md`
     section 3 work on it as written, given `sim/results.json`?
   - Would an instructor rather have this or the book's breadboard, and why? What
     does a student lose by not building it?
2. **The circuit against the book** (`scripts/gen_sch.py`, `out/motorpid.net`,
   `hardware/motorpid.kicad_sch`, `docs/DESIGN_NOTES.md` "The circuit is the book's,
   with these departures"). Fig. 10L.10's pseudo op-amp (unity difference amplifier,
   inverter, summing amplifier), the derivative (Fig. 10L.9) and integral
   (Fig. 10L.10) stages, the motor driver with split feedback (Fig. 10L.3), the plant
   and its end resistors (Fig. 10L.1). Is every value and every connection the book's
   or a stated departure? Are the signs right, so that a positive error drives the
   fader toward the target through every path (P, D, I) with LOOP closed? Does
   `scripts/check_circuit.py` assert everything that matters, and what does it not
   assert?
3. **What the board adds**, each as a circuit: the LM321 everywhere (the book says
   "not 411" for the driver; check its output swing, its slew and its drive into
   270 ohm and the bases); TARGET's knob between 6.8 k end resistors and its detent;
   the TARGET IN jack (what protects U1 from +/-20 V or a generator left at 20 Vpp?);
   the LOOP switch grounding the POSITION side; the 1 ohm emitter resistors; the PTC
   between the push-pull and DRIVE, inside the driver's feedback loop, and the red
   lamps across it; the SS34 clamps and the 10 ohm + 100 nF snubber, both ahead of
   the fuse; the 1 µF polypropylene integrator capacitor (Panasonic ECW-F,
   through-hole) and the LM321's bias current through I's 1 M; the POSITION
   follower and the 1 k series outputs; the input diodes and bypassing; the D2PAKs
   in their pours.
4. **The plant model and the simulation** (`sim/pid_sim.py`, `sim/results.json`,
   `docs/images/sim-*.png`, `docs/DESIGN_NOTES.md` "The fader, measured"). The motor
   and friction are fitted to Jason's bench numbers; the 5 V traverse time (0.8 s),
   the inertia and the friction's fall with speed are not measured. Check the model
   against the Bourns data sheet and the measurements. Then the questions it has not
   been asked: the motor's inductance and brush noise with the LM321 driving a
   push-pull inside a split feedback loop (does U6's loop oscillate on its own, with
   and without the snubber, with a scope probe on BASES?); the D stage with a 10x
   probe on its output; the integrator's windup at an end stop and how long the
   student waits; the D rule's settle time (the sim reports 1500 ms, the end of its
   window, for gain 22 with D by the rule: is that the stick-slip hunt, and does the
   handbook promise something else?); the wiper dropouts the bench saw.
5. **Power, protection and heat** (`docs/DESIGN_NOTES.md` "A stall at a few volts",
   `sim/thermal.py`, `scripts/parts.py` PTC, `sim/results.json` `stall_sweep`). The
   worst stall is 3.7 W in one transistor for as long as the 0.35 A hold / 0.7 A trip
   PTC holds. Check the thermal model (convection coefficients, FR4 conductivities,
   its one calibration point, what it leaves out), the MJB44H11's RthJC and SOA
   against onsemi's data sheet, whether the PTC (LUTE 1812L035/60GR) really
   holds or trips at 0.5 A and 0.61 A and how fast, what a 90 C pour does to its
   neighbours (U6, the SS34 leakage, the electrolytics, the trimmers), and a DRIVE
   or MOTOR short to ground (2 A, 23 W) or to a rail (up to 30 V across the PTC,
   its rating). Is "HOT if the motor stalls" enough?
6. **The silkscreen as a schematic.** Read `docs/images/motorpid-silk-top.png` and
   `motorpid-top.png` as a student would, with no other document: is every
   connection a junction dot where three wires meet and a hop where two cross without
   meeting? Does each transistor symbol put B, C and E on the right pads (the D2PAK's
   tab is the collector; the circle is drawn round the leads and capped by the tab),
   the arrow on the emitter, NPN and PNP distinguishable? Is any label ambiguous,
   misleading, abbreviated or beside the wrong thing? Do the switch legends, the box
   names, the arcs and the loop names match `docs/HANDBOOK.md` and the back? Read the
   back (`motorpid-silk-bottom.png`) as the only manual a student will read.
7. **Copper and board** (`hardware/motorpid.kicad_pcb`, `scripts/gen_pcb.py`,
   `scripts/layout.py`). Copper follows the drawn wires and DRC's parity says every
   net is complete: check the motor current's path (DRIVE, the emitter wires, the
   rails into the pours, the vias that carry it), the hop, the ground plane where the
   back runs cut it, the pours' connection to their rails, clearances to the M3 holes
   and the BNC flanges, the fiducials, the custom footprints in
   `hardware/lib/motorpid.pretty/` (BNC, MSK12C02 slide switch, RK09K knob, 3362P
   trimmer, KF301 terminals, RH-5019 loop) against their drawings, KiCad's TO-263-2
   against onsemi's recommended D2PAK land pattern, and the LM321's SOT-23-5 pinout
   against TI's.
8. **The JLCPCB package** (`out/motorpid/`, `scripts/parts.py JLC_ROTATION`,
   `out/motorpid/PLACEMENT_CHECKS.txt`, `docs/MANUFACTURING.md`). Most CPL rotations
   are *predicted* from JLCPCB's land patterns, never seen in a preview: the D2PAKs
   (+180, datum 2.45 mm toward the leads), the SOT-23-5, the slide switches, the knob,
   the trimmers (`python3 scripts/easyeda.py <LCSC code>` in your copy fetches their
   drawing). Check the polarised parts (diodes, LEDs, electrolytics, the transistors,
   the op-amps). Does Economic PCBA fit the through-hole parts and 2 oz copper, or does
   the order need Standard? Is the cost model in `scripts/gen_docs.py` right? Anything
   else that would stop their line or their importer.
9. **The documents as a lab handout.** `docs/HANDBOOK.md`: does every exercise work
   as described given the simulation; do the expected probe-loop voltages follow from
   the circuit; is anything a student would misread? Do the README, the HANDBOOK, the
   DESIGN_NOTES, the schematic's notes and the back of the board agree with each other
   and with the board (the build checks 31 numbers; which numbers, counts and names
   does it not check)? `docs/DESIGN_NOTES.md` "Not yet proven" is the author's list of
   what could fail on the first board: what is missing from it?
10. **What a student will do to it.** Supply reversed; +15 and -15 swapped; one rail
    only; a 20 V peak generator into TARGET IN; a scope's ground clip on a probe loop
    (it shorts that node to ground: which loops are rails, and can a clip reach
    anything ahead of the fuse?); DRIVE or MOTOR shorted to
    ground or to a rail; a ground clip on R21 or R22 (ahead of the fuse, and the
    handbook tells students to measure the motor current there with two probes);
    the motor wires swapped (the loop runs away to an end and
    stalls); the LOOP left open with TARGET at a few volts through a whole lab
    session; the fader unplugged or replugged with power on; a different fader (a
    SparkFun or ALPS motorized slide pot); every trimmer at an end; a switch half way.
    Which of these damages the board or the fader, and what would prevent it at no
    cost to clarity?

## 4. The standard

The author follows a rules file, `CLAUDE_PCB.md`, that is not in this repository. Its
points that apply here, to be used as checks:

- the silkscreen is the schematic: wires are copper, junction dots where three meet,
  hops where two cross; an op-amp sits in its triangle and a transistor in its
  symbol; grounds point down, rails are lines, + and - are written as such;
- every connector pin and every control labelled beside it, by what it does, in full
  words; connector names big, with their limits; every switch position says what it
  does; every knob and trimmer has an arc saying what clockwise does, and clockwise
  is always more resistance;
- the back of the board is the students' manual: one item per line, https URLs, no
  jargon the class does not use;
- nothing on the silkscreen overlapping anything; no text under 0.8 mm, no line under
  0.15 mm; nothing sits on a dashed box's edge;
- a lab-station board may be big for the sake of probe loops and legibility; a board
  every student gets is squeezed;
- every LCSC code checked against its description and its land pattern; every
  rotation either read in a real preview or marked predicted and listed for the
  preview; polarised parts' marks in the fab notes;
- no hand soldering: JLCPCB fits everything, through-hole included;
- three fiducials; no front copper pour under a drawing, except where copper is a
  heatsink;
- one source of truth for every fact (`scripts/parts.py`, `scripts/layout.py`), and
  every number in a document checked against the build;
- simulate the netlist the schematic exports, not a hand-typed deck;
- a reproducible, deterministic build from one command, relative paths only;
- the most likely causes of a dead board listed, each with what catches it.

## 5. The tools (in your copy)

| command | what it does | writes |
|---|---|---|
| `./make.py` | footprints, models, simulation, schematic, ERC, netlist, circuit checks, board, DRC, thermal check, fab package, documents; stops at the first failure | `hardware/`, `out/`, `build/`, `docs/images/`, `docs/MANUFACTURING.md`, `sim/results.json`, `sim/thermal.json` |
| `./make.py --stage sch` (`libs`, `sim`, `sch`, `pcb`, `out`, `docs`, `project`) | one stage; `sim` reads the netlist `sch` exported last | the same, for that stage |
| `python3 scripts/check_circuit.py out/motorpid.net` | the 249 netlist assertions | nothing |
| `python3 scripts/check_schematic.py hardware/motorpid.kicad_sch` | text overlaps on the sheet | nothing |
| `python3 scripts/check_outputs.py` | the fab package | `scripts/jlc_cache.json` |
| `python3 sim/pid_sim.py [--plots]` | every scenario, printed; edit a copy to ask new questions (the deck is built from `out/motorpid.net`; the plant and scenarios are near the top) | `sim/results.json`, and `docs/images/sim-*.png` with `--plots` |
| `python3 sim/thermal.py` / `--board` | the cooling comparison / the board as built (reads `out/pcb_geom.json`) | nothing / `sim/thermal.json` |
| `python3 scripts/jlc_api.py C233689` | JLCPCB stock, price and description of a code | `scripts/jlc_cache.json` |
| `python3 scripts/easyeda.py C233689` | JLCPCB's land pattern of a code, for the rotation question | `scripts/easyeda_cache.json` |
| `python3 scripts/jlc_datasheet.py C233689` | fetches a code's datasheet | `datasheets/` |
| `python3 -c "import sys; sys.path.insert(0,'scripts'); import kienv; kienv.cli('pcb','drc','--format','report','--severity-all','--schematic-parity','-o','drc.rpt','hardware/motorpid.kicad_pcb')"` | KiCad's DRC on the board as it is | `drc.rpt` |
| `python3 -c "import sys; sys.path.insert(0,'scripts'); import kienv; kienv.cli('pcb','export','pdf','--mode-single','--layers','F.Cu,F.Silkscreen,F.Mask,Edge.Cuts','-o','top.pdf','hardware/motorpid.kicad_pcb')"` | a colour render of any layers (then `pdftoppm -r 400`) | `top.pdf` |

KiCad 10 is found by `scripts/kienv.py`: `kicad-cli` on PATH, or `KICAD_APPIMAGE`
pointing at a KiCad 10 AppImage. The simulation needs `libngspice`; without it the
build uses the committed `sim/results.json` and says so. The thermal model needs
numpy, scipy and matplotlib.

## 6. Already known or decided

Jason's decisions, with his reasons (`CLAUDE_CODE_CHAT.md` has his words):

- **170 x 120 mm**, past JLCPCB's small-board price: one board per lab station, so the
  probe loops and legible silkscreen are worth more than a few dollars.
- **The 0.35 A resettable fuse is the only protection**; an earlier active current
  limiter was removed (it made the push-pull hard to draw, and the fuse covers the
  full-drive stall).
- **D2PAKs (MJB44H11 / MJB45H11) on 2 oz copper**, chosen 2026-10-26 over the lab's
  TO-220 MJE3055T / MJE2955T on screw-on heatsinks: nothing to solder, no live
  heatsinks among the probe loops. The comparison is in DESIGN_NOTES.
- **The trimmers are 1 M linear**, from his breadboard: 1 M spans sluggish to
  aggressive, the best point off centre but not crammed.
- **Clockwise is always more resistance**, with an arc saying what that does to the
  gain (so clockwise is less I).
- **The TARGET SOURCE switch stays** (knob or jack).
- **The fuse sits between the push-pull and DRIVE** (round 1, 2026-10-26), so a
  ground clip on the DRIVE loop or a shorted motor lead opens it; the clamps and the
  snubber stay at the transistors, ahead of it.
- **The integrator's capacitor is a 1 µF polypropylene film** (round 1: "one more
  appropriate for filter work"); 1 µF rather than 10 so that it is not a brick and
  the 1 M trimmer spans 1 ms to 1 s.
- **The back of the board is the students' manual**; they will not read the README.

Known and open (`docs/DESIGN_NOTES.md` "Not yet proven" and "Review round 1"): the
rail sag through D2 that, with TARGET from the jack, lets DRIVE rest at a volt or so
with the slider stuck (the knob cancels it); no common-mode test
without a clip lead; the date on the board (set on the order day); the slide switches'
contact sense; a dead short of DRIVE; the fader model's unmeasured speed and inertia; every
JLCPCB rotation but the BNC's and the LEDs' is predicted; the PTC's trip time; the
knob's turn direction (pin 3 assumed clockwise); the pours as heatsinks, to be
checked with a thermocouple on the first board. The servo track's resistance is
unknown; nothing is connected to it. The wiper's occasional dropouts (seen on the
bench) leave POSITION on U1's 100 k for a moment: a twitch, not a runaway, by the
author's reckoning. The 2 oz copper price is not published by JLCPCB; the cost model
assumes 1.5 times the 1 oz price. The repository is public at
`github.com/gallicchio/motor-pid`, which the back of the board and its QR code carry.

## 7. The report: `REPORT.md` in your directory

It must stand alone: the author reads it without the chat, beside the other reviews.

1. **Verdict**, one paragraph: order as it is; order after named fixes; do not order.
   Say how sure you are.
2. **Findings**, most severe first, numbered, first as a table (number, severity,
   level, where, one line) and then each in full:
   - severity: **blocker** (the board cannot be made, or will not work, or is unsafe
     in a teaching lab, or defeats the lab's purpose); **major** (a feature or an
     exercise is likely to fail, a part is outside its ratings, a document teaches
     something wrong); **minor** (works, but worse than it should); **nit**;
   - level: **lab** (the spirit, the teaching), **circuit**, **simulation**,
     **power/heat**, **silkscreen**, **copper**, **fab**, **docs**, **abuse**;
   - where: file and line, or reference designator and net;
   - what is wrong, and what you expected;
   - the evidence: a calculation, a datasheet's figure and page, a simulation or DRC
     or render you made and kept in your directory;
   - the fix you propose, as a change to the generator where that applies;
   - how sure you are.
3. **Section 3's questions**, each answered by number, with the number or the
   simulation that answers it.
4. **What you checked and found right**, so the next round need not repeat it.
5. **What you could not check**, and why.
6. **Publishing**: anything that should not be in a public repository (copyrighted
   text or drawings, personal information, absolute paths, keys).
7. **Patches**, if any, as files in your directory, listed here.

Write the report as you go. If you are stopped, a half-finished report beats none.
