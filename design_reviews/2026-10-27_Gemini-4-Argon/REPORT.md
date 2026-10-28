# Design Review Report: PID Motor Control Board (Lab 10L), Rev A

> Author's note, 2026-10-27: its findings were applied the same day (`docs/DESIGN_NOTES.md`,
> "Review round 1"); `/home/<user>/` paths in it were shortened to `~/` before committing.

**Reviewer:** Gemini-4-Argon
**Date:** 2026-10-27
**Subject:** `gallicchio/motor-pid` at commit `bd544b1` (after Review Round 1 applied)

## 1. Verdict

**Order after named fixes (high confidence, 95%).** The board is a thoughtful, well-engineered realization of *Learning the Art of Electronics* Lab 10L: the exported netlist matches Fig. 10L.10 stage for stage, negative feedback closes with the right sign for the Bourns PSM01-082A-103B2 fader across P, D, and I, ERC and DRC pass with zero violations on 2 oz rules, and the D2PAK collector pours keep steady-state stall junction temperatures safely below 125 °C on a bench. Before ordering or handing the documents to students, fix at minimum: **(1)** `RV1`'s JLCPCB CPL rotation and datum offset in `scripts/parts.py` (`(90, (2.5, -3.5))` puts the RK09K knob 180° backwards and 1.4 mm off its holes in `motorpid_cpl_jlcpcb_upload.csv`; should be `(270, (3.5, -2.5))`), **(2)** the `F1` resettable fuse rating or its stall-trip claims (`0.634 A` full-drive stall is *below* LUTE `1812L035/30GR`'s `0.70 A` minimum trip current, where the datasheet curve is asymptotic at ~90 s rather than the claimed 5–10 s; `1812L020/30GR` or `1812L030/30GR` actually trips a stall), **(3)** the single-rail power-up hazard (powering only `+15 V` or `-15 V` pulls the floating rail to `+6.5 V` or `-10.2 V`, reverse-biasing the polarized 100 µF electrolytic `C12` or `C11`), **(4)** the false handbook/design-note claim that every probe loop is behind the fuse (only `TP7` `DRIVE` is; `TP9`/`TP10` are unfused rails and `TP2`–`TP6`, `TP12`, `TP13` are direct `LM321` outputs that overheat if shorted to `GND` on `±15 V` supplies), **(5)** the `F.SilkS` text overlap between `"-15 V"` and `"THE FADER'S TRACK"` plus the unclipped `/POSITION` dashed line cutting through `C8`, and **(6)** the schematic and handbook text errors (`D up to 10 ms`, `I up to 10 s`, `±0.5 V`, `10 mA`, title-block overflow, and the missing `SW1` toggle in "Measure your gains"). A complete generator patch (`patch_fixes.diff`) is included in this directory and verified with `./make.py`.

## 2. Findings

| # | Severity | Level | Where | One-line summary |
|---|---|---|---|---|
| 1 | **major** | fab | `scripts/parts.py:264`, `out/motorpid/motorpid_cpl_jlcpcb_upload.csv` (`RV1` / `C351173`) | `JLC_ROTATION["C351173"]` has wrong angle (`+90°` vs `+270°`) and swapped `(dx, dy)` (`(2.5, -3.5)` vs `(3.5, -2.5)`), placing `RV1` 180° backwards and 6–7 mm off its pads in the JLCPCB CPL. |
| 2 | **major** | power/heat | `scripts/parts.py:165`, `F1` (`1812L035/30GR`), `docs/HANDBOOK.md:78`, `docs/DESIGN_NOTES.md:31,247` | Full-drive stall current (`0.634 A`, falling to `~0.58 A` as the winding warms) is below LUTE `1812L035/30GR`'s `0.70 A` $I_{\text{trip}}$ rating (`~90 s` at `0.70 A` on datasheet curve F, not 5–10 s), so a full-drive stall may never trip `F1`. |
| 3 | **major** | abuse | `J6`, `D1`, `D2`, `C11`, `C12`, `LED1` (`scripts/gen_sch.py:766–815`) | Powering one rail with the other disconnected pulls the unpowered rail to `+6.46 V` (on `-15V`) or `-10.21 V` (on `+15V`), reverse-biasing polarized 100 µF electrolytic `C12` or `C11` by 6.5–10.2 V. |
| 4 | **major** | circuit / simulation | `D1`, `D2`, `R3`, `R4`, `sim/pid_sim.py:42,258`, `sim/results.json` | Asymmetric motor current through series Schottky diodes `D1`/`D2` shifts `(V+ + V-)/2` and thus `POSITION` by `60–120 mV` (positive feedback when `TARGET` is ground-referenced on `J1`), latching `sim/pid_sim.py` at `V(DRIVE) = -1.25 V` at `t = 0` (`P = 22`) and drifting `POSITION` to `-38 mV` (`103.8 %` residual error) at `P = 1.5`. |
| 5 | **major** | docs / abuse | `docs/DESIGN_NOTES.md:24–27`, `docs/HANDBOOK.md:172`, `TP2–TP6`, `TP9–TP13` | Only `TP7` (`DRIVE`) is behind fuse `F1`; `TP9`/`TP10` are unfused `±15 V` rails behind 3 A diodes, and `TP2–TP6`, `TP12`, `TP13` are direct `LM321` outputs whose continuous ground-short rating (`V+ <= 15 V`, TI SNOS935B Note 3) is exceeded on `±14.8 V` (`29.6 V` total, `TJ ≈ 182 °C`). |
| 6 | **major** | fab / docs | `scripts/kienv.py:53,141,181`, `make.py:151`, `.gitignore:22` | `kienv.py` picks up system `/usr/bin/kicad-cli` (KiCad 9.0.8) and `/usr/share/kicad` and ignores `KICAD_APPIMAGE`; `make.py` runs `stage_sim` before `stage_sch` while `.gitignore` excludes `out/*.net`, breaking first-pass builds on fresh clones. |
| 7 | **minor** | silkscreen | `scripts/layout.py:345,354,539–548`, `scripts/gen_pcb.py:568,617` | `F.SilkS` overlap between `"-15 V"` flag `(120.6, 102.3)` and `"THE FADER'S TRACK"`; unclipped `/POSITION` dashed line crosses 6 front wires and `C8`'s body; missing junction dot at `/POSITION` T-junction `(46.0, 105.0)`; `C3`, `C4`, `F1`, `TP2`, `TP6`, `TP7`, `C20` sit on dashed stage-box edges. |
| 8 | **minor** | docs / silkscreen | `scripts/gen_sch.py:68–70,309,531,722,939`, `scripts/check_circuit.py:161`, `scripts/check_schematic.py` | Schematic has stale numbers (`D up to 10 ms`, `I up to 10 s`, `±0.5 V` at `J1`, `Quiescent about 10 mA`, `11 Hz` in `check_circuit.py`), title-block text overflowing the sheet border, 3 text-text overlaps (`Q1.Value` vs fuse text, `POSITION OUT`), and 19 wire-text collisions. |
| 9 | **minor** | docs / lab | `docs/HANDBOOK.md:118–119,146–151`, `docs/DESIGN_NOTES.md:7–9,225,256`, `sim/pid_sim.py:48` | Handbook "Measure your gains" omits switching `SW1` (`TARGET SOURCE`) to `3` (jack) for D and back to `1` (knob) for I; `P=10` residual error (`-124 mV`) is overshoot sticking past target, not stopping short; `DESIGN_NOTES.md` misstates why the book says "not 411" (phase reversal, p. 423) and says `RK09K` datasheet could not be fetched when it is in `datasheets/`; Bourns datasheet specifies `200 mm/s` at `10 V` vs model's `340 mm/s`. |
| 10 | **minor** | simulation | `sim/pid_sim.py:211–220`, `sim/results.json` (`pd`, `p_only`) | `step_metrics()` measures settling time to `±5 %` of ideal target `1.0 V` instead of resting value `yy[-1]`, reporting `settle_s = 1.5 s` (window end) and `6.6 %` overshoot for `P=22 + D` (`rule`) when the slider actually stops in `37.3 ms` with `0.52 %` dynamic overshoot. |
| 11 | **nit** | copper / fab / docs | `scripts/gen_pcb.py:701`, `scripts/parts.py:57–71,160`, `scripts/check_outputs.py:341`, `scripts/gen_docs.py:9` | `Q1`/`Q2` internal emitter tracks use `0.35 mm` (`wide=set()`) instead of `0.6 mm`; `C11` is 78 mm from `Q1` on `0.35 mm` trace; unused `MMBT3904`/`MMBT3906`/`1N4148W` remain in `parts.py` and `MANUFACTURING.md` alternates; `check_stock()` uses `15` test points instead of `17`; stale `opamp` docstrings. |

---

### Detailed Findings

#### Finding 1 — `RV1` (`RK09K1130A70`, `C351173`) JLCPCB CPL rotation is 180° backwards and datum shift has `dx` and `dy` swapped
- **Severity:** **major**
- **Level:** **fab**
- **Where:** `scripts/parts.py:264`, `scripts/gen_outputs.py:134–143`, `out/motorpid/motorpid_cpl_jlcpcb_upload.csv` (`RV1`), `docs/MANUFACTURING.md:133`
- **What is wrong, and what was expected:**
  `scripts/parts.py:264` defines:
  ```python
  "C351173": (90, (2.5, -3.5), "predicted", "RK09K: KiCad's pin row runs along +y from pin 1, theirs along +x; their origin at the middle of the body")
  ```
  In `out/motorpid/motorpid_cpl_kicad_native.csv`, `RV1` is placed at `Mid X = 24.0000, Mid Y = 83.5000, Rotation = 180.0` (where CPL `Mid Y = 120 - y_board`). With `JLC_ROTATION["C351173"] = (90, (2.5, -3.5))`, `out/motorpid/motorpid_cpl_jlcpcb_upload.csv` places `RV1` at `Mid X = 21.5000, Mid Y = 87.0000, Rotation = 270.0`.
  Expected: EasyEDA's land pattern for `C351173` (`RES-TH_RK09K1130A70`) after applying the upload CPL's `(Mid X, Mid Y, Rotation)` should superimpose pads `1, 2, 3` and mounting brackets `4, 5` onto the PCB's pads (`(24.0, 83.5)`, `(24.0, 86.0)`, `(24.0, 88.5)` and `MP` at `x = 17.0`). Instead, every pad is off by `5.9` to `7.2 mm` and the part is turned 180° backwards!
- **Evidence:**
  1. In KiCad's unrotated `Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Vertical` (`y_kicad` down, `y_cpl` up):
     - `pad 1` = `(0, 0)`, `pad 2` = `(0, -2.5)` (`y_cpl`), `pad 3` = `(0, -5.0)` (`y_cpl`).
     - Mounting posts `MP` are at `x = +7.0`, centered at `y_cpl = -2.5`.
     - Thus the center of the body in KiCad's unrotated frame (`y_cpl` up) is at **`(dx, dy) = (+3.5, -2.5)`**, not `(+2.5, -3.5)` (`dx` and `dy` were transposed).
  2. From `python3 scripts/easyeda.py C351173` (cached in `scripts/easyeda_cache.json`):
     - `pad 1` is at `(-2.499, +3.499)` (`y_down`) = `(-2.5, -3.5)` (`y_cpl` up).
     - `pad 2` is at `(0.000, +3.499)` (`y_down`) = `(0.0, -3.5)` (`y_cpl` up).
     - `pad 3` is at `(+2.499, +3.499)` (`y_down`) = `(+2.5, -3.5)` (`y_cpl` up).
     - Mounting brackets `pad 4, 5` are at `(±5.000, -3.499)` (`y_down`) = `(±5.0, +3.5)` (`y_cpl` up).
  3. On the PCB (`layout.py:101`, `RV1` at `(24.0, 36.5)` with `rot = 180°`), the mounting brackets are on the **left** (`x = 17.0`) and signal pins `1, 2, 3` are on the **right** (`x = 24.0`, `y_cpl = 83.5, 86.0, 88.5`). Rotating EasyEDA's unrotated footprint so its top mounting brackets (`y_cpl = +3.5`) move to the left (`x = -3.5`) and its bottom signal row (`y_cpl = -3.5`) moves to the right (`x = +3.5`) requires a **counter-clockwise rotation of `urot = 90.0°`**, which from `rot = 180.0°` requires an offset of **`d = 270°` (`-90°`)**, not `+90°`.
  4. With the current `(90, (2.5, -3.5))` (`urot = 270.0°`, `(ux, uy) = (21.5, 87.0)`):
     - EasyEDA `pad 1` lands at `(18.001, 89.499)` vs board `(24.000, 83.500)` (`diff = (-6.00, +6.00) mm`).
     - EasyEDA `pad 2` lands at `(18.001, 87.000)` vs board `(24.000, 86.000)` (`diff = (-6.00, +1.00) mm`).
     - EasyEDA `pad 3` lands at `(18.001, 84.501)` vs board `(24.000, 88.500)` (`diff = (-6.00, -4.00) mm`).
     - EasyEDA `pad 4, 5` (brackets) land at `x = 25.0` (on top of the signal pin column!).
  5. With `(270, (3.5, -2.5))` (`urot = 90.0°`, `(ux, uy) = (20.5, 86.0)`):
     - EasyEDA `pad 1` lands at `(23.999, 83.501)` (`diff = (-0.001, +0.001) mm`).
     - EasyEDA `pad 2` lands at `(23.999, 86.000)` (`diff = (-0.001, +0.000) mm`).
     - EasyEDA `pad 3` lands at `(23.999, 88.499)` (`diff = (-0.001, -0.001) mm`).
     - EasyEDA `pad 4, 5` land at `(17.001, 91.001)` and `(17.001, 81.001)`, matching the PCB bracket slots at `x = 17.0`.
