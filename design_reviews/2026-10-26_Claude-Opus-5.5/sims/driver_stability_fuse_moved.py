"""driver_stability.py again, after the round's fixes were applied: the fuse now
sits between the emitter resistors' junction (pp) and DRIVE, with the clamps
and the snubber on pp and the feedback (R18), DRIVE OUT and the motor on DRIVE.
Same 10 ns steps, plus the PTC at its 0.2 and 1.7 ohm limits and a 10x probe
on DRIVE.  The flat part of each step (30-54 us), less a quadratic trend, is
what an oscillation would show in.  Models are the repository's sim/pid_sim.py.
Run from the review directory:  python3 sims/driver_stability_fuse_moved.py"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim")); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
from ngspice_lib import NgSpice
import pid_sim as P

def deck(case):
    snub = case.get("snubber", True)
    L_m = case.get("L_motor", 1e-3)
    probe = case.get("probe", None)          # node to load with a 10x probe (15 pF + 10 Meg)
    lines = [
        "Vp vp 0 14.78", "Vn vn 0 -14.78",
        f"Vin sum 0 PULSE({case['v0']} {case['v1']} 5u 20n 20n 50u 100u)",
        "Xu6 sum inn u6out vp vn LM321",
        "R18 drive inn 10k", "C9 u6out inn 330n",
        "R19 u6out bases 270",
        "Q1 vp bases e1 QD44", "Q2 vn bases e2 QD45",
        "R21 e1 pp 1", "R22 e2 pp 1",
        "D3 pp vp DSS34", "D4 vn pp DSS34",
        "Rptc pp drive " + str(case.get("r_ptc", 1.0)),
        f"Lm drive m2 {L_m}", "Rm m2 0 14",         # stalled: no back EMF
        "Rdrvout drive dout 1k", "Ccoax dout 0 100p",  # DRIVE OUT with a metre of coax
    ]
    if snub:
        lines += ["R20 pp sn 10", "C10 sn 0 100n"]
    if probe:
        lines += [f"Cpr {probe} 0 15p", f"Rpr {probe} 0 10Meg"]
    return lines

def run(case, tstop=100e-6, tstep=10e-9):
    ng = NgSpice()
    ng.circuit(["driver"] + P.MODELS + deck(case) + [".option method=gear reltol=1e-3",
               f".tran {tstep} {tstop} 0 {tstep}", ".end"])
    ng.cmd("run")
    t = np.array(ng.vec("time")); out = {k: np.array(ng.vec(f"v({k})")) for k in ("u6out", "bases", "drive", "inn")}
    return t, out

CASES = [
    dict(name="step 2 -> 3 V, as built", v0=2.0, v1=3.0),
    dict(name="step -0.3 -> +0.3 V (through the crossover)", v0=-0.3, v1=0.3),
    dict(name="no snubber", v0=2.0, v1=3.0, snubber=False),
    dict(name="motor 10 mH", v0=2.0, v1=3.0, L_motor=10e-3),
    dict(name="10x probe on BASES", v0=2.0, v1=3.0, probe="bases"),
    dict(name="10x probe on U6 OUT", v0=2.0, v1=3.0, probe="u6out"),
    dict(name="PTC at 1.7 ohm (its R1max)", v0=2.0, v1=3.0, r_ptc=1.7),
    dict(name="PTC at 0.2 ohm, motor 10 mH", v0=2.0, v1=3.0, r_ptc=0.2, L_motor=10e-3),
    dict(name="10x probe on DRIVE", v0=2.0, v1=3.0, probe="drive"),
]
for c in CASES:
    t, o = run(c)
    sel = (t > 5e-6) & (t < 50e-6)
    d = o["drive"][sel]; final = float(o["drive"][(t > 45e-6) & (t < 50e-6)].mean())
    over = (d.max() - final) / abs(c["v1"] - c["v0"]) * 100
    w = (t > 30e-6) & (t < 54e-6)
    res = []
    for k in ("drive", "bases", "u6out"):
        r = o[k][w] - np.polyval(np.polyfit(t[w], o[k][w], 2), t[w])
        res.append(f"{k} {(r.max() - r.min()) * 1e3:.3f} mV")
    print(f"{c['name']:44s} DRIVE final {final:+.3f} V, overshoot {over:5.1f} %; flat part, detrended: " + ", ".join(res))
