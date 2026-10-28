import sys, os, math
import numpy as np
sys.path.insert(0, "design_reviews/2026-10-27_Gemini-4-Argon/project/sim")
sys.path.insert(0, "design_reviews/2026-10-27_Gemini-4-Argon/project/scripts")
import pid_sim

D = pid_sim.Deck("design_reviews/2026-10-27_Gemini-4-Argon/project/out/motorpid.net")
base_sw = {"SW1": 3, "SW2": 3, "SW3": 1, "SW4": 1, "SW5": 1}

print("=== 4. Integrator windup at end stop (+10V target for 2s -> +1V target) ===")
for rv4 in (1e6, 200e3):
    lines = D.lines(dict(base_sw, SW3=3, SW4=3), {"RV2": 40e3, "RV3": 231e3, "RV4": rv4},
                    source="pulse(10 1 2.0 1m 1m 10 20)", pot_pos=7.73, ic_zero=("I", "SUM"))
    ng = pid_sim.run(lines, 10.0, tstep=200e-6)
    t = np.array(ng.vec("time"))
    pos = np.array(ng.vec("v(" + pid_sim.spice_name("POSITION") + ")"))
    vpos = np.array(ng.vec("v(pos)"))
    vi = np.array(ng.vec("v(" + pid_sim.spice_name("I") + ")"))
    idx2 = np.searchsorted(t, 1.99)
    after = t >= 2.01
    tt, pp, vpp, vii = t[after], pos[after], vpos[after], vi[after]
    leave = np.where(vpp < 9.5)[0]
    t_leave = (tt[leave[0]] - 2.0) if len(leave) else -1
    settle1 = np.where(np.abs(pp - 1.0) > 0.05)[0]
    t_set1 = (tt[settle1[-1]] - 2.0) if len(settle1) else 0
    print(f"  RV4={rv4/1e3:4.0f}k (RC={rv4*1e-6:.2f}s): at t=2s V(I)={vi[idx2]:+.2f}V, V(pos)={vpos[idx2]:+.2f}V; "
          f"unwinds & leaves stop after {t_leave:.2f}s, settles to 1V after {t_set1:.2f}s (final V(POSITION)={pp[-1]:+.3f}V)")

print("\n=== 5. Wiper dropout (10 ms open circuit on POSITION while holding +4V target) ===")
for p_gain, d_on in ((5, 1), (22, 3), (100, 3)):
    lines = D.lines(dict(base_sw, SW3=d_on), {"RV2": (p_gain - 1)*10e3, "RV3": 231e3, "RV4": 1e6},
                    source="dc 4", pot_pos=4.05, ic_zero=("SUM",))
    new_lines = []
    for l in lines:
        if l.startswith("Rta ") or l.startswith("Rtb "):
            l = l.replace(f" {pid_sim.spice_name('POSITION')} ", " n_wiper_internal ")
        new_lines.append(l)
    # 10 ms open circuit between t=0.200s and t=0.210s using smooth pulse voltage control
    new_lines.append("Vdrop ctrl_drop 0 pulse(1 1e9 0.200 100u 100u 10m 1)")
    new_lines.append(f"Rdrop n_wiper_internal {pid_sim.spice_name('POSITION')} R = {{ V(ctrl_drop) }}")
    ng = pid_sim.run(new_lines, 0.5, tstep=20e-6)
    t = np.array(ng.vec("time"))
    pos_node = np.array(ng.vec("v(" + pid_sim.spice_name("POSITION") + ")"))
    real_pos = np.array(ng.vec("v(pos)"))
    err_node = np.array(ng.vec("v(" + pid_sim.spice_name("ERROR") + ")"))
    drv_node = np.array(ng.vec("v(" + pid_sim.spice_name("DRIVE") + ")"))
    i0 = np.searchsorted(t, 0.195)
    sel_drop = (t >= 0.201) & (t <= 0.209)
    sel_after = t >= 0.200
    print(f"  P={p_gain:3d} D={'IN' if d_on==3 else 'OFF'}: before: POS={pos_node[i0]:+.2f}V, ERR={err_node[i0]:+.2f}V | "
          f"during 10ms dropout: POS={pos_node[sel_drop].mean():+.2f}V, ERR={err_node[sel_drop].mean():+.2f}V, DRIVE_pk={drv_node[sel_drop].max():+.2f}V | "
          f"slider excursion: {(real_pos[sel_after].max() - real_pos[i0])/0.193:+.2f} mm")

print("\n=== 6. Abuse: Single rail powered (+15V on, -15V_IN open; and -15V on, +15V_IN open) ===")
for which in ("pos_only", "neg_only"):
    lines = D.lines(dict(base_sw, SW2=1), {"RV2": 0.0, "RV3": 231e3, "RV4": 1e6}, source="dc 5")
    if which == "pos_only":
        lines = [l for l in lines if not l.startswith("Vneg ") and not l.startswith("Rneg ")]
        lines.append(f"Rneg_open {D.pin('J6', 3)} 0 1e9")
    else:
        lines = [l for l in lines if not l.startswith("Vpos ") and not l.startswith("Rpos ")]
        lines.append(f"Rpos_open {D.pin('J6', 1)} 0 1e9")
    ng = pid_sim.run(lines, 0.2)
    v_m15 = ng.vec("v(" + pid_sim.spice_name("-15V") + ")")[-1]
    v_p15 = ng.vec("v(" + pid_sim.spice_name("+15V") + ")")[-1]
    print(f"  {which:10s}: V(+15V)={v_p15:+.2f}V, V(-15V)={v_m15:+.2f}V")
