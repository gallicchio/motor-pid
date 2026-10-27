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

With --board, the same model on the board as built: the pours as KiCad filled
them and the ground plane as filled, cut where back runs pass, both from
out/pcb_geom.json (scripts/gen_pcb.py), on a 0.5 mm grid and 2 oz copper.  It
writes sim/thermal.json for the documents and fails if either junction passes
T_LIMIT: 125 C leaves 25 C for the model's 25 % on a 95 C rise, under the
MJB44H11's 150 C.

    python3 sim/thermal.py             the comparison of cooling options
    python3 sim/thermal.py --board     the board as built (make.py runs it)
"""
import json, os, sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

HERE = os.path.dirname(os.path.abspath(__file__))
P_WORST = 3.7          # W in one transistor (sim/results.json, stall_sweep)
T_AIR = 25.0
T_LIMIT = 125.0        # the build fails above this junction temperature (see above)
RTH_JC = {"MJB44H11": 2.5, "MJB45H11": 2.5, "MJD44H11": 6.25, "MJD45H11": 6.25}
R_SOLDER = 0.3         # C/W, tab to copper through the solder


def solve_masks(top, bot, tab, P, oz=1.0, h_top=10.0, h_bot=6.0, dx=1e-3,
                t_fr4=1.6e-3, k_cu=385.0, k_fr4_z=0.3, k_fr4_xy=0.8):
    """Temperature rise above the air of every cell of both layers, with the
    copper given as boolean (H, W) masks on a grid of `dx` metres and `P` watts
    entering the top layer evenly over the cells of `tab`."""
    H, W = top.shape
    n = W * H
    t_cu = 35e-6 * oz
    g_fr4 = k_fr4_xy * t_fr4 / 2                     # in-plane, half the FR4 per layer
    K_top = np.where(top, g_fr4 + k_cu * t_cu, g_fr4)
    K_bot = np.where(bot, g_fr4 + k_cu * t_cu, g_fr4)
    gz = k_fr4_z * dx * dx / t_fr4                   # through the FR4, per cell
    rows, cols, vals, diag = [], [], [], np.zeros(2 * n)
    for L, K in ((0, K_top), (1, K_bot)):
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
    cells = np.flatnonzero(tab.ravel())
    q[cells] = P / len(cells)
    T = spl.spsolve((A + sp.diags(diag)).tocsc(), q)
    return T[:n].reshape(H, W), T[n:].reshape(H, W)


def solve(pour, tab, P, oz=1.0, W=170, H=120, plane=True, h_top=10.0, h_bot=6.0, **kw):
    """Temperature rise of the tab (mean over its cells) and of the pour, with
    `pour` and `tab` as (x0, y0, x1, y1) in mm on a 1 mm grid."""
    top, bot, tb = np.zeros((H, W), bool), np.full((H, W), plane), np.zeros((H, W), bool)
    x0, y0, x1, y1 = pour
    top[y0:y1, x0:x1] = True
    tx0, ty0, tx1, ty1 = tab
    tb[ty0:ty1, tx0:tx1] = True
    top |= tb
    Tt, _ = solve_masks(top, bot, tb, P, oz=oz, h_top=h_top, h_bot=h_bot, **kw)
    return float(np.mean(Tt[tb])), float(np.mean(Tt[y0:y1, x0:x1]))


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


def rasterise(polys, W, H, dx):
    """Cells whose centres are inside the filled polygons (each an outline and
    its holes, in mm), on a grid of `dx` mm."""
    from matplotlib.path import Path
    xs, ys = np.meshgrid((np.arange(W) + 0.5) * dx, (np.arange(H) + 0.5) * dx)
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    m = np.zeros(W * H, bool)
    for rings in polys:
        inside = Path(rings[0]).contains_points(pts)
        for hole in rings[1:]:
            inside &= ~Path(hole).contains_points(pts)
        m |= inside
    return m.reshape(H, W)


def board(geom_path, out_path, dx_mm=0.5):
    """The worst stall on the board as built, one transistor at a time."""
    g = json.load(open(geom_path))
    heat = g["heat"]
    W, H = int(round(g["board_w"] / dx_mm)), int(round(g["board_h"] / dx_mm))
    plane = rasterise(heat["plane"], W, H, dx_mm)
    result = {"p_w": P_WORST, "t_air_c": T_AIR, "t_limit_c": T_LIMIT, "oz": 2.0}
    ok = True
    for ref in ("Q1", "Q2"):
        h = heat[ref]
        pour = rasterise(h["pour"], W, H, dx_mm)
        x0, y0, x1, y1 = h["tab"]
        xs, ys = (np.arange(W) + 0.5) * dx_mm, (np.arange(H) + 0.5) * dx_mm
        tab = (ys[:, None] > y0) & (ys[:, None] < y1) & (xs[None, :] > x0) & (xs[None, :] < x1)
        rjc = RTH_JC[h["value"]]
        row = {"value": h["value"], "rth_jc": rjc, "pour_mm2": round(float(pour.sum()) * dx_mm ** 2)}
        for where, (ht, hb) in (("bench", (10.0, 6.0)), ("standoffs", (12.0, 8.0))):
            Tt, Tb = solve_masks(pour | tab, plane, tab, P_WORST, oz=2.0, h_top=ht, h_bot=hb, dx=dx_mm * 1e-3)
            t_tab = T_AIR + float(Tt[tab].mean())
            row[where] = {"junction_c": round(t_tab + P_WORST * (rjc + R_SOLDER), 1),
                          "tab_c": round(t_tab, 1),
                          "pour_mean_c": round(T_AIR + float(Tt[pour].mean()), 1),
                          "pour_edge_c": round(T_AIR + float(np.percentile(Tt[pour], 5)), 1)}
        result[ref] = row
        b_ = row["bench"]
        print(f"  {ref} {h['value']} on {row['pour_mm2']} mm2 of 2 oz: junction {b_['junction_c']:.0f} C "
              f"({row['standoffs']['junction_c']:.0f} on standoffs), pour {b_['pour_mean_c']:.0f} C mean, "
              f"{b_['pour_edge_c']:.0f} C at its far edge")
        if b_["junction_c"] > T_LIMIT:
            print(f"  FAIL {ref}: {b_['junction_c']:.0f} C at the junction in the worst stall, over {T_LIMIT:.0f} C")
            ok = False
    json.dump(result, open(out_path, "w"), indent=1)
    return ok


if __name__ == "__main__":
    if "--board" in sys.argv:
        print(f"the worst stall, {P_WORST} W in one transistor, air at {T_AIR:.0f} C, board on a bench")
        sys.exit(0 if board(os.path.join(HERE, "..", "out", "pcb_geom.json"),
                            os.path.join(HERE, "thermal.json")) else 1)
    main()