- **Proposed fix:** In `scripts/parts.py:264`, change `(90, (2.5, -3.5), ...)` to `(270, (3.5, -2.5), ...)`.
- **Confidence:** **100%**.

---

#### Finding 2 — Full-drive stall (`0.634 A`, dropping to `~0.58 A` warm) is below `F1` (`1812L035/30GR`)'s `0.70 A` trip current; datasheet curve shows `~90 s` or no trip, not "5–10 s"
- **Severity:** **major**
- **Level:** **power/heat**
- **Where:** `scripts/parts.py:165` (`F1`, LCSC `C18198328`), `docs/HANDBOOK.md:78`, `docs/DESIGN_NOTES.md:31,247`, `scripts/gen_sch.py:610`, `scripts/layout.py:598`
- **What is wrong, and what was expected:**
  Every document (`README.md`, `docs/HANDBOOK.md:78`, `docs/DESIGN_NOTES.md:31,247`), the schematic (`scripts/gen_sch.py:610`), and the back silkscreen (`scripts/layout.py:598`) state that stalling the fader at full drive (`0.63 A` at `8.9 V`) trips the `0.35 A` resettable fuse `F1` (`1812L035/30GR`) in **"5–10 s"** ("within seconds the 0.35 A resettable fuse opens, the red lamps across it light").
  In reality, per the manufacturer's datasheet, `0.634 A` is **below the minimum guaranteed trip current $I_{\text{trip}} = 0.70\text{ A}$** at 25 °C!
- **Evidence:**
  1. First, LCSC `C18198328` (`1812L035/30GR`) is manufactured by **LUTE (Shenzhen Lute Electronic Co., Ltd., `www.lutefuse.com`)**, not Littelfuse (`datasheets/1812L035_30GR_C18198328.pdf` / `datasheets/1812L050_60GR_C19078719.pdf`, page 1 & page 4).
  2. On page 4 of `1812L035_30GR_C18198328.pdf` (Electrical Characteristics at 25 °C):
     - `I_hold = 0.35 A` (maximum current device will pass without tripping in 25 °C still air)
     - `I_trip = 0.70 A` (minimum current at which device will trip in 25 °C still air)
     - `V_max = 30 Vdc`, `I_max = 40 A`, `Pd_typ = 1.0 W`, `R_min = 0.200 Ω`, `R_1max = 1.700 Ω`
     - `Time to Trip (Max.)`: `0.10 Sec` at `8.00 A`.
  3. On page 9 of `1812L035_30GR_C18198328.pdf` ("Typical Time to Trip at 25°C" log-log plot, curve **F = `1812L035`**):
     - Curve `F` reaches `t = 5 s` at **`I = 1.15 A`** and `t = 10 s` at **`I = 1.00 A`**.
     - At `I = 0.70 A` ($I_{\text{trip}}$), curve `F` is at the top boundary of the chart at **`t ≈ 90–100 s`** and goes vertical (asymptotic).
     - At `I = 0.634 A` (`sim/results.json` `stall.i_motor_a`), the current is **below `I_trip = 0.70 A`**, in the region where the PTC is not guaranteed to trip at 25 °C.
     - Even worse, during a full-drive stall, the fader's 10 V motor dissipates $P_{\text{motor}} = 8.88\text{ V} \times 0.634\text{ A} = 5.63\text{ W}$ (`sim/results.json`). With copper's temperature coefficient of resistance ($\alpha = +0.00393\,\text{K}^{-1}$), a modest `25 °C` temperature rise in the motor winding increases $R_{\text{motor}}$ from $14.0\,\Omega$ to $15.4\,\Omega$, reducing the stall current to $8.95\text{ V} / 15.4\,\Omega = 0.58\text{ A}$—well below `0.70 A`.
     - While `Q1`/`Q2` (D2PAKs on 2 oz copper) safely survive `2.99 W` indefinitely, the fader's small motor is subjected to `5.6 W` continuously while students hold the slider waiting for the red fuse LEDs that do not light.
     - By contrast, for a dead short of `DRIVE` / `MOTOR` to ground (`2.008 A`), curve `F` gives **`t_trip ≈ 0.8–1.0 s`**, which matches the documents' "about 1 s" claim.
- **Proposed fix:**
  - **Option A (recommended if stall protection of the fader is desired):** Change `F1` to **`1812L020/30GR`** ($I_{\text{hold}} = 0.20\text{ A}, I_{\text{trip}} = 0.40\text{ A}$, curve `D` on page 9: trips `0.63 A` in **`~2.5 s`** and `0.50 A` in **`~6 s`**, also eliminating the `7 V` un-tripped `3.4 W` stall case!) or **`1812L030/30GR`** ($I_{\text{hold}} = 0.30\text{ A}, I_{\text{trip}} = 0.60\text{ A}$, curve `E`: trips `0.63 A` in **`~12 s`**). In `sim/results.json`, the continuous running current at 3 V is `0.16 A` and the RMS current during continuous `P = 100` oscillation is `0.191 A`, both within `0.20–0.30 A`.
  - **Option B (if keeping `1812L035/30GR`):** Update `parts.py`, `gen_sch.py`, `HANDBOOK.md`, `DESIGN_NOTES.md`, and the back silkscreen so they do not promise that a `0.63 A` motor stall trips the `0.35 A / 0.70 A` PTC in `5–10 s` (state that `F1` trips on a shorted motor lead at `2 A` in `~1 s`, and may take a minute or more—or hold—on a `0.6 A` stall).
- **Confidence:** **98%** (directly from LUTE `1812L` datasheet table p. 4 and curve `F` p. 9).

---

#### Finding 3 — Single-rail power-up (`+15 V` on with `-15 V` open, or vice versa) pulls the unpowered rail to `+6.5 V` / `-10.2 V`, reverse-biasing 100 µF electrolytic `C12` or `C11`
- **Severity:** **major**
- **Level:** **abuse / circuit**
- **Where:** `J6`, `D1`, `D2`, `C11`, `C12`, `LED1`, `LED2` (`scripts/gen_sch.py:766–825`, `scripts/layout.py:155–166`)
- **What is wrong, and what was expected:**
  In a teaching lab using dual bench supplies connected via banana-to-screw-terminal leads on `J6`, students routinely turn on one supply output before the other, or leave one rail's banana plug loose. Because `D1` and `D2` (`SS34`) are placed in **series** with `+15V_IN` and `-15V_IN` (rather than antiparallel across the rails to `GND`), an open or unpowered input cannot sink cross-rail current to `GND`. Instead, current from the powered rail flows through the seven `LM321` op-amps (`U1–U7`), the potentiometer dividers (`R1+RV1+R2` and `R3+POT+R4`), and `Q1`/`Q2` into the unpowered rail, driving the unpowered rail to the **opposite polarity** and reverse-biasing the polarized 100 µF aluminum electrolytic bulk capacitor (`C11` or `C12`).
