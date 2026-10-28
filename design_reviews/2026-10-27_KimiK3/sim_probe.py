#!/usr/bin/env python3
"""Probe simulations for the review: run scenarios on the board's netlist and
report simultaneous node values, to answer:

S1. The 10 V step: what are U6's output pin, BASES, DRIVE and the motor
    current at the DRIVE peak and at the current peak?  Does the sim's own
    LM321 output clamp (rail - 1.5 V) permit the reported 13.68 V / 0.79 A?
S2. The driver's own loop (U6 + push-pull + split feedback): stable with a
    scope probe on BASES or U6 OUT (12 pF x10, 100 pF x1)?  With and without
    the snubber?
S3. Integrator windup at the end stop: loop closed, TARGET beyond the stop,
    I IN; then TARGET returns in range: how long before the slider moves?
S4. The D stage's output with a probe on it: ringing after a step?
S5. Wiper dropout for 20 ms mid-run: twitch or runaway?

Run from the copy's project dir:  python3 ../sim_probe.py
Writes nothing outside this directory.
"""
import os, sys
import numpy as np

PROJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project")
sys.path.insert(0, os.path.join(PROJ, "sim"))
sys.path.insert(0, os.path.join(PROJ, "scripts"))
os.chdir(PROJ)

import pid_sim
from pid_sim import Deck, run, spice_name, MODELS
from ngspice_lib import NgSpice

D = Deck()
BASE_SW = dict(pid_sim.BASE_SW) if hasattr(pid_sim, "BASE_SW") else None


def get_base_sw():
    # recover the base switch dict the way main() builds it
    import inspect, re
    src = inspect.getsource(pid_sim.main)
    m = re.search(r"base_sw\s*=\s*dict\(([^)]*)\)", src)
    print("base_sw from source:", m.group(1) if m else "NOT FOUND")
    return m.group(1) if m else None


def traces(ng, names):
    out = {"t": np.array(ng.vec("time"))}
    for n in names:
        try:
            out[n] = np.array(ng.vec(n))
        except KeyError:
            out[n] = None
    return out


def s1_bigstep():
    print("\n== S1: the 10 V step, simultaneous values ==")
    sw = {"SW1": 3, "SW2": 3, "SW3": 3, "SW4": 1, "SW5": 1}
    rc_d = 5.1e-3
    trim = {"RV2": 21e4, "RV3": rc_d / 22e-9, "RV4": 1e6}   # gain 22: (10k+210k)/10k
    lines = D.lines(sw, trim, source="pulse(-5 5 0.1 1m 1m 10 20)")
    ng = run(lines, 1.0)
    names = {}
    u6out = D.pin("U6", "4"); u6vcc = D.pin("U6", "5")
    tr = traces(ng, ["v(" + spice_name("DRIVE") + ")", "v(" + spice_name("BASES") + ")",
                     "v(" + u6out + ")", "v(" + u6vcc + ")", "i(bemf)", "v(" + spice_name("SUM") + ")",
                     "v(" + spice_name("POSITION") + ")"])
    t = tr["t"]; drv = tr["v(" + spice_name("DRIVE") + ")"]
    im = tr["i(bemf)"]; u6o = tr["v(" + u6out + ")"]; rail = tr["v(" + u6vcc + ")"]
    bases = tr["v(" + spice_name("BASES") + ")"]
    i = int(np.argmax(np.abs(drv)))
    print(f"at |DRIVE| peak:  t={t[i]*1e3:.1f} ms  DRIVE={drv[i]:+.2f} V  I_mot={im[i]*1e3:+.0f} mA  "
          f"U6out={u6o[i]:+.2f} V  rail={rail[i]:.2f} V  BASES={bases[i]:+.2f} V  clamp={rail[i]-1.5:.2f}")
    j = int(np.argmax(np.abs(im)))
    print(f"at |I_motor| peak: t={t[j]*1e3:.1f} ms  DRIVE={drv[j]:+.2f} V  I_mot={im[j]*1e3:+.0f} mA  "
          f"U6out={u6o[j]:+.2f} V  rail={rail[j]:.2f} V  BASES={bases[j]:+.2f} V  clamp={rail[j]-1.5:.2f}")
    # headroom the model needed at the current peak: rail - 1.5 - U6out
    print(f"model headroom at current peak: clamp - U6out = {rail[j]-1.5-u6o[j]:+.2f} V")
    # implied requirement with a real 270 ohm + 100 ohm and min hFE=60:
    iA = abs(im[j])
    for hfe in (60, 100, 150):
        need = 15.3 * iA + 0.7 + 370 * iA / hfe
        print(f"  hFE {hfe:3d}: U6 out pin must reach {need:.2f} V; rail-1.5 = {rail[j]-1.5:.2f} V  "
              f"-> {'OK' if need < rail[j]-1.5 else 'SHORT by %.2f V' % (need-(rail[j]-1.5))}")


