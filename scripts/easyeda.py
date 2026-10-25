#!/usr/bin/env python3
"""Fetch the land pattern JLCPCB will place a part with, from EasyEDA.

    python3 scripts/easyeda.py C474882 [C...]      print pads and holes in mm

The same endpoint and parser as gps-gh-adapters/mfg/footprint_check.py, which
was written for ECP5-2ADC-2DAC; only the cache location differs.  The cache is
gitignored (their data, not ours) and refetched when a month old.
"""
import datetime, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "easyeda_cache.json")
URL = "https://easyeda.com/api/products/%s/svgs"
MAX_AGE_H = 24 * 30
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")
UNIT = 0.254                  # EasyEDA canvas unit: 10 mil, in mm
ORIGIN = 4000.0, 3000.0


def _load():
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            pass
    return {}


_cache = _load()


def _save():
    tmp = CACHE + ".tmp"
    json.dump(_cache, open(tmp, "w", encoding="utf-8"), indent=1, sort_keys=True)
    os.replace(tmp, CACHE)


def svgs(code, refresh=False):
    ent = _cache.get(code)
    if ent and not refresh and (time.time() - ent["fetched_epoch"]) / 3600.0 < MAX_AGE_H:
        return ent["result"], ent["fetched"]
    req = urllib.request.Request(URL % code, headers={
        "User-Agent": UA, "Accept": "application/json", "Referer": "https://easyeda.com/"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read().decode("utf-8", "replace"))
            if not d.get("success"):
                raise RuntimeError("easyeda said no for %s" % code)
            now = datetime.datetime.now().astimezone()
            _cache[code] = dict(result=d["result"], fetched=now.isoformat(timespec="seconds"),
                                fetched_epoch=time.time())
            _save()
            time.sleep(0.35)
            return d["result"], _cache[code]["fetched"]
        except Exception as e:  # noqa
            last = e
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("cannot fetch footprint for %s: %s" % (code, last))


def _attrs(tag):
    return {k: v for k, v in re.findall(r'([\w-]+)\s*=\s*"([^"]*)"', tag)}


def land_pattern(code, refresh=False):
    """{package, origin, pads[], holes[], silk[]} in mm, footprint-local, y down."""
    result, ts = svgs(code, refresh)
    body = None
    for r in result:
        b = r.get("svg", "").split("</style>", 1)[-1]
        if 'c_partid="part_pad"' in b or 'c_partid="part_hole"' in b:
            body = b
            break
    if body is None:
        return None, ts
    top = re.search(r"<g [^>]*c_origin=\"([-\d.]+),([-\d.]+)\"[^>]*>", body)
    ox, oy = ((float(top.group(1)), float(top.group(2))) if top else ORIGIN)
    pkg = re.search(r"package`([^`]*)`", body)
    pads, holes = [], []
    for m in re.finditer(r"<g ([^>]*c_partid=\"part_(?:pad|hole)\"[^>]*)>", body):
        a = _attrs(m.group(1))
        cx, cy = a.get("c_origin", "0,0").split(",")
        x = (float(cx) - ox) * UNIT
        y = (float(cy) - oy) * UNIT
        if a.get("c_partid") == "part_hole":
            c = re.search(r"<circle[^>]*r=\"([\d.]+)\"", body[m.end():])
            holes.append(dict(x=x, y=y, d=2 * float(c.group(1)) * UNIT if c else 0.0))
            continue
        h = re.search(r"<circle[^>]*c_padhole=\"1\"[^>]*r=\"([\d.]+)\"", body[m.end():m.end() + 800])
        pads.append(dict(number=a.get("number", ""), layer=int(a.get("layerid") or 0),
                         plated=a.get("plated", "Y") == "Y", x=x, y=y,
                         w=float(a.get("c_width") or 0) * UNIT, h=float(a.get("c_height") or 0) * UNIT,
                         rot=float(a.get("c_rotation") or 0), shape=a.get("c_shape", "?"),
                         drill=2 * float(h.group(1)) * UNIT if h else 0.0))
    # silkscreen outline extent (layerid 3 = top silk in EasyEDA), for the body direction
    xs, ys = [], []
    for m in re.finditer(r"<(?:polyline|path|rect|circle)[^>]*layerid=\"3\"[^>]*>", body):
        for px, py in re.findall(r"([-\d.]+)[, ]([-\d.]+)", m.group(0)):
            xs.append((float(px) - ox) * UNIT); ys.append((float(py) - oy) * UNIT)
    silk = (min(xs), min(ys), max(xs), max(ys)) if xs else None
    return dict(package=pkg.group(1) if pkg else "?", origin=(ox, oy), pads=pads, holes=holes,
                silk=silk), ts


if __name__ == "__main__":
    for code in [a for a in sys.argv[1:] if not a.startswith("-")]:
        lp, ts = land_pattern(code, refresh="--refresh" in sys.argv)
        if lp is None:
            print(code, "no land pattern"); continue
        print(f"{code}  package {lp['package']}  origin {lp['origin']}  silk {lp['silk']}  ({ts})")
        for p in lp["pads"]:
            print(f"   pad {p['number']:>3} at ({p['x']:7.3f},{p['y']:7.3f}) {p['w']:.2f}x{p['h']:.2f} "
                  f"{p['shape']} rot {p['rot']:.0f} drill {p['drill']:.2f} layer {p['layer']}")
        for h in lp["holes"]:
            print(f"   HOLE at ({h['x']:7.3f},{h['y']:7.3f}) d {h['d']:.2f}")