- **Evidence:**
  Simulated in `design_reviews/2026-10-27_Gemini-4-Argon/sims/run_extra_sims2.py` (test 6) on the exported netlist `out/motorpid.net`:
  - **`+15 V` powered (`+15 V`), `-15V_IN` open (`TARGET = +5 V`):**
    `V(+15V) = +14.49 V`, and **`V(-15V) = +6.46 V`**. Because `C12` (`100 µF` 25 V electrolytic, `JVJ25V100M6x5`) has its `+` pad (`pad 1`) on `GND` and its `-` pad (`pad 2`) on `-15V`, `C12` is subjected to **`6.46 V` of reverse bias** (clamped only by `Q2`'s collector-base junction forward-biasing into `BASES`!).
  - **`-15 V` powered (`-15 V`), `+15V_IN` open (`TARGET = +5 V`):**
    `V(-15V) = -14.40 V`, and **`V(+15V) = -10.21 V`**. `C11` (`+` on `+15V`, `-` on `GND`) is subjected to **`10.21 V` of reverse bias**, and `LED1` (`KT-0805G`, typical `VR_max = 5 V`) is reverse-biased through `R26` (`10k`).
  - Per standard aluminum electrolytic ratings (`datasheets/JVJ25V100M6x5_C46550402.pdf`) and IEC 60384-4, continuous reverse voltage above `1.0–1.5 V` causes internal gas evolution, pressure build-up, electrolyte venting, or short-circuit failure.
- **Proposed fix:**
  - In `docs/HANDBOOK.md` and `docs/DESIGN_NOTES.md`, warn students to connect all three `POWER` wires before enabling the bench supply output (so both `+15 V` and `-15 V` come up together).
  - If a hardware change is made in a future revision, place `D3`/`D4`-style `SS34` Schottky diodes antiparallel across `C11` (`GND` anode to `+15V` cathode) and `C12` (`-15V` anode to `GND` cathode), which clamps any single-rail reverse excursion to `< 0.35 V` while keeping series `D1`/`D2` for zero-current reverse-supply blocking.
- **Confidence:** **98%**.

---

#### Finding 4 — Asymmetric rail sag behind `D1`/`D2` couples motor current into `POSITION` (positive feedback when `TARGET` is ground-referenced), latching `sim/pid_sim.py` (`P=22`) at `-1.25 V` at `t=0` and causing `-38 mV` backwards drift (`103.8%` residual) at `P=1.5`
- **Severity:** **major**
- **Level:** **circuit / simulation**
- **Where:** `D1`, `D2`, `R3`, `R4`, `C3`, `C4`, `sim/pid_sim.py:42,258`, `sim/results.json` (`p_only`, `pd`)
- **What is wrong, and what was expected:**
  Both potentiometers (`RV1` via `R1, R2 = 6.8k` and the fader `J5` via `R3, R4 = 4.7k`) derive their `+` and `-` reference ends directly from the post-diode `+15V` and `-15V` rails that also supply the motor driver (`Q1`, `Q2`).
  When the motor draws current $I_m > 0$ from `+15V` (while `-15V` supplies only the `4 mA` op-amp quiescent current), the `+15V` rail drops by:
  $$\Delta V_{+15\text{V}}(I_m) = I_m R_{\text{supply}} + V_{F,\text{D1}}(I_m + I_q) - V_{F,\text{D1}}(I_q)$$
  Even with a `0.3 Ω` supply impedance, the logarithmic forward voltage of the `SS34` Schottky diode `D1` increases by `~90–180 mV` as current rises from `4 mA` to `0.1–0.6 A`, while `D2` on `-15V` stays at `4 mA` (`Vf = 0.218 V`).
  At the midpoint of the fader track ($R_{ta} = R_{tb} = 5\text{ k}\Omega$), the wiper voltage is the average of the two rails:
  $$\Delta V(\text{POSITION}) = \frac{\Delta V_{+15\text{V}} + \Delta V_{-15\text{V}}}{2}$$
  which shifts **negative** by `50–120 mV` when `Q1` conducts (`DRIVE > 0`) and **positive** by `50–120 mV` when `Q2` conducts (`DRIVE < 0`).
  When `TARGET` is driven from the `TARGET IN` BNC (`SW1 = 3`, referenced to `GND` rather than the rails), a negative shift in `POSITION` increases `ERROR = TARGET - POSITION`, which increases `DRIVE = +P * ERROR`—a **positive feedback loop through the power rails** below `C3`/`C4`'s `5 Hz` ($\tau = 32\text{ ms}$) corner frequency whenever the slider is held by static friction!
- **Evidence:**
  Running `design_reviews/2026-10-27_Gemini-4-Argon/check_sim_details.py` on `sim/pid_sim.py` reveals three direct consequences in the committed `sim/results.json`:
  1. **Latched non-zero initial state at `P = 22` (`p_only["22"]` and `pd["none"]`):**
     At `t = 0` (`TARGET = 0 V`, slider mechanically at `V(pos) = 0.00000`), ngspice's `.op` solver (where `C3, C4` are open circuits) converges to a latched state:
     - `V(DRIVE)[0] = -1.2507 V`, `I(Bemf)[0] = -89.3 mA` (since `|-89.3 mA| < I_break = 180 mA`, the slider stays stuck at `V(pos) = 0`!)
     - `V(+15V)[0] = +14.7825 V` (`4.0 mA` through `D1`), `V(-15V)[0] = -14.6629 V` (`92.5 mA` through `D2`, `+119.6 mV` sag)
     - `V(POT+)[0] = +7.6482 V`, `V(POT-)[0] = -7.5313 V` $\implies$ `V(POSITION)[0] = +0.0570 V`
     - `V(ERROR)[0] = -0.0570 V` $\implies$ `V(DRIVE)[0] = 22 × (-0.0570 V) = -1.251 V` (self-consistent positive-feedback latch!).
     Because `step_metrics()` assumes `y0 = 0.0` at `t = 0.1 s` when `V(POSITION)` was actually `+0.0570 V`, `p_only["22"]` reports `overshoot_pct = 26.49 %` (with `ic_zero=("SUM",)`, `V(POSITION)[0] = 0.0000 V` and `overshoot_pct = 27.82 %`).
  2. **Backwards electrical drift at `P = 1.5` (`p_only["1.5"]`):**
     At `P = 1.5`, after the `+1.000 V` step at `t = 0.1 s`, the slider barely moves (`V(pos) = +0.0022 V`), while `DRIVE = +1.56 V` draws `+111 mA` from `+15V`. As `C3` (`10 µF`) discharges over `~32 ms` following the `+15V` sag, `V(POSITION)` drifts **negative** from `0 V` to **`-0.0382 V`**, which is why `sim/results.json` reports `residual_v = 1.0382 V` (`> 1.000 V`!) and `overshoot_pct = -98.79 %`.
  3. **Discrepancy between mechanical `V(pos)` and electrical `V(POSITION)` (`sim/pid_sim.py:42`):**
     `sim/pid_sim.py:42` computes `V_END = 30.0 * 10e3 / (4.7e3 + 10e3 + 4.7e3) / 2 = 7.732 V` using `30.0 V` (`±15.0 V`) instead of the post-diode `29.56 V` (`±14.78 V`, which gives `±7.619 V` unloaded). Combined with rail sag under stalled motor current, at `P = 22` the final mechanical position is `V(pos) = +1.0236 V` while the electrical wiper voltage is `V(POSITION) = +0.9082 V`—a `115 mV` difference.
- **Proposed fix:**
  - In `sim/pid_sim.py`, pass `ic_zero=("SUM",)` in `p_only` and `pd` so `.op` starts at the true zero state (`V(DRIVE)[0] = 0, V(POSITION)[0] = 0`), and compute `V_END` from the post-diode rail voltage (`29.564 V`).
  - In `docs/DESIGN_NOTES.md`, note that because `POT+`/`POT-` share the post-diode motor rails, motor current shifts the potentiometer's zero reference by `~40–100 mV` (`0.2–0.5 mm`) when driven from the ground-referenced `TARGET IN` jack.
- **Confidence:** **100%**.

---

#### Finding 5 — False claims that "every probe loop" is behind the fuse and that a scope ground clip on any probe loop simply opens `F1`
- **Severity:** **major**
- **Level:** **docs / abuse**
- **Where:** `docs/DESIGN_NOTES.md:24–27`, `docs/HANDBOOK.md:172`, `DESIGN_REVIEW_PROMPT.md:104`, `TP2–TP6`, `TP9–TP13`
- **What is wrong, and what was expected:**
  - `docs/DESIGN_NOTES.md:25–26` claims: *"the driver's feedback (R18), the DRIVE loop, DRIVE OUT and the MOTOR terminal are all behind it, so a scope's ground clip on any probe loop, or a shorted motor lead, opens it."*
  - `docs/HANDBOOK.md:172` claims: *"No probe loop is ahead of the fuse."*
  In reality, out of the 13 non-ground probe loops (`TP1–TP13`), **only `TP7` (`DRIVE`) is behind `F1`**.
- **Evidence:**
  1. **`TP9` (`+15V`) and `TP10` (`-15V`)** sit directly on the `+15V` and `-15V` rails after the 3 A `SS34` Schottky diodes `D1` and `D2`, with **no fuse in series**. Clipping a grounded scope clip onto `TP9` or `TP10` shorts the bench supply rail directly to `GND` through `D1` or `D2` (`F1` carries zero current and never opens).
  2. **`TP11` (`BASES`)** sits on the base node of `Q1`/`Q2` after `R19 = 270 Ω`, ahead of `F1`. Clipping a scope ground lead to `TP11` shorts `U6`'s output to `GND` through `270 Ω` (`~40 mA`); `F1` never opens.
  3. **`TP2` (`ERROR`), `TP3` (`P`), `TP4` (`D`), `TP5` (`I`), `TP6` (`SUM`), `TP12` (`U6 OUT`), and `TP13` (`U7 OUT`)** are wired directly to the outputs of `U1–U7` (`LM321` op-amps in SOT-23-5) with no series resistor and no fuse.
     Per TI's `LM321` datasheet (`datasheets/LM321MFX_NOPB_C9405.pdf`, page 2, Absolute Maximum Ratings Note 3, and page 3, Electrical Characteristics Note 6):
     > *"Output Short Circuit to GND, V+ <= 15V and TA = 25°C: Continuous. (3) ... When considering short circuits to ground the maximum output current is approximately 40mA independent of the magnitude of V+. At values of supply voltage in excess of +15V, continuous short circuits can exceed the power dissipation ratings and cause eventual destruction."*
     Because these `LM321` op-amps run on split `±14.8 V` supplies ($V^+ - V^- = 29.6\text{ V}$, right at the `30 V` maximum operating rating), shorting an `LM321` output to `GND` (at `0 V`, which is `14.8 V` below `V+` and `14.8 V` above `V-`) puts `14.8 V` across the `LM321`'s internal output transistor at `~40 mA` sourcing (`P_D = 14.8 V × 40 mA = 0.59 W`). At $\theta_{JA} = 265\,^\circ\text{C/W}$ (TI datasheet page 2), the steady-state temperature rise is $\Delta T_J = 0.59\text{ W} \times 265\,^\circ\text{C/W} = 157\,^\circ\text{C}$ ($T_J \approx 182\,^\circ\text{C} > 150\,^\circ\text{C}$ limit), risking thermal destruction of the op-amp while `F1` remains closed.
- **Proposed fix:** Update `docs/HANDBOOK.md:172` and `docs/DESIGN_NOTES.md:25–26` to state accurately that no *motor-driver output* loop (`DRIVE`) is ahead of the fuse, and explicitly warn students never to attach a scope ground clip to `+15V`, `-15V`, or any signal loop (only to the four `GND` loops `TP100–TP103`).
- **Confidence:** **100%**.

---

#### Finding 6 — `scripts/kienv.py` fails when system KiCad 9 (`/usr/bin/kicad-cli`) is installed alongside a KiCad 10 `.AppImage`, and `make.py` runs `stage_sim` before `stage_sch` while `.gitignore` excludes `out/*.net`
- **Severity:** **major**
- **Level:** **fab / docs**
- **Where:** `scripts/kienv.py:53,141,181`, `make.py:57,151`, `.gitignore:22`
- **What is wrong, and what was expected:**
  1. **`scripts/kienv.py` ignores `KICAD_APPIMAGE` and `~/.local/bin/kicad-10*.AppImage` when KiCad 9 is installed in `/usr/bin`:**
     Line 53 sets `PLAIN_CLI = shutil.which("kicad-cli")` without checking its version or `KICAD_APPIMAGE`. Then `runner()` (line 141) checks:
     ```python
     if APPRUN is None and _MOUNT is None and PLAIN_CLI is None:
         _use_appimage()
     ```
     On this machine, `/usr/bin/kicad-cli` is KiCad `9.0.8` and `~/.local/bin/kicad-10.0.7-x86_64.AppImage` is present. Because `PLAIN_CLI` is `"/usr/bin/kicad-cli"`, `runner()` never calls `_use_appimage()`—even when `KICAD_APPIMAGE=~/.local/bin/kicad-10.0.7-x86_64.AppImage` is explicitly passed! `describe()` then runs `/usr/bin/kicad-cli --version`, sees `'9.0.8'`, and exits with an error telling the user to set `KICAD_APPIMAGE` (which they already set!).
     Furthermore, in `share_dir()` (lines 181–208), `/usr/share/kicad` (line 198, which holds KiCad 9's symbol/footprint libraries when system KiCad 9 is installed) is checked *before* `_use_appimage()` (line 208), so any script that calls `kienv.share_dir()` first (such as `gen_sch.py` or `check_outputs.py`) silently loads KiCad 9 libraries instead of mounting the KiCad 10 AppImage.
  2. **`make.py` stage order vs `.gitignore`:**
     `make.py:151` defines `STAGES = [("libs", stage_libs), ("sim", stage_sim), ("sch", stage_sch), ...]`, while `.gitignore:22` ignores `/out/*.net` (`out/motorpid.net`). On a fresh clone of the repository, `out/motorpid.net` does not exist when `stage_sim` runs (because `stage_sch` exports `out/motorpid.net` *after* `stage_sim`!), causing `stage_sim` to fail with `FileNotFoundError` and print `"!! simulation did not run (no libngspice?); the committed sim/results.json is used"` even when `libngspice` is installed.
- **Evidence:**
  Running `KICAD_APPIMAGE=~/.local/bin/kicad-10.0.7-x86_64.AppImage python3 -c "import sys; sys.path.insert(0,'scripts'); import kienv; print(kienv.describe())"` on the unmodified repo exits with code 1 (`This project needs KiCad 10; the one that was found reports '9.0.8'`). After applying our fix in `project/scripts/kienv.py`, it mounts `~/.local/bin/kicad-10.0.7-x86_64.AppImage` and prints `KiCad 10.0.7`.
- **Proposed fix:**
  - In `scripts/kienv.py`, accept `shutil.which("kicad-cli")` as `PLAIN_CLI` only when `os.environ.get("KICAD_APPIMAGE")` is unset and `kicad-cli --version` starts with `"10."`, and call `_use_appimage()` at the start of `share_dir()` when `APPRUN`, `_MOUNT`, and `PLAIN_CLI` are `None`.
  - In `make.py` (`stage_sim`), run `stage_sch()` first if `out/motorpid.net` does not yet exist.
- **Confidence:** **100%**.

---

#### Finding 7 — Front silkscreen text overlap (`"-15 V"` flag vs `"THE FADER'S TRACK"`), unclipped `/POSITION` dashed line crossing 6 front wires and `C8`'s body, missing junction dot on `/POSITION`, and parts on dashed stage-box edges
- **Severity:** **minor**
- **Level:** **silkscreen**
- **Where:** `scripts/layout.py:345–356,425–426,539–548`, `scripts/gen_pcb.py:568,617`
- **What is wrong, and what was expected:**
  Section 4's standard requires: *"nothing on the silkscreen overlapping anything... nothing sits on a dashed box's edge... junction dots where three meet."*
  Inspection of `hardware/motorpid.kicad_pcb` via `pcbnew` (`design_reviews/2026-10-27_Gemini-4-Argon/check_pcb_deep.py` and `check_pcb_junctions.py`) found:
  1. **Text-to-text overlap on `F.SilkS` (`layout.py:354,546`):**
     The `-15V` flag for `R4` at `(119.0, 102.3)` places its default right-hand text `"-15 V"` at `(120.6, 102.35)` with bounding box `(120.60, 101.62) – (124.70, 103.08)`, which overlaps the stage-box title `"THE FADER'S TRACK"` at `(113.5, 101.2)` (`(113.50, 100.42) – (125.80, 101.98)`) by `4.1 × 0.36 mm`.
     Also, `"TARGET"` at `(17.0, 20.3)` (`y = 18.72..21.88`) and `"centre = 0 V, clockwise +"` at `(17.0, 22.2)` (`y = 21.47..22.93`) overlap vertically in `pcbnew`'s bounding boxes.
  2. **Unclipped `/POSITION` dashed back wire (`gen_pcb.py:617`, `layout.py:345–346`):**
     In `gen_pcb.py:617`, `silk_grounds()` draws `L.DASHED_BACK` (`/POSITION` along `y = 105.0` and `x = 12.0`) without calling `self.clip(a, b)`. When Round 1 replaced `C8` with the `18.1 × 9.3 mm` through-hole film capacitor at `(93.7, 110.3)` (courtyard `y = 105.3..115.3`), `C8`'s feedback row moved down to `y = 110.3` and `DRIVE OUT`'s wire moved down to `y = 118.3`. Consequently, the horizontal dashed `/POSITION` line at `y = 105.0` now cuts right across the `INTEGRATOR` stage, crossing 5 vertical front-layer silkscreen wires (`Net-(SW4-A)` at `x = 86.80` and `104.05`, `/I` at `x = 101.20`, `Net-(J3-In)` at `x = 112.50`, `-15V` at `x = 119.00`) plus `Net-(J2-In)` at `(12.00, 101.00)`, and running through `C8`'s silkscreen outline edge (`y = 105.35`).
  3. **Missing junction dot on `/POSITION` T-junction at `(46.0, 105.0)` (`gen_pcb.py:568`):**
     At `(46.0, 105.0)`, the `/POSITION` dashed line splits into two branches (up along `x = 46.0` to `SW2` pin 3, and left along `y = 105.0` to `U7` pin 1). Because `silk_wires()` filters `front = [sg for sg in self.segments if sg[3] != pcbnew.B_Cu]`, this 3-way T-junction on `/POSITION` gets no junction dot.
     Additionally, `TP4` (`D`, pad spanning `y = 69.8..73.8` at `x = 101.2`) sits directly on top of the `/D` T-junction at `(101.2, 73.5)`, and `_on_pad(margin=0.55)` suppresses the junction dots at `/POT+` `(129.0, 109.4)` and `/POT-` `(119.0, 109.4)` even though those points are outside `R3` and `R4`'s pads.
  4. **Footprints sitting on dashed stage-box edges (`layout.py:539–548`):**
     Although `silk_boxes()` clips the dashed lines around courtyards so no ink lands on pads, the dashed stage-box boundaries pass directly through the bodies of `C3` and `C4` (`y = 109.4` on `THE FADER'S TRACK` bottom edge `y = 109.6`), `F1` (`y = 94.0`, straddling `MOTOR DRIVER` bottom edge `y = 92.5` and fuse box top edge `y = 92.8`), `TP7` (`y = 91.0` on `y = 92.5`), `TP6` (`x = 127.8` on `x = 126.0`), `TP2` (`x = 70.0` on `x = 69.0`), and `C20` (`y = 17.0` on `y = 18.5`).
- **Evidence:** Output of `design_reviews/2026-10-27_Gemini-4-Argon/check_pcb_deep.py` and `check_pcb_junctions.py`.
- **Proposed fix:**
  - In `scripts/layout.py:354`, change `("-15V", POS_X - 5.0, 102.3)` to `("-15V", POS_X - 5.0, 102.3, -1.6, 0.0, "right")` so `"-15 V"` sits to the left of the flag bar (`x = 113.3..117.4`), below `"THE FADER'S TRACK"`.
  - In `scripts/layout.py:425–426`, space `"TARGET"` (`y = 20.1`) and `"centre = 0 V, clockwise +"` (`y = 22.4`) by `2.3 mm`.
  - In `scripts/gen_pcb.py:568,617`, include `L.DASHED_BACK` in the junction-dot counter and clip `L.DASHED_BACK` segments with `self.clip(a, b)`.
- **Confidence:** **100%**.

---

#### Finding 8 — Schematic sheet (`scripts/gen_sch.py`) has stale numbers (`D up to 10 ms`, `I up to 10 s`, `±0.5 V`, `10 mA`, `11 Hz`), title-block overflow off the sheet border, and text/wire collisions missed by `check_schematic.py`
- **Severity:** **minor**
- **Level:** **docs / silkscreen**
- **Where:** `scripts/gen_sch.py:68–70,309,529–533,721–722,939`, `scripts/check_circuit.py:161`, `scripts/check_schematic.py`
- **What is wrong, and what was expected:**
  1. **Four stale numbers on the schematic and netlist checker:**
     - `scripts/gen_sch.py:70` (title block comment 2): `"P from 1 to 101, D up to 10 ms (slide pot) or 100 ms (rotary), I up to 10 s"`. With `C5 = 22 nF` and `RV3 = 1 MΩ`, D reaches **22 ms** (not 10 ms); with `C8 = 1 µF` and `RV4 = 1 MΩ`, I reaches **1 s** (not 10 s).
     - `scripts/gen_sch.py:309` (next to `J1` `TARGET IN`): `"(±0.5 V at 0.2 Hz) replaces the knob"`. Review Round 1 updated the front silkscreen, back silkscreen, handbook, and bottom schematic note to **`±3 V at 0.2 Hz`**, but missed this text at `J1`.
     - `scripts/gen_sch.py:939` (`THE PLANT` note): `"Quiescent about 10 mA."` Every other document and `sim/results.json` state **`4 mA`**.
     - `scripts/check_circuit.py:161`: prints `"(the book's slider: 25 Hz; the simulation: 11 Hz)"`, whereas the simulation's natural oscillation frequency is **`31 Hz`**.
  2. **Title-block text overflows the right border of the A2 frame (`scripts/gen_sch.py:68–69`):**
     In KiCad's title block (`108 mm` text width), `company` is 113 characters (`~156 mm` wide) and `comments[0]` is 93 characters (`~128 mm` wide); in `docs/images/schematic.png` and `out/motorpid/motorpid-schematic.pdf`, both lines visibly protrude past the right border of the title block and page frame. `scripts/check_schematic.py` did not check `title_block` entries.
  3. **Text-text overlaps and wire-text crossings on the schematic (`scripts/gen_sch.py:529–533,721–722`):**
     - `Q1.Value 'MJB44H11'` (`(394.2, 107.8)–(403.6, 109.4)`) overlaps the `FUSE` note lines `"(0.6 A) trips it in 5-10 s..."` (`x = 403.3, y = 106.9..108.1`) and `"about 1 s; the red lamp..."` (`x = 403.3, y = 108.8..110.0`), and is crossed vertically by `Q1`'s collector wire at `x = 401.3`. (`check_schematic.py` missed the overlap by `0.10 mm` because of its `slack = 0.35 mm` allowance.)
     - `POSITION OUT` (`y = 259.9..262.6`, `size = 2.2`) overlaps its subtitle `"the pot's voltage, buffered: ±7.7 V, 1k out"` (`y = 262.4..263.7`).
- **Evidence:** Output of `design_reviews/2026-10-27_Gemini-4-Argon/check_sch_deep.py` and visual inspection of `out/motorpid/motorpid-schematic.pdf`.
- **Proposed fix:** Update lines 68–70, 309, 529–533, 721–722, and 939 in `scripts/gen_sch.py` and line 161 in `scripts/check_circuit.py` (included in `patch_fixes.diff`).
- **Confidence:** **100%**.

---

#### Finding 9 — `docs/HANDBOOK.md` and `docs/DESIGN_NOTES.md` bench-procedure and datasheet discrepancies
- **Severity:** **minor**
- **Level:** **docs / lab**
- **Where:** `docs/HANDBOOK.md:118–119,146–151`, `docs/DESIGN_NOTES.md:7–9,225,256`, `sim/pid_sim.py:48`
- **What is wrong, and what was expected:**
  1. **`docs/HANDBOOK.md:146–151` ("Measure your gains") omits switching `TARGET SOURCE` (`SW1`):**
     The procedure starts with `TARGET` from the knob (`SW1 = 1`) at `0.10 V` to measure `P GAIN = SUM / ERROR`, then says: *"D: switch D IN and feed TARGET IN a ±1 V triangle at 10 Hz, a slope of 40 V/s: the D loop is a square wave..."*, and then *"I: switch I IN with TARGET at 0.10 V..."*. If a student follows this literally without switching `TARGET SOURCE` (`SW1`) from `1` (knob) to `3` (`TARGET IN` jack) for the D measurement and back to `1` for the I measurement, the triangle wave on `TARGET IN` is disconnected from the circuit and `D` reads `0 V`! Also, for `I`, because `U5` is an inverting integrator (`I = -(1/RC) \int ERROR dt`), with `TARGET = +0.10 V` the `I` loop ramps **negative** (`-0.10 V / RC` V/s) and will already be saturated at `-14.7 V` unless the student toggles `I IN / OFF` (`SW4`) from `1` (reset) to `3` (`I IN`).
  2. **`docs/HANDBOOK.md:118–119` ("I." exercise):**
     States: *"Back to a low P gain with its residual error: 5 to 10 (the book's 100k is 10, where the simulation leaves 124 mV of a 1 V step)."*
     In `sim/results.json`, `p_only["10"]["residual_v"]` is **`-0.1238 V` (`-124 mV`)**—negative because at `P = 10` (with D off) a `1 V` step **overshoots by `+12.5 %` to `+1.125 V` and sticks `124 mV` past the target**, rather than stopping short of the target as `P = 5` (`+373 mV` residual) does! Also, on this board `P GAIN = (10k + RV2)/10k` due to series resistor `R14 = 10k`, so `RV2 = 100k` gives gain `11` (`RV2 = 90k` gives gain `10`).
  3. **`docs/DESIGN_NOTES.md:7–9` misstates the book's reason for "not 411" and the book's op-amp:**
     States: *"The lab says 'not 411' for the motor driver (the 411's output cannot drive the push-pull's bases) and uses 411s elsewhere."*
     In *Learning the Art of Electronics* (§10L.2.3, p. 423, footnotes 2 & 3, and Fig. 10L.6, p. 426), the book specifies **"All LM358 op amps"** and explains that the LF411 must not be used because of **input phase reversal** when an input swings near the negative supply rail, turning negative feedback into positive feedback and locking up the loop.
  4. **`docs/DESIGN_NOTES.md:225,256`:**
     - Line 225 says *"the D rule went from 611k to 234k"* (`rv3_k` is `231k`).
     - Line 256 says *"the RK09K sheet itself could not be fetched"*, whereas `datasheets/RK09K1130A70_C351173.pdf` is present in `datasheets/` and its Drawing No. 6 (p. 363) and Circuit Diagram (p. 366) confirm that pin 1 is full CCW and pin 3 is full CW.
  5. **Bourns fader datasheet speed vs `sim/pid_sim.py:48`:**
     `datasheets/bourns_psm_slider_pot.pdf` (p. 1, "Motor Drive Characteristics") specifies **`Lever Speed @ 10 VDC: 20 mm/0.1 sec` (`200 mm/s`)**. In `sim/pid_sim.py:48`, assuming `100 mm` in `0.8 s` at `5 V` (`125 mm/s` at `5 V`, where `2.38 V` is lost to friction `I*R` and only `2.62 V` is back-EMF) gives `KE = 0.1084 V/(pot V/s)`, which predicts **`340 mm/s` at `10 V`** (`1.7×` faster than the Bourns datasheet specification). Fitting `KE` to the Bourns datasheet's `200 mm/s` at `10 V` gives `KE = 0.193 V/(pot V/s)` (corresponding to `~70 mm/s` at `5 V`, or `0.8 s` across the middle `56 mm` of travel).
- **Evidence:** *Learning the Art of Electronics* pp. 423–426; `datasheets/RK09K1130A70_C351173.pdf` pp. 4, 7; `datasheets/bourns_psm_slider_pot.pdf` p. 1; `sim/results.json`.
- **Proposed fix:** Update `docs/HANDBOOK.md` and `docs/DESIGN_NOTES.md` (included in `patch_fixes.diff`).
- **Confidence:** **100%**.

---

#### Finding 10 — `step_metrics()` in `sim/pid_sim.py` reports `settle_s = 1.5 s` (end of window) whenever stiction leaves `> 5 %` static error, hiding the true `37 ms` settling time of `P=22 + D`
- **Severity:** **minor**
- **Level:** **simulation**
- **Where:** `sim/pid_sim.py:206–220`, `sim/results.json` (`pd`, `p_only`)
- **What is wrong, and what was expected:**
  `step_metrics(t, y, t0, y0, y1, band=0.05)` computes both `overshoot_pct` and `settle_s` relative to the ideal target `y1 = 1.0 V` rather than the final resting value `yy[-1]`. Because stiction arrests the slider within a dead band of $\pm V_{\text{break}} / P \approx \pm 2.52\text{ V} / P$ (`±115 mV` at `P = 22`), any step that sticks more than `50 mV` (`5 %`) from `1.000 V` never enters `|yy - 1.0| <= 0.05`, so `settle_s` is reported as `1.5 s` (`1500 ms`, the end of the `1.6 s` simulation window) for **all four `pd` cases (`none`, `rule`, `third`, `triple`)** and for `p_only` at gains `1.5, 5, 10, 22`!
- **Evidence:**
  In `design_reviews/2026-10-27_Gemini-4-Argon/sims/run_extra_sims.py` (test 1), for `P = 22 + D` (`rule`, `RV3 = 231k`), the slider's mechanical position `V(pos)` rises monotonically to `+1.0765 V` (`V(POSITION) = +1.1074 V`) with only **`0.52 %` dynamic overshoot** past its resting value, and **comes to a complete stop (`|vel| < 0.01 V/s`) at `t - t0 = 37.3 ms`** (`53.4 ms` including the `C3`/`C4` rail-recovery tail), not `1500 ms`.
- **Proposed fix:** In `step_metrics()`, report `settle_to_final_s` (time to settle within `±5 %` of `yy[-1]`) alongside `settle_s` (time to enter `±5 %` of `y1`), and report `dynamic_overshoot_pct = max(0, yy.max() - max(y1, yy[-1])) / span * 100`.
- **Confidence:** **100%**.

---

#### Finding 11 — Minor copper, BOM-table, and docstring cleanups
- **Severity:** **nit**
- **Level:** **copper / fab / docs**
- **Where:** `scripts/gen_pcb.py:6,333,701`, `scripts/parts.py:12,57–71,160,260–270`, `scripts/check_outputs.py:341`, `scripts/gen_docs.py:9–10`, `scripts/layout.py:114`
- **What is wrong:**
  1. In `scripts/gen_pcb.py:701`, `_d2pak_geometry` returns `wide=set()`, so the short (`2.2 mm`) copper segments inside `Q1` and `Q2`'s transistor circles from emitter pad `3` to `e_out` are laid at `W_SIG = 0.35 mm` while the external emitter wires to `R21`/`R22` are `W_RAIL = 0.6 mm`. Setting `wide={nE}` and using `L.W_RAIL` in `wires()` makes the entire emitter path `0.6 mm` wide with `0` DRC violations.
  2. `C11` (`100 µF` bulk capacitor on `+15V`) is placed at `(76.0, 17.8)` (`78 mm` west of `Q1`), and both `C11` and `C12` connect to their rails and `GND` via `W_SIG = 0.35 mm` stubs (`C11` pad 1 also sits directly on the `y = 14.0` `+15V` rail line, suppressing its junction dot).
  3. `scripts/parts.py` retains unused `"NPN"` (`MMBT3904`, `C20526`), `"PNP"` (`MMBT3906`, `C53444`), and `"DSW"` (`1N4148W`, `C81598`) entries from the removed current limiter, causing `docs/MANUFACTURING.md:242–249` to print out-of-stock alternates for `MMBT3904` and `MMBT3906`.
  4. `scripts/check_outputs.py:341` uses `"TP": 15` instead of `17` when computing boards' worth of stock for `RH-5019`.
  5. `scripts/gen_docs.py:9–10` and `scripts/gen_pcb.py:6` docstrings still say `out/opamp/...` and `hardware/opamp.kicad_pcb`.
  6. `scripts/parts.py:12` has `BOARD_DATE = "2026-10-24"` (noted as open item 12 for order day).
- **Proposed fix:** Included in `patch_fixes.diff`.
- **Confidence:** **100%**.

## 3. Section 3 Questions

### 1. The spirit of the lab
- **Does the silkscreen-as-schematic help or get in the way?**
  It helps significantly. Each of the seven `LM321` op-amps sits inside its drawn triangle with `+` on top (`pin 1`) and `-` on the bottom (`pin 3`), each D2PAK sits inside its transistor circle with `B, C, E` lettered and capped by its collector pour, and the stage boxes (`DIFFERENCE AMPLIFIER x1`, `INVERTER x-1`, `SUMMING AMPLIFIER`, `DIFFERENTIATOR`, `INTEGRATOR`, `MOTOR DRIVER gain 1`, `THE FADER'S TRACK`, `FOLLOWER x1`) match the functional decomposition of *Learning the Art of Electronics* Figs. 10L.3–10L.10. Once the `/POSITION` dashed line is clipped around component bodies (Finding 7), the front silkscreen reads cleanly at the bench.
- **What does a student lose by not building it on a breadboard, and would an instructor prefer this board?**
  In the book (§10L.1, p. 421), Hayes & Horowitz note that Lab 10L is the most complex analog circuit in the course and that breadboard wiring bugs and missing bypass capacitors dominate student time. On a breadboard, students often spend 2+ hours debugging seven op-amp stages, power-transistor pinouts, and 60 Hz / motor-hash ground bounce before they ever see PID control in action. This board trades wiring practice for control-theory insight: students still perform the open-loop pseudo-op-amp gain check, motor polarity check, P-only residual error & natural oscillation measurement (`f_nat ≈ 31 Hz`), D tuning by the $RC = 1/(2\pi f) \approx T/6$ rule (`5 ms`), I tuning and hunting (`RV4 <= 50 kΩ`), and square-wave vs. slow-triangle stick-slip comparisons. An instructor who wants students to finish and understand all of Lab 10L in a single lab period will strongly prefer this board.
- **Are the right things adjustable and switchable? Is anything missing?**
  - The five slide switches (`TARGET SOURCE`, `LOOP`, `D CAPACITOR` `22 nF / 100 nF`, `D IN / OFF`, `I IN / OFF`) and three `1 MΩ` linear trimmers (`P GAIN`, `D GAIN`, `I GAIN`) with clockwise arcs (`↑R ↑P`, `↑R ↑D`, `↑R ↓I`, `↑TARGET`) cover the entire lab flow.
  - **One missing convenience from the book (§10L.2.4, p. 426, Fig. 10L.6):** The book's first check of the difference amplifier `U1` ties *both* inputs (`R5` and `R7`) to the input pot to verify zero common-mode gain before grounding `R7` for the pseudo-differential gain test. On this board, `SW2` (`LOOP`) switches `R7` between `POSITION` (`3`) and `GND` (`1`), so the common-mode test requires clipping a jumper from `TP1` (`TARGET`) to `J5` pin 2 (`wiper` / `TP8` `POSITION`) with `LOOP` closed (`3`) and the fader unplugged (noted as open item 11 in `DESIGN_NOTES.md`).
- **The sticky plant (2–3 V breakaway, stick-slip on a slow triangle):**
  It is a *better* teacher of why integral control (`I`) is both necessary and dangerous than an ideal frictionless plant: stiction creates an unmistakable static dead band (`373 mV` residual on a `1 V` step at `P = 5`) that `P` and `D` cannot remove without cranking `P` to oscillation, and on a `0.05 Hz` triangle wave (`sim-triangle.png`) students directly see the classic integral stick-slip sawtooth/staircase (described in the book's §10L.4, p. 431: *"the motor fails to move till the I voltage reaches some minimal level; then output voltage jumps to a new level, and waits for another shove"*).

### 2. The circuit against the book
- **Stage-by-stage comparison against *Learning the Art of Electronics* (pp. 421–432):**
  - **Target pot (Fig. 10L.7, p. 427):** `10k` pot (`RV1`) between `+15V` and `-15V` with `6.8k` end resistors (`R1, R2`, giving `±6.26 V` on `±14.8 V` rails, quoted as `±6.4 V` nominal on `±15 V`) and `10 µF` decoupling caps (`C1, C2`, book uses `15 µF`).
  - **Plant pot (Fig. 10L.3, p. 424):** `10k` fader track (`J5`) between `+15V` and `-15V` with `4.7k` end resistors (`R3, R4`, giving `±7.62 V` on `±14.8 V` rails, `±7.73 V` nominal) and `10 µF` decoupling caps (`C3, C4`, book uses `15 µF`).
  - **Difference amplifier `U1` (Fig. 10L.6, p. 426):** Four `100k` resistors (`R5, R6, R7, R8`), `TARGET` into `+` via `R5`, `LOOP` (`POSITION` or `GND`) into `-` via `R7`, output `ERROR = TARGET - POSITION`. Exact match.
  - **Inverter `U2` (Fig. 10L.6, p. 426):** `R9 = 10k` in, `R10 = 10k` feedback, `+` grounded, output `P = -ERROR`. Exact match.
  - **Summing amplifier `U3` (Fig. 10L.6 / 10L.10, p. 431):** Three `10k` summing resistors (`R11` from `P`, `R12` from `D` via `SW3`, `R13` from `I` via `SW4`) into `-` input; feedback is `R14 = 10k` in series with `RV2 = 1M` rheostat (departure from the book's bare resistor substitution box so minimum gain is bounded at `1.0` instead of `0`, maximum `101`). Output `SUM = +((10k + RV2)/10k) × (ERROR + RV3·C·dERROR/dt + (1/RC)∫ERROR dt)`.
  - **Differentiator `U4` (Fig. 10L.9, p. 429):** `ERROR` through `SW5` (`C5 = 22 nF` or book's `C6 = 100 nF`) and `R15 = 1k` into `-` input; feedback is `RV3 = 1M` in parallel with `C7 = 470 pF`; `SW3` selects `D IN` (`3`) or shorts `U4` output to `-` input (`1`, as in Fig. 10L.9).
  - **Integrator `U5` (Fig. 10L.10, p. 431):** `ERROR` through `R17 = 1k` + `RV4 = 1M` into `-` input; feedback is `C8 = 1 µF` polypropylene film (book uses two `15 µF` polarized electrolytics back-to-back = `7.5 µF`); `SW4` connects `I` to `R13` (`3`) or shorts `C8` (`1`, resetting the integrator).
  - **Motor driver `U6` + `Q1/Q2` (Fig. 10L.3, p. 424):** `SUM` into `U6+`; `U6` output drives `BASES` through `R19 = 270 Ω`; HF feedback `C9 = 0.33 µF` from `U6` output to `U6-`; DC feedback `R18 = 10k` from `DRIVE` (behind `F1`) to `U6-`; `1 Ω` emitter resistors `R21, R22` (added), `SS34` clamp diodes `D3, D4` (added), book's `R20 = 10 Ω` + `C10 = 0.1 µF` snubber, and `F1 = 0.35 A` PTC with `R23 = 1k` + antiparallel red LEDs `LED3, LED4` (added).
- **Signs:** With `LOOP` closed (`SW2 = 3`), a positive error ($\text{TARGET} > \text{POSITION}$) produces:
  - `U1` (`ERROR`): $+(\text{TARGET} - \text{POSITION}) > 0$
  - `U2` (`P`): $-(\text{TARGET} - \text{POSITION}) < 0$
  - `U4` (`D`, on rising error): $-R_{V3} C \frac{d\text{ERROR}}{dt} < 0$
  - `U5` (`I`, for sustained positive error): $-\frac{1}{(R_{17}+R_{V4})C_8}\int \text{ERROR}\,dt < 0$
  - `U3` (`SUM`, inverting summer): $-\frac{R_{14}+R_{V2}}{10\text{k}}(P + D + I) > 0$
  - `U6` + `Q1/Q2` (`DRIVE`, non-inverting follower): $\text{DRIVE} = \text{SUM} > 0$.
  Per Bourns' `PSM` datasheet (`datasheets/bourns_psm_slider_pot.pdf`, p. 2), positive voltage on motor terminal `A` (`MOTOR`) relative to `B` (`GND`) drives the lever toward track terminal `1` (`POT+`), increasing `POSITION` toward `TARGET` (negative feedback through all three paths).
- **What `scripts/check_circuit.py` does and does not assert:**
  It makes 252 assertions covering every net, pin, value, footprint suffix, switch throw, diode/electrolytic polarity, probe loop net, and absence of single-pin nets or shorted 2-pin parts. What it does **not** assert: voltage ratings of capacitors/switches/fuses, power ratings of resistors, op-amp common-mode limits, or PCB physical layout/rotations.

### 3. What the board adds (circuit-level analysis)
- **`LM321` everywhere (`U1–U7`):**
  - **Why the book says "not 411":** As noted in Finding 9, the book (§10L.2.3, p. 423, footnotes 2 & 3) forbids the LF411 because of input phase reversal near $V^-$, and uses `LM358`s throughout. The `LM321` is the single-channel `LM358`/`LM324` core (`datasheets/LM321MFX_NOPB_C9405.pdf`), so its input common-mode range includes $V^-$ (`-14.8 V`) up to $V^+ - 1.5\text{ V}$ (`+13.3 V` at 25 °C, $V^+ - 2.0\text{ V}$ over temperature) with no phase reversal.
  - **Supply voltage margin:** At `±15.0 V` bench input, after `D1`/`D2` (`±0.22 V` at `4 mA`), $V^+ - V^- = 29.56\text{ V}$, which is within `0.44 V` of the `LM321`'s `30 V` maximum operating rating (`32 V` absolute maximum, TI SNOS935B p. 2).
  - **Slew rate and output drive into `270 Ω` (`U6`):** At `0.4 V/µs`, a `26 V` rail-to-rail swing takes `65 µs`, negligible against the `15 ms` mechanical time constant. At the `0.79 A` peak current of a `10 V` step (`sim/results.json` `big_step`), `MJB44H11` ($h_{FE} \ge 60$ at `2 A`, typ `120` at `0.8 A`, `datasheets/MJB44H11T4G_C233689.pdf` Fig. 4) requires `~7–13 mA` of base current. With `DRIVE` at `+13.0 V` (`emitter = +13.8 V`, `BASES = +14.5 V`), wait: `U6`'s output itself saturates at $V^+ - 1.5\text{ V} \approx +13.3\text{ V}$, and `R19 = 270 Ω` drops `270 Ω × 10 mA = 2.7 V`, which limits the maximum positive `DRIVE` under load: at a `0.634 A` stall (`I_B ≈ 6.3 mA`), `V(U6 OUT) ≈ +11.6 V`, `V(BASES) ≈ +10.2 V`, `V(Q1_E) ≈ +9.5 V`, and `V(DRIVE) = +8.88 V`. Into a dead short (`DRIVE = 0 V`), `BASES` sits at `+2.8 V`, and `R19 = 270 Ω` limits the base drive from `U6` (`+13.3 V`) to `(13.3 - 2.8)/270 ≈ 39 mA` (matching `LM321`'s `40 mA` typical `I_SOURCE` limit), which caps the short-circuit collector current to `~2.0 A` even without an active current limiter!
- **`TARGET` knob (`RV1`) and `TARGET IN` jack (`J1`):**
  - `RV1` (`10k` between `6.8k` end resistors `R1, R2`) spans $\pm 14.78\text{ V} \times \frac{10\text{k}}{23.6\text{k}} = \pm 6.26\text{ V}$ (`±6.36 V` at `±15 V`), safely inside the fader track's $\pm 14.78\text{ V} \times \frac{10\text{k}}{19.4\text{k}} = \pm 7.62\text{ V}$ range.
  - **What protects `U1` from `±20 V` on `TARGET IN` (`J1`)?** The `R5 = 100 kΩ` / `R6 = 100 kΩ` input divider attenuates `±20 V` to `±10.0 V` at `U1`'s `+` input (within `[-14.8 V, +13.3 V]` when powered). If the board is unpowered ($V^+ = V^- = 0\text{ V}$), TI SNOS935B p. 2 Note 2 & p. 3 Note 5 specify that positive inputs up to `+32 V` cause no damage independent of $V^+$, and negative inputs below `-0.3 V` are clamped by the substrate collector-base diode rated to `50 mA`, with `R5 = 100 kΩ` limiting `-20 V` to `0.20 mA` (`250×` below the damage limit).
- **The `1 µF` polypropylene integrator capacitor (`C8`, `ECWF2W105JA`) and `LM321` input bias current:**
  - `LM321` has a PNP input stage whose bias current ($I_B = 45\text{ nA}$ typ, $250\text{ nA}$ max at 25 °C, $500\text{ nA}$ over temperature) flows **out** of `U5`'s `-` input (`pin 3`).
  - In steady state with `I IN` (`SW4 = 3`), `I`'s output stops ramping when the current through `R17 + RV4` equals $I_B$, which occurs at:
    $$V_{\text{ERROR, null}} = -I_B (R_{17} + R_{V4})$$
    At `RV4 = 1 MΩ` (`RC = 1 s`, fully clockwise), $V_{\text{ERROR, null}} = -45\text{ mV}$ typical (`-0.23 mm` of slider position) and **$-250\text{ mV}$ maximum at 25 °C** (`-1.29 mm` of slider position). As `I GAIN` is turned anticlockwise (`RV4 <= 200 kΩ`), this bias-induced offset drops below `9 mV` typ (`50 mV` max).
  - With `LOOP` closed and `I OFF` (`SW4 = 1`), `SW4` shorts `C8` so `U5` becomes a unity-gain follower (`V(I) = V(U5-) = 0 V`) and `I_B` is sunk directly by `U5`'s output; when `SW4` switches to `3` (`I IN`), `C8` starts cleanly from `0.000 V`.
- **PTC `F1` (`1812L035/30GR`) inside `U6`'s feedback loop, `SS34` clamps, and snubber:**
  - Putting `R18` (`10k` DC feedback) on `DRIVE` behind `F1` while keeping `C9` (`330 nF` HF feedback), `D3/D4` (`SS34`), and `R20 + C10` (`10 Ω + 100 nF`) ahead of `F1` means `F1`'s cold resistance (`0.2–1.7 Ω`) is divided by `U6`'s open-loop gain at DC, while at high frequencies (or when `F1` trips open!) `U6`'s feedback loop still closes locally through `C9` (`330 nF`).

### 4. The plant model and the simulation
- **Comparison against the Bourns `PSM01-082A-103B2` datasheet and bench measurements:**
  - `R_MOTOR = 14 Ω`, `I_BREAK = 0.18 A` (`2.52 V`), `I_COULOMB = 0.15 A` match Jason's bench measurements (`0.36 A` stalled at `5 V`, `2–3 V` breakaway, `0.16 A` running at `3 V`).
  - Taper `B2` (`datasheets/bourns_psm_slider_pot.pdf`, p. 2 chart) is flat over the first and last `~10 %` (`10 mm`) of the `100 mm` stroke and linear over the middle `80 mm`, which `sim/pid_sim.py` models via `MM_LINEAR = 80.0` and `V_STOP = V_END + 10.0 * V_PER_MM`.
  - As detailed in Finding 9.5, the Bourns datasheet (p. 1) specifies `Lever Speed @ 10 VDC: 20 mm/0.1 sec` (`200 mm/s`), whereas `sim/pid_sim.py`'s `SPEED_5V = 100 mm / 0.8 s` gives `340 mm/s` at `10 V`.
- **Does `U6`'s loop oscillate on its own, with and without the snubber, with a scope probe on `BASES`, or across PTC resistances?**
  Simulated in `design_reviews/2026-10-27_Gemini-4-Argon/sims/run_extra_sims.py` (test 2) across 18 combinations (`snubber` in/out × `R_PTC` = `0.2 Ω, 1.7 Ω, 10 kΩ` × `C_probe` on `BASES` = `0 pF, 15 pF, 120 pF` with a `10 ns` step):
  - **No sustained oscillation in any of the 18 cases.** With `R_PTC = 0.2 Ω` or `1.7 Ω`, `DRIVE` settles cleanly to `+0.997 V` / `+0.996 V` with zero tail ripple (`< 0.3 mV` after the crossover step), with or without the snubber and with up to `120 pF` (`1x` scope probe) on `BASES`.
  - When `F1` is tripped (`R_PTC = 10 kΩ`), `DRIVE` drops to `0 V` while `U6` saturates driving `LED3` (`RED`) through `R23 = 1k`, with no HF oscillation.
- **The `D` stage (`U4`) and other op-amps with a `10x` (`15 pF`) or `1x` (`120 pF`) scope probe on their probe loops:**
  Simulated in `sims/run_extra_sims.py` (test 3): adding `15 pF` (`10x` probe) or `120 pF` (`1x` probe) to `TP4` (`D`), `TP2` (`ERROR`), `TP3` (`P`), or `TP6` (`SUM`) changes `POSITION` overshoot (`+1.1126 V`) and `D` peak (`5.062 V`) by `< 0.01 %` with no ringing (`C7 = 470 pF` in `U4`'s feedback already dominates over `15–120 pF` load capacitance).
- **Integrator windup at an end stop and recovery time:**
  Simulated in `sims/run_extra_sims2.py` (test 4): when `TARGET` is held at `+10 V` (past the track's `+7.62 V` end) for `2.0 s` and then steps back to `+1.0 V`:
  - With `RV4 = 1 MΩ` (`RC = 1.0 s`), `V(I)` winds up to `-7.87 V` over `2 s`; after `TARGET` steps to `+1 V`, the slider leaves the end stop in **`0.36 s`** and settles to `+1.0 V` in **`5.46 s`**.
  - With `RV4 = 200 kΩ` (`RC = 0.20 s`), `V(I)` saturates at the negative rail (`-14.58 V`); after `TARGET` steps to `+1 V`, the slider leaves the end stop in **`0.40 s`** (and students can also flip `SW4` to `1 = OFF (reset)` to discharge `C8` in `< 1 ms`).
- **The `D` rule's settle time (`1500 ms` in `sim/results.json` for `P = 22 + D`):**
  Answered in Finding 10: `1500 ms` is **not** a stick-slip hunt; the slider moves monotonically without a peak (`0.52 %` dynamic overshoot) and comes to a dead stop at **`37.3 ms`**, sticking `6.6 %` (`66 mV`) past `1.000 V` inside the `±115 mV` friction dead band (which exceeds `step_metrics`'s `±5 %` band around `1.000 V`, causing `settle_s` to report `tstop - t0 = 1.5 s`).
- **Wiper dropouts (`sims/run_extra_sims2.py`, test 5):**
  When the slider is holding `+4.0 V` and the wiper (`POSITION`) lifts open-circuit for `10 ms`, zero current flows in `R7` (`100k`) and `R8` (`100k`), so `U1` acts as a unity follower of its `+` input (`TARGET / 2 = +2.00 V`). Both `V(POSITION)` and `V(ERROR)` jump to `+2.00 V`, `DRIVE` kicks to `+9.88 V` for `10 ms`, and the slider twitches forward by **`+1.39 mm`** (`P = 100 + D`) to **`+2.27 mm`** (`P = 5`), re-establishing wiper contact and returning to target.

### 5. Power, protection, and heat
- **Thermal model (`sim/thermal.py`):**
  `sim/thermal.py` solves the 2D finite-difference heat diffusion equation across the 2 oz (`70 µm`) top copper mask, `1.6 mm` FR4 ($k_z = 0.3\text{ W/(m·K)}, k_{xy} = 0.8\text{ W/(m·K)}$), and 2 oz bottom ground plane (including its routing cuts from `out/pcb_geom.json`) with $h_{\text{top}} = 10, h_{\text{bot}} = 6\text{ W/(m}^2\text{·K)}$ on a bench ($12, 8$ on standoffs). At `3.7 W` (`3.41 W` worst-case transistor dissipation at a `7 V` stall plus `0.25 W` in `R21`), it gives $T_J = 119.6\,^\circ\text{C}$ (`Q1`, `836 mm²` pour) and $121.9\,^\circ\text{C}$ (`Q2`, `670 mm²` pour) on a bench ($113.3\,^\circ\text{C}$ and $115.7\,^\circ\text{C}$ on standoffs), with pour mean temperatures of $84.7\,^\circ\text{C}$ and $88.1\,^\circ\text{C}$.
  What `sim/thermal.py` leaves out:
  1. `F1` (`1812L035`) self-heating (`0.13–0.43 W` at `0.5 A`, located `3.5 mm` below `Q2`'s pour).
  2. Transient heating during a `2.0 A`, `22.6 W` short of `DRIVE` to `GND`: in `1.0 s`, $\Delta T_{\text{J–tab}} = 22.6\text{ W} \times 2.8\,^\circ\text{C/W} = 63.3\,^\circ\text{C}$ and the tab/copper heat capacity (`~0.73 J/K` over a `10.6 mm` diffusion radius) rises `~31 °C`, so from a `25 °C` start $T_J(1\text{ s}) \approx 119\,^\circ\text{C} < 150\,^\circ\text{C}$ (survives a cold short, but a short immediately following a hot `110 °C` stall reaches $T_J \approx 204\,^\circ\text{C}$).
- **`MJB44H11` / `MJB45H11` $R_{\theta JC}$ and SOA (`datasheets/MJB44H11T4G_C233689.pdf`):**
  Page 1 specifies $R_{\theta JC} = 2.5\,^\circ\text{C/W}$ max ($P_D = 50\text{ W}$ at $T_C = 25\,^\circ\text{C}$). Figure 2 (p. 3, Forward Bias Safe Operating Area) shows no second-breakdown derating below $V_{CE} = 16\text{ V}$ (at $V_{CE} \le 15\text{ V}$, the DC limit is $3.3\text{ A}$ thermal and the $100\text{ ms}$ pulse limit is $10\text{ A}$), so both the `0.5–0.63 A` stall and the `2.0 A` short to `GND` ($V_{CE} \approx 11.3\text{ V}$) are well inside the SOA.
- **PTC (`1812L035/30GR`) hold/trip behavior:**
  Detailed in Finding 2: at `0.50 A` (`7 V` stall) and `0.634 A` (full-drive stall), current is below $I_{\text{trip}} = 0.70\text{ A}$ (`datasheets/1812L035_30GR_C18198328.pdf` p. 4 & p. 9 curve `F`), so it holds at `0.50 A` and takes `> 90 s` or holds at `0.634 A`; at `2.0 A` (short to `GND`), curve `F` trips in `~0.8–1.0 s`.
- **Effect of `~90 °C` pours on neighboring parts:**
  - `D3, D4` (`SS34`, pads inside the pours): at `90 °C` and `20 V` reverse bias, `SS34` reverse leakage rises to `~1–2 mA` (`datasheets/SS34_C8678.pdf` Fig. 2), which flows harmlessly into the low-impedance push-pull node (`< 45 mW`).
  - `U6` (`LM321`, surrounded on three sides by `Q1`/`Q2` pours): local board temperature reaches `~80–85 °C`, right at the `85 °C` top of `LM321`'s Operating Temperature Range (`datasheets/LM321MFX_NOPB_C9405.pdf` p. 2), though well below its `150 °C` maximum junction temperature.
  - `C11, C12` (`100 µF` 105 °C electrolytics) and `RV2–RV4` (`3362P`, 125 °C cermet) are `> 10 mm` from the pours (`< 55 °C`).
- **`DRIVE` or `MOTOR` shorted to a rail (`±15 V`):**
  If `DRIVE` is shorted to `-15 V` while `U6` commands positive drive, `Q1` sees $V_{CE} \approx 27\text{ V}$ at $I_C \approx 2.2\text{ A}$ (`~60 W`, exceeding `T_J = 150 °C` in `< 0.2 s` before `F1` trips), and when `F1` does trip, `F1` sees `29.6 V` right at its `30 Vdc` `V_max` limit. The warning on the back silkscreen (*"Never short MOTOR or DRIVE to a rail"*) is essential.
- **Is `"HOT if the motor stalls"` enough?**
  At `85–88 °C` mean (`110 °C` at the D2PAK tab), the copper pour exceeds the `~60 °C` human burn threshold for bare skin contact after a couple of minutes of stall. Having `"HOT if the motor stalls"` printed directly on both pours plus the warning on the back silkscreen and in the handbook is appropriate for a university teaching lab, especially if `F1` is stepped down to `1812L020` or `1812L030` (Finding 2) so full-drive stalls actually trip in seconds.

### 6. The silkscreen as a schematic
- **Junction dots and hops:**
  Every 3-way front-copper junction in open board space has a `r = 0.5 mm` filled dot except the `/POSITION` back-wire T-junction at `(46.0, 105.0)` and the two pot-end junctions at `(129.0, 109.4)` and `(119.0, 109.4)` suppressed by `_on_pad` (Finding 7.3). The single hop (`BASES` crossing under `Q2`'s emitter wire at `(151.45, 66.2)`) is clearly drawn as a semicircular jump arc.
- **Transistor symbols (`Q1` NPN, `Q2` PNP):**
  Both symbols place `B`, `C`, and `E` on the right pads (`1 = B` on the left for `Q1` at `rot = 90°` and on the right for `Q2` at `rot = 270°`; `2 = C` on the tab; `3 = E` on the other lead), with the collector leg ending at the tab, the emitter arrow pointing outward on the emitter leg for `Q1` (NPN) and inward against the base bar on the emitter leg for `Q2` (PNP), and `Q1 MJB44H11` / `Q2 MJB45H11` printed inside each pour.
- **Labels, switch legends, box names, arcs, and back manual:**
  All five switches have `"1"` and `"3"` printed at their ends matching the `"1 = ... / 3 = ..."` legends on the front, on the back, and in `HANDBOOK.md`. The two silkscreen issues found—`"-15 V"` overlapping `"THE FADER'S TRACK"` at `(120.6, 102.3)` and the unclipped `/POSITION` dashed line crossing `C8` and 6 front wires—are fixed in `patch_fixes.diff` (Finding 7).

### 7. Copper and board
- **Motor current path:**
  - `+15V`: `J6` pin 1 $\to$ `0.6 mm` track $\to$ `D1` (`SS34`) $\to$ `0.6 mm` track along `y = 14.0` and down `x = 143.0` into `Q1`'s `836 mm²` 2 oz pour.
  - `-15V`: `J6` pin 3 $\to$ `0.6 mm` track $\to$ `D2` (`SS34`) $\to$ `0.6 mm` track to 3 parallel vias (`0.3 mm` drill) at `(163.5..165.5, 12.5)` $\to$ `0.6 mm` `B.Cu` track down the right edge (`x = 168.8`) $\to$ 3 parallel vias at `(166.0, 73.0..75.0)` into `Q2`'s `670 mm²` 2 oz pour (all 3 vias verified inside `Q2`'s filled polygon by `check_pcb_copper.py`).
  - Emitters & `DRIVE`: `Q1`/`Q2` emitter pads $\to$ `R21`/`R22` (`0.6 mm` outside circle; `0.35 mm` inside circle unless `wide={nE}` is applied per Finding 11) $\to$ `0.6 mm` `PP_NET` down `x = 167.0` to `F1` $\to$ `0.6 mm` `/DRIVE` to `J4` pin 1.
  - Ground return: `J4` pin 2 (`GND`) and `J6` pin 2 (`GND`) connect directly to the 2 oz `B.Cu` ground plane via 4-spoke thermal reliefs (`4 × 0.5 mm = 2.0 mm` total spoke width) plus a `0.3 mm` via each.
  - At `0.63 A` continuous (`2.0 A` for `1 s`), a `0.6 mm` track in 2 oz (`70 µm`) outer copper has cross-section $0.042\text{ mm}^2$ (`~2.8 mΩ` per cm) and per IPC-2152 carries `2.5 A` for a `10 °C` rise (`4.2 A` for `30 °C`), so all motor-current traces have ample ampacity.
- **Ground plane integrity under pours:**
  No `B.Cu` track crosses under `Q1` or `Q2`'s pours; the ground plane is continuous underneath both pours and reaches all 73 ground/signal vias cleanly (`0` unconnected items in DRC).
- **Clearances to M3 holes (`MH1–MH4`), BNC flanges, and fiducials:**
  `check_pcb_copper.py` confirmed zero tracks or vias within `3.2 mm` of any M3 mounting hole center (ample room for M3 standoffs/screw heads). Three fiducials (`1 mm` bare copper dot, `2 mm` solder-mask opening) sit at `(12, 10)`, `(12, 110)`, `(158, 112)` with `>= 4 mm` edge clearance.
- **Custom and standard footprints against datasheets:**
  - `BNC_KYWE_RightAngle` (`C41416668`), `SW_SPDT_Shouhan_MSK12C02` (`C431540`), `Potentiometer_Bourns_3362P_Vertical` (`C118945`), `TerminalBlock_KF301_1x03_P5.00mm` (`C474882`), `C_Film_Panasonic_ECWF_L18.1mm_W9.3mm_P15.00mm` (`C242107`), and `TestPoint_Loop_RH-5019` (`C5199800`) all match their manufacturer drawings and EasyEDA land patterns (`<= 0.05 mm` pad tolerance).
  - `Package_TO_SOT_SMD:TO-263-2` (`Q1, Q2`) matches onsemi's `MJB44H11/D` (Case 418B-04, p. 5) recommended soldering footprint (`10.8 × 9.4 mm` tab vs `10.49 × 8.38 mm`; `4.6 × 1.1 mm` leads on `5.08 mm` pitch vs `3.50 × 1.02 mm` on `5.08 mm` pitch).
  - `Package_TO_SOT_SMD:SOT-23-5` (`U1–U7`) matches TI's `LM321MFX/NOPB` (DBV0005A) pinout (`1 = +IN, 2 = V-, 3 = -IN, 4 = OUT, 5 = V+`).

### 8. The JLCPCB package
- **CPL rotations and datum shifts (`scripts/parts.py JLC_ROTATION`):**
  Every BOM code on the board was tested mathematically by transforming EasyEDA's pad coordinates by the upload CPL's `(Mid X, Mid Y, Rotation)` and comparing against the PCB pad coordinates:
  - **`RV1` (`C351173`) is wrong (`(90, (2.5, -3.5))` instead of `(270, (3.5, -2.5))`)** — see Finding 1.
  - All other 15 distinct polarized/asymmetric codes (`C233689` `Q1`, `C154570` `Q2`, `C9405` `U1–U7`, `C431540` `SW1–SW5`, `C118945` `RV2–RV4`, `C41416668` `J1–J3`, `C474882` `J4–J6`, `C242107` `C8`, `C46550402` `C11–C12`, `C8678` `D1–D4`, `C2297` `LED1–LED2`, `C84256` `LED3–LED4`, `C18198328` `F1`, `C3000711` `R21–R22`, `C5199800` `TP*`) align to within `0.00–0.20 mm` with correct pin-1 / cathode / tab orientation.
- **Economic vs. Standard PCBA and cost model (`scripts/gen_docs.py`):**
  All parts are on the top side, and JLCPCB fits THT parts on single-side orders (`$3.58` THT setup + `$0.03`/joint). Note that on JLCPCB's order page, selecting **2 oz outer copper** sometimes forces the assembly tier from *Economic PCBA* (`$8` setup) to *Standard PCBA* (`$25–$40` setup); the per-board parts cost (`$12.12`), extended part count (`13` codes × `$3.00` = `$39.00`), and joint counts (`197` SMT, `29` THT) in `scripts/gen_docs.py` are exact.

### 9. The documents as a lab handout
- Checked across `README.md`, `docs/HANDBOOK.md`, `docs/DESIGN_NOTES.md`, `docs/MANUFACTURING.md`, schematic notes, and back silkscreen.
- See Findings 5, 8, and 9 for the specific mismatches found (`SW1` toggle omitted in "Measure your gains", `P = 10` residual error sign/meaning, `"not 411"` reason in `DESIGN_NOTES.md`, stale schematic numbers `10 ms` / `10 s` / `±0.5 V` / `10 mA`, `234k` vs `231k`, `RK09K` datasheet availability, and probe-loop fuse claims).
- **What is missing from `docs/DESIGN_NOTES.md` "Not yet proven":**
  1. Single-rail power-up reverse-biasing `C11` or `C12` (`-10.2 V` / `+6.5 V`, Finding 3).
  2. Supply-diode voltage-drop asymmetry coupling motor current into `POSITION` (`~60–120 mV` shift when `TARGET` is driven from `J1`, Finding 4).
  3. Whether `F1` (`1812L035/30GR`, $I_{\text{trip}} = 0.70\text{ A}$) ever trips on a `0.63 A` full-drive stall as the motor winding warms (Finding 2).

### 10. What a student will do to it (abuse analysis)
| Abuse scenario | What happens | Damages board or fader? | Prevention / mitigation |
|---|---|---|---|
| **Supply reversed (`+15 V` $\leftrightarrow$ `-15 V`)** | `D1` and `D2` (`SS34`, 40 V rated) are reverse-biased at `15 V`; leakage `< 50 µA` is shunted by `R1–R4` and bypass caps (`< 0.1 V` on rails). | **No.** | Covered by `D1, D2`. |
| **One rail only (`+15 V` on, `-15 V` open; or vice versa)** | Cross-rail current through `U1–U7`, `RV1`, `POT`, and `Q1`/`Q2` pulls floating `-15V` to `+6.5 V` or floating `+15V` to `-10.2 V`, reverse-biasing 100 µF electrolytic `C12` or `C11`. | **Yes (`C11` or `C12` can vent/short if left on single rail).** | Finding 3: switch both rails together; add antiparallel Schottkys across `C11, C12` in rev B. |
| **`20 V` peak (`±20 V`) generator into `TARGET IN` (`J1`)** | `R5`/`R6` (`100k`/`100k`) divides to `±10 V` at `U1+` (inside `[-14.8 V, +13.3 V]` when powered; limited to `0.2 mA << 50 mA` when unpowered). | **No.** | Covered by `R5, R6 = 100k`. |
| **Scope ground clip on a probe loop (`TP1–TP13`)** | On `TP7` (`DRIVE`): `2.0 A` for `~1 s` until `F1` trips. On `TP9`/`TP10` (`±15V`): unfused short of bench supply through `D1`/`D2`! On `TP2–TP6, TP12, TP13` (`LM321` outputs): `40 mA × 14.8 V = 0.59 W` in SOT-23-5 (`TJ ≈ 182 °C`, exceeds continuous rating on `±15 V`). | **Yes, if clipped to `TP9`/`TP10` (high-current supply) or left on an `LM321` output loop.** | Finding 5: correct docs to warn against clipping ground to rail or signal loops. |
| **Scope ground clip on `R21` or `R22` (ahead of `F1`)** | Direct short of `Q1`/`Q2` emitter to `GND` ahead of `F1`: `2.0–2.3 A` (`23–28 W` in `Q1`/`Q2`, `4–5 W` in `R21`) continuously without tripping `F1`. | **Yes (`Q1`/`Q2` thermal failure in `~3–5 s`).** | Handbook warns to use two probes (`A - B`) and never a ground clip on `R21`/`R22`. |
| **`DRIVE` or `MOTOR` shorted to `GND`** | `2.01 A`, `22.6 W` in `Q1`, `4.0 W` in `R21` for `~0.8–1.0 s` until `F1` trips (`TJ` rises from `25 °C` to `~119 °C`). | **Survives a cold short; repeated rapid shorts can overheat `Q1`.** | Covered by `F1` + `R19` base resistance limiting $I_{\text{short}}$ to `2 A`. |
| **`DRIVE` or `MOTOR` shorted to `+15 V` or `-15 V` rail** | Up to `29.6 V` across `Q1`/`Q2` (`~60 W`, exceeds SOA in `< 0.2 s`) and `29.6 V` across `F1` (`30 V` max rating). | **Yes (destroys `Q1`/`Q2`).** | Back silkscreen and handbook explicitly warn never to short `MOTOR` or `DRIVE` to a rail. |
| **Motor wires swapped** | Positive feedback drives slider to an end stop and stalls at `8.88 V, 0.634 A` (`2.99 W` in `Q1`/`Q2`, `5.63 W` in motor). | **Board survives (`TJ <= 122 °C`); fader motor gets hot if `1812L035` does not trip (Finding 2).** | Bring-up procedure checks polarity at low P gain first; step `F1` down to `1812L020`/`030`. |
| **`LOOP` left open with `TARGET` at a few volts all session** | Slider stalls at end stop; at `7 V` drive (`0.50 A`), `F1` (`0.35 A` hold / `0.70 A` trip) holds indefinitely, putting `3.41 W` in `Q1` (`TJ ≈ 120 °C` on bench, pour `~88 °C`). | **Board survives; pour is `~88 °C` (hot to touch).** | `MJB44H11`/`45H11` D2PAKs on 2 oz pours + `"HOT if the motor stalls"` silkscreen + standoffs. |
| **Fader unplugged or replugged with power on** | Unplugging `J5` leaves `POSITION` floating (follows `TARGET/2` via `R7, R8`); motor inductive kick on `J4` is clamped at the transistors by `D3, D4` (`SS34`). | **No.** | Covered by `D3, D4` and `100k` input resistors. |
| **Different fader (SparkFun / TOP-UP / ALPS)** | Any `10k` linear track and `6–11 V` DC motor (`10–25 Ω` winding) works; `SW5` (`22 nF / 100 nF`) and `1 MΩ` trimmers cover both fast slide pots and slow geared rotary pots. | **No.** | Covered by screw terminals `J4, J5` and `SW5`. |
| **Every trimmer at an end (`0 Ω` or `1 MΩ`)** | `R14 = 10k`, `R15 = 1k`, `R17 = 1k` fixed series resistors prevent zero-ohm shorting on `P` (`gain >= 1`), `D` (`R_in >= 1k`), and `I` (`RC >= 1 ms`); wiper-to-3 tie prevents open-circuit if wiper lifts. | **No.** | Covered by `R14, R15, R17` and rheostat wiring. |
| **Slide switch half-way (open common)** | `SW1` open: `R5+R6` (`200k`) pulls `U1+` to `0 V`. `SW2` open: `U1` becomes unity follower of `TARGET/2`. `SW3`/`SW4` open: `D`/`I` disconnected from sum; `U5` integrates to rail harmlessly. `SW5` open: `D` input open (`D = 0 V`). | **No.** | All open-pole states are benign. |

---

## 4. What Was Checked and Found Right

1. **Netlist & Schematic Parity (252 assertions + ERC + DRC):**
   - `out/motorpid.net` matches *Learning the Art of Electronics* Figs. 10L.1, 10L.3, 10L.6, 10L.9, and 10L.10 across all seven op-amp stages, all five switches, all three trimmers, the knob, the push-pull driver, the fuse, and the connectors.
   - KiCad 10 ERC reports `0` violations; KiCad 10 DRC with `--severity-all --schematic-parity` reports `0` violations (`0` unconnected pads, `0` clearance/track/via/hole/silk violations on `0.21 mm` 2 oz rules).
2. **Trimmer & Switch Sense:**
   - All three `3362P` trimmers (`RV2, RV3, RV4`) have terminal `1` as one end, terminal `2` (wiper) tied to terminal `3` (the CW end per BOCHEN/Bourns `3362P` datasheet p. 4), so turning clockwise always increases resistance (`↑R ↑P`, `↑R ↑D`, `↑R ↓I`).
   - Shouhan `MSK12C02` datasheet (`datasheets/MSK12C02_C431540.pdf` p. 5 cross-section) confirms the actuator connects the common terminal (`2`) to the end terminal (`1` or `3`) on the side toward which the handle is slid.
   - ALPS `RK09K1130A70` datasheet (`datasheets/RK09K1130A70_C351173.pdf` p. 4 Drawing No. 6 & p. 7 Circuit Diagram) confirms terminal `1` is full CCW (`-15 V` via `R2`), terminal `3` is full CW (`+15 V` via `R1`), taper `1B` is linear, and the shaft has a center detent (`0 V`).
3. **Footprints & 3D Models:**
   - All 6 custom footprints (`BNC_KYWE_RightAngle`, `SW_SPDT_Shouhan_MSK12C02`, `Potentiometer_Bourns_3362P_Vertical`, `TerminalBlock_KF301_1x03_P5.00mm`, `C_Film_Panasonic_ECWF_L18.1mm_W9.3mm_P15.00mm`, `TestPoint_Loop_RH-5019`) and all standard KiCad footprints (`SOT-23-5`, `TO-263-2`, `CP_Elec_6.3x5.4`, `D_SMA`, `LED_0805`, `Fuse_1812`, `R_0805`, `R_1206`, `R_2512`, `C_0805`, `Potentiometer_Alps_RK09K_Single_Vertical`) match their datasheet dimensions and EasyEDA land patterns.
   - All 87 3D model references resolve on disk; `RV1–RV4` through-hole patterns are rotationally asymmetric (keyed).
4. **QR Code & Fab Package:**
   - The `B.Silkscreen` QR code at `(133.0, 83.0)` decodes cleanly (Reed-Solomon + BCH verified) to `https://github.com/gallicchio/motor-pid` when viewed from the back, with no vias or through-holes underneath it.
   - Gerber extent (`170.00 × 120.00 mm`), layer set (9 layers + 2 drill files + map files), BOM (`48` lines, `108` placed parts), and all 15 CPL entries other than `C351173` (`RV1`) are verified.

---

## 5. What Could Not Be Checked

1. **Live JLCPCB "Confirm Parts Placement" 3D viewer render:** Cannot upload to JLCPCB's order cart from this environment without placing a draft order; instead, every LCSC code's EasyEDA SVG land pattern (`scripts/easyeda.py`) was mathematically transformed by the upload CPL's `(Mid X, Mid Y, Rotation)` and compared pad-by-pad against `out/pcb_geom.json` (which caught Finding 1 on `RV1` `C351173`).
2. **Physical fader traverse speed at 10 V vs. 5 V and servo-track (`1'-2'-3'`) resistance:** Requires bench measurement on the physical Bourns `PSM01-082A-103B2` unit (the datasheet specifies `200 mm/s` at `10 V` and does not state whether the `1'-2'-3'` servo track is also `10 kΩ`).
3. **Empirical thermocouple measurement of the 2 oz D2PAK pours and `1812L035` trip time at `0.63 A`:** Requires the first assembled board on the bench.

---

## 6. Publishing

- Checked all git-tracked files (`git ls-files`) for `/home/`, `/Users/`, API keys, tokens, personal emails, and copyrighted documents: **none found**.
- `.gitignore` properly excludes `/datasheets/`, `/datasheets_not_in_git/`, `/scripts/jlc_cache.json`, `/scripts/easyeda_cache.json`, and `/design_reviews/*/project/`.
- Any temporary datasheet text/image extractions used during this review were kept inside `design_reviews/2026-10-27_Gemini-4-Argon/project/notes/` (which is gitignored under `/design_reviews/*/project/`) so no copyrighted material is left in the tracked review directory.

---

## 7. Patches and Verification Files in This Directory

- [`patch_fixes.diff`](./patch_fixes.diff) — `diff -ru` patch against the repository root fixing Findings 1, 5, 6, 7, 8, 9, and 11 across `make.py`, `scripts/kienv.py`, `scripts/parts.py`, `scripts/gen_sch.py`, `scripts/check_circuit.py`, `scripts/layout.py`, `scripts/gen_pcb.py`, `scripts/check_outputs.py`, `scripts/gen_docs.py`, `docs/HANDBOOK.md`, and `docs/DESIGN_NOTES.md`. Verified end-to-end with `./make.py` in `project/` (ERC `0`, 252 circuit checks, schematic overlap check `0`, DRC `0` with schematic parity, thermal check `120 / 122 °C`, all fab checks passed, `30/30` document claims matched).
- [`check_sch_deep.py`](./check_sch_deep.py) — Checks all schematic text items (including `#PWR` values and title-block widths) against other text items, wires, and box outlines.
- [`check_pcb_deep.py`](./check_pcb_deep.py), [`check_pcb_shapes.py`](./check_pcb_shapes.py), [`check_pcb_junctions.py`](./check_pcb_junctions.py), [`check_pcb_copper.py`](./check_pcb_copper.py) — `pcbnew`-based scripts verifying front/back silkscreen bounding-box overlaps, `/POSITION` dashed-line crossings, 3-way junction dots, stage-box edge clearances, pour via hits, and M3 mounting-hole clearances.
- [`check_sim_details.py`](./check_sim_details.py) & [`sims/run_extra_sims.py`](./sims/run_extra_sims.py), [`sims/run_extra_sims2.py`](./sims/run_extra_sims2.py) — `ngspice` simulations of the `.op` rail-sag latch, `P=22 + D` true settling time, `U6` driver stability across 18 snubber/PTC/probe cases, scope probe loading on `D`/`ERROR`/`P`/`SUM`, integrator end-stop windup, `10 ms` wiper dropout, and single-rail power-up reverse bias on `C11`/`C12`.