def s2_driver_stability():
    print("\n== S2: the driver loop alone, probe capacitance on BASES / U6 OUT ==")
    u6out = D.pin("U6", "4")
    for extra_name, extra in (
        ("no probe", []),
        ("12 pF on BASES (x10 probe)", [f"CprobeB {spice_name('BASES')} 0 12p"]),
        ("100 pF on BASES (x1 probe)", [f"CprobeB {spice_name('BASES')} 0 100p"]),
        ("100 pF on U6 OUT", [f"CprobeO {u6out} 0 100p"]),
    ):
        sw = {"SW1": 3, "SW2": 1, "SW3": 1, "SW4": 1, "SW5": 1}   # loop open
        trim = {"RV2": 40e3, "RV3": 1e6, "RV4": 1e6}             # gain 5
        lines = D.lines(sw, trim, source="pulse(0 3 0.1 1m 1m 10 20)") + extra
        ng = run(lines, 0.3)
        tr = traces(ng, ["v(" + u6out + ")", "v(" + spice_name("DRIVE") + ")"])
        t, o = tr["t"], tr["v(" + u6out + ")"]
        sel = (t > 0.1005) & (t < 0.115)
        seg = o[sel]
        # ringing metric: peak-to-peak of the residual after the edge, and zero-cross count
        zc = int(np.sum(np.diff(np.sign(seg - seg.mean())) != 0))
        print(f"  {extra_name:32s}: post-edge p-p {np.ptp(seg):.3f} V, sign flips {zc}")


def s2b_no_snubber():
    print("\n== S2b: same, snubber (C10/R20) removed ==")
    u6out = D.pin("U6", "4")
    sw = {"SW1": 3, "SW2": 1, "SW3": 1, "SW4": 1, "SW5": 1}
    trim = {"RV2": 40e3, "RV3": 1e6, "RV4": 1e6}
    lines = D.lines(sw, trim, source="pulse(0 3 0.1 1m 1m 10 20)")
    lines = [l for l in lines if not l.startswith(("CC10", "RR20"))]
    ng = run(lines, 0.3)
    tr = traces(ng, ["v(" + u6out + ")", "v(" + spice_name("DRIVE") + ")"])
    t, o = tr["t"], tr["v(" + u6out + ")"]
    sel = (t > 0.1005) & (t < 0.115)
    seg = o[sel]
    zc = int(np.sum(np.diff(np.sign(seg - seg.mean())) != 0))
    print(f"  no snubber: post-edge p-p {np.ptp(seg):.3f} V, sign flips {zc}")


def s3_windup():
    print("\n== S3: integrator windup at the end stop ==")
    # loop closed, P 5, I IN at RV4 = 1M (RC 1 s); TARGET 8 V (past the 7.73 V
    # end) for 3 s, then back to 5 V: when does POSITION leave the stop?
    for rv4 in (1e6, 100e3):
        sw = {"SW1": 3, "SW2": 3, "SW3": 1, "SW4": 3, "SW5": 1}
        trim = {"RV2": 40e3, "RV3": 1e6, "RV4": rv4}
        lines = D.lines(sw, trim, source="pulse(0 8 0.1 1m 1m 10 20)")
        ng = run(lines, 3.0, tstep=50e-6)
        inode = spice_name("I")
        tr = traces(ng, ["v(" + inode + ")", "v(" + spice_name("POSITION") + ")"])
        i_end = tr["v(" + inode + ")"][-1]
        print(f"  RV4 {rv4/1e3:.0f}k: after 3 s of TARGET 8 V at the stop, I = {i_end:+.2f} V "
              f"(saturated near the rail: wound up)")
        # now step TARGET to 5 V and watch POSITION leave the stop
        lines = D.lines(sw, trim, source="pulse(8 5 0.1 1m 1m 10 20)", pot_pos=7.73,
                        ic_zero=("I",))
        # hand-set I's initial charge to the wound-up value: instead use a DC run-in
        ng = run(lines, 6.0, tstep=50e-6)
        t, pos = tr["t"], None
        tr2 = traces(ng, ["v(" + spice_name("POSITION") + ")", "v(" + inode + ")"])
        t2, pos2, i2 = tr2["t"], tr2["v(" + spice_name("POSITION") + ")"], tr2["v(" + inode + ")"]
        # note: ic_zero=('I',) RESETS the integrator, so this run starts unwound;
        # for the wound-up start, run the 8 V phase without ic and continue.
        print(f"  (with I reset at the step) I goes {i2[0]:+.2f} -> {i2[-1]:+.2f} V; "
              f"POSITION leaves the stop when ... see full-run below")


