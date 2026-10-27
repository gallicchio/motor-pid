"""Temperatures at the pours' neighbours in each worst stall (3.7 W in Q1 or
in Q2, board on a bench, 25 C air), from the project's own model on the board
as built.  Run from the review directory: python3 sims/neighbours.py"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "project", "sim"))
import thermal as T
g = json.load(open(os.path.join(HERE, "..", "..", "..", "out", "pcb_geom.json")))
h = g["heat"]; dx = 0.5
W, H = int(g["board_w"] / dx), int(g["board_h"] / dx)
plane = T.rasterise(h["plane"], W, H, dx)
PTS = {"U6 (LM321)": (135.0, 58.0), "F1 (the PTC)": (160.0, 94.0), "D3 (SS34)": (164.8, 55.4),
       "D4 (SS34)": (164.8, 62.6), "C12 (100 uF, -15 V)": (155.5, 18.0), "R21": (156.5, 56.0),
       "R22": (151.5, 62.0), "RV2 (P GAIN)": (117.0, 51.5), "C9 (330 nF)": (134.7, 72.0)}
for ref in ("Q1", "Q2"):
    pour = T.rasterise(h[ref]["pour"], W, H, dx)
    x0, y0, x1, y1 = h[ref]["tab"]
    xs, ys = (np.arange(W) + 0.5) * dx, (np.arange(H) + 0.5) * dx
    tab = (ys[:, None] > y0) & (ys[:, None] < y1) & (xs[None, :] > x0) & (xs[None, :] < x1)
    Tt, Tb = T.solve_masks(pour | tab, plane, tab, T.P_WORST, oz=2.0, h_top=10.0, h_bot=6.0, dx=dx * 1e-3)
    print(f"stall in {ref}: " + ", ".join(f"{k} {T.T_AIR + Tt[int(y / dx), int(x / dx)]:.0f} C" for k, (x, y) in PTS.items()))
