import math, os, sys
sys.path.insert(0, "scripts")
import pcbnew
import gen_pcb
import layout as L

b = gen_pcb.Board("out/motorpid.net", "/tmp/dummy.kicad_pcb")
b.place()
b.wires()
b.keepouts()

# Check all front segments for crossings and T-junctions
front = [sg for sg in b.segments if sg[3] != pcbnew.B_Cu]
count = {}
for (net, a, c, layer) in front:
    for e in (a, c):
        k = (net, round(e[0], 2), round(e[1], 2))
        count[k] = count.get(k, 0) + 1
for (net, a, c, layer) in front:
    if net == "GND":
        continue
    for e in (a, c):
        for (n2, p, q, l2) in front:
            if n2 != net or (p, q) == (a, c):
                continue
            if b._interior(e, p, q):
                k = (net, round(e[0], 2), round(e[1], 2))
                count[k] = max(count[k], 3)

print("=== 3+ way wire junctions on F.Cu ===")
for (net, x, y), n in sorted(count.items()):
    if net != "GND" and n >= 3:
        on_p = b._on_pad(x, y)
        # Find which pad if on_p
        near_pads = [k for k, p in b.pads.items()
                     if p["x0"] - 0.55 <= x <= p["x1"] + 0.55 and p["y0"] - 0.55 <= y <= p["y1"] + 0.55]
        print(f"  {net:15s} at ({x:6.2f}, {y:6.2f}) deg={n} dot={not on_p} near_pads={near_pads}")

# Also check if any two front segments cross each other in their interiors!
def seg_cross(a1, a2, b1, b2):
    # axis-aligned or general segment intersection
    x1, y1 = a1; x2, y2 = a2
    x3, y3 = b1; x4, y4 = b2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-6:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    if 0.01 < t < 0.99 and 0.01 < u < 0.99:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None

print("\n=== Interior crossings of front segments ===")
for i in range(len(front)):
    for j in range(i + 1, len(front)):
        n1, a1, a2, _ = front[i]
        n2, b1, b2, _ = front[j]
        pt = seg_cross(a1, a2, b1, b2)
        if pt:
            print(f"  CROSSING: {n1} {a1}-{a2} crosses {n2} {b1}-{b2} at ({pt[0]:.2f}, {pt[1]:.2f})")

# Check where the dashed /POSITION back wire crosses front wires and footprint silkscreen outlines!
print("\n=== Crossings of dashed /POSITION back segments with front wires ===")
back_pos = [sg for sg in b.segments if sg[3] == pcbnew.B_Cu and sg[0] in L.DASHED_BACK]
for (_, a1, a2, _) in back_pos:
    for (n2, b1, b2, _) in front:
        pt = seg_cross(a1, a2, b1, b2)
        if pt:
            print(f"  /POSITION dashed {a1}-{a2} crosses front wire {n2} {b1}-{b2} at ({pt[0]:.2f}, {pt[1]:.2f})")