def s3_windup_full():
    print("\n== S3b: windup, single run: 3 s at TARGET 8 V (at the stop), then 5 V ==")
    sw = {"SW1": 3, "SW2": 3, "SW3": 1, "SW4": 3, "SW5": 1}
    trim = {"RV2": 40e3, "RV3": 1e6, "RV4": 1e6}
    # two-segment source: 8 V for 3 s, then 5 V
    lines = D.lines(sw, trim, source="pwl(0 8 2.999 8 3.001 5 100 5)")
    ng = run(lines, 10.0, tstep=100e-6)
    inode = spice_name("I")
    tr = traces(ng, ["v(" + inode + ")", "v(" + spice_name("POSITION") + ")", "v(" + spice_name("DRIVE") + ")"])
    t, i_v, pos = tr["t"], tr["v(" + inode + ")"], tr["v(" + spice_name("POSITION") + ")"]
    drv = tr["v(" + spice_name("DRIVE") + ")"]
    print(f"  I at t=3 s (before the step back): {np.interp(3.0, t, i_v):+.2f} V")
    # when does POSITION drop 100 mV below the stop reading?
    after = t > 3.0
    idx = np.where(after & (pos < 7.73 - 0.1))[0]
    if len(idx):
        print(f"  POSITION leaves the stop {t[idx[0]] - 3.0:.2f} s after TARGET returns to 5 V "
              f"(I must unwind from {np.interp(3.0,t,i_v):+.1f} V)")
    else:
        print("  POSITION never leaves the stop within 7 s of the step back!")
    print(f"  DRIVE just before leaving: {np.interp(t[idx[0]] if len(idx) else 9.9, t, drv):+.2f} V")


def s5_dropout():
    print("\n== S5: wiper dropout for 20 ms while tracking ==")
    # P 22 + D, 1 V step; at t = 0.5 s open the wiper for 20 ms.
    # Implement: raise the wiper's tie to the POSITION net via a time-switched R.
    sw = {"SW1": 3, "SW2": 3, "SW3": 3, "SW4": 1, "SW5": 1}
    trim = {"RV2": 21e4, "RV3": 5.1e-3 / 22e-9, "RV4": 1e6}
    lines = D.lines(sw, trim, source="pulse(0 1 0.1 1m 1m 10 20)")
    # find the track's wiper tie: Rta/Rtb sit between POT+/POSITION/POT-.
    # Insert a dropout switch: replace the POSITION net tie of the track by a
    # resistor that goes huge for 20 ms at t = 0.5 s.  Simplest: add a
    # behavioural resistor from POSITION to a copy of itself is hard; instead
    # cut the wiper: rename the track wiper node and bridge with a pulsed R.
    new = []
    for l in lines:
        if l.startswith("Rta ") or l.startswith("Rtb "):
            l = l.replace(spice_name("POSITION"), "wiperx")
        new.append(l)
    new.append("Rdrop wiperx %s R = { (TIME > 0.5 && TIME < 0.52) ? 1e9 : 1 }" % spice_name("POSITION"))
    ng = run(new, 1.0)
    tr = traces(ng, ["v(" + spice_name("POSITION") + ")", "v(" + spice_name("DRIVE") + ")",
                     "v(wiperx)", "v(" + spice_name("ERROR") + ")"])
    t = tr["t"]; pos = tr["v(" + spice_name("POSITION") + ")"]; drv = tr["v(" + spice_name("DRIVE") + ")"]
    err = tr["v(" + spice_name("ERROR") + ")"]
    sel = (t > 0.5) & (t < 0.52)
    print(f"  during dropout: ERROR spans {err[sel].min():+.2f} .. {err[sel].max():+.2f} V, "
          f"DRIVE spans {drv[sel].min():+.2f} .. {drv[sel].max():+.2f} V")
    after = (t > 0.52) & (t < 0.9)
    print(f"  after it: POSITION returns within band at "
          f"{t[np.where(after & (np.abs(pos - 1.0) < 0.05))[0][0]] - 0.52:.3f} s; "
          f"max excursion {np.abs(pos[(t>0.5)&(t<0.9)]-1).max()*1e3:.0f} mV")


if __name__ == "__main__":
    get_base_sw()
    s1_bigstep()
    s2_driver_stability()
    s2b_no_snubber()
    s3_windup()
    s3_windup_full()
    s5_dropout()
