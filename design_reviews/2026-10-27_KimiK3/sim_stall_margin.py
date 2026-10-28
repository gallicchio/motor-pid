#!/usr/bin/env python3
"""The full-drive end-stop stall: U6's output pin vs its rail, in the model.
Then the same requirement recomputed for min hFE and the real fuse range."""
import os, sys
import numpy as np
PROJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project")
sys.path.insert(0, os.path.join(PROJ, "sim")); sys.path.insert(0, os.path.join(PROJ, "scripts"))
os.chdir(PROJ)
from pid_sim import Deck, run, spice_name

D = Deck()
sw = {"SW1": 3, "SW2": 1, "SW3": 1, "SW4": 1, "SW5": 1}      # LOOP open
trim = {"RV2": 21e4, "RV3": 1e6, "RV4": 1e6}                 # P gain 22
ng = run(D.lines(sw, trim, source="dc 1"), 1.0)
u6o = np.array(ng.vec("v(" + D.pin("U6", "4") + ")"))
rail = np.array(ng.vec("v(" + D.pin("U6", "5") + ")"))
bases = np.array(ng.vec("v(" + spice_name("BASES") + ")"))
drv = np.array(ng.vec("v(" + spice_name("DRIVE") + ")"))
im = np.array(ng.vec("i(bemf)"))
print(f"END-STOP STALL (loop open, gain 22, TARGET 1 V):")
print(f"  DRIVE {drv[-1]:+.2f} V, I_motor {im[-1]*1e3:+.0f} mA")
print(f"  U6 out pin {u6o[-1]:+.2f} V, its + rail {rail[-1]:+.2f} V -> model drop {rail[-1]-u6o[-1]:.2f} V (clamp at 1.50 V)")
print(f"  BASES {bases[-1]:+.2f} V -> drop across R19 = {u6o[-1]-bases[-1]:.2f} V -> Ib = {(u6o[-1]-bases[-1])/270*1e3:.1f} mA")
iA = abs(im[-1])
print(f"  implied model hFE at this point: {iA/((u6o[-1]-bases[-1])/270):.0f}")
print()
print("Same operating point with datasheet worst cases (Ib grows, drops grow):")
for hfe in (60, 40):
    ib = iA / hfe
    for rptc in (0.3, 1.7):
        vbe = 0.75
        emitter = 14 * iA + rptc * iA + 1.0 * iA
        u6_need = emitter + vbe + 270 * ib + 100 * ib   # + the model's Ro
        for voh_drop in (1.5, 2.0, 3.0):
            avail = 14.4 - voh_drop        # rail sags to ~14.4 at 0.63 A through the SS34
            margin = avail - u6_need
            print(f"  hFE {hfe}, PTC {rptc} ohm, LM321 drop {voh_drop} V: U6 must give {u6_need:.2f} V, "
                  f"has {avail:.2f} V -> margin {margin:+.2f} V")
