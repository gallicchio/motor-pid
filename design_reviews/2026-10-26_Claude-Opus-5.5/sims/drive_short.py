"""DRIVE (TP7, ahead of the fuse) clipped to ground by a scope's ground lead,
with SUM at +5 V and at +13 V: the current and the power in Q1.  The models
are pid_sim.py's; nothing limits the current but the LM321's output and the
270 ohm into the bases.  Run from the review directory."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "project", "sim"))
from ngspice_lib import NgSpice
import pid_sim as P
for vsum in (2.0, 5.0, 13.0):
    ng = NgSpice()
    ng.circuit(["drive short"] + P.MODELS + [
        "Vp vp 0 14.78", "Vn vn 0 -14.78", f"Vs sum 0 {vsum}",
        "Xu6 sum inn u6out vp vn LM321", "R18 drive inn 10k", "C9 u6out inn 330n",
        "R19 u6out bases 270", "Q1 vp bases e1 QD44", "Q2 vn bases e2 QD45",
        "R21 e1 drive 1", "R22 e2 drive 1", "Vclip drive 0 0", ".end"])
    ng.cmd("op")
    i = -ng.vec("i(vclip)")[0]
    ve1 = ng.vec("v(e1)")[0]; vb = ng.vec("v(bases)")[0]; vo = ng.vec("v(u6out)")[0]
    print(f"SUM {vsum:4.1f} V: DRIVE shorted carries {i:.2f} A; Q1 takes {(14.78 - ve1) * i:.1f} W, "
          f"R21 {i * i:.1f} W; U6 out {vo:.1f} V, bases {vb:.2f} V")
