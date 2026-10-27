#!/usr/bin/env python3
"""Write the ordering documents, then check the hand-written ones.

Generated, from the parts table, the costed BOM, the board geometry and the
simulation results, so none of their numbers can drift from the files in out/:

    docs/MANUFACTURING.md                 what to upload, what to pick, what it costs
    out/opamp/opamp-fabrication-notes.txt JLCPCB's order form, field by field
    out/opamp/PLACEMENT_CHECKS.txt        what to look at in JLCPCB's preview

Checked: every number README.md, docs/HANDBOOK.md and docs/DESIGN_NOTES.md
quote from the build is matched against the build (CLAIMS below), and the
build fails when a sentence no longer says what the files say.
"""
import csv, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts, layout

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "out")
DOCS = os.path.join(ROOT, "docs")
STEM = "motorpid"

# JLCPCB list prices, autumn 2026.  These move; the fab's quote is the
# authority and the build prints these only as an order of magnitude.
# 2 oz copper (the push-pull's heatsink): JLCPCB does not publish its price;
# a third-party guide says 20-50 % more for the bare boards; the high end here
COPPER_2OZ = 1.5
PCB_2L_5PCS = 14.00 * COPPER_2OZ      # 170 x 120 mm, 2 layers, 5 pieces, green, HASL (past the 100 x 100 discount)
PCB_2L_10PCS = 24.00 * COPPER_2OZ
SHIPPING = 22.00             # DHL to the US; the slow post is about $8
PCBA_SETUP = 8.00
STENCIL = 1.50
PER_JOINT = 0.0017
EXTENDED_PART_FEE = 3.00     # per distinct Extended code, not per placement
THT_SETUP = 3.58             # per order, once any through-hole part is fitted
THT_PER_JOINT = 0.03         # JLCPCB's rate for THT joints, per joint


def joint_counts():
    """Solder joints only: a mounting hole is not a joint."""
    geom = json.load(open(os.path.join(OUT, "pcb_geom.json")))
    real = [p for p in geom["pads"] if p["net"] and not p["ref"].startswith("MH")]
    smt = sum(1 for p in real if not p["through"])
    tht = sum(1 for p in real if p["through"])
    tht_refs = sorted({p["ref"] for p in real if p["through"]},
                      key=lambda r: (r[0], int(re.sub(r"\D", "", r) or 0)))
    loops = len({p["ref"] for p in real if p["ref"].startswith("TP")})
    return smt, tht, tht_refs, loops, geom


def via_sizes():
    pcb = open(os.path.join(ROOT, "hardware", STEM + ".kicad_pcb")).read()
    vias = re.findall(r"\(via\s+\(at [^)]*\)\s+\(size ([0-9.]+)\)\s+\(drill ([0-9.]+)\)", pcb)
    if not vias:
        return None, None, 0
    return (min(float(s) for s, d in vias), min(float(d) for s, d in vias), len(vias))


def bom_rows():
    return list(csv.DictReader(open(os.path.join(OUT, STEM, f"{STEM}_bom_costed.csv"))))


def money(x):
    return f"${x:,.2f}"


def circuit_check_count():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_circuit.py"),
                          os.path.join(OUT, STEM + ".net")], capture_output=True, text=True).stdout
    m = re.search(r"(\d+) circuit checks passed", out)
    return int(m.group(1)) if m else 0


