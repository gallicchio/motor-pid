#!/usr/bin/env python3
"""Simulate the PID loop AS DRAWN: the SPICE deck is built from the netlist
KiCad exported (out/motorpid.net), so a wire drawn to the wrong pin shows up
here as a loop that runs away, not as a surprise on the bench.

Each part of the netlist becomes a SPICE element: resistors and capacitors
as they are, the diodes and transistors with their models, every LM321 as a
behavioural macro (1 MHz, 0.4 V/us, output to V+ - 1.5 V), the slide
switches as the positions a scenario sets, the trimmers as the resistance a
scenario sets, the fuse as its cold resistance, and the three terminals as
the world outside the board: a bench supply on J6, the fader's motor on J4
and its track on J5 (a behavioural model: 15 ohm, back EMF, an effective
inertia, stiction and end stops, scaled to the TOP-UP MD100 data sheet).

    python3 sim/pid_sim.py           prints the results and writes sim/results.json
    python3 sim/pid_sim.py --plots   also draws docs/images/sim-*.png

Needs libngspice (ctypes); matplotlib only for the plots.
"""
import json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from ngspice_lib import NgSpice
from sexp_parse import parse_file

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
NETLIST = os.path.join(ROOT, "out", "motorpid.net")
RESULTS = os.path.join(ROOT, "sim", "results.json")
IMAGES = os.path.join(ROOT, "docs", "images")

# ---------------------------------------------------------------- the plant --
# TOP-UP MD100AM2B (SparkFun COM-10976): 10 V rated, 6-11 V, stall 0.4-0.8 A at
# 10 V, at least 200 mm/s at 10 V, 100 mm of travel, 10 k track.  On the board
# the track sits between +7.73 V and -7.73 V (4.7 k to each rail), so position
# is measured in "pot volts": 0.1546 V per mm, 30.9 V/s at full speed.
V_END = 30.0 * 10e3 / (4.7e3 + 10e3 + 4.7e3) / 2        # 7.73 V at the track's ends
R_MOTOR = 15.0                                          # ohm: 10 V / 0.67 A stall
L_MOTOR = 1e-3
KE = (10.0 - 0.05 * R_MOTOR) / (200.0 * V_END * 2 / 100.0)   # V per (pot volt / s): 0.30
KT = KE                                                 # the same constant the other way (effective)
TAU_M = 0.015                                           # s: mechanical time constant (reflected inertia)
MASS = TAU_M * KE * KT / R_MOTOR                         # effective mass in these units
I_STICK = 0.05                                          # A needed to break the slider loose
F_STICK = KT * I_STICK
B_VISC = KT * 0.05 / (200.0 * V_END * 2 / 100.0)          # 50 mA at full speed, no load

MODELS = [
    ".model Q3904 NPN(IS=1E-14 VAF=100 Bf=300 IKF=0.4 XTB=1.5 BR=4 CJC=4E-12 CJE=8E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12 ITF=1 VTF=2 XTF=3)",
    ".model Q3906 PNP(IS=1E-14 VAF=100 Bf=200 IKF=0.4 XTB=1.5 BR=4 CJC=4.5E-12 CJE=10E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12 ITF=1 VTF=2 XTF=3)",
    ".model QD44 NPN(IS=5E-13 VAF=120 Bf=100 IKF=6 XTB=1.5 BR=5 CJC=1.2E-10 CJE=3E-10 RB=1 RC=0.05 RE=0.03 TF=5E-9 TR=5E-8)",
    ".model QD45 PNP(IS=5E-13 VAF=120 Bf=100 IKF=6 XTB=1.5 BR=5 CJC=1.2E-10 CJE=3E-10 RB=1 RC=0.05 RE=0.03 TF=6E-9 TR=5E-8)",
    ".model D4148 D(IS=2.52e-9 RS=0.568 N=1.752 CJO=4e-12 M=0.4 TT=20e-9 BV=75)",
    ".model DSS34 D(IS=2e-6 RS=0.04 N=1.1 CJO=250e-12 M=0.4 BV=40)",
    ".model DLEDR D(IS=1e-20 N=1.8 RS=1.5 CJO=30e-12)",
    ".model DLEDG D(IS=1e-23 N=2.2 RS=2 CJO=30e-12)",
    # the LM321: gm into a dominant pole, slew-limited, output clamped to the rails
    ".subckt LM321 inp inn out vp vn",
    "Rin inp inn 1e9",
    "Bg 0 x I = { min(max(1e-3*(V(inp)-V(inn)), -64u), 64u) - 1e-3*(V(x) - min(max(V(x), V(vn)-1), V(vp)+1)) }",
    "Rx x 0 1e7",
    "Cx x 0 159p",
    "Bo o 0 V = { min(max(V(x), V(vn)+0.1), V(vp)-1.5) }",
    "Ro o out 100",
    ".ends",
]


