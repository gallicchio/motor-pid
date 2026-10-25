#!/usr/bin/env python3
"""Draw the schematic of the Lab 10L PID motor control loop, laid out as
Fig. 10L.10 of Learning the Art of Electronics draws it.

Left to right: the TARGET knob and jack; the book's "pseudo op-amp" (the
unity-gain difference amplifier, the inverter P and the summing amplifier with
the gain trimmer) with the differentiator D and the integrator I hanging
under it; the motor driver (an op-amp with split feedback round a push-pull
pair); the motor fuse; the terminals for the motorized slide pot, drawn with
the pot and the motor that hang on them; the feedback from the pot's wiper
running back along the bottom to the LOOP switch and the difference
amplifier's inverting input.  +15 V rail along the top, -15 V along the
bottom, power entry at the right.  Every signal is a drawn wire; only the
rails and ground use power symbols.  Notes sit in a band under the circuit.

Every op-amp is drawn with + on top, because that is where the SOT-23-5 puts
it, and the board generator (scripts/layout.py) places the same parts in the
same arrangement, so the silkscreen is this drawing.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kienv, parts
from schlib import Sheet

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "hardware", "motorpid.kicad_sch")
SIM = os.path.join(HERE, "..", "sim", "results.json")

G = 2.54


def g(n):
    """Grid units to millimetres."""
    return round(n * G, 4)


# ---------------------------------------------------------------- geometry --
VP_Y, VM_Y = g(26), g(128)             # the two rails
A_Y = g(52)                            # the main amplifier row
D_Y = g(78)                            # the differentiator
I_Y = g(106)                           # the integrator
FB_Y = g(123)                          # the position feedback, back along the bottom
NOTE_Y = g(134)                        # the band of notes


def passive_fields(value):
    p = parts.PASSIVES.get(value)
    return {"LCSC": p["lcsc"], "MPN": p["mpn"]} if p else {}


def part_fields(key):
    p = parts.PARTS[key]
    return {"LCSC": p["lcsc"], "MPN": p["mpn"]}


def fp(key):
    return parts.PARTS[key]["footprint"]


def sym(key):
    return parts.PARTS[key]["symbol"]


def sim_results():
    try:
        return json.load(open(SIM))
    except (OSError, ValueError):
        return {}


# Every probe loop has a fixed number, so the board's placement (keyed by
# reference) never slides when a loop is added to the sheet.
TP_NUMBER = {"TARGET": 1, "ERROR": 2, "P": 3, "D": 4, "I": 5, "SUM": 6, "DRIVE": 7,
             "POSITION": 8, "+15V": 9, "-15V": 10, "MOTOR": 11, "BASES": 12}


def build():
    R = sim_results()
    s = Sheet(kienv.share_dir(), paper="A2",
              title=f"{parts.BOARD_NAME}: Lab 10L of Learning the Art of Electronics",
              date=parts.BOARD_DATE, rev=parts.REV,
              company="Circuit: Hayes & Horowitz, Learning the Art of Electronics (2016), Lab 10L  |  Board: Jason Gallicchio and Claude",
              comments=["LM321 (the single LM358) in SOT-23-5, one per triangle; MJD44H11 / MJD45H11 push-pull",
                        "P from 1 to 101, D up to 10 ms (slide pot) or 100 ms (rotary), I up to 10 s",
                        "Open source, CERN-OHL-P-2.0 -- " + parts.PROJECT_URL])
    pwr_n = [0]

    def pwr_ref():
        pwr_n[0] += 1
        return f"#PWR{pwr_n[0]:04d}"

    def gnd(x, y, up=False):
        s.place("power:GND", pwr_ref(), "GND", x, y, rot=180 if up else 0,
                in_bom=False, on_board=False, hide_ref=True, hide_value=True)

    def rail(name, x, y, rot=0, to=None):
        s.place(f"power:{name}", pwr_ref(), name, x, y, rot=rot, in_bom=False,
                on_board=False, hide_ref=True,
                val_off=(0, -3.81) if rot == 0 else (0, 3.81))
        if to is not None:
            s.wire((x, y), (x, to))

    def flag(x, y, to_y=None, to_x=None):
        """A PWR_FLAG hanging from a wire at (x, to_y), or lying sideways on a
        wire at (to_x, y)."""
        n = sum(1 for it in s.symbols if it[0].startswith("#FLG")) + 1
        if to_x is None:
            s.place("power:PWR_FLAG", f"#FLG{n:02d}", "PWR_FLAG", x, y,
                    in_bom=False, on_board=False, hide_ref=True,
                    rot=0 if y < to_y else 180,
                    val_off=(0, -3.81) if y < to_y else (0, 3.81))
            s.wire((x, y), (x, to_y))
            s.junction(x, to_y)
        else:
            left = x < to_x
            s.place("power:PWR_FLAG", f"#FLG{n:02d}", "PWR_FLAG", x, y,
                    in_bom=False, on_board=False, hide_ref=True,
                    rot=90 if left else 270,
                    val_off=(-3.81, 0) if left else (3.81, 0),
                    val_justify="right" if left else "left")
            s.wire((x, y), (to_x, y))
            s.junction(to_x, y)

    def res(ref, value, x, y, rot=0, lcsc=None, side="right", footprint=None, above=True):
        """above=True: ref above, value below a horizontal resistor; False: both below;
        "both": both above."""
        """R_US: rot 0 vertical (pin 1 top), rot 90 horizontal (pin 1 left).
        Reference and value to the `side` of a vertical resistor; above and
        below a horizontal one (or both below when above is False)."""
        if rot == 0:
            dx = 2.4 if side == "right" else -2.4
            ro, vo, j = (dx, -1.4), (dx, 1.4), ("left" if side == "right" else "right")
        elif above == "both":
            ro, vo, j = (0, -4.4), (0, -2.6), None
        elif above:
            ro, vo, j = (0, -2.6), (0, 2.6), None
        else:
            ro, vo, j = (-3.0, 2.6), (3.0, 2.6), None
        s.place("Device:R_US", ref, value, x, y, rot=rot,
                footprint=footprint or fp("R_0805"),
                fields=passive_fields(lcsc or value),
                ref_off=ro, val_off=vo, ref_justify=j, val_justify=j)

    def cap(ref, value, x, y, side="right", rot=0, lcsc=None, hide=False, fields_at="split"):
        """Vertical (rot 0) with the fields to one side; horizontal (rot 90) with
        the reference above and the value below, or both above ("above") or
        both below ("below").  hide=True prints neither (the bypass capacitors)."""
        if rot == 0:
            dx = 2.6 if side == "right" else -2.6
            j = "left" if side == "right" else "right"
            ro, vo = (dx, -1.4), (dx, 1.4)
        elif fields_at == "above":
            ro, vo, j = (0, -4.6), (0, -2.8), None
        elif fields_at == "below":
            ro, vo, j = (0, 2.8), (0, 4.6), None
        else:
            ro, vo, j = (0, -2.8), (0, 2.8), None
        s.place("Device:C", ref, value, x, y, rot=rot, footprint=fp("C_0805"),
                fields=passive_fields(lcsc or value), ref_off=ro, val_off=vo,
                ref_justify=j, val_justify=j, hide_ref=hide, hide_value=hide)

    gnd_tp = [100]

    def testpoint(x, y, name, rot=0, dx=1.8, dy=-3.0, justify="left"):
        """A test loop at the node, carrying the name of what it probes.
        rot 0: loop above the wire, 180 below, 90 left of a vertical wire, 270 right."""
        if name == "GND":
            n = gnd_tp[0]
            gnd_tp[0] += 1
        else:
            n = TP_NUMBER[name]
        ref = f"TP{n}"
        s.place("Connector:TestPoint", ref, name, x, y, rot=rot,
                footprint=fp("TP"), fields=part_fields("TP"),
                hide_ref=True, val_off=(dx, dy), val_justify=justify)
        s.junction(x, y)
        return ref

    def note(lines, x, y, size=1.3, justify="left", pitch=None):
        for i, line in enumerate(lines):
            if line:
                s.text(line, x, y + i * (pitch or size * 1.95), size=size, justify=justify)

    def label(txt, x, y, size=1.3, justify="left"):
        """A net name, anchored ON the wire so ERC sees it attached."""
        s.label(txt, x, y, size=size, justify=justify)

    cap_n = [20]

    def opamp(ref, x, y, caption=None, drop_dx=10.16, vminus_dy=25.4):
        """An LM321 at (x, y), + on top.  V+ goes up to a +15V symbol with a
        100 nF beside it; V- goes down and right to a -15V symbol with its
        100 nF, below the feedback rows.  The output's feedback drops at
        x + drop_dx.  Returns (p_plus, p_minus, p_out)."""
        s.place(sym("OPAMP"), ref, "LM321", x, y, footprint=fp("OPAMP"),
                fields=part_fields("OPAMP"), ref_off=(-0.6, -3.4), val_off=(-0.6, -1.0),
                ref_justify="left", val_justify="left", hide_value=True)
        pp, pm, po = s.pin(ref, 1, "1"), s.pin(ref, 1, "3"), s.pin(ref, 1, "4")
        vp, vm = s.pin(ref, 1, "5"), s.pin(ref, 1, "2")
        # V+: up to a +15V symbol, the capacitor hanging off the wire to the right
        s.wire(vp, (vp[0], y - 20.32))
        rail("+15V", vp[0], y - 20.32)
        cy = y - 17.78
        s.junction(vp[0], cy)
        c1 = f"C{cap_n[0]}"
        cap_n[0] += 1
        s.wire((vp[0], cy), (x + 2.54, cy))
        cap(c1, "100nF", x + 2.54, cy + 3.81, hide=True)
        gnd(x + 2.54, cy + 7.62)
        # V-: down past the feedback rows, right, to a -15V symbol; the
        # capacitor stands up from that wire with its ground above it
        vy = y + vminus_dy
        s.wire(vm, (vm[0], vy), (x + 20.32, vy))
        rail("-15V", x + 20.32, vy, rot=180)
        c2 = f"C{cap_n[0]}"
        cap_n[0] += 1
        cap(c2, "100nF", x + 20.32, vy - 3.81, hide=True)
        gnd(x + 20.32, vy - 7.62, up=True)
        s.junction(x + 20.32, vy)
        if caption:
            s.text(caption, x, y + 7.0, size=1.2, justify=None)
        return pp, pm, po

    def inverting_node(ref, pm, y):
        """The - input's node row under a stage: pin 3 goes straight down to
        the row; returns the node point."""
        nx, ny = pm[0], y + 10.16
        s.wire(pm, (nx, ny))
        return (nx, ny)

    def ground_plus(pp):
        """A grounded + input: left 5.08, then down to a ground symbol."""
        gx = pp[0] - 5.08
        s.wire(pp, (gx, pp[1]), (gx, pp[1] + 5.08))
        gnd(gx, pp[1] + 5.08)

    def switch(ref, name, x, y, mirror, up_txt, low_txt, below=False):
        """An SPDT slide switch with its name and what each pole does printed
        beside it; the reference and value fields stay hidden (the words say it).
        below=True stacks all three lines under the switch, to its right."""
        s.place(sym("SW"), ref, name, x, y, mirror=mirror, footprint=fp("SW"),
                fields=part_fields("SW"), hide_ref=True, hide_value=True)
        if below:
            tx = x + 1.0
            s.text(f"{ref}  {name}", tx, y + 9.0, size=1.1)
            s.text(up_txt, tx, y + 11.2, size=1.0)
            s.text(low_txt, tx, y + 13.2, size=1.0)
        else:
            tx = x - 7.0 if mirror else x - 1.0
            s.text(f"{ref}  {name}", tx, y - 10.5, size=1.1)
            s.text(up_txt, tx, y - 8.0, size=1.0)
            s.text(low_txt, tx, y + 9.0, size=1.0)
        return s.pin(ref, 1, "1"), s.pin(ref, 1, "2"), s.pin(ref, 1, "3")

    def drop(po, dx, ny):
        """The output's wire right and down to the node row; returns the column x."""
        s.wire(po, (po[0] + dx - 7.62, po[1]), (po[0] + dx - 7.62, ny))
        s.junction(po[0] + dx - 7.62, po[1])
        return po[0] + dx - 7.62

    # ================================================================ target ==
    # The knob between its 6.8k end resistors, decoupled; the BNC; the source switch.
    KX = g(22)
    res("R1", "6.8k", KX, g(36))
    s.wire((KX, VP_Y), (KX, g(36) - 3.81))
    s.junction(KX, VP_Y)
    s.place(sym("POT_KNOB"), "RV1", "10k", KX, A_Y, footprint=fp("POT_KNOB"),
            fields=part_fields("POT_KNOB"), ref_off=(-3.4, -1.4), val_off=(-3.4, 1.4),
            ref_justify="right", val_justify="right")
    k1, k2, k3 = s.pin("RV1", 1, "1"), s.pin("RV1", 1, "2"), s.pin("RV1", 1, "3")
    s.wire((KX, g(36) + 3.81), k1)
    s.wire(k3, (KX, g(68) - 3.81))
    res("R2", "6.8k", KX, g(68))
    s.wire((KX, g(68) + 3.81), (KX, VM_Y))
    s.junction(KX, VM_Y)
    s.text("TARGET", g(12), A_Y - 7.0, size=2.5)
    s.text("knob, centre detent = 0 V", g(12), A_Y - 4.6, size=1.1)
    # 10 uF at each end of the knob, as the book's 15 uF
    for ref, yy, up in (("C1", g(42), False), ("C2", g(62), True)):
        ex = KX - 7.62
        s.wire((KX, yy), (ex, yy))
        s.junction(KX, yy)
        cap(ref, "10uF", ex, yy + (3.81 if not up else -3.81), side="left")
        gnd(ex, yy + (7.62 if not up else -7.62), up=up)
    # the wiper goes to the switch's upper pole; the BNC to its lower pole
    SW1_X = g(36)
    w1, w2, w3 = switch("SW1", "TARGET SOURCE", SW1_X, A_Y, "y", "1: the knob", "3: the jack")
    s.wire(k2, (k2[0] + 2.54, k2[1]), (k2[0] + 2.54, w1[1]), w1)
    label("KNOB", k2[0] + 2.54, w1[1], justify="left")
    s.place("Connector:Conn_Coaxial", "J1", "BNC", KX, g(60) + 2.54, mirror="y",
            footprint=fp("BNC"), fields=part_fields("BNC"),
            ref_off=(-4.0, 1.6), val_off=(-4.0, 3.4), ref_justify="right", val_justify="right")
    j1 = s.pin("J1", 1, "1")
    s.wire(j1, (w3[0] - 2.54, j1[1]), (w3[0] - 2.54, w3[1]), w3)
    s.wire(s.pin("J1", 1, "2"), (KX, g(66)))
    gnd(KX, g(66))
    s.text("TARGET IN", g(13), g(56.5), size=2.2)
    s.text("±12 V max; a slow square wave (±0.5 V at 0.2 Hz) replaces the knob", g(13), g(58.2), size=1.1)
    label("TARGET IN", j1[0] + 5.08, j1[1], justify="left")
    # the switched target, then on to the difference amplifier
    TX = w2[0] + 5.08
    s.wire(w2, (TX, w2[1]))
    testpoint(TX, A_Y, "TARGET", rot=0)
    label("TARGET", TX + 2.54, A_Y)

    # ========================================================= pseudo op-amp ==
    # U1: the unity-gain difference amplifier, "Error".  Target into +, position into -.
    U1_X = g(60)
    p1, m1, o1 = opamp("U1", U1_X, A_Y)
    # + input: 100k from TARGET, 100k to ground hanging from the + node
    res("R5", "100k", p1[0] - 7.62, p1[1], rot=90, above="both")
    s.wire((TX, A_Y), (p1[0] - 11.43, A_Y), (p1[0] - 11.43, p1[1]))
    s.wire((p1[0] - 3.81, p1[1]), p1)
    s.junction(p1[0] - 2.54, p1[1])
    res("R6", "100k", p1[0] - 2.54, p1[1] + 3.81, side="left")
    gnd(p1[0] - 2.54, p1[1] + 7.62)
    # - input node: 100k from the LOOP switch (feedback), 100k from the output
    n1 = inverting_node("U1", m1, A_Y)
    res("R7", "100k", n1[0] - 5.08, n1[1], rot=90)             # from LOOP
    s.wire((n1[0] - 1.27, n1[1]), n1)
    res("R8", "100k", U1_X + 2.54, n1[1], rot=90, above=False)  # from the output
    s.wire(n1, (U1_X - 1.27, n1[1]))
    c = drop(o1, 10.16, n1[1])
    s.wire((U1_X + 6.35, n1[1]), (c, n1[1]))
    s.junction(n1[0], n1[1])
    s.wire(o1, (g(72), A_Y))
    testpoint(g(68), A_Y, "ERROR", rot=0)
    label("ERROR", g(68) + 1.5, A_Y)
    s.text("ERROR = TARGET - POSITION", U1_X - 2.0, A_Y - 29.21, size=1.3, justify=None)
    s.text("difference amplifier, gain 1", U1_X - 2.0, A_Y - 26.67, size=1.1, justify=None)

    # U2: the inverter P (gain -1), so P, D and I share a sign at the summing junction
    U2_X = g(84)
    p2, m2, o2 = opamp("U2", U2_X, A_Y)
    ground_plus(p2)
    n2 = inverting_node("U2", m2, A_Y)
    res("R9", "10k", n2[0] - 5.08, n2[1], rot=90)
    s.wire((g(72), A_Y), (g(72), n2[1]), (n2[0] - 8.89, n2[1]))
    s.junction(g(72), A_Y)
    s.wire((n2[0] - 1.27, n2[1]), n2)
    res("R10", "10k", U2_X + 2.54, n2[1], rot=90, above=False)
    s.wire(n2, (U2_X - 1.27, n2[1]))
    c = drop(o2, 10.16, n2[1])
    s.wire((U2_X + 6.35, n2[1]), (c, n2[1]))
    s.junction(n2[0], n2[1])
    s.wire(o2, (g(97), A_Y))
    testpoint(g(94), A_Y, "P", rot=0)
    label("P", g(94) + 1.5, A_Y)
    s.text("P = -ERROR", U2_X - 2.0, A_Y - 29.21, size=1.3, justify=None)
    s.text("inverter, gain -1", U2_X - 2.0, A_Y - 26.67, size=1.1, justify=None)

    # U3: the summing amplifier with the gain trimmer: SUM = -(Rgain / 10k) (P + D + I)
    U3_X = g(112)
    p3, m3, o3 = opamp("U3", U3_X, A_Y)
    ground_plus(p3)
    n3 = inverting_node("U3", m3, A_Y)
    SUMX = n3[0]                                        # the summing junction's column
    res("R11", "10k", n3[0] - 5.08, n3[1], rot=90)             # from P
    s.wire((g(97), A_Y), (g(97), n3[1]), (n3[0] - 8.89, n3[1]))
    s.junction(g(97), A_Y)
    s.wire((n3[0] - 1.27, n3[1]), n3)
    s.junction(n3[0], n3[1])
    # the feedback: 10k in series with the 1M trimmer as a rheostat, under the amplifier
    res("R14", "10k", U3_X + 2.54, n3[1], rot=90, above=False)
    s.wire(n3, (U3_X - 1.27, n3[1]))
    RV2_X = U3_X + 10.16
    s.place(sym("TRIM"), "RV2", "1M", RV2_X, n3[1], rot=90, footprint=fp("TRIM"),
            fields=part_fields("TRIM"), ref_off=(0, 3.4), val_off=(0, 5.6))
    t1, t2, t3 = s.pin("RV2", 1, "1"), s.pin("RV2", 1, "2"), s.pin("RV2", 1, "3")
    c = drop(o3, 15.24, n3[1])
    s.wire(t3, (c, n3[1]))
    s.wire(t2, (c, t2[1]))                                      # wiper to the end: a rheostat
    s.junction(c, t2[1])
    s.text("P GAIN: (10k + RV2) / 10k", U3_X + 2.54, n3[1] + 9.0, size=1.2)
    s.text("= 1 to 101", U3_X + 2.54, n3[1] + 11.0, size=1.1)
    s.wire(o3, (g(126), A_Y))
    testpoint(g(122), A_Y, "SUM", rot=0)
    label("SUM", g(122) + 1.5, A_Y)
    s.text("SUM = GAIN x (P + D + I)", U3_X - 2.0, A_Y - 29.21, size=1.3, justify=None)
    s.text("summing amplifier, gain -Rgain/10k", U3_X - 2.0, A_Y - 26.67, size=1.1, justify=None)
    # the box round the three: the book's "home-made pseudo op-amp"
    s.rect(g(49), A_Y - 32.0, g(126), A_Y + 32.0, style="dash", key="box/pseudo")
    s.text("PSEUDO OP-AMP: the book's home-made control amplifier, modest gain and no phase shift (Fig. 10L.6)",
           g(49.5), A_Y - 33.8, size=1.3)

    # ======================================================== D and I ==========
    # Both take the ERROR node (a drop from x = g(72)) and feed the summing junction.
    EX_D = g(72)
    # --- D: the differentiator, C in, 1k, 1M trimmer || 470 pF, 10k out through SW3 ---
    U4_X = g(90)
    p4, m4, o4 = opamp("U4", U4_X, D_Y, drop_dx=15.24)
    ground_plus(p4)
    n4 = inverting_node("U4", m4, D_Y)
    # the capacitor selector: poles on the left, 1 = 10 nF (slide pot), 3 = 100 nF (book)
    SW5_X = EX_D + 17.78
    v1, v2, v3 = switch("SW5", "D CAPACITOR", SW5_X, n4[1], "y",
                        "1: 22 nF, the slide pot", "3: 100 nF, the rotary pot (the book)")
    cap("C5", "22nF", EX_D + 7.62, v1[1], rot=90, fields_at="above")
    cap("C6", "100nF", EX_D + 7.62, v3[1], rot=90, fields_at="below")
    s.wire((EX_D, v1[1]), (EX_D + 3.81, v1[1]))
    s.wire((EX_D + 11.43, v1[1]), v1)
    s.wire((EX_D, v3[1]), (EX_D + 3.81, v3[1]))
    s.wire((EX_D + 11.43, v3[1]), v3)
    s.junction(EX_D, v1[1])
    s.junction(EX_D, v3[1])
    res("R15", "1k", v2[0] + 6.35, v2[1], rot=90, above=False)
    s.wire(v2, (v2[0] + 2.54, v2[1]))
    s.wire((v2[0] + 10.16, v2[1]), n4)
    s.junction(n4[0], n4[1])
    # feedback: the trimmer (rheostat) on the row, 470 pF across it one row up
    RV3_X = U4_X + 10.16
    s.place(sym("TRIM"), "RV3", "1M", RV3_X, n4[1], rot=90, footprint=fp("TRIM"),
            fields=part_fields("TRIM"), ref_off=(0, 3.4), val_off=(0, 5.6))
    d1, d2, d3 = s.pin("RV3", 1, "1"), s.pin("RV3", 1, "2"), s.pin("RV3", 1, "3")
    s.wire(n4, d1)
    c = drop(o4, 15.24, n4[1])
    s.wire(d3, (c, n4[1]))
    CY = D_Y + 5.08
    cap("C7", "470pF", U4_X + 3.81, CY, rot=90)
    s.wire((n4[0], CY), (U4_X, CY))
    s.junction(n4[0], CY)
    s.wire((U4_X + 7.62, CY), (c, CY))
    s.junction(c, CY)
    s.wire(d2, (d2[0], CY))                                     # wiper to the output side
    s.junction(d2[0], CY)
    s.text("D GAIN: RC = RV3 x C", U4_X + 2.54, n4[1] + 9.0, size=1.2)
    s.text("to 22 ms (22 nF), 100 ms (100 nF)", U4_X + 2.54, n4[1] + 11.0, size=1.1)
    # output to the summing junction through SW3 and 10k; the other pole shorts the feedback (D off)
    s.wire(o4, (o4[0] + 12.7, o4[1]))
    testpoint(o4[0] + 12.7, o4[1], "D", rot=0)
    label("D", o4[0] + 14.2, o4[1])
    SW3_X = o4[0] + 22.86
    a1, a2, a3 = switch("SW3", "D IN / OFF", SW3_X, o4[1], None,
                        "1: D IN, to the sum", "3: D OFF, output shorted to its - input")
    s.wire((o4[0] + 12.7, o4[1]), a2)
    res("R12", "10k", a1[0] + 6.35, a1[1], rot=90)
    s.wire(a1, (a1[0] + 2.54, a1[1]))
    s.wire((a1[0] + 10.16, a1[1]), (SUMX, a1[1]), (SUMX, n3[1]))
    # D off: the switch's lower pole back to the - input node (shorts the feedback)
    RET_D = D_Y + 33.02
    s.wire(a3, (a3[0] + 2.54, a3[1]), (a3[0] + 2.54, RET_D), (n4[0], RET_D), (n4[0], n4[1]))
    s.text("D = -RV3 C dERROR/dt", U4_X - 2.0, D_Y - 29.21, size=1.3, justify=None)
    s.text("differentiator; 470 pF rolls it off above 500 Hz", U4_X - 2.0, D_Y - 26.67, size=1.1, justify=None)
    s.rect(g(76), D_Y - 31.5, g(126), RET_D + 3.0, style="dash", key="box/D")
    s.text("DERIVATIVE  (Fig. 10L.9)", g(76.5), D_Y - 33.3, size=1.3)

    # --- I: the integrator, 1k + 1M trimmer in, 10 uF across, 10k out through SW4 ---
    U5_X = g(90)
    p5, m5, o5 = opamp("U5", U5_X, I_Y)
    ground_plus(p5)
    n5 = inverting_node("U5", m5, I_Y)
    s.wire((EX_D, n2[1]), (EX_D, n5[1]))
    s.junction(EX_D, n2[1])
    res("R17", "1k", EX_D + 7.62, n5[1], rot=90, above=False)
    s.wire((EX_D, n5[1]), (EX_D + 3.81, n5[1]))
    RV4_X = EX_D + 15.24
    s.place(sym("TRIM"), "RV4", "1M", RV4_X, n5[1], rot=90, footprint=fp("TRIM"),
            fields=part_fields("TRIM"), ref_off=(0, 3.4), val_off=(0, 5.6))
    i1, i2, i3 = s.pin("RV4", 1, "1"), s.pin("RV4", 1, "2"), s.pin("RV4", 1, "3")
    s.wire(i3, n5)
    s.wire(i2, (i2[0], i2[1] - 2.54), (RV4_X + 6.35, i2[1] - 2.54), (RV4_X + 6.35, n5[1]))
    s.junction(RV4_X + 6.35, n5[1])
    s.junction(n5[0], n5[1])
    s.text("I GAIN: RC = (1k + RV4) x 10 uF", EX_D + 2.54, n5[1] + 9.0, size=1.2)
    s.text("10 ms to 10 s", EX_D + 2.54, n5[1] + 11.0, size=1.1)
    # the integrating capacitor from the - node to the output
    cap("C8", "10uF", U5_X + 3.81, n5[1], rot=90)
    s.wire(n5, (U5_X, n5[1]))
    c = drop(o5, 10.16, n5[1])
    s.wire((U5_X + 7.62, n5[1]), (c, n5[1]))
    s.wire(o5, (o5[0] + 12.7, o5[1]))
    testpoint(o5[0] + 12.7, o5[1], "I", rot=0)
    label("I", o5[0] + 14.2, o5[1])
    SW4_X = o5[0] + 22.86
    b1, b2, b3 = switch("SW4", "I IN / OFF", SW4_X, o5[1], None,
                        "1: I IN, to the sum", "3: I OFF, capacitor shorted (reset)")
    s.wire((o5[0] + 12.7, o5[1]), b2)
    res("R13", "10k", b1[0] + 6.35, b1[1], rot=90)
    s.wire(b1, (b1[0] + 2.54, b1[1]))
    s.wire((b1[0] + 10.16, b1[1]), (SUMX, b1[1]))
    s.wire((SUMX, a1[1]), (SUMX, b1[1]))
    s.junction(SUMX, a1[1])
    # I off: shorts the capacitor, so the integrator starts from zero when switched in
    RET_I = I_Y + 33.02
    s.wire(b3, (b3[0] + 2.54, b3[1]), (b3[0] + 2.54, RET_I), (n5[0], RET_I), (n5[0], n5[1]))
    s.text("I = -(1/RC) integral of ERROR dt", U5_X - 2.0, I_Y - 29.21, size=1.3, justify=None)
    s.text("integrator; the loop itself keeps it from drifting away", U5_X - 2.0, I_Y - 26.67, size=1.1, justify=None)
    s.rect(g(76), I_Y - 31.5, g(126), RET_I + 3.0, style="dash", key="box/I")
    s.text("INTEGRAL  (Fig. 10L.10)", g(76.5), I_Y - 33.3, size=1.3)

    # ========================================================= motor driver ==
    # U6: SUM into +, split feedback: 10k from the push-pull output (DC), 0.33 uF
    # from its own output (HF), 270 ohm into both bases.  The book's Fig. 10L.3.
    U6_X = g(140)
    p6, m6, o6 = opamp("U6", U6_X, A_Y, vminus_dy=33.02)
    s.wire((g(126), A_Y), (p6[0] - 2.54, A_Y), (p6[0] - 2.54, p6[1]), p6)
    n6 = inverting_node("U6", m6, A_Y)
    cap("C9", "330nF", U6_X + 2.54, n6[1], rot=90)
    s.wire(n6, (U6_X - 1.27, n6[1]))
    c = drop(o6, 10.16, n6[1])
    s.wire((U6_X + 6.35, n6[1]), (c, n6[1]))
    s.junction(n6[0], n6[1])
    DCY = A_Y + 40.64                                   # the DC feedback row, from DRIVE
    s.wire(n6, (n6[0], DCY))
    res("R18", "10k", U6_X + 2.54, DCY, rot=90, above=False)
    s.wire((n6[0], DCY), (U6_X - 1.27, DCY))
    res("R19", "270R", o6[0] + 7.62, o6[1], rot=90)
    s.wire(o6, (o6[0] + 3.81, o6[1]))
    BX = o6[0] + 17.78                                  # the bases' column
    s.wire((o6[0] + 11.43, o6[1]), (BX, o6[1]))
    label("BASES", o6[0] + 12.7, o6[1])
    # the push-pull: NPN above, PNP below, 1 ohm in each emitter, joined at DRIVE
    QX = BX + 7.62
    s.place(sym("NPN_PWR"), "Q1", "MJD44H11", QX, A_Y - 22.86, footprint=fp("NPN_PWR"),
            fields=part_fields("NPN_PWR"), ref_off=(5.6, -3.0), val_off=(5.6, -0.6),
            ref_justify="left", val_justify="left")
    s.place(sym("PNP_PWR"), "Q2", "MJD45H11", QX, A_Y + 22.86, mirror="x", footprint=fp("PNP_PWR"),
            fields=part_fields("PNP_PWR"), ref_off=(5.6, 0.6), val_off=(5.6, 3.0),
            ref_justify="left", val_justify="left")
    q1b, q1c, q1e = s.pin("Q1", 1, "1"), s.pin("Q1", 1, "2"), s.pin("Q1", 1, "3")
    q2b, q2c, q2e = s.pin("Q2", 1, "1"), s.pin("Q2", 1, "2"), s.pin("Q2", 1, "3")
    s.wire(q1b, (BX, q1b[1]), (BX, q2b[1]), q2b)
    s.junction(BX, o6[1])
    s.wire(q1c, (q1c[0], VP_Y))
    s.junction(q1c[0], VP_Y)
    s.wire(q2c, (q2c[0], VM_Y))
    s.junction(q2c[0], VM_Y)
    OX = q1e[0]
    res("R21", "1R", OX, A_Y - 7.62, side="left", footprint=fp("R_2512"))
    res("R22", "1R", OX, A_Y + 7.62, side="left", footprint=fp("R_2512"))
    s.wire(q1e, (OX, A_Y - 11.43))
    s.wire((OX, A_Y - 3.81), (OX, A_Y + 3.81))
    s.wire((OX, A_Y + 11.43), q2e)
    s.junction(OX, A_Y)
    DX0 = OX + 17.78                                    # DRIVE runs right from here
    s.wire((OX, A_Y), (DX0, A_Y))
    # the DC feedback from DRIVE back to U6's - node, under everything, tapped past the limiter
    s.wire((U6_X + 6.35, DCY), (DX0, DCY), (DX0, A_Y))
    s.junction(DX0, A_Y)
    label("DRIVE", OX + 7.0, A_Y)
    s.text("MOTOR DRIVER, gain 1  (Fig. 10L.3)", U6_X - 22.0, A_Y - 33.8, size=1.3)
    # --- the output current limit (not in the book): Q3 senses R21, Q4 senses R22 ---
    LX = OX + 8.89
    s.place(sym("NPN"), "Q3", "2N3904", LX, A_Y - 15.24, footprint=fp("NPN"),
            fields=part_fields("NPN"), ref_off=(3.6, -3.0), val_off=(3.6, -0.6),
            ref_justify="left", val_justify="left")
    s.place(sym("PNP"), "Q4", "2N3906", LX, A_Y + 15.24, mirror="x", footprint=fp("PNP"),
            fields=part_fields("PNP"), ref_off=(3.6, 0.6), val_off=(3.6, 3.0),
            ref_justify="left", val_justify="left")
    q3b, q3c, q3e = s.pin("Q3", 1, "1"), s.pin("Q3", 1, "3"), s.pin("Q3", 1, "2")
    q4b, q4c, q4e = s.pin("Q4", 1, "1"), s.pin("Q4", 1, "3"), s.pin("Q4", 1, "2")
    s.wire((OX, q3b[1]), q3b)
    s.junction(OX, q3b[1])
    s.wire((OX, q4b[1]), q4b)
    s.junction(OX, q4b[1])
    s.wire(q3e, (q3e[0], A_Y), q4e)
    s.junction(q3e[0], A_Y)
    # the steering diodes back to the bases, round the top and bottom
    DX = q3c[0]
    s.place("Device:D", "D5", "1N4148W", DX, A_Y - 27.94, rot=90,
            footprint=fp("DSW"), fields=part_fields("DSW"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.place("Device:D", "D6", "1N4148W", DX, A_Y + 27.94, rot=90,
            footprint=fp("DSW"), fields=part_fields("DSW"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.wire(q3c, (DX, A_Y - 24.13))
    s.wire((DX, A_Y - 31.75), (DX, A_Y - 35.56), (BX, A_Y - 35.56), (BX, q1b[1]))
    s.junction(BX, q1b[1])
    s.wire(q4c, (DX, A_Y + 24.13))
    s.wire((DX, A_Y + 31.75), (DX, A_Y + 35.56), (BX, A_Y + 35.56), (BX, q2b[1]))
    s.junction(BX, q2b[1])
    s.rect(LX - 5.5, A_Y - 38.0, LX + 10.0, A_Y + 38.0, style="dash", key="box/limit")
    s.text("OUTPUT CURRENT LIMIT", LX - 5.5, A_Y + 44.0, size=1.2)
    s.text("not in the book: a safety net.", LX - 5.5, A_Y + 46.4, size=1.0)
    s.text("0.65 V across 1 ohm turns Q3 (Q4)", LX - 5.5, A_Y + 48.4, size=1.0)
    s.text("on and it steals the drive: 0.65 A,", LX - 5.5, A_Y + 50.4, size=1.0)
    s.text("so a shorted MOTOR terminal lives", LX - 5.5, A_Y + 52.4, size=1.0)
    s.text("for seconds; a stall (0.4-0.8 A) is", LX - 5.5, A_Y + 54.4, size=1.0)
    s.text("barely limited.", LX - 5.5, A_Y + 56.4, size=1.0)
    # --- clamps to the rails, the book's snubber, the fuse, the lamp ---------
    CLX = DX0 + 5.08
    s.wire((DX0, A_Y), (CLX, A_Y))
    s.place("Device:D_Schottky", "D3", "SS34", CLX, A_Y - 10.16, rot=270,
            footprint=fp("DSCH"), fields=part_fields("DSCH"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.place("Device:D_Schottky", "D4", "SS34", CLX, A_Y + 10.16, rot=270,
            footprint=fp("DSCH"), fields=part_fields("DSCH"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.wire((CLX, A_Y - 13.97), (CLX, VP_Y))
    s.junction(CLX, VP_Y)
    s.wire((CLX, A_Y - 6.35), (CLX, A_Y + 6.35))
    s.junction(CLX, A_Y)
    s.wire((CLX, A_Y + 13.97), (CLX, VM_Y))
    s.junction(CLX, VM_Y)
    s.text("D3, D4: clamps, so the motor's inductive kick", CLX + 3.0, A_Y - 33.0, size=1.0)
    s.text("stays inside the rails", CLX + 3.0, A_Y - 31.0, size=1.0)
    SNX = CLX + 7.62
    s.wire((CLX, A_Y), (SNX, A_Y))
    res("R20", "10R", SNX, A_Y + 7.62)
    s.wire((SNX, A_Y), (SNX, A_Y + 3.81))
    s.junction(SNX, A_Y)
    cap("C10", "100nF", SNX, A_Y + 15.24)
    gnd(SNX, A_Y + 19.05)
    s.text("snubber", SNX, A_Y + 24.5, size=1.0, justify=None)
    DOX = SNX + 5.08                                    # the DRIVE loop and the DRIVE OUT branch
    s.wire((SNX, A_Y), (DOX, A_Y))
    testpoint(DOX, A_Y, "DRIVE", rot=0)
    FX = SNX + 15.24
    s.wire((DOX, A_Y), (FX - 3.81, A_Y))
    s.place("Device:Polyfuse", "F1", "0.35A", FX, A_Y, rot=90, footprint=fp("PTC"),
            fields=part_fields("PTC"), ref_off=(0, 3.0), val_off=(0, 5.0))
    TPM = FX + 17.78
    s.wire((FX + 3.81, A_Y), (TPM, A_Y))
    testpoint(TPM, A_Y, "MOTOR", rot=0)
    label("MOTOR", TPM + 1.5, A_Y)
    # the tripped lamp: two red LEDs anti-parallel with 1k, across the fuse
    LY = A_Y - 12.7
    TL, TR = FX - 7.62, FX + 13.97
    s.wire((TL, A_Y), (TL, LY))
    s.junction(TL, A_Y)
    s.wire((TR, A_Y), (TR, LY))
    s.junction(TR, A_Y)
    res("R23", "1k", TL + 5.08, LY, rot=90)
    s.wire((TL, LY), (TL + 1.27, LY))
    XJ = TL + 8.89
    LEDX = FX + 6.35
    s.place("Device:LED", "LED3", "RED", LEDX, LY - 2.54, footprint=fp("LED_R"),
            fields=part_fields("LED_R"), ref_off=(0, -2.6), val_off=(0, -4.4), hide_value=True)
    s.place("Device:LED", "LED4", "RED", LEDX, LY + 2.54, rot=180, footprint=fp("LED_R"),
            fields=part_fields("LED_R"), ref_off=(0, 3.2), val_off=(0, 5.0), hide_value=True)
    l3k, l3a = s.pin("LED3", 1, "1"), s.pin("LED3", 1, "2")
    l4k, l4a = s.pin("LED4", 1, "1"), s.pin("LED4", 1, "2")
    s.wire((XJ, LY), (XJ, l3k[1]), l3k)
    s.wire((XJ, LY), (XJ, l4a[1]), l4a)
    s.junction(XJ, LY)
    XK = LEDX + 5.08
    s.wire(l3a, (XK, l3a[1]), (XK, LY))
    s.wire(l4k, (XK, l4k[1]), (XK, LY))
    s.junction(XK, LY)
    s.wire((XK, LY), (TR, LY))
    s.text("MOTOR FUSE: 0.35 A resettable (not in the book)", TL - 4.0, A_Y - 27.0, size=1.2)
    s.text("a stalled motor (0.6 A at full drive) trips it in 5-10 s; the", TL - 4.0, A_Y - 25.0, size=1.0)
    s.text("red lamp lights while it is tripped; it resets when the drive", TL - 4.0, A_Y - 23.0, size=1.0)
    s.text("stops.  The loop runs the motor at 50-150 mA rms.", TL - 4.0, A_Y - 21.0, size=1.0)
    s.rect(CLX - 4.0, A_Y - 35.5, TR + 2.0, A_Y + 30.0, style="dash", key="box/fuse")
    # DRIVE OUT: the push-pull output through 1k to a jack, below the snubber
    J3Y = A_Y + 40.64
    s.wire((DOX, A_Y), (DOX, A_Y + 24.13))
    res("R24", "1k", DOX, A_Y + 27.94, lcsc="1k_1206", footprint=fp("R_1206"))
    s.wire((DOX, A_Y + 31.75), (DOX, J3Y))
    s.place("Connector:Conn_Coaxial", "J3", "BNC", DOX + 5.08, J3Y,
            footprint=fp("BNC"), fields=part_fields("BNC"),
            ref_off=(4.0, -2.6), val_off=(4.0, 0.4), ref_justify="left", val_justify="left")
    s.wire(s.pin("J3", 1, "2"), (DOX + 5.08, J3Y + 7.62))
    gnd(DOX + 5.08, J3Y + 7.62)
    s.text("DRIVE OUT", DOX + 1.0, J3Y + 15.0, size=2.2)
    s.text("the motor's voltage through 1k: ±13 V", DOX + 1.0, J3Y + 17.0, size=1.1)

    # ------------------------------------------------- the plant: motor and pot
    # MOTOR terminal: motor +, motor - (ground), shield (ground); the motor drawn on it
    JM_X = FX + 43.18
    s.place(sym("TERM3"), "J4", "MOTOR + - shield", JM_X, A_Y + 2.54,
            footprint=fp("TERM3"), fields=part_fields("TERM3"), hide_value=True,
            ref_off=(3.0, -1.0), val_off=(3.0, 1.0), ref_justify="left", val_justify="left")
    jm1, jm2, jm3 = s.pin("J4", 1, "1"), s.pin("J4", 1, "2"), s.pin("J4", 1, "3")
    s.wire((TPM, A_Y), jm1)
    s.wire(jm2, (jm2[0] - 2.54, jm2[1]), (jm2[0] - 2.54, jm3[1] + 2.54))
    s.wire(jm3, (jm3[0] - 2.54, jm3[1]))
    s.junction(jm3[0] - 2.54, jm3[1])
    gnd(jm2[0] - 2.54, jm3[1] + 2.54)
    s.text("MOTOR", JM_X + 1.0, A_Y - 3.6, size=2.2)
    s.text("±13 V, 0.65 A max", JM_X - 12.0, A_Y + 14.0, size=1.0)
    s.text("+ makes POSITION rise", JM_X - 12.0, A_Y + 16.0, size=1.0)
    MX = JM_X + 15.24
    s.place("Motor:Motor_DC", "M1", "fader motor", MX, A_Y + 2.54, footprint="",
            in_bom=False, on_board=False, ref_off=(4.0, -1.0), val_off=(4.0, 1.6),
            ref_justify="left", val_justify="left")
    mp, mm = s.pin("M1", 1, "1"), s.pin("M1", 1, "2")
    s.wire(jm1, (jm1[0], A_Y - 10.16), (MX, A_Y - 10.16), mp)
    s.junction(jm1[0], jm1[1])
    s.wire(mm, (MX, mm[1] + 2.54))
    gnd(MX, mm[1] + 2.54)
    # POT terminal below it: 1 (+15 side), 2 wiper, 3 (-15 side); 4.7k ends, 10 uF decoupling
    JP_X = JM_X
    JP_Y = A_Y + 33.02
    s.place(sym("TERM3"), "J5", "POT 1 (+) 2 (wiper) 3 (-)", JP_X, JP_Y,
            footprint=fp("TERM3"), fields=part_fields("TERM3"), hide_value=True,
            ref_off=(3.0, -1.0), val_off=(3.0, 1.0), ref_justify="left", val_justify="left")
    jp1, jp2, jp3 = s.pin("J5", 1, "1"), s.pin("J5", 1, "2"), s.pin("J5", 1, "3")
    PX = JP_X - 15.24
    res("R3", "4.7k", PX, jp1[1] - 10.16)
    rail("+15V", PX, jp1[1] - 13.97)
    s.wire((PX, jp1[1] - 6.35), (PX, jp1[1]), jp1)
    label("POT+", PX + 2.54, jp1[1])
    res("R4", "4.7k", PX, jp3[1] + 10.16)
    rail("-15V", PX, jp3[1] + 13.97, rot=180)
    s.wire(jp3, (PX, jp3[1]), (PX, jp3[1] + 6.35))
    label("POT-", PX + 2.54, jp3[1])
    # C3 hangs from the + end to the left; C4 from the - end to the right, both to ground
    CX3 = PX - 7.62
    s.wire((PX, jp1[1]), (CX3, jp1[1]))
    s.junction(PX, jp1[1])
    cap("C3", "10uF", CX3, jp1[1] + 3.81, side="left")
    gnd(CX3, jp1[1] + 7.62)
    CX4 = PX + 5.08
    s.junction(CX4, jp3[1])
    cap("C4", "10uF", CX4, jp3[1] + 3.81)
    gnd(CX4, jp3[1] + 7.62)
    s.text("POT", JP_X + 1.0, JP_Y - 6.0, size=2.2)
    s.text("the fader's 10k track: 1 at +7.7 V, 3 at -7.7 V, 2 the wiper", JP_X - 9.0, JP_Y + 15.5, size=1.0)
    # the fader's pot, external, drawn under the motor and tied to the terminal pins
    s.place("Device:R_Potentiometer_US", "RV5", "fader 10k", MX, JP_Y, footprint="",
            in_bom=False, on_board=False, ref_off=(6.0, -1.0), val_off=(6.0, 1.6),
            ref_justify="left", val_justify="left")
    f1, f2, f3 = s.pin("RV5", 1, "1"), s.pin("RV5", 1, "2"), s.pin("RV5", 1, "3")
    s.wire(jp1, (jp1[0], jp1[1] - 7.62), (MX, jp1[1] - 7.62), f1)
    s.junction(jp1[0], jp1[1])
    s.wire(jp3, (jp3[0], jp3[1] + 7.62), (MX, jp3[1] + 7.62), f3)
    s.junction(jp3[0], jp3[1])
    # the wiper: the POSITION node, out to the left and down to the loop, and back
    # round from the external pot below everything
    POSX = JP_X - 20.32
    s.wire(jp2, (POSX, jp2[1]), (POSX, FB_Y), (g(44), FB_Y))
    s.wire(f2, (f2[0] + 2.54, f2[1]), (f2[0] + 2.54, JP_Y + 25.4), (POSX, JP_Y + 25.4))
    s.junction(POSX, JP_Y + 25.4)
    label("POSITION", POSX - 15.0, FB_Y)
    testpoint(POSX - 7.62, FB_Y, "POSITION", rot=0)
    s.text("the motorized slide pot (external, on flying", MX - 10.0, JP_Y + 19.0, size=1.0)
    s.text("leads): SparkFun COM-10976 or any fader with", MX - 10.0, JP_Y + 20.8, size=1.0)
    s.text("a 10k track and a 6-11 V motor", MX - 10.0, JP_Y + 22.6, size=1.0)
    s.rect(CX3 - 3.0, A_Y - 13.0, MX + 18.0, JP_Y + 28.0, style="dash", key="box/plant")
    s.text("THE PLANT: motor and pot  (Fig. 10L.1)", CX3 - 2.5, A_Y - 14.8, size=1.3)

    # U7: the position buffer for the jack (keeps a 50 ohm scope off the loop)
    U7_X = POSX + 15.24
    U7_Y = I_Y
    p7, m7, o7 = opamp("U7", U7_X, U7_Y)
    s.wire((POSX, p7[1]), p7)
    s.junction(POSX, p7[1])
    n7 = inverting_node("U7", m7, U7_Y)
    c = drop(o7, 10.16, n7[1])
    s.wire(n7, (c, n7[1]))
    res("R25", "1k", o7[0] + 7.62, o7[1], rot=90, lcsc="1k_1206", footprint=fp("R_1206"))
    s.wire(o7, (o7[0] + 3.81, o7[1]))
    s.wire((o7[0] + 11.43, o7[1]), (o7[0] + 17.78, o7[1]))
    s.place("Connector:Conn_Coaxial", "J2", "BNC", o7[0] + 22.86, o7[1],
            footprint=fp("BNC"), fields=part_fields("BNC"),
            ref_off=(4.0, -2.6), val_off=(4.0, 0.4), ref_justify="left", val_justify="left")
    s.wire(s.pin("J2", 1, "2"), (o7[0] + 22.86, o7[1] + 7.62))
    gnd(o7[0] + 22.86, o7[1] + 7.62)
    s.text("POSITION OUT", o7[0] + 14.0, o7[1] - 8.0, size=2.2)
    s.text("the pot's voltage, buffered: ±7.7 V, 1k out", o7[0] + 14.0, o7[1] - 6.2, size=1.1)
    s.text("follower", U7_X - 2.0, U7_Y - 26.67, size=1.1, justify=None)

    # ========================================================== the loop switch
    # SW2: common to the difference amplifier's - input (through R7); 3 = POSITION
    # (closed loop), 1 = ground (open loop, the book's first test)
    SW2_X = g(44)
    SW2_Y = n1[1]
    c1_, c2_, c3_ = switch("SW2", "LOOP", SW2_X, SW2_Y, "y",
                           "upper pole 1: OPEN (- input grounded)", "lower pole 3: CLOSED (position)", below=True)
    s.wire(c2_, (n1[0] - 8.89, c2_[1]))
    s.wire((g(44), FB_Y), (c3_[0] - 2.54, FB_Y), (c3_[0] - 2.54, c3_[1]), c3_)
    s.wire(c1_, (c1_[0] - 7.62, c1_[1]), (c1_[0] - 7.62, c1_[1] + 7.62))
    gnd(c1_[0] - 7.62, c1_[1] + 7.62)
    label("LOOP", c2_[0] + 1.5, c2_[1])

    # ========================================================== rails ========
    PR = g(221)
    s.wire((KX, VP_Y), (PR, VP_Y))
    s.wire((KX, VM_Y), (PR, VM_Y))
    rail("+15V", g(30), VP_Y - 3.81, to=VP_Y)
    s.junction(g(30), VP_Y)
    rail("-15V", g(30), VM_Y + 3.81, rot=180, to=VM_Y)
    s.junction(g(30), VM_Y)
    testpoint(g(190), VP_Y, "+15V", rot=0)
    testpoint(g(190), VM_Y, "-15V", rot=180, dy=3.2)

    # ====================================================== power entry ======
    J6_X = g(224)
    s.place(sym("TERM3"), "J6", "+15 / GND / -15", J6_X, A_Y + 2.54,
            footprint=fp("TERM3"), fields=part_fields("TERM3"), hide_value=True,
            ref_off=(3.0, -1.0), val_off=(3.0, 1.0), ref_justify="left", val_justify="left")
    j6a, j6b, j6c = s.pin("J6", 1, "1"), s.pin("J6", 1, "2"), s.pin("J6", 1, "3")
    s.text("POWER", J6_X - 2.0, A_Y - 7.0, size=3.0)
    s.text("+15 V, GND, -15 V from a bench", J6_X - 14.0, A_Y + 13.5, size=1.0)
    s.text("supply; 1 A for the motor", J6_X - 14.0, A_Y + 15.5, size=1.0)
    DP_X = g(216)
    s.place("Device:D_Schottky", "D1", "SS34", DP_X, g(38), rot=270,
            footprint=fp("DSCH"), fields=part_fields("DSCH"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.wire(j6a, (DP_X, j6a[1]), (DP_X, g(38) + 3.81))
    s.wire((DP_X, g(38) - 3.81), (DP_X, VP_Y))
    s.junction(DP_X, VP_Y)
    label("+15V_IN", DP_X, j6a[1] - 12.7)
    flag(DP_X - 5.08, j6a[1] - 5.08, to_x=DP_X)
    DM_X = g(214)
    s.place("Device:D_Schottky", "D2", "SS34", DM_X, g(112), rot=270,
            footprint=fp("DSCH"), fields=part_fields("DSCH"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.wire(j6c, (DM_X, j6c[1]), (DM_X, g(112) - 3.81))
    s.wire((DM_X, g(112) + 3.81), (DM_X, VM_Y))
    s.junction(DM_X, VM_Y)
    label("-15V_IN", DM_X, j6c[1] + 12.7)
    flag(DM_X - 5.08, j6c[1] + 5.08, to_x=DM_X)
    s.wire(j6b, (j6b[0] - 2.54, j6b[1]), (j6b[0] - 2.54, j6b[1] + 7.62))
    gnd(j6b[0] - 2.54, j6b[1] + 7.62)
    flag(j6b[0] - 7.62, j6b[1] + 5.08, to_x=j6b[0] - 2.54)
    flag(g(205), VP_Y - 2.54, VP_Y)                   # the rails themselves are sources too
    flag(g(205), VM_Y + 2.54, VM_Y)
    # bulk and bypass on each rail, and a lamp per rail
    BXc = g(209)
    s.place("Device:C_Polarized_US", "C11", "100uF", BXc, g(34), footprint=fp("CBULK"),
            fields=part_fields("CBULK"), ref_off=(2.6, -1.4), val_off=(2.6, 1.4),
            ref_justify="left", val_justify="left")
    s.wire((BXc, VP_Y), (BXc, g(34) - 3.81))
    s.wire((BXc, g(34) + 3.81), (BXc, g(38)))
    gnd(BXc, g(38))
    s.junction(BXc, VP_Y)
    cap("C13", "100nF", BXc - 7.62, g(34))
    s.wire((BXc - 7.62, VP_Y), (BXc - 7.62, g(34) - 3.81))
    s.wire((BXc - 7.62, g(34) + 3.81), (BXc - 7.62, g(38)))
    gnd(BXc - 7.62, g(38))
    s.junction(BXc - 7.62, VP_Y)
    s.place("Device:C_Polarized_US", "C12", "100uF", BXc, g(118), footprint=fp("CBULK"),
            fields=part_fields("CBULK"), ref_off=(2.6, -1.4), val_off=(2.6, 1.4),
            ref_justify="left", val_justify="left")
    s.wire((BXc, VM_Y), (BXc, g(118) + 3.81))
    s.wire((BXc, g(118) - 3.81), (BXc, g(114)))
    gnd(BXc, g(114), up=True)
    s.junction(BXc, VM_Y)
    cap("C14", "100nF", BXc - 7.62, g(118))
    s.wire((BXc - 7.62, VM_Y), (BXc - 7.62, g(118) + 3.81))
    s.wire((BXc - 7.62, g(118) - 3.81), (BXc - 7.62, g(114)))
    gnd(BXc - 7.62, g(114), up=True)
    s.junction(BXc - 7.62, VM_Y)
    LX2 = PR
    res("R26", "10k", LX2, g(34))
    s.wire((LX2, VP_Y), (LX2, g(34) - 3.81))
    s.place("Device:LED", "LED1", "GREEN", LX2, g(40), rot=90, footprint=fp("LED"),
            fields=part_fields("LED"), ref_off=(2.8, -1.4), val_off=(2.8, 1.4),
            ref_justify="left", val_justify="left")
    s.wire((LX2, g(34) + 3.81), s.pin("LED1", 1, "2"))
    s.wire(s.pin("LED1", 1, "1"), (LX2, g(44)))
    gnd(LX2, g(44))
    s.text("+15 V present", LX2 + 2.8, g(34) + 4.6, size=1.2)
    res("R27", "10k", LX2, g(118))
    s.wire((LX2, VM_Y), (LX2, g(118) + 3.81))
    s.place("Device:LED", "LED2", "GREEN", LX2, g(112), rot=90, footprint=fp("LED"),
            fields=part_fields("LED"), ref_off=(2.8, -1.4), val_off=(2.8, 1.4),
            ref_justify="left", val_justify="left")
    s.wire((LX2, g(118) - 3.81), s.pin("LED2", 1, "1"))
    s.wire(s.pin("LED2", 1, "2"), (LX2, g(108)))
    gnd(LX2, g(108), up=True)
    s.text("-15 V present", LX2 + 2.8, g(118) - 3.6, size=1.2)

    # ================================================== probe grounds ========
    for x in (g(40), g(80), g(130), g(180)):
        testpoint(x, g(130), "GND", rot=0, dx=1.8, dy=-3.0)
        s.wire((x, g(130)), (x, g(130.5)))
        gnd(x, g(130.5))
    s.text("ground loops for the scope's clip", g(40) + 3.5, g(130) + 0.4, size=1.1)

    # ================================================== mechanical ===========
    for i in range(4):
        s.place(sym("MH"), f"MH{i + 1}", "MountingHole", g(200 + 4 * i), g(10),
                footprint=fp("MH"), in_bom=False, ref_off=(0, -3.5), val_off=(0, 3.5),
                hide_value=True)
    s.text("M3 mounting holes, one per corner", g(198), g(14), size=1.2)

    # ================================================== the story ============
    note([f"{parts.BOARD_NAME.upper()}",
          "",
          "Lab 10L of Learning the Art of Electronics (Hayes & Horowitz, 2016): a potentiometer sets a target position, a DC motor",
          "drives a second potentiometer to match it, and the controller is the book's home-made 'pseudo op-amp' of modest, adjustable",
          "gain, with the derivative and the integral of the error summed in.  The board is the book's Fig. 10L.10 with every amplifier its",
          "own LM321 (the single LM358), the book's MJE3055/2955 as DPAK MJD44H11/45H11, and its resistor substitution boxes as trimmers.",
          "",
          "Why a home-made op-amp: the motor integrates (voltage in, position out: -90 degrees from DC), so an ordinary op-amp's own",
          "-90 degrees would make -180 at a few hertz.  The pseudo op-amp has gain 1 to 101 and no phase shift of its own.",
          f"Simulated as drawn (sim/pid_sim.py, the fader modelled from its data sheet): P only rings at {R.get('f_nat_hz', 11):.0f} Hz when the gain",
          f"nears 100; D equal to P there wants RC = 1 / 2 pi f = {R.get('rc_d_ms', 14):.0f} ms (RV3 near {R.get('rv3_k', 640):.0f}k with 22 nF), and then gain 100 settles",
          f"in {R.get('pd_gain100', {}).get('settle_s', 0.07)*1e3:.0f} ms with {R.get('pd_gain100', {}).get('overshoot_pct', 1):.0f} % overshoot.  I removes the residual error at low P gain."],
         g(13), g(8), size=1.5, pitch=3.1)

    # ================================================== the notes band =======
    col = [g(13), g(52), g(94), g(136), g(180)]
    note(["TARGET",
          "Knob or jack, on the TARGET SOURCE switch.  The knob's",
          "6.8k ends keep it to ±6.4 V, inside what the motor pot",
          "can reach (±7.7 V): a target the loop can always meet.",
          "A ±0.5 V square wave at 0.2 Hz from a generator on the",
          "jack gives repeatable steps.  TARGET IN ±12 V max.",
          "",
          "LOOP (SW2)",
          "CLOSED: the pot's voltage into the difference amplifier.",
          "OPEN: its - input grounded, so the motor runs to an end",
          "stop as the knob leaves zero (the book's first test).",
          "Watch the fuse lamp: a stall trips it."],
         col[0], NOTE_Y)
    note(["PSEUDO OP-AMP  (U1, U2, U3)",
          "U1 takes TARGET - POSITION with four 100k.  U2 inverts",
          "it so P, D and I all arrive inverted at U3, which sums",
          "them through 10k each and multiplies by RV2's",
          "(10k + RV2)/10k = 1 to 101: the P GAIN.  All three op-amps",
          "work at low closed-loop gain, so the chain has no phase",
          "shift where the loop's crossover is (a few hertz).",
          "At P gain 1.5 the loop is stable and slow; near 20 it",
          "overshoots; near 100 (P only) it oscillates: the period",
          "of that 'natural oscillation' sets D below.",
          "",
          "Op-amps are drawn + on top: that is how the SOT-23-5 sits."],
         col[1], NOTE_Y)
    note(["DERIVATIVE  (U4, SW3, SW5)",
          "D = -RV3 C dERROR/dt, rolled off above 500 Hz by the",
          "470 pF.  Set RV3 C to 1/6 of the natural period: for",
          "the slide pot (T of 40-90 ms) that is 6-14 ms, 300k-",
          "640k with the 22 nF; for the book's rotary motor-pot",
          "(T 0.6 s) use 100 nF and 1M.  SW5 picks the capacitor,",
          "SW3 puts D into the sum or shorts it out.",
          "",
          "INTEGRAL  (U5, SW4)",
          "I = -(1/RC) integral ERROR dt, RC = (1k + RV4) x 10 uF.",
          "OFF shorts the capacitor, so I starts from zero.  I",
          "drives the residual error to zero; too much I rings."],
         col[2], NOTE_Y)
    note(["MOTOR DRIVER  (U6, Q1, Q2)",
          "The book's Fig. 10L.3: the op-amp drives the push-pull",
          "through 270 ohm and the 10k takes the feedback from the",
          "motor side, so crossover distortion is inside the loop;",
          "the 0.33 uF feeds the op-amp's own output straight back",
          "so the phase-shifting transistors are bypassed at high",
          "frequency (split feedback, Lab 9L).  10 ohm + 0.1 uF snub",
          "the brush hash.  Output ±13 V; the motor is rated 10 V,",
          "6-11 V running, and sees full drive only in a step.",
          "",
          "CURRENT LIMIT and FUSE: not in the book.  1 ohm and a",
          "small transistor per half hold a short to 0.65 A; the",
          "0.35 A PTC opens a stall in seconds and resets itself."],
         col[3], NOTE_Y)
    note(["THE PLANT",
          "Any motorized fader with a 10k track and a 6-11 V motor.",
          "Wire POT 1 to the track end that must read +7.7 V, 3 to",
          "the other, 2 to the wiper; MOTOR + and - so that a",
          "positive drive moves the wiper toward POT 1.  If the",
          "loop runs away, swap the two motor wires.  The second",
          "track and the touch pin of the SparkFun fader stay unused.",
          "POWER: ±15 V, 1 A (the motor's stall current).",
          "Series Schottkys against a reversed supply; 100 uF a",
          "rail for the motor's pulses; a green LED per rail.",
          "Quiescent about 10 mA.  100 nF at every op-amp pin."],
         col[4], NOTE_Y)
    return s


if __name__ == "__main__":
    s = build()
    added = s.add_missing_junctions()
    if added:
        print(f"  auto-placed {added} junction(s) where wires meet end-to-middle")
    bad = s.check_grid()
    if bad:
        print(f"  !! {len(bad)} off-grid endpoint(s):")
        for what, pt in bad[:12]:
            print(f"       {what} at {pt}")
        raise SystemExit("off-grid endpoints would confuse KiCad's connectivity")
    s.write(OUT)
    print(f"  wrote {os.path.relpath(OUT)}")