# ------------------------------------------------------------ the order form
def order_form(w, h, min_drill, min_via, tht_refs):
    """JLCPCB's order form, field by field in the order the web form shows them."""
    via_opt = "0.3 mm / (0.4 / 0.45 mm)" if min_drill >= 0.3 else "0.25 mm / (0.35 / 0.4 mm)"
    return [
        ("PCB", None, None),
        ("Base Material", "FR-4", "the default"),
        ("Layers", "2", "what the gerber set contains"),
        ("Dimensions", f"{w:.0f} x {h:.0f} mm", "read from the board outline; past the 100 x 100 mm discount, so the bare boards cost a little more"),
        ("PCB Qty", "5", f"the minimum; 10 costs about ${PCB_2L_10PCS - PCB_2L_5PCS:.0f} more"),
        ("Product Type", "Industrial/Consumer electronics", "the default"),
        ("PCB Specifications", None, None),
        ("Different Design", "1", "one board in the outline"),
        ("Delivery Format", "Single PCB", "no panel"),
        ("PCB Thickness", "1.6 mm", "the BNC flanges, the knob and the terminal blocks expect it"),
        ("PCB Color", "Green", "any; the white silkscreen reads best on green or black"),
        ("Silkscreen", "White", "the default for green"),
        ("Material Type", "FR4-Standard TG 135-140", "the default; the worst stall holds the board round a transistor near 110 C, below the TG"),
        ("Surface Finish", "LeadFree HASL", "students handle this board: lead-free.  ENIG is fine too"),
        ("High-spec Options", None, None),
        ("Outer Copper Weight", "2 oz", "NOT the default: the copper round Q1 and Q2 is their heatsink (DESIGN_NOTES, \"A stall at a few volts\"); the 0.21 mm rules assume it"),
        ("Via Covering", "Tented", "or Plugged if the form upgrades it: either is fine, no via must stay open"),
        ("Min via hole size/diameter", via_opt,
         f"the smallest via on the board is {min_drill:.2f} mm drill, {min_via:.2f} mm pad"),
        ("Board Outline Tolerance", "+/-0.2 mm (Regular)", "nothing mates with the edge"),
        ("Confirm Production file", "No", "the gerbers are checked here"),
        ("Mark on PCB", "Remove Mark", "the whole front is a drawing; nowhere for an order number"),
        ("Electrical Test", "Flying Probe Fully Test", "the default"),
        ("Gold Fingers", "No", ""),
        ("Castellated Holes", "No", ""),
        ("Edge Plating", "No", ""),
        ("PCB Assembly", None, None),
        ("PCBA Type", "Economic", "all parts on one side, nothing fine-pitch"),
        ("Assembly Side", "Top", "every part is on the front"),
        ("PCBA Qty", "2, or as many as the class needs", "the per-order fees are the same for 2 or 20"),
        ("Edge Rails/Fiducials", "Added by JLCPCB", "the board carries three fiducials; rails do no harm, removed before delivery"),
        ("Confirm Parts Placement", "Yes", "look at the preview against PLACEMENT_CHECKS.txt before paying"),
        ("Parts Selection", "By JLCPCB", "every BOM line has an LCSC code"),
        ("Through-hole parts", f"keep them: {', '.join(tht_refs)}",
         "the form lists them separately; the BNCs, terminals, knob and trimmers are meant to be fitted"),
        ("Bake Components", "No", "nothing moisture-sensitive"),
        ("Stencil", "none", "JLCPCB keeps its own; nothing to order"),
    ]