def spice_name(net):
    if net in ("GND", "/GND"):
        return "0"
    n = net.lstrip("/").replace("+", "P").replace("-", "M")
    n = re.sub(r"[^A-Za-z0-9_]", "_", n).strip("_")
    return "n_" + n


def value_si(text):
    t = text.strip()
    m = re.match(r"([0-9.]+)\s*([a-zA-Z]*)", t)
    v, unit = float(m.group(1)), m.group(2)
    mult = {"": 1, "R": 1, "k": 1e3, "K": 1e3, "M": 1e6, "u": 1e-6, "uF": 1e-6, "n": 1e-9, "nF": 1e-9,
            "p": 1e-12, "pF": 1e-12, "F": 1}.get(unit, None)
    if mult is None:
        raise ValueError(text)
    return v * mult


class Deck:
    def __init__(self, netlist=NETLIST):
        root = parse_file(netlist)
        self.value = {}
        for c in root.first("components").kids("comp"):
            self.value[c.first("ref").atom(0)] = c.first("value").atom(0)
        self.net = {}
        for n in root.first("nets").kids("net"):
            name = n.first("name").atom(0)
            for x in n.kids("node"):
                self.net[(x.first("ref").atom(0), x.first("pin").atom(0))] = spice_name(name)

    def pin(self, ref, p):
        return self.net[(ref, str(p))]

    def lines(self, sw, trim, knob=0.0, source="pulse(0 1 0.1 1m 1m 10 20)", loop_open=False,
              motor_short=False, pot_pos=0.0, stall_at=None, ic_zero=()):
        """The deck for one scenario.  sw: {"SW1": 1 or 3, ...}; trim: {"RV2": ohms, ...}."""
        self._ic_zero = tuple(ic_zero)
        L = []
        for ref, val in sorted(self.value.items()):
            kind = re.match(r"[A-Z]+", ref).group(0)
            if kind in ("TP", "MH"):
                continue
            if kind == "R":
                L.append(f"R{ref} {self.pin(ref, 1)} {self.pin(ref, 2)} {value_si(val):g}")
            elif kind == "C":
                L.append(f"C{ref} {self.pin(ref, 1)} {self.pin(ref, 2)} {value_si(val):g}")
            elif kind == "RV":
                if ref == "RV1":                       # the knob: pin 3 is the + end, pin 1 the - end, 2 the wiper
                    f = (1.0 + knob) / 2.0             # knob = +1 puts the wiper at the + end (pin 3)
                    L.append(f"R{ref}a {self.pin(ref, 1)} {self.pin(ref, 2)} {max(1.0, 10e3 * f):g}")
                    L.append(f"R{ref}b {self.pin(ref, 2)} {self.pin(ref, 3)} {max(1.0, 10e3 * (1 - f)):g}")
                else:                                  # a rheostat: 1 to 3, the wiper tied to 3
                    L.append(f"R{ref} {self.pin(ref, 1)} {self.pin(ref, 3)} {max(1.0, trim[ref]):g}")
            elif kind == "D":
                model = {"1N4148W": "D4148", "SS34": "DSS34"}[val]
                L.append(f"D{ref} {self.pin(ref, 2)} {self.pin(ref, 1)} {model}")      # 2 = A, 1 = K
            elif kind == "LED":
                model = "DLEDR" if val == "RED" else "DLEDG"
                L.append(f"D{ref} {self.pin(ref, 2)} {self.pin(ref, 1)} {model}")
            elif kind == "Q":
                if val in ("MJD44H11", "MJD45H11"):    # DPAK: 1 = B, 2 = C, 3 = E
                    L.append(f"Q{ref} {self.pin(ref, 2)} {self.pin(ref, 1)} {self.pin(ref, 3)} "
                             f"{'QD44' if val == 'MJD44H11' else 'QD45'}")
                else:                                  # SOT-23: 1 = B, 2 = E, 3 = C
                    L.append(f"Q{ref} {self.pin(ref, 3)} {self.pin(ref, 1)} {self.pin(ref, 2)} "
                             f"{'Q3904' if val == '2N3904' else 'Q3906'}")
            elif kind == "U":
                L.append(f"X{ref} {self.pin(ref, 1)} {self.pin(ref, 3)} {self.pin(ref, 4)} "
                         f"{self.pin(ref, 5)} {self.pin(ref, 2)} LM321")
            elif kind == "SW":
                pos = sw[ref]
                on, off = (1, 3) if pos == 1 else (3, 1)
                L.append(f"R{ref}on {self.pin(ref, 2)} {self.pin(ref, on)} 0.05")
                L.append(f"R{ref}off {self.pin(ref, 2)} {self.pin(ref, off)} 1e9")
            elif kind == "F":
                L.append(f"R{ref} {self.pin(ref, 1)} {self.pin(ref, 2)} 0.3")
            elif kind == "J":
                if ref == "J1":
                    L.append(f"Vtarget {self.pin(ref, 1)} 0 {source}")
                elif ref in ("J2", "J3"):
                    L.append(f"R{ref}scope {self.pin(ref, 1)} 0 1e6")
                elif ref == "J4":
                    L += self.motor(self.pin(ref, 1), motor_short, stall_at)
                elif ref == "J5":
                    L += self.track(self.pin(ref, 1), self.pin(ref, 2), self.pin(ref, 3), pot_pos)
                elif ref == "J6":
                    L.append(f"Vpos {self.pin(ref, 1)}_s 0 15")
                    L.append(f"Rpos {self.pin(ref, 1)}_s {self.pin(ref, 1)} 0.3")
                    L.append(f"Vneg {self.pin(ref, 3)}_s 0 -15")
                    L.append(f"Rneg {self.pin(ref, 3)}_s {self.pin(ref, 3)} 0.3")
            else:
                raise ValueError(f"no SPICE for {ref} ({val})")
        return L

    def motor(self, node, short, stall_at):
        """The fader's motor between `node` and ground, and its mechanics.

        vel is the slider's speed in pot volts per second, pos its position in
        pot volts (+/- V_END at the end stops).  The force is KT * I less viscous
        and Coulomb friction; past an end stop a stiff spring and a heavy damper
        hold it; `stall_at` clamps the slider wherever it is (a finger on it)."""
        L = []
        if short:
            L.append(f"Rshort {node} 0 0.01")
        L.append(f"Rm {node} m1 {R_MOTOR}")
        L.append(f"Lm m1 m2 {L_MOTOR}")
        L.append(f"Bemf m2 0 V = {{ {KE} * V(vel) }}")
        stop = (f"((V(pos) > {V_END}) ? ( -200*(V(pos)-{V_END}) - 5*V(vel) ) : 0)"
                f" + ((V(pos) < {-V_END}) ? ( -200*(V(pos)+{V_END}) - 5*V(vel) ) : 0)")
        hold = f" - 5*V(vel) - 200*(V(pos)-({stall_at}))" if stall_at is not None else ""
        L.append(f"Bfor 0 vel I = {{ ( {KT}*I(Bemf) - {B_VISC}*V(vel) - {F_STICK}*tanh(V(vel)/0.05) + {stop}{hold} ) / {MASS} }}")
        L.append("Cvel vel 0 1")
        L.append("Rvel vel 0 1e12")
        L.append("Bpos 0 pos I = { V(vel) }")
        L.append("Cpos pos 0 1")
        L.append("Rpos2 pos 0 1e12")
        return L

    def track(self, top, wiper, bottom, pos0):
        """The 10 k track: the wiper at pos (pot volts) between its ends."""
        return [f"Rta {top} {wiper} R = {{ 10e3 * (0.5 - min(max(V(pos), {-V_END}), {V_END}) / {2 * V_END}) + 1 }}",
                f"Rtb {wiper} {bottom} R = {{ 10e3 * (0.5 + min(max(V(pos), {-V_END}), {V_END}) / {2 * V_END}) + 1 }}",
                f".ic V(pos)={pos0}"] + [f".ic V({spice_name(n)})=0" for n in self._ic_zero]


