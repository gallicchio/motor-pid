import math, os, sys
sys.path.insert(0, "scripts")
import pcbnew
import layout as L

board = pcbnew.LoadBoard("hardware/motorpid.kicad_pcb")
tomm = pcbnew.ToMM

def tight_text_box(t):
    bb = t.GetBoundingBox()
    # pcbnew's GetBoundingBox includes stroke thickness and descender margin; shrink by 0.15 mm
    return (tomm(bb.GetLeft()) + 0.15, tomm(bb.GetTop()) + 0.15,
            tomm(bb.GetRight()) - 0.15, tomm(bb.GetBottom()) - 0.15)

texts_f, texts_b = [], []
for d in board.GetDrawings():
    if isinstance(d, pcbnew.PCB_TEXT):
        layer = d.GetLayer()
        if layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            pos = (tomm(d.GetPosition().x), tomm(d.GetPosition().y))
            (texts_f if layer == pcbnew.F_SilkS else texts_b).append(
                (f"TEXT {d.GetText()!r} at ({pos[0]:.1f},{pos[1]:.1f})", tight_text_box(d)))

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for f in fp.GetFields():
        if not f.IsVisible():
            continue
        layer = f.GetLayer()
        if layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            pos = (tomm(f.GetPosition().x), tomm(f.GetPosition().y))
            (texts_f if layer == pcbnew.F_SilkS else texts_b).append(
                (f"{ref}.{f.GetName()} {f.GetText()!r} at ({pos[0]:.1f},{pos[1]:.1f})", tight_text_box(f)))

def seg_intersects_box(a, b, box):
    x1, y1 = a; x2, y2 = b
    bx0, by0, bx1, by1 = box
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

# Collect all F.SilkS segments (both board drawings and footprint graphics)
segs_f = []
for d in board.GetDrawings():
    if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() == pcbnew.F_SilkS:
        sh = d.GetShape()
        if sh == pcbnew.SHAPE_T_SEGMENT:
            a = (tomm(d.GetStart().x), tomm(d.GetStart().y))
            b = (tomm(d.GetEnd().x), tomm(d.GetEnd().y))
            w = tomm(d.GetWidth())
            segs_f.append(("board_seg", a, b, w))

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for d in fp.GraphicalItems():
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() == pcbnew.F_SilkS:
            if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                a = (tomm(d.GetStart().x), tomm(d.GetStart().y))
                b = (tomm(d.GetEnd().x), tomm(d.GetEnd().y))
                w = tomm(d.GetWidth())
                segs_f.append((f"{ref}_seg", a, b, w))

print(f"Checking {len(segs_f)} F.SilkS segments against {len(texts_f)} F.SilkS texts:")
hits = 0
for kind, a, b, w in segs_f:
    for tname, tbox in texts_f:
        if seg_intersects_box(a, b, tbox):
            print(f"  SILK LINE-TEXT HIT: {kind} ({a[0]:.2f},{a[1]:.2f})-({b[0]:.2f},{b[1]:.2f}) w={w:.2f} hits {tname} {tuple(round(v,2) for v in tbox)}")
            hits += 1
print(f"Total F.SilkS line-text hits: {hits}")
