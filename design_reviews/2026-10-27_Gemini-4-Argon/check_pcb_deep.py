import math, os, sys
sys.path.insert(0, "scripts")
import pcbnew
import layout as L

board = pcbnew.LoadBoard("hardware/motorpid.kicad_pcb")
tomm = pcbnew.ToMM

def bbox_mm(item):
    bb = item.GetBoundingBox()
    return (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()))

# 1. Collect all visible silkscreen text items on F.SilkS and B.SilkS
texts_f, texts_b = [], []
for d in board.GetDrawings():
    if isinstance(d, pcbnew.PCB_TEXT):
        layer = d.GetLayer()
        if layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            sz = (tomm(d.GetTextSize().x), tomm(d.GetTextSize().y))
            th = tomm(d.GetTextThickness())
            pos = (tomm(d.GetPosition().x), tomm(d.GetPosition().y))
            entry = (f"TEXT {d.GetText()!r} at ({pos[0]:.1f},{pos[1]:.1f})", bbox_mm(d), sz, th, pos, d.GetText())
            (texts_f if layer == pcbnew.F_SilkS else texts_b).append(entry)

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for f in fp.GetFields():
        if not f.IsVisible():
            continue
        layer = f.GetLayer()
        if layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            sz = (tomm(f.GetTextSize().x), tomm(f.GetTextSize().y))
            th = tomm(f.GetTextThickness())
            pos = (tomm(f.GetPosition().x), tomm(f.GetPosition().y))
            entry = (f"{ref}.{f.GetName()} {f.GetText()!r} at ({pos[0]:.1f},{pos[1]:.1f})", bbox_mm(f), sz, th, pos, f.GetText())
            (texts_f if layer == pcbnew.F_SilkS else texts_b).append(entry)

print(f"F.SilkS texts: {len(texts_f)}, B.SilkS texts: {len(texts_b)}")

# Check min text size and thickness
for side, tlist in (("F.SilkS", texts_f), ("B.SilkS", texts_b)):
    for name, bb, sz, th, pos, raw in tlist:
        if min(sz) < 0.79 or th < 0.149:
            print(f"SMALL TEXT on {side}: {name} size={sz} thick={th}")

# Check text-to-text overlaps on F.SilkS and B.SilkS (using tight glyph box: shrink pcbnew bbox slightly for stroke width/margin)
def boxes_overlap(a, b, shrink=0.15):
    return not (a[2] - shrink <= b[0] + shrink or b[2] - shrink <= a[0] + shrink or
                a[3] - shrink <= b[1] + shrink or b[3] - shrink <= a[1] + shrink)

for side, tlist in (("F.SilkS", texts_f), ("B.SilkS", texts_b)):
    for i in range(len(tlist)):
        for j in range(i + 1, len(tlist)):
            if boxes_overlap(tlist[i][1], tlist[j][1], shrink=0.18):
                print(f"SILK TEXT-TEXT OVERLAP ({side}): {tlist[i][0]} {tuple(round(x,2) for x in tlist[i][1])} <-> {tlist[j][0]} {tuple(round(x,2) for x in tlist[j][1])}")

# 2. Check dashed POSITION line (y=105, x=46, etc.) vs front silkscreen wires, boxes, pads, and texts
pos_segs = [((124.0, 105.0), (46.0, 105.0)),
            ((46.0, 105.0), (46.0, 64.0)),
            ((46.0, 64.0), (41.75, 64.0)),
            ((46.0, 105.0), (12.0, 105.0)),
            ((12.0, 105.0), (12.0, 83.0))]

def seg_intersects_box(a, b, box, pad=-0.1):
    x1, y1 = a; x2, y2 = b
    bx0, by0, bx1, by1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    if bx0 >= bx1 or by0 >= by1:
        return False
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
        if abs(p) < 1e-9:
            if q < 0: return False
        else:
            r = q / p
            if p < 0: t0 = max(t0, r)
            else: t1 = min(t1, r)
    return t0 < t1

print("\n=== Checking dashed /POSITION back line on F.SilkS ===")
for a, b in pos_segs:
    for name, bb, sz, th, pos, raw in texts_f:
        if seg_intersects_box(a, b, bb, pad=-0.15):
            print(f"  /POSITION dashed segment {a}-{b} hits {name} bbox={tuple(round(v,2) for v in bb)}")
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith(("TP", "MH")): continue
        poly = fp.GetCourtyard(pcbnew.F_CrtYd)
        if poly.OutlineCount():
            cbb = poly.BBox()
            cbox = (tomm(cbb.GetLeft()), tomm(cbb.GetTop()), tomm(cbb.GetRight()), tomm(cbb.GetBottom()))
            if seg_intersects_box(a, b, cbox, pad=-0.1):
                print(f"  /POSITION dashed segment {a}-{b} runs through {ref} courtyard {tuple(round(v,2) for v in cbox)}")

# 3. Check if any component courtyard or text sits on a dashed stage BOX edge
print("\n=== Checking stage BOXES edges against components and texts ===")
for x0, y0, x1, y1, titles in L.BOXES:
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    bname = titles[0][0] if titles else f"({x0},{y0})-({x1},{y1})"
    for ea, eb in edges:
        for name, bb, sz, th, pos, raw in texts_f:
            if seg_intersects_box(ea, eb, bb, pad=-0.2):
                print(f"  BOX {bname} edge {ea}-{eb} crosses text {name} {tuple(round(v,2) for v in bb)}")
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            if ref.startswith("MH"): continue
            poly = fp.GetCourtyard(pcbnew.F_CrtYd)
            if poly.OutlineCount():
                cbb = poly.BBox()
                cbox = (tomm(cbb.GetLeft()), tomm(cbb.GetTop()), tomm(cbb.GetRight()), tomm(cbb.GetBottom()))
                if seg_intersects_box(ea, eb, cbox, pad=-0.2):
                    print(f"  BOX {bname} edge {ea}-{eb} crosses footprint {ref} courtyard {tuple(round(v,2) for v in cbox)}")
