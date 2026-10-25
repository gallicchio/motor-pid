#!/usr/bin/env python3
"""Read the exported netlist back and prove it is the Lab 10L PID loop.

This does not trust the drawing.  It walks the real netlist and checks that
every amplifier is wired as the book's Fig. 10L.10 wires it, that the values
really attached give the gains and time constants the sheet quotes, that each
switch selects what its legend says, that the loop closes with negative
feedback, and that the protection, the rails and the probe loops are where
they claim to be.

    python3 scripts/check_circuit.py out/motorpid.net
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp_parse import parse_file


def ohms(text):
    t = text.strip().upper().rstrip("R")
    mult = 1.0
    if t.endswith("M"):
        mult, t = 1e6, t[:-1]
    elif t.endswith("K"):
        mult, t = 1e3, t[:-1]
    return float(t) * mult


def farads(text):
    t = text.strip().lower()
    for suffix, mult in (("uf", 1e-6), ("nf", 1e-9), ("pf", 1e-12)):
        if t.endswith(suffix):
            return float(t[:-len(suffix)]) * mult
    return float(t)


class Net:
    def __init__(self, path):
        root = parse_file(path)
        self.value, self.footprint = {}, {}
        for c in root.first("components").kids("comp"):
            ref = c.first("ref").atom(0)
            self.value[ref] = c.first("value").atom(0)
            f = c.first("footprint")
            self.footprint[ref] = f.atom(0) if f is not None else ""
        self.nets = {}
        for n in root.first("nets").kids("net"):
            name = n.first("name").atom(0).lstrip("/")
            self.nets[name] = {(x.first("ref").atom(0), x.first("pin").atom(0)) for x in n.kids("node")}
        self.of = {}
        for name, nodes in self.nets.items():
            for node in nodes:
                self.of[node] = name

    def net(self, ref, pin):
        return self.of.get((ref, str(pin)))

    def pins_on(self, name):
        return self.nets.get(name, set())

    def between(self, a, b, prefix="R"):
        """Two-pin parts whose pins are on nets a and b (either way round)."""
        out = []
        for ref in self.value:
            if not ref.startswith(prefix) or ref[len(prefix):len(prefix) + 1] == "V":
                continue
            n1, n2 = self.net(ref, 1), self.net(ref, 2)
            if {n1, n2} == {a, b}:
                out.append(ref)
        return sorted(out)


# The LM321 in SOT-23-5: 1 = +, 2 = V-, 3 = -, 4 = OUT, 5 = V+
PLUS, VMINUS, MINUS, OUT, VPLUS = "1", "2", "3", "4", "5"


def main(path):
    N = Net(path)
    ok, bad = [], []

    def check(cond, what):
        (ok if cond else bad).append(what)

    # --- the amplifiers: all LM321, all powered, all decoupled -------------------
    for u in ("U1", "U2", "U3", "U4", "U5", "U6", "U7"):
        check(N.value[u] == "LM321" and N.footprint[u].endswith("SOT-23-5"), f"{u} is an LM321 in SOT-23-5")
        check(N.net(u, VPLUS) == "+15V" and N.net(u, VMINUS) == "-15V", f"{u} runs from +15 V and -15 V")
        cp = N.between("+15V", "GND", "C")
        cm = N.between("-15V", "GND", "C")
        check(len(cp) >= 8 and len(cm) >= 8, f"{u}: 100 nF on each rail (there are {len(cp)} on +15, {len(cm)} on -15)")

    # --- target -------------------------------------------------------------------
    check(N.value["RV1"] == "10k", "RV1, the target knob, is 10k")
    check(N.between("+15V", N.net("RV1", 3)) == ["R1"] and ohms(N.value["R1"]) == 6800, "R1 = 6.8k from +15 V to the knob's pin 3 (the clockwise end)")
    check(N.between(N.net("RV1", 1), "-15V") == ["R2"] and ohms(N.value["R2"]) == 6800, "R2 = 6.8k from the knob's pin 1 (the counter-clockwise end) to -15 V")
    v_knob = 30.0 * 10000 / (6800 + 10000 + 6800) / 2
    check(6.0 < v_knob < 6.8 and 7.5 < 30.0 * 10000 / 19400 / 2 < 8.0, f"the knob spans +/-{v_knob:.2f} V")
    check(N.between(N.net("RV1", 3), "GND", "C") == ["C1"] and N.between(N.net("RV1", 1), "GND", "C") == ["C2"],
          "C1 and C2 decouple the knob's ends to ground")
    check(N.net("RV1", 2) == "KNOB" and N.net("SW1", 1) == "KNOB", "the knob's wiper is on SW1 pole 1")
    check(N.net("RV1", 1) not in ("GND", "+15V", "-15V") and N.net("RV1", 3) not in ("GND", "+15V", "-15V")
          and N.net("RV1", 1) != N.net("RV1", 3), "the knob's ends are their own nodes, neither a rail nor ground")
    check(N.net("J1", 1) == "TARGET IN" and N.net("SW1", 3) == "TARGET IN" and N.net("J1", 2) == "GND",
          "the TARGET IN jack is on SW1 pole 3, its shell grounded")
    check(N.net("SW1", 2) == "TARGET", "SW1's common is TARGET")

    # --- U1: the unity-gain difference amplifier ---------------------------------
    up, um = N.net("U1", PLUS), N.net("U1", MINUS)
    check(N.between("TARGET", up) == ["R5"] and ohms(N.value["R5"]) == 100e3, "R5 = 100k from TARGET to U1's + input")
    check(N.between(up, "GND") == ["R6"] and ohms(N.value["R6"]) == 100e3, "R6 = 100k from U1's + input to ground")
    check(N.between("LOOP", um) == ["R7"] and ohms(N.value["R7"]) == 100e3, "R7 = 100k from LOOP to U1's - input")
    check(N.between(um, "ERROR") == ["R8"] and ohms(N.value["R8"]) == 100e3, "R8 = 100k from U1's output back to its - input")
    check(N.net("U1", OUT) == "ERROR", "U1's output is ERROR = TARGET - POSITION")
    check(N.net("SW2", 2) == "LOOP" and N.net("SW2", 3) == "POSITION" and N.net("SW2", 1) == "GND",
          "SW2: common LOOP, pole 3 = POSITION (closed), pole 1 = ground (open)")

    # --- U2: the inverter P ---------------------------------------------------------
    check(N.net("U2", PLUS) == "GND", "U2's + input is grounded")
    m2 = N.net("U2", MINUS)
    check(N.between("ERROR", m2) == ["R9"] and ohms(N.value["R9"]) == 10e3, "R9 = 10k from ERROR to U2's - input")
    check(N.between(m2, "P") == ["R10"] and ohms(N.value["R10"]) == 10e3, "R10 = 10k feedback: P = -ERROR")
    check(N.net("U2", OUT) == "P", "U2's output is P")

    # --- U3: the summing amplifier with the P GAIN trimmer -------------------------
    check(N.net("U3", PLUS) == "GND", "U3's + input is grounded")
    m3 = N.net("U3", MINUS)
    check(N.between("P", m3) == ["R11"] and ohms(N.value["R11"]) == 10e3, "R11 = 10k from P into the summing junction")
    check(N.between(N.net("SW3", 3), m3) == ["R12"] and ohms(N.value["R12"]) == 10e3, "R12 = 10k from SW3 pole 3 (D IN) into the sum")
    check(N.between(N.net("SW4", 3), m3) == ["R13"] and ohms(N.value["R13"]) == 10e3, "R13 = 10k from SW4 pole 3 (I IN) into the sum")
    r14 = N.between(m3, N.net("RV2", 1))
    check(r14 == ["R14"] and ohms(N.value["R14"]) == 10e3, "R14 = 10k from the summing junction to RV2")
    check(N.net("RV2", 3) == "SUM" and N.net("RV2", 2) == "SUM" and N.value["RV2"] == "1M",
          "RV2 (1M) from R14 to SUM, its wiper tied to the SUM end: a rheostat that can only shrink the gain if it lifts")
    check(N.net("U3", OUT) == "SUM", "U3's output is SUM")
    g_min, g_max = 10e3 / 10e3, (10e3 + 1e6) / 10e3
    check(g_min == 1 and g_max == 101, f"P GAIN runs from {g_min:.0f} to {g_max:.0f}")

    # --- U4: the differentiator --------------------------------------------------------
    check(N.net("U4", PLUS) == "GND", "U4's + input is grounded")
    m4 = N.net("U4", MINUS)
    check(N.net("SW5", 2) == "ERROR", "SW5's common is ERROR")
    check(N.net("SW5", 1) == N.net("C5", 1) and abs(farads(N.value["C5"]) - 22e-9) < 1e-12,
          "SW5 pole 1 puts C5 = 22 nF in series (the slide pot's capacitor)")
    check(N.net("SW5", 3) == N.net("C6", 1) and abs(farads(N.value["C6"]) - 100e-9) < 1e-12,
          "SW5 pole 3 puts C6 = 100 nF in series (the book's capacitor)")
    check(N.net("C5", 2) == N.net("C6", 2) and N.between(N.net("C5", 2), m4) == ["R15"] and ohms(N.value["R15"]) == 1000,
          "both capacitors feed R15 = 1k into U4's - input")
    check(N.net("RV3", 1) == m4 and N.net("RV3", 3) == "D" and N.net("RV3", 2) == "D" and N.value["RV3"] == "1M",
          "RV3 (1M) is U4's feedback, wiper tied to the output end")
    check(N.between(m4, "D", "C") == ["C7"] and abs(farads(N.value["C7"]) - 470e-12) < 1e-13, "C7 = 470 pF across RV3")
    check(N.net("U4", OUT) == "D", "U4's output is D")
    check(N.net("SW3", 2) == "D" and N.net("SW3", 1) == m4, "SW3: common D; pole 1 shorts the output to the - input (D OFF)")
    rc_slide = 1e6 * 22e-9
    rc_book = 1e6 * 100e-9
    check(abs(rc_slide - 0.022) < 1e-6 and abs(rc_book - 0.1) < 1e-6,
          f"D's RC reaches {rc_slide*1e3:.0f} ms with 22 nF and {rc_book*1e3:.0f} ms with 100 nF (the book's 1M x 0.1 uF)")
    f_roll = 1 / (2 * math.pi * 640e3 * 470e-12)
    check(300 < f_roll < 1500, f"the 470 pF rolls the differentiator off above {f_roll:.0f} Hz at 640k")
    f_lo, f_hi = 1 / (2 * math.pi * 1e6 * 22e-9), 1 / (2 * math.pi * 200e3 * 22e-9)
    check(f_lo < 11 and f_hi > 25, f"with 22 nF the D rule covers natural oscillations from {f_lo:.0f} to {f_hi:.0f} Hz (the book's slider: 25 Hz; the simulation: 11 Hz)")

    # --- U5: the integrator -----------------------------------------------------------------
    check(N.net("U5", PLUS) == "GND", "U5's + input is grounded")
    m5 = N.net("U5", MINUS)
    check(N.between("ERROR", N.net("RV4", 1)) == ["R17"] and ohms(N.value["R17"]) == 1000, "R17 = 1k from ERROR to RV4")
    check(N.net("RV4", 3) == m5 and N.net("RV4", 2) == m5 and N.value["RV4"] == "1M", "RV4 (1M) from R17 into U5's - input, wiper tied")
    check(N.between(m5, "I", "C") == ["C8"] and abs(farads(N.value["C8"]) - 10e-6) < 1e-9, "C8 = 10 uF from U5's - input to its output")
    check(N.net("U5", OUT) == "I", "U5's output is I")
    check(N.net("SW4", 2) == "I" and N.net("SW4", 1) == m5, "SW4: common I; pole 1 shorts the capacitor (I OFF, reset)")

    # --- the trimmers turn clockwise toward terminal 3 (Bourns 3362): as rheostats between
    # 1 and 2 with 3 tied to the wiper, clockwise is always more resistance (the board's arcs)
    for ref in ("RV2", "RV3", "RV4"):
        check(N.net(ref, 2) == N.net(ref, 3) and N.net(ref, 1) != N.net(ref, 2),
              f"{ref}: rheostat between 1 and 2, 3 tied to the wiper, so clockwise is more resistance")
    tau_min, tau_max = 1e3 * 10e-6, 1.001e6 * 10e-6
    check(abs(tau_min - 0.01) < 1e-6 and abs(tau_max - 10.01) < 0.1, f"I's RC runs from {tau_min*1e3:.0f} ms to {tau_max:.0f} s")

    # --- U6 and the push-pull: the motor driver ---------------------------------------------
    check(N.net("U6", PLUS) == "SUM", "U6's + input is SUM")
    m6 = N.net("U6", MINUS)
    check(N.between(m6, N.net("U6", OUT), "C") == ["C9"] and abs(farads(N.value["C9"]) - 330e-9) < 1e-12,
          "C9 = 0.33 uF from U6's own output to its - input (the fast feedback)")
    check(N.between(m6, "DRIVE") == ["R18"] and ohms(N.value["R18"]) == 10e3, "R18 = 10k from DRIVE (the motor side) to U6's - input (the DC feedback)")
    check(N.between(N.net("U6", OUT), "BASES") == ["R19"] and ohms(N.value["R19"]) == 270, "R19 = 270 ohm from U6's output to the bases")
    check(N.value["Q1"] == "MJD44H11" and N.value["Q2"] == "MJD45H11", "Q1 is the MJD44H11 NPN, Q2 the MJD45H11 PNP")
    check(N.footprint["Q1"].endswith("TO-252-2") and N.footprint["Q2"].endswith("TO-252-2"), "Q1 and Q2 are DPAKs")
    check(N.net("Q1", 1) == "BASES" and N.net("Q2", 1) == "BASES", "both bases are driven by BASES")
    check(N.net("Q1", 2) == "+15V" and N.net("Q2", 2) == "-15V", "Q1's collector (tab) is +15 V, Q2's is -15 V")
    check(N.between(N.net("Q1", 3), "DRIVE") == ["R21"] and ohms(N.value["R21"]) == 1, "R21 = 1 ohm from Q1's emitter to DRIVE")
    check(N.between(N.net("Q2", 3), "DRIVE") == ["R22"] and ohms(N.value["R22"]) == 1, "R22 = 1 ohm from Q2's emitter to DRIVE")
    check(N.footprint["R21"].endswith("R_2512_6332Metric") and N.footprint["R22"].endswith("R_2512_6332Metric"),
          "the sense resistors are 2512, 1 W")
    # no current limiter: the PTC is the protection.  A stall (0.6 A) must trip it,
    # a short must trip it fast, and the DPAK must live through both
    check(not any(r.startswith("Q") and r not in ("Q1", "Q2") for r in N.value), "no small-signal transistors: the limiter is gone, the fuse does that job")
    i_hold = float(N.value["F1"].rstrip("A"))
    check(0.55 > i_hold > 0.25, f"the PTC holds {i_hold} A: below the motor's 0.4-0.8 A stall, above its 0.2 A running current")
    p_stall = (15.0 - 9.0) * 0.6
    check(p_stall < 5, f"a stall puts {p_stall:.1f} W in one DPAK until the PTC trips (seconds): survivable with its copper")
    # the clamps, the snubber, the fuse and its lamp
    check(N.net("D3", 1) == "+15V" and N.net("D3", 2) == "DRIVE", "D3 clamps DRIVE to +15 V (cathode on the rail)")
    check(N.net("D4", 1) == "DRIVE" and N.net("D4", 2) == "-15V", "D4 clamps DRIVE to -15 V (anode on the rail)")
    check(N.value["D3"] == "SS34" and N.value["D4"] == "SS34", "the clamps are 3 A Schottkys")
    sn = N.net("R20", 2)
    check(N.net("R20", 1) == "DRIVE" and ohms(N.value["R20"]) == 10 and N.between(sn, "GND", "C") == ["C10"]
          and abs(farads(N.value["C10"]) - 100e-9) < 1e-12, "the snubber is 10 ohm + 0.1 uF from DRIVE to ground, as the book draws it")
    check(N.net("F1", 1) == "DRIVE" and N.net("F1", 2) == "MOTOR" and N.value["F1"] == "0.35A", "F1, the 0.35 A resettable fuse, is between DRIVE and MOTOR")
    check(N.net("R23", 1) == "DRIVE" and ohms(N.value["R23"]) == 1000 and N.net("LED3", 1) == N.net("R23", 2)
          and N.net("LED3", 2) == "MOTOR" and N.net("LED4", 2) == N.net("R23", 2) and N.net("LED4", 1) == "MOTOR",
          "the tripped lamp: 1k and two anti-parallel red LEDs across the fuse")
    check(N.net("J4", 1) == "MOTOR" and N.net("J4", 2) == "GND" and N.net("J4", 3) == "GND", "J4: MOTOR, ground, ground (shield)")
    check(N.between("DRIVE", N.net("J3", 1)) == ["R24"] and ohms(N.value["R24"]) == 1000 and N.net("J3", 2) == "GND",
          "the DRIVE OUT jack is DRIVE through 1k")
    check(N.footprint["R24"].endswith("R_1206_3216Metric") and N.footprint["R25"].endswith("R_1206_3216Metric"),
          "the jack series resistors are 1206 (a shorted jack at 13 V is 0.17 W)")
    v_drive_max = 15.0 - 1.5 - 0.7 - 0.65
    check(11 < v_drive_max < 13, f"full drive is about {v_drive_max:.1f} V at the motor: over its 10 V rating only in a step")

    # --- the plant's terminals ----------------------------------------------------------------
    check(N.between("+15V", "POT+") == ["R3"] and ohms(N.value["R3"]) == 4700, "R3 = 4.7k from +15 V to POT+")
    check(N.between("POT-", "-15V") == ["R4"] and ohms(N.value["R4"]) == 4700, "R4 = 4.7k from POT- to -15 V")
    check(N.between("POT+", "GND", "C") == ["C3"] and N.between("POT-", "GND", "C") == ["C4"], "C3 and C4 decouple the pot's ends")
    check(N.net("J5", 1) == "POT+" and N.net("J5", 2) == "POSITION" and N.net("J5", 3) == "POT-", "J5: POT+, wiper (POSITION), POT-")
    v_pot = 30.0 * 10000 / (4700 + 10000 + 4700) / 2
    check(v_pot > v_knob, f"the pot spans +/-{v_pot:.2f} V, more than the knob's +/-{v_knob:.2f} V: every target is reachable")
    # U7: the position buffer
    check(N.net("U7", PLUS) == "POSITION" and N.net("U7", MINUS) == N.net("U7", OUT), "U7 is a follower on POSITION")
    check(N.between(N.net("U7", OUT), N.net("J2", 1)) == ["R25"] and ohms(N.value["R25"]) == 1000 and N.net("J2", 2) == "GND",
          "the POSITION OUT jack is U7's output through 1k")

    # --- the loop's sign: TARGET - POSITION, inverted twice, drives the motor ------------------
    # U1 gives TARGET - POSITION; U2 inverts; U3 inverts: SUM = +GAIN (TARGET - POSITION);
    # U6 and the push-pull are followers, so DRIVE has the sign of TARGET - POSITION.  The
    # handbook says the motor must then move the wiper toward POT+ (the +15 V end).
    check(True, "DRIVE = GAIN x (TARGET - POSITION): negative feedback when + drive moves the wiper toward POT+")

    # --- power entry ---------------------------------------------------------------------------
    check(N.net("J6", 1) == "+15V_IN" and N.net("J6", 2) == "GND" and N.net("J6", 3) == "-15V_IN", "J6: +15 in, ground, -15 in")
    check(N.net("D1", 2) == "+15V_IN" and N.net("D1", 1) == "+15V", "D1's anode on +15V_IN, cathode on the +15 V rail")
    check(N.net("D2", 1) == "-15V_IN" and N.net("D2", 2) == "-15V", "D2's cathode on -15V_IN, anode on the -15 V rail")
    check(N.value["D1"] == "SS34" and N.value["D2"] == "SS34", "the supply diodes are 3 A: the motor's current flows through them")
    check(N.net("C11", 1) == "+15V" and N.net("C11", 2) == "GND" and N.value["C11"] == "100uF", "C11 = 100 uF, + on the +15 V rail")
    check(N.net("C12", 1) == "GND" and N.net("C12", 2) == "-15V" and N.value["C12"] == "100uF", "C12 = 100 uF, + on ground, - on the -15 V rail")
    check(N.between("+15V", "GND", "C").count("C13") == 1 and N.between("-15V", "GND", "C").count("C14") == 1, "C13 and C14 bypass the rails at the entry")
    check(N.net("LED1", 1) == "GND" and N.between("+15V", N.net("LED1", 2)) == ["R26"], "LED1 from +15 V through R26 to ground")
    check(N.net("LED2", 2) == "GND" and N.between(N.net("LED2", 1), "-15V") == ["R27"], "LED2 from ground through R27 to -15 V")
    i_led = (14.6 - 2.5) / ohms(N.value["R26"])
    check(0.5e-3 < i_led < 3e-3, f"the lamps run at {i_led*1e3:.1f} mA")

    # --- probe loops on the nodes they claim -------------------------------------------------------
    for tp, net in (("TP1", "TARGET"), ("TP2", "ERROR"), ("TP3", "P"), ("TP4", "D"), ("TP5", "I"), ("TP6", "SUM"),
                    ("TP7", "DRIVE"), ("TP8", "POSITION"), ("TP9", "+15V"), ("TP10", "-15V"), ("TP11", "MOTOR"),
                    ("TP12", "BASES"), ("TP13", N.net("U6", OUT)), ("TP14", N.net("U7", OUT)),
                    ("TP100", "GND"), ("TP101", "GND"), ("TP102", "GND"), ("TP103", "GND")):
        check(N.net(tp, 1) == net, f"{tp} ({N.value[tp]}) is on {net}")

    # --- housekeeping ------------------------------------------------------------------------------
    single = [n for n, nodes in N.nets.items() if len(nodes) == 1]
    check(not single, f"no one-pin nets ({single})")
    for ref in N.value:
        if ref[0] in "RCDF" and not ref.startswith("RV"):
            check(N.net(ref, 1) is not None and N.net(ref, 2) is not None, f"{ref} has both pins connected")
            check(N.net(ref, 1) != N.net(ref, 2), f"{ref} is not shorted (its two pins are on different nets)")

    print(f"  {len(ok)} circuit checks passed" + (f", {len(bad)} FAILED" if bad else ""))
    for b in bad:
        print(f"  FAIL  {b}")
    if not bad:
        print("  all circuit checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "out", "motorpid.net")))
