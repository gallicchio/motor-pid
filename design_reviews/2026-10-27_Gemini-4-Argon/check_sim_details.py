import sys, os
import numpy as np
sys.path.insert(0, "design_reviews/2026-10-27_Gemini-4-Argon/project/sim")
sys.path.insert(0, "design_reviews/2026-10-27_Gemini-4-Argon/project/scripts")
import pid_sim

D = pid_sim.Deck("design_reviews/2026-10-27_Gemini-4-Argon/project/out/motorpid.net")
base_sw = {"SW1": 3, "SW2": 3, "SW3": 1, "SW4": 1, "SW5": 1}
for g in (1.5, 5, 22, 100):
    trim = {"RV2": (g - 1) * 10e3, "RV3": 231e3, "RV4": 1e6}
    ng = pid_sim.run(D.lines(base_sw, trim), 1.6)
    t = np.array(ng.vec("time"))
    pos = np.array(ng.vec("v(" + pid_sim.spice_name("POSITION") + ")"))
    vel = np.array(ng.vec("v(vel)"))
    drv = np.array(ng.vec("v(" + pid_sim.spice_name("DRIVE") + ")"))
    idx0 = np.searchsorted(t, 0.1)
    print(f"P={g:5.1f}: pos(0)={pos[0]:+.4f} pos(0.1s)={pos[idx0]:+.4f} pos(end)={pos[-1]:+.4f} max={pos.max():+.4f} vel(0)={vel[0]:+.4f}")