def main():
    rows = bom_rows()
    smt, tht, tht_refs, loops, geom = joint_counts()
    min_via, min_drill, n_vias = via_sizes()
    R = json.load(open(os.path.join(ROOT, "sim", "results.json")))
    parts_cost = sum(float(r["Ext $"]) for r in rows)
    ext_codes = sorted({r["LCSC Part #"] for r in rows if r["JLC"] == "extended"})
    basic = [r for r in rows if r["JLC"] != "extended"]
    ext_fee = EXTENDED_PART_FEE * len(ext_codes)
    w, h = geom["board_w"], geom["board_h"]
    ref_lcsc = {}
    for r in rows:
        for ref in r["Designator"].split(","):
            ref_lcsc[ref.strip()] = r["LCSC Part #"].strip()

    def quote(qty, pcb_cost):
        parts_total = parts_cost * qty
        assembly = (PCBA_SETUP + STENCIL + ext_fee + THT_SETUP
                    + PER_JOINT * smt * qty + THT_PER_JOINT * tht * qty)
        return pcb_cost, parts_total, assembly, SHIPPING, pcb_cost + parts_total + assembly + SHIPPING

    form = order_form(w, h, min_drill, min_via, tht_refs)

    # ---------------------------------------------------------------- MANUFACTURING.md
    L = []
    a = L.append
    a("# Manufacturing")
    a("")
    a(f"One board, two layers, {w:.0f} x {h:.0f} mm, every part on the top side, a solid")
    a("ground plane on the back.  It passes ERC, DRC with schematic parity, the")
    a(f"{circuit_check_count()} circuit assertions and the fab-package checks with zero violations,")
    a("and `./make.py` rebuilds and rechecks everything from scratch in about a minute.")
    a("")
    a("## What to upload")
    a("")
    a("| file | where it goes |")
    a("|---|---|")
    a(f"| `out/{STEM}/{STEM}-gerbers.zip` | the *Add gerber file* box |")
    a(f"| `out/{STEM}/{STEM}_bom_jlcpcb_upload.csv` | the BOM box (JLCPCB's column layout) |")
    a(f"| **`out/{STEM}/{STEM}_cpl_jlcpcb_upload.csv`** | the CPL / pick-and-place box, at JLCPCB |")
    a(f"| `out/{STEM}/{STEM}_cpl_kicad_native.csv` | the CPL box at any other fab |")
    a(f"| `out/{STEM}/{STEM}-assembly-notes.txt` | paste into the assembly remark |")
    a("")
    a("## The order form, field by field")
    a("")
    a(f"The same list is in `out/{STEM}/{STEM}-fabrication-notes.txt` to keep open while")
    a("ordering.  The values that come from the board are computed, not typed.")
    a("")
    a("| field | pick | why |")
    a("|---|---|---|")
    for field, value, why in form:
        if value is None:
            a(f"| **{field}** | | |")
        else:
            a(f"| {field} | {value} | {why} |")
    a("")
    a("## Cost")
    a("")
    a(f"The board has **{smt} SMT joints** and **{tht} through-hole joints** on")
    a(f"{len(rows)} BOM lines; {len(ext_codes)} distinct order codes are JLCPCB *Extended* parts")
    a(f"(the op-amps, the BNCs, the terminal blocks, the knob, the trimmers, the slide")
    a(f"switches, the test loops, the power transistors, the fuse and the 1 ohm resistors),")
    a(f"each with a one-off {money(EXTENDED_PART_FEE)} feeder fee.  Parts alone are")
    a(f"**{money(parts_cost)} per board**, of which the three BNC jacks are")
    a(f"{money(3 * parts.PARTS['BNC']['price'])} and the {loops} test loops {money(loops * parts.PARTS['TP']['price'])}.")
    a("")
    for qty, pcb in ((2, PCB_2L_5PCS), (5, PCB_2L_5PCS), (10, PCB_2L_10PCS), (20, PCB_2L_10PCS * 1.8)):
        p, pr, asm, ship, tot = quote(qty, pcb)
        a(f"**{qty} boards, fully assembled, through-hole parts included**")
        a("")
        a("| line | cost |")
        a("|---|---|")
        a(f"| bare PCBs ({max(qty, 5)} made) | {money(p)} |")
        a(f"| parts ({money(parts_cost)} x {qty}) | {money(pr)} |")
        a(f"| assembly: setup {money(PCBA_SETUP)} + stencil {money(STENCIL)} + THT setup {money(THT_SETUP)} "
          f"+ {len(ext_codes)} extended codes + {smt * qty} SMT and {tht * qty} THT joints | {money(asm)} |")
        a(f"| shipping (DHL) | {money(ship)} |")
        a(f"| **total** | **{money(tot)}**  ({money(tot / qty)} each) |")
        a("")
    a("The fixed fees dominate a small order: a second board costs about")
    p2 = quote(2, PCB_2L_5PCS)[4]
    p1 = quote(1, PCB_2L_5PCS)[4]
    a(f"{money(p2 - p1)} more than the first, so order one per bench, not one per class.")
    a("")
    a("## Rotations JLCPCB needs")
    a("")
    a("JLCPCB places from its own drawing of each part, and for some parts that")
    a("drawing is turned from KiCad's footprint, so a placement file that is right")
    a("everywhere else is wrong there by a fixed angle.  The upload CPL has these")
    a("angles already applied, per LCSC code, from `scripts/parts.py`:")
    a("")
    a("| parts | LCSC | turned by | datum shift | evidence |")
    a("|---|---|---|---|---|")
    for code, (deg, (dx, dy), how, note) in sorted(parts.JLC_ROTATION.items(), key=lambda kv: (-kv[1][0], kv[0])):
        refs = sorted((r for r, c in ref_lcsc.items() if c == code),
                      key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
        if not refs:
            continue
        shift = f"({dx:+.1f}, {dy:+.1f}) mm" if (dx or dy) else "none"
        a(f"| {', '.join(refs)} | {code} | {deg} deg | {shift} | {how}: {note} |")
    a("")
    a("*read* means seen in a JLCPCB preview on a real order of that part on that")
    a("footprint; *predicted* means derived by fitting JLCPCB's own land pattern")
    a("onto ours by pin number (`scripts/easyeda.py <code>`).  Every predicted part is")
    a(f"in `out/{STEM}/PLACEMENT_CHECKS.txt`, the list to hold against the preview.")
    a("`check_outputs.py` proves the two CPL files differ in nothing but those angles.")
    a("")
    a("## Check these in the preview before you pay")
    a("")
    a("| part | what to look for | should be |")
    a("|---|---|---|")
    for line in PREVIEW_CHECKS:
        a(f"| {line[0]} | {line[1]} | {line[2]} |")
    a("")
    a("The parts that cannot go in wrong are the knob and the three trimmers: their")
    a("hole patterns fit one way.  `check_outputs.py` re-derives that from the board")
    a("file on every build.  The BNCs are not keyed (four symmetric posts and a centre")
    a("pin), which is why their correction is read, not predicted, and worth a glance.")
    a("")
    a("## The through-hole parts")
    a("")
    a(f"{len(tht_refs)} parts are through-hole: **{', '.join(tht_refs)}**, the three BNC")
    a("jacks, the three terminal blocks, the knob and the three trimmers.  They are in the BOM and the")
    a("CPL and JLCPCB fits them for a per-order fee plus pennies a joint; keep them")
    a("selected when the form lists them.  If you would rather solder them yourself")
    a(f"they are the {tht} largest, easiest joints on the board.  Everything else is 0805,")
    a("1206, 2512, SMA or SOT-23-5 and is hand-workable with a fine iron; the two")
    a("D2PAKs' tabs sit in 2 oz pours and need hot air or a large iron to move.")
    a("")
    a("## Parts, stock and alternates")
    a("")
    a(f"Stock as JLCPCB's parts API reported it on {parts.STOCK_DATE}; the build re-reads")
    a("every code's description against the value and package here and stops if")
    a("one has changed.  JLCPCB's assembly stock is what counts and their BOM")
    a("upload shows it per line.")
    a("")
    a("| ref | value | LCSC | JLC | unit | stock then | notes |")
    a("|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (re.sub(r"\d", "", r["Designator"].split(",")[0]),
                                         int(re.sub(r"\D", "", r["Designator"].split(",")[0]) or 0))):
        key = next((k for k, p in parts.PARTS.items() if p.get("lcsc") == r["LCSC Part #"]), None)
        p = parts.PARTS.get(key, {})
        if p:
            stock, note = p.get("stock", ""), p.get("desc", "")
        else:
            pv = next((v for v in parts.PASSIVES.values() if v["lcsc"] == r["LCSC Part #"]), {})
            stock, note = pv.get("stock", ""), pv.get("note", "")
        stock_s = f"{stock:,}" if isinstance(stock, int) else str(stock)
        a(f"| {r['Designator']} | {r['Comment']} | {r['LCSC Part #']} | {r['JLC']} | "
          f"${r['Unit $']} | {stock_s} | {note} |")
    a("")
    a("### If something is out of stock")
    a("")
    for key, p in parts.PARTS.items():
        if p.get("alt"):
            a(f"**{p['mpn']}** ({p['lcsc']})")
            for alt in p["alt"]:
                a(f"  - {alt}")
            a("")
    per_board = {r["LCSC Part #"]: len(r["Designator"].split(",")) for r in rows}
    worth = sorted((p["stock"] // per_board[p["lcsc"]], p["mpn"], p["stock"], per_board[p["lcsc"]])
                   for p in parts.PARTS.values()
                   if p.get("lcsc") in per_board and isinstance(p.get("stock"), int))
    a(f"The thinnest line is the {worth[0][1]}: {worth[0][2]:,} in stock and {worth[0][3]} per")
    a(f"board, about {worth[0][0]:,} boards' worth; next the {worth[1][1]} at about {worth[1][0]:,}.")
    a("The BNC alternates share the 'BNC-KYWE' body (10 x 10 mm flange, four posts on")
    a("8 x 8 mm, centre pin), so the footprint takes any of them.  Any 100 mm motorized")
    a("fader with a 10k track and a 6-11 V motor is the plant; see the handbook.")
    a("")
    a("## After the boards arrive")
    a("")
    a("The bring-up order, the expected voltage at every loop and the student")
    a("exercises are in [HANDBOOK.md](HANDBOOK.md).  In one line: with the fader")
    a("unplugged and the LOOP switch open, power it at ±15 V, both green lamps light,")
    a("and the TARGET knob moves the P loop's output; then wire the fader and close")
    a("the loop at a P gain of a few.")
    a("")
    os.makedirs(DOCS, exist_ok=True)
    path = os.path.join(DOCS, "MANUFACTURING.md")
    open(path, "w").write("\n".join(L) + "\n")
    print(f"  wrote {os.path.relpath(path, ROOT)} (parts {money(parts_cost)}/board, "
          f"{smt} SMT + {tht} THT joints, {len(ext_codes)} extended codes)")

    # ---------------------------------------------------------- fabrication notes
    N = [f"{parts.BOARD_NAME} rev {parts.REV} ({parts.BOARD_DATE}) -- JLCPCB order form, field by field",
         "=" * 78, ""]
    for field, value, why in form:
        if value is None:
            N.append(f"[{field}]")
        else:
            N.append(f"  {field:28s} {value}" + (f"      ({why})" if why else ""))
    N += ["", "Upload:", f"  gerbers     out/{STEM}/{STEM}-gerbers.zip",
          f"  BOM         out/{STEM}/{STEM}_bom_jlcpcb_upload.csv",
          f"  CPL         out/{STEM}/{STEM}_cpl_jlcpcb_upload.csv   (JLCPCB only; others take _kicad_native)",
          f"  remark      paste out/{STEM}/{STEM}-assembly-notes.txt",
          "", "Then read PLACEMENT_CHECKS.txt against the preview, front and (empty) back."]
    path = os.path.join(OUT, STEM, f"{STEM}-fabrication-notes.txt")
    open(path, "w").write("\n".join(N) + "\n")
    print(f"  wrote {os.path.relpath(path, ROOT)}")

    # ----------------------------------------------------------- placement checks
    P = [f"PLACEMENT CHECKS for {parts.BOARD_NAME} rev {parts.REV}: JLCPCB's 'Confirm Parts Placement' preview",
         "=" * 78, "",
         "The upload CPL turns these parts by the angle JLCPCB's own drawing needs.",
         "'read' angles were seen in a real preview of the same part; 'predicted' ones",
         "come from fitting JLCPCB's land pattern on ours and have not been seen yet.",
         "Look at each predicted part in the preview; if one is turned, do NOT nudge it",
         "in their viewer (the fix is lost on the next upload): change its entry in",
         "scripts/parts.py JLC_ROTATION and rebuild.", ""]
    for code, (deg, (dx, dy), how, note) in sorted(parts.JLC_ROTATION.items(), key=lambda kv: (kv[1][2] != "predicted", kv[0])):
        refs = sorted((r for r, c in ref_lcsc.items() if c == code),
                      key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
        if not refs:
            continue
        shift = f", datum ({dx:+.1f}, {dy:+.1f}) mm" if (dx or dy) else ""
        P.append(f"[{how.upper():9s}] {', '.join(refs)}  ({code}, +{deg} deg{shift})")
        P.append(f"            {note}")
        look = next((l for l in PREVIEW_CHECKS if l[0].split(",")[0].strip() in refs), None)
        if look:
            P.append(f"            look for: {look[1]}; should be: {look[2]}")
        P.append("")
    P += ["Symmetric parts (every resistor and capacitor) cannot go in wrong.",
          "The back of the board carries no parts: check it anyway, it should be empty.", ""]
    path = os.path.join(OUT, STEM, "PLACEMENT_CHECKS.txt")
    open(path, "w").write("\n".join(P) + "\n")
    print(f"  wrote {os.path.relpath(path, ROOT)}")

    # --------------------------------------------------------- the claims check
    op = R["op"]

    def v(x):
        s = f"{x:+.1f}"
        return "0.0" if s in ("+0.0", "-0.0") else s

    TH = json.load(open(os.path.join(ROOT, "sim", "thermal.json")))
    claims = CLAIMS(parts_cost, circuit_check_count(), loops, smt, tht, n_vias, R, p1, p2,
                    round(quote(10, PCB_2L_10PCS)[4] / 10), TH)
    bad, n = [], 0
    for rel, pat, want in claims:
        text = re.sub(r"\s+", " ", open(os.path.join(ROOT, rel)).read())   # prose wraps lines
        m = re.search(pat, text)
        n += 1
        if not m:
            bad.append(f"{rel}: no sentence matches /{pat}/")
            continue
        got = m.groups() if isinstance(want, tuple) else m.group(1)
        if got != want:
            bad.append(f"{rel}: says {got!r}, the build says {want!r}  (/{pat}/)")
    for b in bad:
        print(f"  STALE {b}")
    print(f"  {n - len(bad)} of {n} document claims match the build")
    return 1 if bad else 0


# What to look for in JLCPCB's preview, per orientation-sensitive part.
PREVIEW_CHECKS = [
    ("U1, U2, U3, U4, U5, U6, U7", "SOT-23-5: three pads on the left, two on the right",
     "the three-pad side under the triangle's inputs (left); pin 1 top-left"),
    ("Q1", "D2PAK tab", "tab pointing UP into the copper pour, the two leads down inside the circle"),
    ("Q2", "D2PAK tab", "tab pointing DOWN into the copper pour, the two leads up inside the circle"),
    ("SW1, SW2, SW3, SW4, SW5", "MSK12C02 slide switch: the three pins on one edge",
     "SW1, SW2: pins along the bottom edge of the body; SW3, SW4, SW5: pins down the left edge"),
    ("RV1", "RK09K knob, keyed by its two posts", "fits one way; the shaft up, the pins toward the switch"),
    ("RV2, RV3, RV4", "3362P trimmer, keyed", "fits one way; screw on top, wiper pin toward the top"),
    ("J1, J2", "BNC barrel", "pointing off the LEFT edge"),
    ("J3", "BNC barrel", "pointing off the BOTTOM edge"),
    ("J4, J5", "screw terminal wire openings", "facing the BOTTOM edge"),
    ("J6", "screw terminal wire openings", "facing the TOP edge"),
    ("D1, D2", "SMA cathode band", "D1 cathode on the LEFT (toward the rail); D2 cathode at the TOP (toward the terminal)"),
    ("D3, D4", "SMA cathode band", "D3 cathode UP toward the +15 V pour; D4 cathode DOWN toward the DRIVE row"),
    ("LED1, LED2", "0805 LED cathode mark", "LED1 cathode DOWN toward its ground via; LED2 cathode UP toward its 10k"),
    ("LED3, LED4", "0805 LED cathode mark", "antiparallel across the fuse: LED3 cathode on the RIGHT, LED4 cathode on the LEFT"),
    ("C11, C12", "electrolytic stripe (negative)", "C11 negative DOWN toward its ground; C12 negative DOWN toward its ground"),
    ("TP1-TP14, TP100-TP103", "test loops", "the loop lying along the pad's long side; not polarised"),
]


def CLAIMS(parts_cost, nchecks, loops, smt, tht, n_vias, R, p1, p2, each10, TH):
    """Every number the hand-written documents quote from the build."""
    q1, q2 = TH["Q1"], TH["Q2"]
    pour_hot = max(q1["bench"]["pour_mean_c"], q2["bench"]["pour_mean_c"])
    p5, p22 = R["p_only"]["5"], R["p_only"]["22"]
    sweep = {x["target_v"]: x for x in R["stall_sweep"]}
    stall_max = max(x["p_q1_w"] for x in R["stall_sweep"])
    return [
        ("README.md", r"about \$([0-9.]+) in parts per board", f"{parts_cost:.2f}"),
        ("README.md", r"(\d+) circuit assertions", str(nchecks)),
        ("README.md", r"\((\d+) probe loops", str(loops)),
        ("README.md", r"\b(\d+) x (\d+) mm printed circuit board", (f"{layout.BOARD_W:.0f}", f"{layout.BOARD_H:.0f}")),
        ("docs/HANDBOOK.md", r"draws about (\d+) mA with no motor", f"{R['i_supply_ma']:.0f}"),
        ("docs/HANDBOOK.md", r"the rails after the diodes \| ±([0-9.]+) V", f"{R['op']['+15V']:.1f}"),
        ("docs/HANDBOOK.md", r"gain of 5 the simulation leaves (\d+) mV", f"{p5['residual_v'] * 1e3:.0f}"),
        ("docs/HANDBOOK.md", r"each step rings near (\d+) Hz", f"{R['f_nat_hz']:.0f}"),
        ("docs/HANDBOOK.md", r"about (\d+) in the simulation\)", "22"),
        ("docs/HANDBOOK.md", r"\((\d+) ms; (\d+)k\)", (f"{R['rc_d_ms']:.0f}", f"{R['rv3_k']:.0f}")),
        ("docs/HANDBOOK.md", r"settles \(to 5 %\) in (\d+) ms with (\d+) % overshoot",
         (f"{R['pd_gain100']['settle_s'] * 1e3:.0f}", f"{R['pd_gain100']['overshoot_pct']:.0f}")),
        ("docs/HANDBOOK.md", r"stalls the motor at about ([0-9.]+) A", f"{R['stall']['i_motor_a']:.1f}"),
        ("docs/HANDBOOK.md", r"pulls about ([0-9.]+) A through the driver", f"{R['short']['i_short_a']:.0f}"),
        ("docs/HANDBOOK.md", r"at that current, 2 to ([0-9.]+) W", f"{stall_max:.1f}"),
        ("docs/DESIGN_NOTES.md", r"from ([0-9.]+) W at 2 V to ([0-9.]+) W at 7 V",
         (f"{sweep[2.0]['p_q1_w']:.1f}", f"{sweep[7.0]['p_q1_w']:.1f}")),
        ("docs/DESIGN_NOTES.md", r"draws about ([0-9.]+) A at ([0-9.]+) V in the simulation, ([0-9.]+) W",
         (f"{R['stall']['i_motor_a']:.2f}", f"{R['stall']['v_motor']:.1f}", f"{R['stall']['p_q1_w']:.1f}")),
        ("docs/DESIGN_NOTES.md", r"puts ([0-9.]+) A and (\d+) W into one transistor",
         (f"{R['short']['i_short_a']:.1f}", f"{R['short']['p_q1_w']:.0f}")),
        ("docs/DESIGN_NOTES.md", r"natural frequency with P gain at the\s+top is about (\d+) Hz", f"{R['f_nat_hz']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"asks for\s+(\d+) ms, which with 22 nF puts the D GAIN trimmer at (\d+)k",
         (f"{R['rc_d_ms']:.0f}", f"{R['rv3_k']:.0f}")),
        ("docs/DESIGN_NOTES.md", r"(\d+) SMT and (\d+) through-hole joints, (\d+) vias", (str(smt), str(tht), str(n_vias))),
        ("docs/DESIGN_NOTES.md", r"makes (\d+) assertions", str(nchecks)),
        ("docs/DESIGN_NOTES.md", r"quiescent (\d+) mA", f"{R['i_supply_ma']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"overshoots (\d+) % at gain 22 and rings at about (\d+) Hz",
         (f"{p22['overshoot_pct']:.0f}", f"{R['f_nat_hz']:.0f}")),
        ("docs/DESIGN_NOTES.md", r"with D by the rule: ([0-9.]+) % overshoot at gain 22; at gain 100, (\d+) % and (\d+) ms",
         (f"{R['pd']['rule']['overshoot_pct']:.1f}", f"{R['pd_gain100']['overshoot_pct']:.0f}",
          f"{R['pd_gain100']['settle_s'] * 1e3:.0f}")),
        ("docs/DESIGN_NOTES.md", r"Q1's pour is (\d+) mm² and its junction reaches (\d+) °C in the worst stall, "
                                 r"Q2's (\d+) mm² and (\d+) °C \((\d+) and (\d+) °C on standoffs\)",
         (str(q1["pour_mm2"]), f"{q1['bench']['junction_c']:.0f}", str(q2["pour_mm2"]),
          f"{q2['bench']['junction_c']:.0f}", f"{q1['standoffs']['junction_c']:.0f}",
          f"{q2['standoffs']['junction_c']:.0f}")),
        ("docs/DESIGN_NOTES.md", r"puts the junctions at (\d+) and (\d+) °C in the worst stall",
         (f"{q1['bench']['junction_c']:.0f}", f"{q2['bench']['junction_c']:.0f}")),
        ("docs/DESIGN_NOTES.md", r"the model says about (\d+) °C",
         f"{round(q1['bench']['tab_c'], -1):.0f}"),
        ("docs/DESIGN_NOTES.md", r"\(Q1: (\d+) mm², from the U6 column to the board edge; Q2: (\d+) mm²\)",
         (str(q1["pour_mm2"]), str(q2["pour_mm2"]))),
        ("docs/HANDBOOK.md", r"the pours marked HOT reach about\s+(\d+) °C", f"{round(pour_hot, -1):.0f}"),
        ("docs/DESIGN_NOTES.md", r"a 10 V step peaks at ([0-9.]+) A and ([0-9.]+) V of drive",
         (f"{R['big_step']['i_peak_a']:.2f}", f"{R['big_step']['drive_peak_v']:.1f}")),
    ]


if __name__ == "__main__":
    sys.exit(main())
