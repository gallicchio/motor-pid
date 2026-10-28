import math, os, sys
sys.path.insert(0, "scripts")
import pcbnew
import layout as L

board = pcbnew.LoadBoard("hardware/motorpid.kicad_pcb")
tomm = pcbnew.ToMM

zones = list(board.Zones())
print(f"Total zones: {len(zones)}")
for z in zones:
    net = z.GetNetname()
    layer = z.GetLayerName()
    ps = z.GetFilledPolysList(z.GetLayer())
    print(f"  Zone net={net} layer={layer} outlines={ps.OutlineCount()}")

# Check via hits on Q2 pour (-15V) and Q1 pour (+15V)
q2_zone = [z for z in zones if z.GetNetname() == "-15V"][0]
q1_zone = [z for z in zones if z.GetNetname() == "+15V"][0]
gnd_zone = [z for z in zones if z.GetNetname() == "GND"][0]

for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        vx, vy = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        net = t.GetNetname()
        if net == "-15V" and vx > 140 and vy > 60:
            hit = q2_zone.HitTestFilledArea(pcbnew.F_Cu, t.GetPosition(), 0)
            print(f"  -15V via at ({vx:.2f}, {vy:.2f}) in Q2 F.Cu pour: {hit}")

# Check clearances to mounting holes MH1-MH4 and BNC posts
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("MH"):
        mx, my = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
        # M3 screw head is ~5.5-6.0 mm diameter (radius 2.75-3.0 mm); M3 standoff is ~5-6 mm hex
        r_head = 3.2
        near = []
        for t in board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                tx, ty = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
                d = math.hypot(tx - mx, ty - my) - tomm(t.GetWidth())/2
                if d < r_head:
                    near.append(f"via {t.GetNetname()} at ({tx:.1f},{ty:.1f}) d={d:.2f}mm")
            else:
                a = (tomm(t.GetStart().x), tomm(t.GetStart().y))
                b = (tomm(t.GetEnd().x), tomm(t.GetEnd().y))
                # dist from (mx,my) to segment a-b
                dx, dy = b[0] - a[0], b[1] - a[1]
                L2 = dx*dx + dy*dy
                u = 0 if L2 < 1e-12 else max(0.0, min(1.0, ((mx-a[0])*dx + (my-a[1])*dy)/L2))
                d = math.hypot(mx - (a[0]+u*dx), my - (a[1]+u*dy)) - tomm(t.GetWidth())/2
                if d < r_head:
                    near.append(f"track {t.GetNetname()} ({t.GetLayerName()}) d={d:.2f}mm")
        print(f"  {ref} at ({mx:.1f}, {my:.1f}): items within {r_head}mm of center: {near}")