def run(deck_lines, tstop, tstep=20e-6, extra_cmds=()):
    ng = NgSpice()
    ng.circuit(["pid loop"] + MODELS + deck_lines + [".option method=gear reltol=2e-3 abstol=1e-9 vntol=1e-5",
                                                       f".tran {tstep} {tstop} 0 {tstep*5}", ".end"])
    for c in extra_cmds:
        ng.cmd(c)
    ng.cmd("run")
    errors = [l for l in ng.log if l.startswith("stderr Error") or "aborted" in l or "Timestep too small" in l]
    if errors:
        raise RuntimeError("\n".join(errors[:10]))
    return ng


def step_metrics(t, y, t0, y0, y1):
    """Overshoot (%), 2 % settling time and the period of any ringing after a step at t0."""
    import numpy as np
    t, y = np.asarray(t), np.asarray(y)
    sel = t >= t0
    tt, yy = t[sel], y[sel]
    span = y1 - y0
    over = (yy.max() - y1) / span * 100 if span > 0 else (y1 - yy.min()) / abs(span) * 100
    err = np.abs(yy - y1) / abs(span)
    outside = np.where(err > 0.02)[0]
    ts = (tt[outside[-1]] - t0) if len(outside) else 0.0
    # period from the zero crossings of the error about the final value, in the first second
    e = yy - y1
    zc = np.where(np.diff(np.sign(e)) != 0)[0]
    zc = zc[tt[zc] < t0 + 1.0]
    period = float(2 * np.mean(np.diff(tt[zc]))) if len(zc) > 3 else None
    # sustained: the last 0.4 s still swings by more than 5 % of the step
    tail = yy[tt > tt[-1] - 0.4]
    sustained = (tail.max() - tail.min()) > 0.05 * abs(span) if len(tail) else False
    return dict(overshoot_pct=float(over), settle_s=float(ts), period_s=period, sustained=bool(sustained))


