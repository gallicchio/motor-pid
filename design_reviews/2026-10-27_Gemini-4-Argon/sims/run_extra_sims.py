import sys, os, math
import numpy as np
sys.path.insert(0, "design_reviews/2026-10-27_Gemini-4-Argon/project/sim")
sys.path.insert(0, "design_reviews/2026-10-27_Gemini-4-Argon/project/scripts")
import pid_sim

D = pid_sim.Deck("design_reviews/2026-10-27_Gemini-4-Argon/project/out/motorpid.net")
base_sw = {"SW1": 3, "SW2": 3, "SW3": 1, "SW4": 1, "SW5": 1}

print("=== 1. P=22 + D (rule, RV3=231k) true settling to final value vs target ===")
sw = dict(base_sw, SW3=3)
trim = {"RV2": 21 * 10e3, "RV3": 231e3, "RV4": 1e6}
for ic in ((), ("SUM",)):
    ng = pid_sim.run(D.lines(sw, trim, ic_zero=ic), 1.6)
    t = np.array(ng.vec("time"))
    pos = np.array(ng.vec("v(" + pid_sim.spice_name("POSITION") + ")"))
    vpos = np.array(ng.vec("v(pos)"))
    vel = np.array(ng.vec("v(vel)"))
    sel = t >= 0.1
    tt, yy, vv = t[sel], pos[sel], vel[sel]
    # True dynamic overshoot past final resting value yy[-1]:
    dyn_over = (yy.max() - yy[-1]) / (yy[-1] - yy[0]) * 100
    # Time when slider actually stops moving (|vel| < 0.01 V/s)
    moving = np.where(np.abs(vv) > 0.01)[0]
    t_stop = (tt[moving[-1]] - 0.1) * 1e3 if len(moving) else 0.0
    # Time to enter +/-5% of final resting value yy[-1]
    outside_final = np.where(np.abs(yy - yy[-1]) > 0.05)[0]
    t_settle_final = (tt[outside_final[-1]] - 0.1) * 1e3 if len(outside_final) else 0.0
    print(f"  ic={ic}: yy[0]={yy[0]:+.4f}V, yy_max={yy.max():+.4f}V, yy_end={yy[-1]:+.4f}V, vpos_end={vpos[-1]:+.4f}V, "
          f"dyn_overshoot={dyn_over:.2f}%, t_settle_to_final={t_settle_final:.1f}ms, t_stop={t_stop:.1f}ms")

print("\n=== 2. Driver U6 stability (with/without snubber, probe on BASES/U6_OUT, PTC 0.2/1.7/10k ohm) ===")
for snub in (True, False):
    for r_ptc in (0.2, 1.7, 10000.0):
        for c_bases in (0.0, 15e-12, 120e-12):
            lines = D.lines(dict(base_sw, SW2=1), {"RV2": 0.0, "RV3": 231e3, "RV4": 1e6},
                            source="pulse(-1 1 0.01 10n 10n 0.05 0.1)")
            if not snub:
                lines = [l for l in lines if not l.startswith("RC10") and not l.startswith("CC10") and not l.startswith("RR20")]
            lines = [f"RF1 {D.pin('F1',1)} {D.pin('F1',2)} {r_ptc}" if l.startswith("RF1 ") else l for l in lines]
            if c_bases > 0:
                lines.append(f"Cprobe_b {pid_sim.spice_name('BASES')} 0 {c_bases}")
            ng = pid_sim.run(lines, 0.04, tstep=2e-6)
            drv = np.array(ng.vec("v(" + pid_sim.spice_name("DRIVE") + ")"))
            u6o = np.array(ng.vec("v(" + D.pin("U6", 4) + ")"))
            t = np.array(ng.vec("time"))
            sel = (t > 0.0105) & (t < 0.039)
            pk_drv = drv[sel].max()
            ring_u6 = np.ptp(u6o[(t > 0.02) & (t < 0.039)])
            print(f"  snub={str(snub):5s} r_ptc={r_ptc:7.1f} C_bases={c_bases*1e12:5.0f}pF -> drv_max={pk_drv:+.3f}V, u6_tail_ptp={ring_u6*1e3:.2f}mV")

print("\n=== 3. Scope probe capacitance (15pF 10x, 120pF 1x) on D (TP4) and U7 OUT (TP13) ===")
for node in ("D", "ERROR", "P", "SUM"):
    for c_probe in (0.0, 15e-12, 120e-12):
        lines = D.lines(dict(base_sw, SW3=3), {"RV2": 210e3, "RV3": 231e3, "RV4": 1e6}, ic_zero=("SUM",))
        if c_probe > 0:
            lines.append(f"Cprobe {pid_sim.spice_name(node)} 0 {c_probe}")
        ng = pid_sim.run(lines, 0.4)
        pos = np.array(ng.vec("v(" + pid_sim.spice_name("POSITION") + ")"))
        d_v = np.array(ng.vec("v(" + pid_sim.spice_name(node) + ")"))
        print(f"  probe on {node:5s} C={c_probe*1e12:5.0f}pF -> pos_max={pos.max():+.4f}V, {node}_peak={np.abs(d_v).max():.3f}V")

