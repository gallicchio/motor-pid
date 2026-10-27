#!/usr/bin/env python3
"""How hot the push-pull gets in the worst stall, for each way of cooling it.

The worst stall puts 3.7 W in one transistor for as long as it lasts
(sim/results.json, stall_sweep: DRIVE about 7 V into the stalled 14 ohm motor,
0.49 A, which the 0.35 A fuse may hold for minutes).  This is a steady-state
model of the board as two copper sheets with FR4 between them: the top one
copper only under the collector pour, the bottom one the ground plane over the
whole 170 x 120 mm; both faces lose heat by convection and radiation (h, in
W/m^2K, 10 on top and 6 underneath for a board lying on a bench, 12 and 8 for
one on standoffs).  The heat enters through the transistor's tab, and the
junction is RthJC above it.  Calibrated against TI's LM2585 data sheet (DDPAK
on 1 oz, 1 square inch: 26 C/W), which it gives as 25-27 C/W with the plane
underneath; trust it to perhaps 25 %.  Signal traces and the back runs that
cut the plane are left out.

The TO-220 cases need no board model: junction = ambient + P (RthJC + case to
sink + sink to air), from the heatsink makers' natural-convection ratings.

    python3 sim/thermal.py
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

P_WORST = 3.7          # W in one transistor (sim/results.json, stall_sweep)
T_AIR = 25.0


def solve(pour, tab, P, oz=1.0, W=170, H=120, plane=True, h_top=10.0, h_bot=6.0,
          t_fr4=1.6e-3, k_cu=385.0, k_fr4_z=0.3, k_fr4_xy=0.8, dx=1e-3):
    """Temperature rise of the tab (mean over its cells) above the air, with
    `pour` and `tab` as (x0, y0, x1, y1) in mm on a 1 mm grid."""
    n = W * H
    t_cu = 35e-6 * oz
    g_fr4 = k_fr4_xy * t_fr4 / 2                     # in-plane, half the FR4 per layer
    top = np.full((H, W), g_fr4)
    x0, y0, x1, y1 = pour
    top[y0:y1, x0:x1] += k_cu * t_cu
    bot = np.full((H, W), g_fr4 + (k_cu * t_cu if plane else 0.0))
    gz = k_fr4_z * dx * dx / t_fr4                   # through the FR4, per cell
    rows, cols, vals, diag = [], [], [], np.zeros(2 * n)
    for L, K in ((0, top), (1, bot)):
        for g, shape, step in ((2 * K[:, :-1] * K[:, 1:] / (K[:, :-1] + K[:, 1:]), (H, W - 1), 1),
                               (2 * K[:-1, :] * K[1:, :] / (K[:-1, :] + K[1:, :]), (H - 1, W), W)):
            ys, xs = np.mgrid[0:shape[0], 0:shape[1]]
            a = (L * n + ys * W + xs).ravel(); b = a + step; gg = g.ravel()
            rows += [a, b]; cols += [b, a]; vals += [-gg, -gg]
            np.add.at(diag, a, gg); np.add.at(diag, b, gg)
    a = np.arange(n)
    rows += [a, a + n]; cols += [a + n, a]; vals += [np.full(n, -gz)] * 2
    diag[:n] += gz + h_top * dx * dx
    diag[n:] += gz + h_bot * dx * dx
    A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(2 * n, 2 * n))
    q = np.zeros(2 * n)
    tx0, ty0, tx1, ty1 = tab
    cells = [ty * W + tx for ty in range(ty0, ty1) for tx in range(tx0, tx1)]
    q[cells] = P / len(cells)
    T = spl.spsolve((A + sp.diags(diag)).tocsc(), q)
    Tt = T[:n].reshape(H, W)
    return float(np.mean(Tt[ty0:ty1, tx0:tx1])), float(np.mean(Tt[y0:y1, x0:x1]))


# Q1 at (152, 43.5), its tab toward the +15 V rail; the pour as large as the
# MOTOR DRIVER box allows above R21.  RthJC: MJD44H11 (DPAK, 20 W) 6.25 C/W,
# MJB44H11 (D2PAK, 50 W) 2.5 C/W, MJE3055T (TO-220, 75 W) 1.67 C/W.
DPAK_TAB, D2PAK_TAB = (149, 30, 155, 37), (147, 28, 157, 37)
SMT = [
    ("now: DPAK, its 12 x 5.8 mm pour, 1 oz", 6.25, DPAK_TAB, (146, 27, 158, 37), 1.0),
    ("DPAK, 25 x 25 mm pour, 1 oz",           6.25, DPAK_TAB, (141, 27, 166, 52), 1.0),
    ("DPAK, 25 x 25 mm pour, 2 oz",           6.25, DPAK_TAB, (141, 27, 166, 52), 2.0),
    ("D2PAK, 25 x 25 mm pour, 1 oz",          2.5,  D2PAK_TAB, (141, 27, 166, 52), 1.0),
    ("D2PAK, 25 x 25 mm pour, 2 oz",          2.5,  D2PAK_TAB, (141, 27, 166, 52), 2.0),
    ("D2PAK, 28 x 30 mm pour, 2 oz",          2.5,  D2PAK_TAB, (139, 24, 167, 54), 2.0),
]
TO220 = [   # (heatsink, sink-to-air C/W natural convection)
    ("a small clip-on, about 24 C/W", 24.0),
    ("30 x 30 x 25 mm, 13.6 C/W", 13.6),
    ("Aavid 6398BG, 4.4 C/W", 4.4),
    ("Aavid 530002B02500G, 2.6 C/W", 2.6),
]


def main():
    rise, _ = solve((37, 37, 63, 63), (45, 45, 55, 54), 1.0, W=100, H=100)
    print(f"check: DDPAK on 1 sq in of 1 oz, 100 mm board with a plane: {rise + 2:.0f} C/W (TI: 26)")
    print(f"\nthe worst stall, {P_WORST} W, air at {T_AIR:.0f} C; board on a bench (on standoffs)")
    for name, rjc, tab, pour, oz in SMT:
        out = []
        for h in ((10, 6), (12, 8)):
            t_tab, t_pour = solve(pour, tab, P_WORST, oz=oz, h_top=h[0], h_bot=h[1])
            out.append((T_AIR + t_tab + P_WORST * (rjc + 0.3), T_AIR + t_pour))
        print(f"  {name:38s} junction {out[0][0]:4.0f} ({out[1][0]:3.0f}) C, pour {out[0][1]:4.0f} ({out[1][1]:3.0f}) C")
    for hs, rsa in TO220:
        for pad, rcs in (("grease", 0.5), ("insulating pad", 1.8)):
            print(f"  TO-220 on {hs:32s} {pad:15s} junction {T_AIR + P_WORST * (1.67 + rcs + rsa):4.0f} C, "
                  f"heatsink {T_AIR + P_WORST * rsa:4.0f} C")


if __name__ == "__main__":
    main()