def main(plots=False):
    import numpy as np
    D = Deck()
    R = {"date": "2026-10-24", "plant": dict(v_end=round(V_END, 3), r_motor=R_MOTOR, ke_v_per_vps=round(KE, 4),
                                             tau_m_s=TAU_M, i_stick_a=I_STICK)}
    base_sw = {"SW1": 3, "SW2": 3, "SW3": 1, "SW4": 1, "SW5": 1}      # D and I off (pole 1), loop closed, the jack
    base_trim = {"RV2": 0.0, "RV3": 640e3, "RV4": 100e3}
    curves = {}

    def gain_trim(g):
        return {"RV2": (g - 1) * 10e3, "RV3": base_trim["RV3"], "RV4": base_trim["RV4"]}

    # ---- quiescent point, closed loop, target 0 -----------------------------------
    ng = run(D.lines(base_sw, gain_trim(10), source="dc 0"), 0.3)
    t = ng.vec("time")
    op = {}
    for name in ("TARGET", "ERROR", "P", "SUM", "DRIVE", "MOTOR", "POSITION", "+15V", "-15V", "D", "I", "BASES"):
        try:
            op[name] = round(ng.vec("v(" + spice_name(name) + ")")[-1], 3)
        except KeyError:
            pass
    R["op"] = op
    R["i_supply_ma"] = round(-ng.vec("i(vpos)")[-1] * 1e3, 1)
    print("quiescent:", op, f"supply {R['i_supply_ma']} mA")

    # ---- P only: steps at several gains ----------------------------------------------
    P = {}
    for g in (1.5, 5, 10, 22, 50, 100):
        ng = run(D.lines(base_sw, gain_trim(g)), 1.6)
        t = np.array(ng.vec("time")); pos = np.array(ng.vec("v(" + spice_name("POSITION") + ")"))
        drv = np.array(ng.vec("v(" + spice_name("DRIVE") + ")"))
        m = step_metrics(t, pos, 0.1, 0.0, 1.0)
        m["drive_peak_v"] = float(np.abs(drv).max())
        m["residual_v"] = float(1.0 - pos[-1])
        im = np.array(ng.vec("i(bemf)"))
        sel = t > 0.1
        m["i_motor_rms_a"] = float(np.sqrt(np.mean(im[sel] ** 2)))
        m["i_motor_peak_a"] = float(np.abs(im).max())
        P[str(g)] = m
        curves[f"p{g}"] = (t, pos, drv)
        print(f"P only, gain {g:5.1f}: overshoot {m['overshoot_pct']:5.1f} %, settles {m['settle_s']*1e3:6.0f} ms, "
              f"period {m['period_s'] and round(m['period_s']*1e3, 1)} ms, sustained {m['sustained']}, "
              f"drive peak {m['drive_peak_v']:.1f} V, residual {m['residual_v']*1e3:.0f} mV, "
              f"motor {m['i_motor_rms_a']*1e3:.0f} mA rms / {m['i_motor_peak_a']*1e3:.0f} peak")
    R["p_only"] = P
    # the natural oscillation: the ringing period right after the step at the
    # highest gain (the slow hunt that stiction makes at lower gains is not it)
    m = P["100"]
    f_nat, g_nat = (1.0 / m["period_s"] if m["period_s"] else 25.0), 100
    rc_d = 1.0 / (2 * math.pi * f_nat)
    R["f_nat_hz"] = round(f_nat, 1)
    R["g_nat"] = g_nat
    R["rc_d_ms"] = round(rc_d * 1e3, 2)
    R["rv3_k"] = round(rc_d / 22e-9 / 1e3, 0)
    print(f"natural oscillation near {f_nat:.1f} Hz at gain {g_nat}: RC_D = {rc_d*1e3:.1f} ms, RV3 = {R['rv3_k']:.0f}k with 22 nF")

    # ---- P + D at the book's moderate gain, D set by the rule, too little and too much ---
    PD = {}
    g = 22
    for label, rv3 in (("none", None), ("rule", rc_d / 22e-9), ("third", rc_d / 22e-9 / 3), ("triple", 3 * rc_d / 22e-9)):
        sw = dict(base_sw, SW3=(1 if rv3 is None else 3))
        trim = gain_trim(g)
        if rv3 is not None:
            trim["RV3"] = min(rv3, 1e6)
        ng = run(D.lines(sw, trim), 1.6)
        t = np.array(ng.vec("time")); pos = np.array(ng.vec("v(" + spice_name("POSITION") + ")"))
        drv = np.array(ng.vec("v(" + spice_name("DRIVE") + ")"))
        m = step_metrics(t, pos, 0.1, 0.0, 1.0)
        m["rv3_k"] = None if rv3 is None else round(min(rv3, 1e6) / 1e3)
        PD[label] = m
        curves[f"pd_{label}"] = (t, pos, drv)
        print(f"P {g} + D {label:6s} (RV3 {m['rv3_k']}k): overshoot {m['overshoot_pct']:5.1f} %, settles {m['settle_s']*1e3:5.0f} ms")
    R["pd"] = PD
    # high P gain rescued by D
    sw = dict(base_sw, SW3=3)
    trim = gain_trim(100); trim["RV3"] = min(rc_d / 22e-9, 1e6)
    ng = run(D.lines(sw, trim), 1.6)
    t = np.array(ng.vec("time")); pos = np.array(ng.vec("v(" + spice_name("POSITION") + ")"))
    m = step_metrics(t, pos, 0.1, 0.0, 1.0)
    R["pd_gain100"] = m
    curves["pd100"] = (t, pos, np.array(ng.vec("v(" + spice_name("DRIVE") + ")")))
    print(f"P 100 + D: overshoot {m['overshoot_pct']:.1f} %, settles {m['settle_s']*1e3:.0f} ms, sustained {m['sustained']}")

    # ---- I: the residual error at low gain, and its removal ------------------------------
    PI = {}
    for label, sw4, rv4 in (("P only", 1, 100e3), ("with I", 3, 100e3), ("too much I", 3, 5e3)):
        sw = dict(base_sw, SW3=3, SW4=sw4)
        trim = gain_trim(5); trim["RV3"] = min(rc_d / 22e-9, 1e6); trim["RV4"] = rv4
        ng = run(D.lines(sw, trim, source="pulse(0 1 0.1 1m 1m 10 20)", ic_zero=("I",)), 8.0)
        t = np.array(ng.vec("time")); pos = np.array(ng.vec("v(" + spice_name("POSITION") + ")"))
        m = step_metrics(t, pos, 0.1, 0.0, 1.0)
        m["residual_mv"] = float((1.0 - pos[-1]) * 1e3)
        m["rv4_k"] = rv4 / 1e3
        PI[label] = m
        curves[f"pi_{label}"] = (t, pos, np.array(ng.vec("v(" + spice_name("I") + ")")))
        print(f"P 5 {label:10s} (RV4 {rv4/1e3:.0f}k): residual {m['residual_mv']:6.0f} mV, overshoot {m['overshoot_pct']:.1f} %, sustained {m['sustained']}")
    R["pi"] = PI

    # ---- the driver: a stall, and a short ------------------------------------------------
    sw = dict(base_sw, SW2=1)                             # loop open: the motor runs to the stop
    ng = run(D.lines(sw, gain_trim(22), source="dc 1"), 1.0)
    i_m = np.array(ng.vec("i(bemf)")); v_m = np.array(ng.vec("v(" + spice_name("MOTOR") + ")"))
    vc = np.array(ng.vec("v(" + spice_name("+15V") + ")")) - np.array(ng.vec("v(" + spice_name("DRIVE") + ")"))
    R["stall"] = dict(i_motor_a=round(float(abs(i_m[-1])), 3), v_motor=round(float(v_m[-1]), 2),
                      p_q1_w=round(float(abs(i_m[-1]) * vc[-1]), 2), p_motor_w=round(float(abs(i_m[-1] * v_m[-1])), 2),
                      i_peak_a=round(float(np.abs(i_m).max()), 2))
    print("open loop, end stop:", R["stall"])
    ng = run(D.lines(sw, gain_trim(22), source="dc 1", motor_short=True), 0.3)
    i_s = np.array(ng.vec("i(vpos)"))
    drv = np.array(ng.vec("v(" + spice_name("DRIVE") + ")"))
    R["short"] = dict(i_short_a=round(float(abs(i_s[-1])), 3), v_drive=round(float(drv[-1]), 2),
                      p_q1_w=round(float(abs(i_s[-1]) * (15 - drv[-1])), 1))
    print("MOTOR shorted to ground:", R["short"])
    # the slew of the motor drive, large step, closed loop at gain 22 with D
    sw = dict(base_sw, SW3=3)
    trim = gain_trim(22); trim["RV3"] = min(rc_d / 22e-9, 1e6)
    ng = run(D.lines(sw, trim, source="pulse(-5 5 0.1 1m 1m 10 20)"), 1.0)
    t = np.array(ng.vec("time")); pos = np.array(ng.vec("v(" + spice_name("POSITION") + ")"))
    drv = np.array(ng.vec("v(" + spice_name("DRIVE") + ")")); i_m = np.array(ng.vec("i(bemf)"))
    m = step_metrics(t, pos, 0.1, -5.0, 5.0)
    R["big_step"] = dict(overshoot_pct=round(m["overshoot_pct"], 1), settle_s=round(m["settle_s"], 3),
                         drive_peak_v=round(float(np.abs(drv).max()), 2), i_peak_a=round(float(np.abs(i_m).max()), 2))
    curves["big"] = (t, pos, drv)
    print("10 V step with P 22 + D:", R["big_step"])

    json.dump(R, open(RESULTS, "w"), indent=1, sort_keys=True)
    print(f"wrote {os.path.relpath(RESULTS, ROOT)}")
    if plots:
        draw(curves, R)
    return R


