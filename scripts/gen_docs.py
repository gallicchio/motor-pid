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
STEM = "opamp"

# JLCPCB list prices, autumn 2026.  These move; the fab's quote is the
# authority and the build prints these only as an order of magnitude.
PCB_2L_5PCS = 2.00           # 100 x 100 mm, 2 layers, 5 pieces, green, HASL
PCB_2L_10PCS = 5.00
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
        ("Dimensions", f"{w:.0f} x {h:.0f} mm", "read from the board outline; the discounted size"),
        ("PCB Qty", "5", "the minimum; 10 costs about three dollars more"),
        ("Product Type", "Industrial/Consumer electronics", "the default"),
        ("PCB Specifications", None, None),
        ("Different Design", "1", "one board in the outline"),
        ("Delivery Format", "Single PCB", "no panel"),
        ("PCB Thickness", "1.6 mm", "the BNC flanges and the terminal blocks expect it"),
        ("PCB Color", "Green", "any; the white silkscreen reads best on green or black"),
        ("Silkscreen", "White", "the default for green"),
        ("Material Type", "FR4-Standard TG 135-140", "the default; nothing here gets warm"),
        ("Surface Finish", "LeadFree HASL", "students handle this board: lead-free.  ENIG is fine too"),
        ("High-spec Options", None, None),
        ("Outer Copper Weight", "1 oz", "the design rules assume it"),
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
        ("Edge Rails/Fiducials", "Added by JLCPCB", "the board carries no fiducials; let them add rails with fiducials, removed before delivery"),
        ("Confirm Parts Placement", "Yes", "look at the preview against PLACEMENT_CHECKS.txt before paying"),
        ("Parts Selection", "By JLCPCB", "every BOM line has an LCSC code"),
        ("Through-hole parts", f"keep them: {', '.join(tht_refs)}",
         "the form lists them separately; the BNCs, terminals and trimmer are meant to be fitted"),
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
    a("The same list is in `out/opamp/opamp-fabrication-notes.txt` to keep open while")
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
    a(f"(the BNCs, the terminal blocks, the trimmer, the DIP switches, the test loops")
    a(f"and the PNPs), each with a one-off {money(EXTENDED_PART_FEE)} feeder fee.  Parts alone are")
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
    a("| parts | LCSC | turned by | evidence |")
    a("|---|---|---|---|")
    for code, (deg, how, note) in sorted(parts.JLC_ROTATION.items(), key=lambda kv: (-kv[1][0], kv[0])):
        refs = sorted((r for r, c in ref_lcsc.items() if c == code),
                      key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
        if not refs:
            continue
        a(f"| {', '.join(refs)} | {code} | {deg} deg | {how}: {note} |")
    a("")
    a("*read* means seen in a JLCPCB preview on a real order of that part on that")
    a("footprint; *predicted* means derived by fitting JLCPCB's own land pattern")
    a("onto ours by pin number (`scripts/easyeda.py <code>`).  Every predicted part is")
    a("in `out/opamp/PLACEMENT_CHECKS.txt`, the list to hold against the preview.")
    a("`check_outputs.py` proves the two CPL files differ in nothing but those angles.")
    a("")
    a("## Check these in the preview before you pay")
    a("")
    a("| part | what to look for | should be |")
    a("|---|---|---|")
    for line in PREVIEW_CHECKS:
        a(f"| {line[0]} | {line[1]} | {line[2]} |")
    a("")
    a("The one part that cannot go in wrong is the trimmer: its three holes form an")
    a("L, so it fits one way.  `check_outputs.py` re-derives that from the board file")
    a("on every build.  The BNCs are not keyed (four symmetric posts and a centre")
    a("pin), which is why their correction is read, not predicted, and worth a glance.")
    a("")
    a("## The through-hole parts")
    a("")
    a(f"{len(tht_refs)} parts are through-hole: **{', '.join(tht_refs)}**, the three BNC")
    a("jacks, the four terminal blocks and the trimmer.  They are in the BOM and the")
    a("CPL and JLCPCB fits them for a per-order fee plus pennies a joint; keep them")
    a("selected when the form lists them.  If you would rather solder them yourself")
    a(f"they are the {tht} largest, easiest joints on the board.  Everything else is 0805,")
    a("1206, SOD-123 or SOT-23 and is hand-workable with a fine iron.")
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
    a("8 x 8 mm, centre pin), so the footprint takes any of them.")
    a("")
    a("## After the boards arrive")
    a("")
    a("The bring-up order, the expected voltage at every loop and the student")
    a("exercises are in [HANDBOOK.md](HANDBOOK.md).  In one line: power it from a")
    a("current-limited supply at 30 mA, both green LEDs light, and as a follower")
    a("(FEEDBACK 2 on) with IN+ grounded OUT sits within a few tens of millivolts")
    a("of zero and the trimmer nulls it.")
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
    for code, (deg, how, note) in sorted(parts.JLC_ROTATION.items(), key=lambda kv: (kv[1][1] != "predicted", kv[0])):
        refs = sorted((r for r, c in ref_lcsc.items() if c == code),
                      key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
        if not refs:
            continue
        P.append(f"[{how.upper():9s}] {', '.join(refs)}  ({code}, +{deg} deg)")
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

    claims = [
        ("README.md", r"about \$([0-9.]+) in parts per board", f"{parts_cost:.2f}"),
        ("README.md", r"(\d+) circuit assertions", str(circuit_check_count())),
        ("README.md", r"first board about \$(\d+) and each further one about \$(\d+)",
         (f"{round(p1):d}", f"{round(p2 - p1):d}")),
        ("README.md", r"(\d+) probe loops", str(loops)),
        ("README.md", r"about \$(\d+) each for (\d+) assembled boards", (f"{round(quote(10, PCB_2L_10PCS)[4] / 10):d}", "10")),
        ("docs/HANDBOOK.md", r"(\d+) probe loops", str(loops)),
        ("docs/HANDBOOK.md", r"\| TP3 \| TAIL \|[^|]*\| ([-+0-9.]+) V", v(op["tail"])),
        ("docs/HANDBOOK.md", r"\| TP6 \| Q2 C \|[^|]*\| ([-+0-9.]+) V", v(op["c2"])),
        ("docs/HANDBOOK.md", r"\| TP7 \| Q3 E \|[^|]*\| ([-+0-9.]+) V", v(op["e3"])),
        ("docs/HANDBOOK.md", r"\| TP8 \| Q3 C \|[^|]*\| ([-+0-9.]+) V", v(op["c3"])),
        ("docs/HANDBOOK.md", r"\| TP5 \| Q6 B \|[^|]*\| ([-+0-9.]+) V", v(op["b6"])),
        ("docs/HANDBOOK.md", r"\| TP4 \| Q6 E \|[^|]*\| ([-+0-9.]+) V", v(op["e6"])),
        ("docs/HANDBOOK.md", r"limits at about (\d+) mA", f"{R['isc_ma']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"into a dead short is about (\d+) mA", f"{R['isc_ma']:.0f}"),
        ("docs/HANDBOOK.md", r"\| TP11 \| \+15V \|[^|]*\| ([-+0-9.]+) V", v(R["vrail"])),
        ("docs/HANDBOOK.md", r"\| TP12 \| -15V \|[^|]*\| ([-+0-9.]+) V", v(-R["vrail"])),
        ("docs/HANDBOOK.md", r"null range of about \+/-(\d+) mV", f"{R['null_mv']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"open-loop gain at the quiescent point of about (\d+)", f"{R['a0']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"phase margin of about (\d+) degrees as a follower", f"{R['pm_x1']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"the x11 amplifier really has a gain of ([0-9.]+)", f"{R['g11']:.1f}"),
        ("docs/DESIGN_NOTES.md", r"swings from ([-0-9.]+) V to \+([0-9.]+) V", (f"{R['swing'][0]:.1f}", f"{R['swing'][1]:.1f}")),
        ("docs/DESIGN_NOTES.md", r"null range of about \+/-(\d+) mV", f"{R['null_mv']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"tail current of ([0-9.]+) mA", f"{R['i_tail_ma']:.2f}"),
        ("docs/DESIGN_NOTES.md", r"from ([0-9.]+) with the resistor to ([0-9.]+) with the sink",
         (f"{R['gcm_r']:.3f}", f"{R['gcm_cs']:.4f}")),
        ("docs/DESIGN_NOTES.md", r"[Ww]ithout the 1 k the follower's phase margin is ([-0-9]+) degrees", f"{R['pm_x1_bare']:.0f}"),
        ("docs/DESIGN_NOTES.md", r"follower settles in about ([0-9.]+) us", f"{R['ts_x1_us']:.1f}"),
        ("docs/DESIGN_NOTES.md", r"(\d+) SMT and (\d+) through-hole joints", (str(smt), str(tht))),
        ("docs/DESIGN_NOTES.md", r"(\d+) vias", str(n_vias)),
    ]
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
    ("Q1, Q3, Q4, Q5, Q7, Q8", "SOT-23: the lone pad (collector) on the side the collector wire leaves",
     "lone pad at the TOP, the pair at the bottom"),
    ("Q2, Q6", "the same, the other way up", "lone pad at the BOTTOM, the pair at the top"),
    ("SW1, SW2, SW3", "2-way DIP switch: pads on pads; sliders move toward the '1 / 2' legends",
     "SW1 and SW2 sliders moving toward the labelled side; electrically it cannot go in wrong"),
    ("RV1", "3362P trimmer, keyed", "fits one way; screw on top"),
    ("J1, J2", "BNC barrel", "pointing off the LEFT edge"),
    ("J3", "BNC barrel", "pointing off the RIGHT edge"),
    ("J4, J5", "screw terminal wire openings", "facing the LEFT edge"),
    ("J6, J7", "screw terminal wire openings", "facing the RIGHT edge"),
    ("D1, D2", "SOD-123 cathode band", "at the end the silkscreen bar marks (they are anti-parallel: one up, one down)"),
    ("D3, D4", "SOD-123 cathode band", "D3 toward the +15 V rail (top); D4 toward the terminal (right)"),
    ("D5, D6", "SOD-123 cathode band", "D5 cathode DOWN toward Q7; D6 cathode DOWN toward the bus"),
    ("LED1, LED2", "0805 LED cathode mark", "LED1 cathode on the RIGHT (its ground via), anode toward R12; "
     "LED2 cathode on the LEFT toward R13, anode to the ground via on its right"),
    ("TP1-TP14, TP100-TP103", "test loops", "the loop lying along the pad's long side; not polarised"),
]


if __name__ == "__main__":
    sys.exit(main())
