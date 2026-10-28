#!/usr/bin/env python3
"""S3 redone: integrator windup at the end stop, measured on the mechanical
position node v(pos), with the drive and fuse current watched through it.

Scenario: loop closed, P gain 5, I IN, TARGET = 8 V (past the 7.73 V the wiper
can ever read) for 5 s, then back to 5 V.  Reported: I's voltage at the step
back, the wait until the slider's mechanical position leaves the stop, and
what DRIVE does during the wait (does the motor sit stalled?).
"""
import os, sys
import numpy as np

PROJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project")
sys.path.insert(0, os.path.join(PROJ, "sim"))
sys.path.insert(0, os.path.join(PROJ, "scripts"))
os.chdir(PROJ)

from pid_sim import Deck, run, spice_name

D = Deck()

for rv4, gain in ((1e6, 5), (100e3, 5), (1e6, 22)):
    sw = {"SW1": 3, "SW2": 3, "SW3": 1, "SW4": 3, "SW5": 1}
    trim = {"RV2": (gain - 1) * 10e3, "RV3": 1e6, "RV4": rv4}
    lines = D.lines(sw, trim, source="pwl(0 0 0.1 8 4.999 8 5.001 5 100 5)")
    ng = run(lines, 14.0, tstep=100e-6)
    t = np.array(ng.vec("time"))
    pos = np.array(ng.vec("v(pos)"))          # mechanical, pot volts; stop at +9.66
    iread = np.array(ng.vec("v(" + spice_name("I") + ")"))
    drv = np.array(ng.vec("v(" + spice_name("DRIVE") + ")"))
    imot = np.array(ng.vec("i(bemf)"))
    i5 = np.interp(5.0, t, iread)
    print(f"\nRV4 {rv4/1e3:5.0f}k, P gain {gain}: I when TARGET steps back = {i5:+.2f} V")
    at_stop = np.interp(4.9, t, pos)
    print(f"  mechanical position at the stop: {at_stop:+.2f} pot-V (stop is 9.66)")
    moved = np.where((t > 5.0) & (pos < at_stop - 0.1))[0]
    if len(moved):
        t_move = t[moved[0]] - 5.0
        print(f"  slider starts back {t_move:.2f} s after the step; "
              f"DRIVE during the wait = {np.interp(5.0 + t_move/2, t, drv):+.2f} V "
              f"at {abs(np.interp(5.0 + t_move/2, t, imot))*1e3:.0f} mA (stalled)")
        settled = np.where((t > 5.0) & (np.abs(pos - 5.0) < 0.05))[0]
        if len(settled):
            print(f"  within 5%% of the 5 V target {t[settled[0]] - 5.0:.2f} s after the step")
    else:
        print("  slider never leaves the stop in the 9 s after the step back")
    # how long is the motor stalled at > 0.35 A in total?
    hot = (t > 0.1) & (np.abs(imot) > 0.35)
    if len(hot) and hot.any():
        idx = np.where(hot)[0]
        print(f"  motor above the fuse's 0.35 A hold for {len(idx) * (t[1]-t[0]):.2f} s in all "
              f"(the fuse at 0.63 A: see the PTC finding)")