def draw(curves, R):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(IMAGES, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})

    fig, ax = plt.subplots(2, 1, figsize=(7, 5.2), sharex=True)
    for g, c in ((1.5, "#4C78A8"), (10, "#54A24B"), (22, "#F58518"), (50, "#B279A2"), (100, "#E45756")):
        t, pos, drv = curves[f"p{g}"]
        ax[0].plot(t, pos, color=c, lw=1.2, label=f"P gain {g:g}")
        ax[1].plot(t, drv, color=c, lw=0.8)
    ax[0].axhline(1.0, color="k", lw=0.6, ls="--")
    ax[0].set_ylabel("position (pot volts)"); ax[0].set_title("P only: a 1 V step in the target (simulated as drawn)")
    ax[0].legend(loc="lower right", fontsize=8, ncol=3)
    ax[1].set_ylabel("motor drive (V)"); ax[1].set_xlabel("time (s)"); ax[1].set_xlim(0.05, 1.0)
    fig.tight_layout(); fig.savefig(os.path.join(IMAGES, "sim-p-only.png"), dpi=130); plt.close(fig)

    fig, ax = plt.subplots(1, 1, figsize=(7, 3.4))
    for label, c, txt in (("none", "#E45756", "P 22, no D"), ("third", "#F58518", "D a third of the rule"),
                          ("rule", "#54A24B", "D by the rule: RC = 1/(2 pi f)"), ("triple", "#4C78A8", "three times the rule")):
        t, pos, drv = curves[f"pd_{label}"]
        ax.plot(t, pos, color=c, lw=1.2, label=txt)
    t, pos, drv = curves["pd100"]
    ax.plot(t, pos, color="#333333", lw=1.0, ls=":", label="P 100 + D by the rule")
    ax.axhline(1.0, color="k", lw=0.6, ls="--")
    ax.set_xlim(0.05, 0.8); ax.set_xlabel("time (s)"); ax.set_ylabel("position (pot volts)")
    ax.set_title("Adding D: the derivative lets the gain go up"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(IMAGES, "sim-pd.png"), dpi=130); plt.close(fig)

    fig, ax = plt.subplots(2, 1, figsize=(7, 5.2), sharex=True)
    for label, c in (("P only", "#E45756"), ("with I", "#54A24B"), ("too much I", "#4C78A8")):
        t, pos, iv = curves[f"pi_{label}"]
        ax[0].plot(t, pos, color=c, lw=1.2, label=f"P 5 + D, {label}")
        ax[1].plot(t, iv, color=c, lw=0.9)
    ax[0].axhline(1.0, color="k", lw=0.6, ls="--")
    ax[0].set_ylabel("position (pot volts)"); ax[0].set_title("Adding I at low P gain: the residual error goes away")
    ax[0].legend(fontsize=8)
    ax[1].set_ylabel("integrator output I (V)"); ax[1].set_xlabel("time (s)"); ax[1].set_xlim(0.05, 8.0)
    fig.tight_layout(); fig.savefig(os.path.join(IMAGES, "sim-pid.png"), dpi=130); plt.close(fig)

    fig, ax = plt.subplots(2, 1, figsize=(7, 4.6), sharex=True)
    t, pos, drv = curves["big"]
    ax[0].plot(t, pos, color="#4C78A8", lw=1.2); ax[0].set_ylabel("position (pot volts)")
    ax[0].set_title("A 10 V step (end to end) with P 22 + D: the drive saturates, the motor slews")
    ax[1].plot(t, drv, color="#F58518", lw=1.0); ax[1].set_ylabel("motor drive (V)"); ax[1].set_xlabel("time (s)")
    ax[1].set_xlim(0.05, 1.0)
    fig.tight_layout(); fig.savefig(os.path.join(IMAGES, "sim-big-step.png"), dpi=130); plt.close(fig)
    print(f"wrote docs/images/sim-*.png")


if __name__ == "__main__":
    main(plots="--plots" in sys.argv)