print("\n=== 4. Integrator windup at end stop (+10V target -> +1V target) ===")
for rv4 in (1e6, 200e3):
    lines = D.lines(dict(base_sw, SW3=3, SW4=3), {"RV2": 40e3, "RV3": 231e3, "RV4": rv4},
                    source="pulse(10 1 2.0 1m 1m 10 20)", ic_zero=("I", "SUM"))
    ng = pid_sim.run(lines, 8.0, tstep=100e-6)
    t = np.array(ng.vec("time"))
    pos = np.array(ng.vec("v(" + pid_sim.spice_name("POSITION") + ")"))
    vi = np.array(ng.vec("v(" + pid_sim.spice_name("I") + ")"))
    idx2 = np.searchsorted(t, 1.99)
    # Find when pos leaves the end stop (< 7.70 V) after t=2.0s
    after = t >= 2.0
    tt, pp = t[after], pos[after]
    leave = np.where(pp < 7.6)[0]
    t_leave = (tt[leave[0]] - 2.0) if len(leave) else -1
    settle1 = np.where(np.abs(pp - 1.0) > 0.05)[0]
    t_set1 = (tt[settle1[-1]] - 2.0) if len(settle1) else 0
    print(f"  RV4={rv4/1e3:4.0f}k: V(I) at t=2s is {vi[idx2]:+.2f}V, leaves end-stop after {t_leave:.2f}s, settles to 1V after {t_set1:.2f}s")

print("\n=== 5. Wiper dropout (5 ms open circuit on POSITION while at +4V target) ===")
lines = D.lines(dict(base_sw, SW3=3), {"RV2": 210e3, "RV3": 231e3, "RV4": 1e6},
                source="dc 4", pot_pos=4.0, ic_zero=("SUM",))
# Replace Rta/Rtb connection to wiper with a time-dependent switch that opens from t=0.100 to t=0.105s
new_lines = []
for l in lines:
    if l.startswith("Rta ") or l.startswith("Rtb "):
        l = l.replace(f" {pid_sim.spice_name('POSITION')} ", " n_wiper_internal ")
    new_lines.append(l)
new_lines.append(f"Bdrop n_wiper_internal {pid_sim.spice_name('POSITION')} I = {{ ((time > 0.1) & (time < 0.105)) ? 0 : (V(n_wiper_internal) - V({pid_sim.spice_name('POSITION')}))/1.0 }}")
ng = pid_sim.run(new_lines, 0.3, tstep=10e-6)
t = np.array(ng.vec("time"))
pos_node = np.array(ng.vec("v(" + pid_sim.spice_name("POSITION") + ")"))
real_pos = np.array(ng.vec("v(pos)"))
err_node = np.array(ng.vec("v(" + pid_sim.spice_name("ERROR") + ")"))
drv_node = np.array(ng.vec("v(" + pid_sim.spice_name("DRIVE") + ")"))
sel_drop = (t >= 0.100) & (t <= 0.105)
print(f"  Before dropout (t=0.09s): V(POSITION)={pos_node[np.searchsorted(t,0.09)]:+.3f}V, V(ERROR)={err_node[np.searchsorted(t,0.09)]:+.3f}V")
print(f"  During 5ms dropout: V(POSITION)={pos_node[sel_drop].mean():+.3f}V, V(ERROR)={err_node[sel_drop].mean():+.3f}V, V(DRIVE) peak={drv_node[sel_drop].max():+.2f}V")
print(f"  Slider mechanical excursion V(pos): from {real_pos[np.searchsorted(t,0.09)]:+.3f}V to peak {real_pos.max():+.3f}V (jump of {(real_pos.max()-real_pos[np.searchsorted(t,0.09)])/0.193:.2f} mm)")

print("\n=== 6. Abuse: Single rail powered (+15V on, -15V_IN open/floating) ===")
lines = D.lines(dict(base_sw, SW2=1), {"RV2": 0.0, "RV3": 231e3, "RV4": 1e6}, source="dc 5")
lines = [l for l in lines if not l.startswith("Vneg ") and not l.startswith("Rneg ")]
lines.append(f"Rneg_open {D.pin('J6', 3)} 0 1e9")
ng = pid_sim.run(lines, 0.2)
v_m15 = ng.vec("v(" + pid_sim.spice_name("-15V") + ")")[-1]
v_p15 = ng.vec("v(" + pid_sim.spice_name("+15V") + ")")[-1]
print(f"  +15V on, -15V_IN open (TARGET=5V): V(+15V)={v_p15:+.2f}V, V(-15V)={v_m15:+.2f}V (C12 reverse voltage = {v_m15:+.2f}V!)")
