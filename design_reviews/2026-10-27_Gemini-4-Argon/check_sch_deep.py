import os, sys, math
sys.path.insert(0, "design_reviews/2026-10-27_Gemini-4-Argon/project/scripts")
from sexp_parse import parse_file
import check_schematic as cs

sch_path = "hardware/motorpid.kicad_sch"
root = parse_file(sch_path)
W, H, items = cs.collect(sch_path)

for s in root.kids("symbol"):
    ref = next((p.atom(1) for p in s.kids("property") if p.atom(0) == "Reference"), "?")
    if not ref.startswith("#PWR"):
        continue
    for p in s.kids("property"):
        if p.atom(0) != "Value":
            continue
        if p.first("hide") is not None and p.first("hide").atom(0) == "yes":
            continue
        at = p.first("at")
        e = p.first("effects")
        f = e.first("font") if e else None
        size = float(f.first("size").atom(0)) if f and f.first("size") else 1.27
        box = cs.text_box(float(at.atom(0)), float(at.atom(1)), p.atom(1), size, "")
        items.append((f"{ref}.Value {p.atom(1)!r} at ({float(at.atom(0)):.1f},{float(at.atom(1)):.1f})", box))

print(f"Total text items including #PWR values: {len(items)}")
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        if cs.overlaps(items[i][1], items[j][1], slack=0.05):
            print(f"TEXT-TEXT OVERLAP: {items[i][0]} {tuple(round(v,1) for v in items[i][1])} <-> {items[j][0]} {tuple(round(v,1) for v in items[j][1])}")

wires = []
for w in root.kids("wire"):
    pts = list(w.first("pts").kids("xy"))
    if len(pts) >= 2:
        wires.append(("wire", float(pts[0].atom(0)), float(pts[0].atom(1)),
                      float(pts[1].atom(0)), float(pts[1].atom(1))))

for pl in root.kids("polyline"):
    pts = list(pl.first("pts").kids("xy"))
    for a, b in zip(pts, pts[1:]):
        wires.append(("box_edge", float(a.atom(0)), float(a.atom(1)),
                      float(b.atom(0)), float(b.atom(1))))

def seg_intersects_box(x1, y1, x2, y2, box, pad=-0.15):
    bx0, by0, bx1, by1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    if bx0 >= bx1 or by0 >= by1:
        return False
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
        if abs(p) < 1e-9:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
    return t0 < t1

for name, box in items:
    if name.startswith("label "):
        continue
    for kind, x1, y1, x2, y2 in wires:
        if seg_intersects_box(x1, y1, x2, y2, box, pad=-0.2):
            print(f"TEXT-{kind.upper()} COLLISION: {name} {tuple(round(v,1) for v in box)} crossed by {kind} ({x1:.1f},{y1:.1f})-({x2:.1f},{y2:.1f})")

tb = root.first("title_block")
if tb:
    for k in tb.kids():
        txt = str(k.atoms()[-1]) if k.atoms() else ""
        print(f"Title block {k.tag} {k.atoms()[:-1]}: len={len(txt)} chars (~{len(txt)*1.5*0.92:.1f} mm at 1.5mm): {txt!r}")
